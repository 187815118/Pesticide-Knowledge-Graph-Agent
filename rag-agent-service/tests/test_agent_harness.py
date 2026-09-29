import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import agent.agent_runner as agent_runner
from agent.agent_harness import AgentState
from evaluation.agent_eval_runner import run_evaluation
from evaluation.agent_evaluator import evaluate_agent_result
from evaluation.agent_evaluator import compute_required_fact_accuracy


def _rag_result(answer="spinetoram affects insect nerves. [D1]"):
    return {
        "answer": answer,
        "evidence": [
            {
                "label": "D1",
                "id": "active_substance:spinetoram",
                "name": "spinetoram",
                "source": "test-corpus",
                "retrieval_rank": 1,
            }
        ],
        "invalid_citations": [],
    }


def _multistep_item():
    return {
        "id": "smoke-1",
        "category": "kg_to_rag_multistep",
        "question": "What is the active substance of Sparta and its mode of action?",
        "expected_tools": ["query_active_substance", "hybrid_rag_query"],
        "expected_tool_sequence": ["query_active_substance", "hybrid_rag_query"],
        "expected_entities": ["Sparta", "spinetoram"],
        "propagation_entities": ["spinetoram"],
        "expected_keywords": ["insect nerves"],
        "requires_citation": True,
    }


def _multistep_result(rag_question="What is the mode of action of spinetoram?"):
    state = AgentState("What is the active substance of Sparta and its mode of action?")
    state.record_success(
        "query_active_substance",
        {"pesticide_name": "Sparta"},
        ["spinetoram"],
        latency_ms=1.0,
        attempts=1,
    )
    state.record_success(
        "hybrid_rag_query",
        {"question": rag_question},
        _rag_result(),
        latency_ms=2.0,
        attempts=1,
    )
    state.final_answer = (
        "Sparta's active substance is spinetoram; "
        "spinetoram affects insect nerves. [D1]"
    )
    state.status = "COMPLETED"
    return {
        "answer": state.final_answer,
        "tool_trace": state.tool_history,
        "execution_state": state.to_dict(),
    }


def test_agent_state_updates_entities_evidence_citations_and_trace():
    result = _multistep_result()
    state = result["execution_state"]
    assert "spinetoram" in state["resolved_entities"]
    assert state["evidence"][0]["label"] == "D1"
    assert state["citations"] == ["[D1]"]
    assert [item["step"] for item in result["tool_trace"]] == [1, 2]
    assert [item["status"] for item in result["tool_trace"]] == ["success", "success"]


def test_tool_retry_resumes_without_reexecuting_completed_tool(monkeypatch):
    calls = {"kg": 0, "rag": 0}

    def fake_execute(tool_name, arguments):
        if tool_name == "query_active_substance":
            calls["kg"] += 1
            return ["spinetoram"]
        calls["rag"] += 1
        if calls["rag"] == 1:
            raise TimeoutError("temporary RAG timeout")
        return _rag_result()

    monkeypatch.setattr(agent_runner, "execute_tool", fake_execute)
    monkeypatch.setattr(agent_runner, "TOOL_RETRY_DELAY_SECONDS", 0.0)
    state = AgentState("test")
    kg_args = {"pesticide_name": "Sparta"}
    agent_runner._execute_tool_with_retry(state, "query_active_substance", kg_args)
    agent_runner._execute_tool_with_retry(
        state,
        "hybrid_rag_query",
        {"question": "What is the mode of action of spinetoram?"},
    )
    agent_runner._execute_tool_with_retry(state, "query_active_substance", kg_args)

    assert calls == {"kg": 1, "rag": 2}
    assert state.tool_history[-1]["status"] == "reused"
    assert state.tool_history[-1]["attempts"] == 0


def test_permanent_tool_failure_is_traced_without_fake_result(monkeypatch):
    def always_fail(tool_name, arguments):
        raise ConnectionError("service unavailable")

    monkeypatch.setattr(agent_runner, "execute_tool", always_fail)
    monkeypatch.setattr(agent_runner, "TOOL_RETRY_DELAY_SECONDS", 0.0)
    state = AgentState("test")

    try:
        agent_runner._execute_tool_with_retry(
            state,
            "hybrid_rag_query",
            {"question": "What is the mode of action of spinetoram?"},
        )
    except RuntimeError as exc:
        assert "已尝试 2 次" in str(exc)
    else:
        raise AssertionError("permanent tool failure must raise RuntimeError")

    assert state.status == "FAILED"
    assert state.tool_history[-1]["status"] == "failed"
    assert state.tool_history[-1]["result"] is None
    assert state.tool_history[-1]["attempts"] == 2


