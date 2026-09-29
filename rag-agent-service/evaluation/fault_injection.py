import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent.agent_harness import AgentState
from agent.agent_runner import _decode_tool_arguments, _execute_tool_with_retry
from evaluation.agent_evaluator import (
    compute_citation_validity,
    compute_no_answer_accuracy,
    compute_required_fact_accuracy,
)
from runtime.checkpoint_store import CheckpointStore


def _result_record(case_id: str, fault: str, passed: bool, **details) -> Dict[str, Any]:
    return {"id": case_id, "fault": fault, "passed": passed, **details}


def run_fault_injection(output_path: Optional[Path] = None) -> Dict[str, Any]:
    cases: List[Dict[str, Any]] = []

    for index in range(1, 5):
        calls = {"count": 0}
        def transient(tool_name, arguments, calls=calls):
            calls["count"] += 1
            if calls["count"] == 1:
                raise TimeoutError("injected first-attempt timeout")
            return ["spinetoram"]
        state = AgentState(f"retry-{index}")
        result = _execute_tool_with_retry(
            state, "query_active_substance", {"pesticide_name": "Sparta"},
            execute_fn=transient,
        )
        passed = result == ["spinetoram"] and calls["count"] == 2 and state.tool_history[-1]["retry_count"] == 1
        cases.append(_result_record(f"fi{index:03d}", "transient_timeout", passed, retry_applicable=True, recovered=passed, detected=True, calls=calls["count"]))

    for index in range(5, 7):
        calls = {"count": 0}
        def permanent(tool_name, arguments, calls=calls):
            calls["count"] += 1
            raise ConnectionError("injected permanent failure")
        state = AgentState(f"permanent-{index}")
        detected = False
        try:
            _execute_tool_with_retry(state, "hybrid_rag_query", {"question": "test"}, execute_fn=permanent)
        except RuntimeError:
            detected = state.status == "FAILED" and calls["count"] == 2
        cases.append(_result_record(f"fi{index:03d}", "permanent_tool_failure", detected, retry_applicable=True, recovered=False, detected=detected, calls=calls["count"]))

    calls = {"kg": 0, "rag": 0}
    state = AgentState("KG succeeds and RAG fails")
    def kg_then_rag(tool_name, arguments):
        if tool_name == "query_active_substance":
            calls["kg"] += 1
            return ["spinetoram"]
        calls["rag"] += 1
        raise TimeoutError("injected RAG outage")
    _execute_tool_with_retry(state, "query_active_substance", {"pesticide_name": "Sparta"}, execute_fn=kg_then_rag)
    detected = False
    try:
        _execute_tool_with_retry(state, "hybrid_rag_query", {"question": "mode of action of spinetoram"}, execute_fn=kg_then_rag)
    except RuntimeError:
        detected = calls == {"kg": 1, "rag": 2}
    cases.append(_result_record("fi007", "kg_success_rag_failure", detected, recovered=False, detected=detected, duplicate_executions=0, calls=calls))

    for index in range(8, 12):
        calls = {"kg": 0, "rag": 0}
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "checkpoint.sqlite3"
            first_store = CheckpointStore(db_path)
            state = AgentState(f"resume-{index}")
            state.step_count = 1
            def executor(tool_name, arguments, calls=calls):
                calls["kg" if tool_name == "query_active_substance" else "rag"] += 1
                return ["spinetoram"] if tool_name == "query_active_substance" else {"answer": "mode [D1]", "evidence": [{"label": "D1", "id": "spinetoram", "name": "spinetoram"}]}
            kg_args = {"pesticide_name": "Sparta"}
            _execute_tool_with_retry(state, "query_active_substance", kg_args, first_store, executor)
            task_id = state.task_id
            first_store.close()
            resumed_store = CheckpointStore(db_path)
            resumed = resumed_store.load(task_id)
            resumed.record_resume()
            _execute_tool_with_retry(resumed, "query_active_substance", kg_args, resumed_store, executor)
            resumed.step_count = 2
            _execute_tool_with_retry(resumed, "hybrid_rag_query", {"question": "mode of action of spinetoram"}, resumed_store, executor)
            passed = calls == {"kg": 1, "rag": 1} and any(item.get("reused") and item.get("resumed") for item in resumed.tool_history)
            cases.append(_result_record(f"fi{index:03d}", "checkpoint_resume", passed, resume_applicable=True, recovered=passed, detected=True, duplicate_executions=max(0, calls["kg"] - 1), calls=calls, trace=resumed.tool_history))
            resumed_store.close()

    malformed_detected = False
    try:
        _decode_tool_arguments("query_active_substance", "{not-json")
    except ValueError:
        malformed_detected = True
    cases.append(_result_record("fi012", "malformed_tool_arguments", malformed_detected, recovered=False, detected=malformed_detected))

    invalid = compute_citation_validity("claim [D9]", [{"tool": "hybrid_rag_query", "result": {"evidence": [{"label": "D1"}]}}], True)
    cases.append(_result_record("fi013", "invalid_citation", not invalid["passed"], recovered=False, detected=not invalid["passed"]))

    no_answer_result = {"answer": "The current knowledge base does not contain enough evidence to answer this question.", "execution_state": {"status": "NO_ANSWER", "no_answer_reason": "empty_tool_result"}}
    no_answer = compute_no_answer_accuracy(no_answer_result, True)
    cases.append(_result_record("fi014", "empty_tool_result", no_answer["passed"], recovered=True, detected=no_answer["passed"]))

    required = compute_required_fact_accuracy("Boscalid affects complex II.", ["succinate dehydrogenase"])
    cases.append(_result_record("fi015", "missing_required_fact", not required["passed"], recovered=False, detected=not required["passed"]))

    retry_cases = [case for case in cases if case.get("retry_applicable")]
    resume_cases = [case for case in cases if case.get("resume_applicable")]
    recoverable = [case for case in cases if case["fault"] in {"transient_timeout", "checkpoint_resume", "empty_tool_result"}]
    duplicate_count = sum(case.get("duplicate_executions", 0) for case in cases)
    successful_tool_calls = sum(sum(case.get("calls", {}).values()) for case in cases if isinstance(case.get("calls"), dict))
    summary = {
        "num_cases": len(cases),
        "retry_success_rate": sum(case["passed"] for case in retry_cases) / len(retry_cases),
        "resume_success_rate": sum(case["passed"] for case in resume_cases) / len(resume_cases),
        "duplicate_successful_tool_execution_rate": duplicate_count / successful_tool_calls if successful_tool_calls else 0.0,
        "fault_recovery_rate": sum(case["passed"] for case in recoverable) / len(recoverable),
        "error_detection_rate": sum(bool(case.get("detected")) for case in cases) / len(cases),
    }
    payload = {"metadata": {"dataset_version": "agent-fault-v1", "normal_benchmark_metrics_included": False}, "summary": summary, "cases": cases}
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload
