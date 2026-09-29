import json
import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

CITATION_PATTERN = re.compile(r"\[D[1-9]\d*\]")
RUNNING, FAILED, COMPLETED, NO_ANSWER = "RUNNING", "FAILED", "COMPLETED", "NO_ANSWER"


def tool_call_key(tool_name: str, arguments: Dict[str, Any]) -> str:
    normalized = json.dumps(arguments, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return f"{tool_name}:{normalized}"


def _append_unique(target: List[str], values: List[str]) -> None:
    for value in values:
        if value and value not in target:
            target.append(value)


def _strings(value: Any) -> List[str]:
    if isinstance(value, str):
        return [value]
    return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []


def extract_entities(tool: str, arguments: Dict[str, Any], result: Any) -> List[str]:
    entities: List[str] = []
    if tool.startswith("query_"):
        _append_unique(entities, [value for value in arguments.values() if isinstance(value, str)])
        _append_unique(entities, _strings(result))
    elif tool == "hybrid_rag_query" and isinstance(result, dict):
        evidence = [item for item in result.get("evidence", []) if isinstance(item, dict)]
        if evidence:
            _append_unique(entities, [evidence[0].get("name", "")])
    return entities


def extract_evidence(result: Any) -> List[Dict[str, Any]]:
    return [item for item in result.get("evidence", []) if isinstance(item, dict)] if isinstance(result, dict) else []


def extract_citations(result: Any) -> List[str]:
    return list(dict.fromkeys(CITATION_PATTERN.findall(result.get("answer", "") or ""))) if isinstance(result, dict) else []


def summarize_result(result: Any, max_chars: int = 500) -> str:
    text = str(result.get("answer", "")) if isinstance(result, dict) and "answer" in result else json.dumps(result, ensure_ascii=False, default=str)
    return text if len(text) <= max_chars else text[: max_chars - 3] + "..."


def is_empty_tool_result(tool: str, result: Any) -> bool:
    if result is None or result == [] or result == "":
        return True
    if tool == "hybrid_rag_query" and isinstance(result, dict):
        raw_answer = str(result.get("answer", "")).strip()
        answer = raw_answer.lower()
        evidence_labels = {
            str(item.get("label", ""))
            for item in result.get("evidence", [])
            if isinstance(item, dict)
        }
        cited_labels = {
            citation[1:-1]
            for citation in CITATION_PATTERN.findall(raw_answer)
        }
        factual_text = CITATION_PATTERN.sub("", raw_answer).strip()
        if evidence_labels.intersection(cited_labels) and len(factual_text) >= 20:
            return False
        markers = ("not enough evidence", "insufficient evidence", "evidence is insufficient", "does not provide", "does not include", "no information", "没有足够证据", "未提供")
        return not result.get("evidence") or not answer or any(marker in answer for marker in markers)
    return False


@dataclass
class AgentState:
    original_query: str
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    current_query: str = ""
    resolved_entities: List[str] = field(default_factory=list)
    tool_history: List[Dict[str, Any]] = field(default_factory=list)
    completed_tools: List[Dict[str, Any]] = field(default_factory=list)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    citations: List[str] = field(default_factory=list)
    step_count: int = 0
    final_answer: str = ""
    status: str = RUNNING
    observations: List[Dict[str, Any]] = field(default_factory=list)
    checkpoint_version: int = 0
    resumed: bool = False
    resumed_from_step: Optional[int] = None
    no_answer_reason: str = ""
    _completed_results: Dict[str, Any] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        self.current_query = self.current_query or self.original_query

    def has_completed_result(self, tool: str, arguments: Dict[str, Any]) -> bool:
        return tool_call_key(tool, arguments) in self._completed_results

    def completed_result(self, tool: str, arguments: Dict[str, Any]) -> Optional[Any]:
        return self._completed_results.get(tool_call_key(tool, arguments))

    def latest_active_substances(self) -> List[str]:
        for observation in reversed(self.observations):
            arguments = observation.get("arguments", {})
            if isinstance(arguments.get("active_substance_name"), str):
                return [arguments["active_substance_name"]]
            if observation.get("tool") == "query_active_substance" and _strings(observation.get("result")):
                return _strings(observation["result"])
        return []

    def latest_kg_result_entities(self) -> List[str]:
        return self.latest_active_substances()

    def record_success(self, tool: str, arguments: Dict[str, Any], result: Any, latency_ms: float, attempts: int, reused: bool = False, resumed: bool = False) -> Dict[str, Any]:
        key = tool_call_key(tool, arguments)
        entities, evidence, citations = extract_entities(tool, arguments, result), extract_evidence(result), extract_citations(result)
        trace_step = self.step_count or 1 + sum(bool(item.get("tool")) for item in self.tool_history)
        trace = {
            "task_id": self.task_id, "step": trace_step, "event_type": "tool_reused" if reused else "tool_success",
            "tool": tool, "arguments": arguments, "status": "reused" if reused else "success", "result": result,
            "result_summary": summarize_result(result), "extracted_entities": entities, "evidence": evidence, "citations": citations,
            "latency_ms": round(latency_ms, 3), "attempt": attempts, "attempts": attempts, "retry_count": max(0, attempts - 1),
            "retry": attempts > 1, "reused": reused, "resumed": resumed,
            "resumed_from_step": self.resumed_from_step if resumed else None, "checkpoint_version": self.checkpoint_version,
            "failure_type": None, "error": None,
        }
        self.tool_history.append(trace)
        if not reused:
            self.observations.append({"tool": tool, "arguments": arguments, "result": result})
            self._completed_results[key] = result
            self.completed_tools.append({"key": key, "tool": tool, "arguments": arguments, "result": result})
        _append_unique(self.resolved_entities, entities)
        for item in evidence:
            if not any((old.get("label"), old.get("id")) == (item.get("label"), item.get("id")) for old in self.evidence):
                self.evidence.append(item)
        _append_unique(self.citations, citations)
        if tool == "hybrid_rag_query":
            self.current_query = str(arguments.get("question", self.current_query))
        self.status = RUNNING
        return trace

    def record_failure(self, tool: str, arguments: Dict[str, Any], latency_ms: float, attempts: int, error: Exception) -> Dict[str, Any]:
        trace_step = self.step_count or 1 + sum(bool(item.get("tool")) for item in self.tool_history)
        trace = {
            "task_id": self.task_id, "step": trace_step, "event_type": "tool_failure", "tool": tool, "arguments": arguments,
            "status": "failed", "result": None, "result_summary": "", "extracted_entities": [], "evidence": [], "citations": [],
            "latency_ms": round(latency_ms, 3), "attempt": attempts, "attempts": attempts, "retry_count": max(0, attempts - 1),
            "retry": attempts > 1, "reused": False, "resumed": self.resumed, "resumed_from_step": self.resumed_from_step,
            "checkpoint_version": self.checkpoint_version, "failure_type": type(error).__name__, "error": f"{type(error).__name__}: {error}",
        }
        self.tool_history.append(trace)
        self.status = FAILED
        return trace

    def record_resume(self) -> Dict[str, Any]:
        self.resumed, self.resumed_from_step, self.status = True, self.step_count, RUNNING
        event = {
            "task_id": self.task_id, "step": self.step_count, "event_type": "task_resumed", "tool": "", "arguments": {},
            "status": "resumed", "result": None, "result_summary": "", "extracted_entities": [], "evidence": [], "citations": [],
            "latency_ms": 0.0, "attempt": 0, "attempts": 0, "retry_count": 0, "retry": False, "reused": False,
            "resumed": True, "resumed_from_step": self.resumed_from_step, "checkpoint_version": self.checkpoint_version,
            "failure_type": None, "error": None,
        }
        self.tool_history.append(event)
        return event

    def record_no_answer(self, reason: str) -> Dict[str, Any]:
        self.no_answer_reason, self.status = reason, NO_ANSWER
        event = {
            "task_id": self.task_id, "step": self.step_count, "event_type": "no_answer",
            "tool": "", "arguments": {}, "status": "no_answer", "result": None,
            "result_summary": reason, "extracted_entities": [], "evidence": [], "citations": [],
            "latency_ms": 0.0, "attempt": 0, "attempts": 0, "retry_count": 0,
            "retry": False, "reused": False, "resumed": self.resumed,
            "resumed_from_step": self.resumed_from_step, "checkpoint_version": self.checkpoint_version,
            "failure_type": "EMPTY_OR_UNSUPPORTED", "error": None,
        }
        self.tool_history.append(event)
        return event

    def all_observations_empty(self) -> bool:
        return bool(self.observations) and all(is_empty_tool_result(item.get("tool", ""), item.get("result")) for item in self.observations)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id, "user_question": self.original_query, "original_query": self.original_query,
            "current_query": self.current_query, "resolved_entities": self.resolved_entities, "tool_history": self.tool_history,
            "completed_tools": self.completed_tools, "completed_tool_calls": self.completed_tools, "evidence": self.evidence,
            "citations": self.citations, "step_count": self.step_count, "final_answer": self.final_answer, "status": self.status,
            "observations": self.observations, "checkpoint_version": self.checkpoint_version, "resumed": self.resumed,
            "resumed_from_step": self.resumed_from_step, "no_answer_reason": self.no_answer_reason,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "AgentState":
        completed = payload.get("completed_tool_calls") or payload.get("completed_tools", [])
        state = cls(
            original_query=payload.get("original_query") or payload.get("user_question", ""), task_id=payload.get("task_id") or str(uuid.uuid4()),
            current_query=payload.get("current_query", ""), resolved_entities=list(payload.get("resolved_entities", [])),
            tool_history=list(payload.get("tool_history", [])), completed_tools=list(completed), evidence=list(payload.get("evidence", [])),
            citations=list(payload.get("citations", [])), step_count=int(payload.get("step_count", 0)), final_answer=payload.get("final_answer", ""),
            status=payload.get("status", RUNNING).upper(), observations=list(payload.get("observations", [])),
            checkpoint_version=int(payload.get("checkpoint_version", 0)), resumed=bool(payload.get("resumed", False)),
            resumed_from_step=payload.get("resumed_from_step"), no_answer_reason=payload.get("no_answer_reason", ""),
        )
        state._completed_results = {item["key"]: item["result"] for item in completed if "key" in item and "result" in item}
        return state