def test_downstream_rag_arguments_are_grounded_with_latest_kg_entity():
    state = AgentState("test")
    state.record_success(
        "query_active_substance",
        {"pesticide_name": "Example Product"},
        ["resolved-ingredient"],
        latency_ms=1.0,
        attempts=1,
    )
    grounded = agent_runner._ground_tool_arguments(
        state,
        "hybrid_rag_query",
        {"question": "What is the mode of action of misspelled-ingredient?"},
    )
    assert "resolved-ingredient" in grounded["question"]

    unchanged = agent_runner._ground_tool_arguments(
        state,
        "hybrid_rag_query",
        {"question": "What is the mode of action of resolved-ingredient?"},
    )
    assert unchanged["question"].count("resolved-ingredient") == 1


def test_final_citations_are_restricted_to_observed_evidence():
    rag_state = AgentState("test")
    rag_state.record_success(
        "hybrid_rag_query",
        {"question": "test"},
        _rag_result(),
        latency_ms=1.0,
        attempts=1,
    )
    restored = agent_runner._ground_final_citations("Grounded claim.", rag_state)
    assert restored.endswith("[D1]")
    assert "[D9]" not in agent_runner._ground_final_citations(
        "Grounded claim [D1], invented claim [D9].", rag_state
    )

    kg_state = AgentState("test")
    kg_state.record_success(
        "query_active_substance",
        {"pesticide_name": "Example Product"},
        ["resolved-ingredient"],
        latency_ms=1.0,
        attempts=1,
    )
    assert "[D1]" not in agent_runner._ground_final_citations(
        "KG result [D1]", kg_state
    )


def test_single_tool_selection_evaluator():
    item = {
        "id": "single",
        "category": "single_kg_forward",
        "question": "What is the active substance of Sparta?",
        "expected_tools": ["query_active_substance"],
        "expected_entities": ["Sparta", "spinetoram"],
        "requires_citation": False,
    }
    result = {
        "answer": "Sparta's active substance is spinetoram.",
        "tool_trace": [
            {
                "tool": "query_active_substance",
                "arguments": {"pesticide_name": "Sparta"},
                "result": ["spinetoram"],
            }
        ],
    }
    evaluation = evaluate_agent_result(item, result)
    assert evaluation["tool_selection_accuracy"] == 1.0
    assert evaluation["tool_sequence_accuracy"] == 1.0
    assert evaluation["task_completed_rule"]


def test_multistep_sequence_and_entity_propagation_evaluator():
    correct = evaluate_agent_result(_multistep_item(), _multistep_result())
    assert correct["tool_sequence_accuracy"] == 1.0
    assert correct["entity_propagation"]["passed"]

    wrong_order_result = _multistep_result()
    wrong_order_result["tool_trace"].reverse()
    wrong_order = evaluate_agent_result(_multistep_item(), wrong_order_result)
    assert wrong_order["tool_selection_accuracy"] == 1.0
    assert wrong_order["tool_sequence_accuracy"] == 0.0
    assert not wrong_order["task_completed_rule"]

    vague = evaluate_agent_result(
        _multistep_item(),
        _multistep_result("What is the mode of action of the active substance?"),
    )
    assert not vague["entity_propagation"]["passed"]
    assert not vague["task_completed_rule"]


def test_citation_evaluator_rejects_nonexistent_evidence_label():
    result = _multistep_result()
    result["answer"] = result["answer"].replace("[D1]", "[D9]")
    evaluation = evaluate_agent_result(_multistep_item(), result)
    assert evaluation["citation_presence"]["passed"]
    assert not evaluation["citation_validity"]["passed"]
    assert evaluation["citation_validity"]["invalid_citations"] == ["D9"]
    assert not evaluation["task_completed_rule"]


def test_required_fact_matching_normalizes_punctuation_but_not_words():
    matched = compute_required_fact_accuracy(
        "International Insecticide Resistance Action Committee (IRAC) Group 5.",
        ["IRAC Group 5"],
    )
    assert matched["passed"]

    missing = compute_required_fact_accuracy("IRAC Group 6", ["IRAC Group 5"])
    assert not missing["passed"]


def test_eval_harness_smoke_checkpoint(tmp_path):
    output_path = tmp_path / "agent_eval_results.json"
    payload = run_evaluation(
        [_multistep_item()],
        lambda question: _multistep_result(),
        output_path=output_path,
        retrieval_results_path=tmp_path / "missing-retrieval-results.json",
    )
    assert output_path.exists()
    assert payload["summary"]["num_cases"] == 1
    assert payload["summary"]["tool_selection_accuracy"] == 1.0
    assert payload["summary"]["entity_propagation_accuracy"] == 1.0
    assert payload["summary"]["citation_validity_accuracy"] == 1.0
    assert payload["summary"]["answer_accuracy"] == 1.0
