import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import agent.agent_runner as agent_runner
from agent.agent_harness import AgentState, FAILED, is_empty_tool_result, tool_call_key
from agent.tool_registry import TOOLS
from evaluation.agent_evaluator import evaluate_agent_result, validate_benchmark_schema
from evaluation.fault_injection import run_fault_injection
from runtime.checkpoint_store import CheckpointStore


class Function:
    def __init__(self, name, arguments):
        self.name, self.arguments = name, json.dumps(arguments)


class ToolCall:
    type = "function"
    def __init__(self, call_id, name, arguments):
        self.id, self.function = call_id, Function(name, arguments)


class Message:
    def __init__(self, content="", tool_calls=None):
        self.content, self.tool_calls = content, tool_calls
    def model_dump(self, exclude_none=True):
        data = {"role": "assistant", "content": self.content}
        if self.tool_calls:
            data["tool_calls"] = [{"id": call.id, "type": "function", "function": {"name": call.function.name, "arguments": call.function.arguments}} for call in self.tool_calls]
        return data


class Response:
    def __init__(self, message):
        self.choices = [type("Choice", (), {"message": message})()]


class ResumeCompletions:
    def __init__(self):
        self.count = 0
    def create(self, **kwargs):
        self.count += 1
        if self.count == 1:
            return Response(Message(tool_calls=[ToolCall("duplicate", "query_active_substance", {"pesticide_name": "Sparta"})]))
        if self.count == 2:
            return Response(Message(tool_calls=[ToolCall("rag", "hybrid_rag_query", {"question": "mode of action of spinetoram"})]))
        if self.count == 3:
            return Response(Message("candidate [D1]"))
        return Response(Message("Sparta contains spinetoram; its mode is grounded. [D1]"))


class ResumeClient:
    def __init__(self):
        self.chat = type("Chat", (), {"completions": ResumeCompletions()})()


def rag_result():
    return {"answer": "grounded mode [D1]", "evidence": [{"label": "D1", "id": "active_substance:spinetoram", "name": "spinetoram", "source": "test", "retrieval_rank": 1}], "invalid_citations": []}


def test_agent_state_serialization_round_trip_preserves_completed_cache():
    state = AgentState("question", task_id="task-1")
    state.step_count = 1
    state.record_success("query_active_substance", {"pesticide_name": "Sparta"}, ["spinetoram"], 1.0, 1)
    restored = AgentState.from_dict(state.to_dict())
    assert restored.task_id == "task-1"
    assert restored.completed_result("query_active_substance", {"pesticide_name": "Sparta"}) == ["spinetoram"]
    assert tool_call_key("x", {"b": 2, "a": 1}) == tool_call_key("x", {"a": 1, "b": 2})


def test_checkpoint_save_load_and_version(tmp_path):
    store = CheckpointStore(tmp_path / "state.sqlite3")
    state = AgentState("question", task_id="task-checkpoint")
    assert store.save(state) == 1
    state.step_count = 1
    assert store.save(state) == 2
    loaded = store.load(state.task_id)
    assert loaded.step_count == 1 and loaded.checkpoint_version == 2


def test_process_restart_resume_does_not_repeat_successful_kg(monkeypatch, tmp_path):
    db = tmp_path / "resume.sqlite3"
    first_store = CheckpointStore(db)
    calls = {"kg": 0, "rag": 0}
    def execute(tool, arguments):
        if tool == "query_active_substance":
            calls["kg"] += 1
            return ["spinetoram"]
        calls["rag"] += 1
        return rag_result()
    state = AgentState("What is the active substance of Sparta and its mode?", task_id="resume-task")
    state.step_count = 1
    agent_runner._execute_tool_with_retry(state, "query_active_substance", {"pesticide_name": "Sparta"}, first_store, execute)
    first_store.close()

    second_store = CheckpointStore(db)
    monkeypatch.setattr(agent_runner, "_make_client", ResumeClient)
    monkeypatch.setattr(agent_runner, "execute_tool", execute)
    monkeypatch.setattr(agent_runner, "_build_openai_tools_schema", lambda: [])
    result = agent_runner.resume_agent("resume-task", second_store)
    assert calls == {"kg": 1, "rag": 1}
    assert any(event["event_type"] == "task_resumed" for event in result["tool_trace"])
    reused = [event for event in result["tool_trace"] if event.get("tool") == "query_active_substance" and event.get("reused")]
    assert reused and reused[-1]["resumed"]
    assert "[D1]" in result["answer"]


def test_retry_and_permanent_failure_trace(monkeypatch):
    monkeypatch.setattr(agent_runner, "TOOL_RETRY_DELAY_SECONDS", 0.0)
    calls = {"count": 0}
    def transient(tool, arguments):
        calls["count"] += 1
        if calls["count"] == 1:
            raise TimeoutError("once")
        return ["ok"]
    state = AgentState("retry")
    assert agent_runner._execute_tool_with_retry(state, "query_active_substance", {"pesticide_name": "x"}, execute_fn=transient) == ["ok"]
    assert state.tool_history[-1]["retry_count"] == 1
    with pytest.raises(RuntimeError):
        agent_runner._execute_tool_with_retry(AgentState("fail"), "query_active_substance", {"pesticide_name": "x"}, execute_fn=lambda *_: (_ for _ in ()).throw(ConnectionError("down")))


def test_new_tools_registered_and_entity_grounding():
    for name in ("query_chemical_classes", "query_target_sites", "query_modes_of_action"):
        assert name in TOOLS
        assert TOOLS[name]["parameters"]["required"] == ["active_substance_name"]
    state = AgentState("question")
    state.record_success("query_active_substance", {"pesticide_name": "Product"}, ["resolved-active"], 1.0, 1)
    grounded = agent_runner._ground_tool_arguments(state, "query_target_sites", {"active_substance_name": "that substance"})
    assert grounded == {"active_substance_name": "resolved-active"}


def test_synthesis_state_is_compact_but_keeps_kg_and_rag_facts():
    state = AgentState("question")
    state.record_success("query_active_substance", {"pesticide_name": "Sparta"}, ["spinetoram"], 1.0, 1)
    state.record_success("hybrid_rag_query", {"question": "mode of action of spinetoram"}, rag_result(), 1.0, 1)
    compact = agent_runner._compact_execution_state_for_synthesis(state)
    serialized = json.dumps(compact)
    assert "spinetoram" in serialized and "grounded mode [D1]" in serialized
    assert "tool_history" not in compact and "completed_tool_calls" not in compact


def test_dispatch_guard_separates_text_mechanism_from_structured_kg():
    text_state = AgentState("What complex II target is described for boscalid?")
    tool, arguments, reason = agent_runner._apply_tool_dispatch_guard(
        text_state, "query_target_sites", {"active_substance_name": "boscalid"}
    )
    assert tool == "hybrid_rag_query" and "boscalid" in arguments["question"]
    assert reason == "text_knowledge_requires_hybrid_rag"

    structured_state = AgentState(
        "According to the knowledge graph, what structured target site is linked to boscalid?"
    )
    tool, arguments, reason = agent_runner._apply_tool_dispatch_guard(
        structured_state, "query_target_sites", {"active_substance_name": "boscalid"}
    )
    assert tool == "query_target_sites" and reason is None


def test_final_entity_grounding_and_no_answer_trace():
    state = AgentState("How does acephate work?")
    state.record_success(
        "hybrid_rag_query", {"question": state.original_query},
        {"answer": "Claim [D1]", "evidence": [{"label": "D1", "id": "acephate", "name": "acephate"}]},
        1.0, 1,
    )
    grounded = agent_runner._ground_final_entities("Acephate inhibits AChE [D1].", state)
    assert "Grounded entities: acephate" in grounded
    state.record_no_answer("empty")
    assert state.tool_history[-1]["event_type"] == "no_answer"
    assert state.tool_history[-1]["failure_type"] == "EMPTY_OR_UNSUPPORTED"


def test_valid_grounded_citation_prevents_false_no_answer():
    result = {
        "answer": (
            "Retrieved evidence is insufficient, but glyphosate inhibits EPSPS [D1]."
        ),
        "evidence": [{"label": "D1", "id": "active_substance:glyphosate"}],
    }

    assert not is_empty_tool_result("hybrid_rag_query", result)
    result["answer"] = "Retrieved evidence is insufficient [D9]."
    assert is_empty_tool_result("hybrid_rag_query", result)


def test_no_answer_and_schema_evaluator():
    item = {"id": "na", "category": "no_answer", "question": "unknown", "expected_tools": ["query_active_substance"], "expected_entities": ["unknown"], "requires_citation": False, "requires_no_answer": True}
    result = {"answer": "The current knowledge base does not contain enough evidence to answer this question.", "tool_trace": [{"tool": "query_active_substance", "arguments": {"pesticide_name": "unknown"}, "result": []}], "execution_state": {"status": "NO_ANSWER"}}
    assert evaluate_agent_result(item, result)["task_completed_rule"]
    validate_benchmark_schema([item])
    with pytest.raises(ValueError):
        validate_benchmark_schema([{"id": "broken"}])


def test_fault_injection_harness_smoke(tmp_path, monkeypatch):
    monkeypatch.setattr(agent_runner, "TOOL_RETRY_DELAY_SECONDS", 0.0)
    payload = run_fault_injection(tmp_path / "fault.json")
    assert payload["summary"]["num_cases"] == 15
    assert payload["summary"]["resume_success_rate"] == 1.0
    assert payload["summary"]["duplicate_successful_tool_execution_rate"] == 0.0
    assert (tmp_path / "fault.json").exists()
