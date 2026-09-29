import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


CITATION_PATTERN = re.compile(r"\[(D[1-9]\d*)\]")
CATEGORY_ORDER = [
    "single_kg_forward",
    "single_kg_reverse",
    "single_rag",
    "kg_to_rag_multistep",
    "kg_to_kg_multistep",
    "cross_lingual_zh",
    "empty_or_unknown",
    "single_kg_classification",
    "single_kg_target_site",
    "single_kg_mode_of_action",
    "kg_to_kg_to_rag",
    "entity_ambiguity",
    "no_answer",
]


def load_agent_eval_queries(eval_path: Path) -> List[Dict[str, Any]]:
    with Path(eval_path).open("r", encoding="utf-8") as eval_file:
        queries = json.load(eval_file)
    if not isinstance(queries, list):
        raise ValueError(f"Agent evaluation queries must be a JSON array: {eval_path}")
    validate_benchmark_schema(queries)
    return queries


def validate_benchmark_schema(queries: List[Dict[str, Any]]) -> None:
    required = {"id", "category", "question", "expected_tools", "expected_entities", "requires_citation"}
    ids = set()
    for index, item in enumerate(queries):
        missing = sorted(required - set(item))
        if missing:
            raise ValueError(f"Benchmark case #{index} 缺少字段: {missing}")
        if item["id"] in ids:
            raise ValueError(f"Benchmark id 重复: {item['id']}")
        ids.add(item["id"])
        if not isinstance(item["expected_tools"], list) or not isinstance(item.get("expected_tool_sequence", item["expected_tools"]), list):
            raise ValueError(f"{item['id']} tool fields 必须是 list")


def _tool_sequence(tool_trace: Iterable[Dict[str, Any]]) -> List[str]:
    return [item.get("tool", "") for item in tool_trace if item.get("tool") and item.get("event_type") in {None, "tool_success", "tool_reused"} and item.get("status") != "failed"]


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def _combined_result_text(result: Optional[Dict[str, Any]]) -> str:
    if not result:
        return ""
    parts = [result.get("answer", "")]
    for item in result.get("tool_trace", []):
        parts.extend(
            [_json_text(item.get("arguments", {})), _json_text(item.get("result", ""))]
        )
    return "\n".join(parts)


def _result_strings(value: Any) -> List[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def compute_tool_sequence_exact_match(
    actual_tools: List[str], expected_tools: List[str]
) -> float:
    return 1.0 if actual_tools == expected_tools else 0.0


def compute_tool_selection_recall(
    actual_tools: List[str], expected_tools: List[str]
) -> float:
    if not expected_tools:
        return 1.0
    return len(set(actual_tools) & set(expected_tools)) / len(set(expected_tools))


def compute_tool_selection_accuracy(
    actual_tools: List[str], expected_tools: List[str]
) -> float:
    return 1.0 if set(actual_tools) == set(expected_tools) else 0.0


def compute_unnecessary_tool_call_rate(
    actual_tools: List[str], expected_tools: List[str]
) -> float:
    if not actual_tools:
        return 0.0
    expected_set = set(expected_tools)
    return sum(tool not in expected_set for tool in actual_tools) / len(actual_tools)


def compute_entity_preservation(
    result: Optional[Dict[str, Any]], expected_entities: List[str]
) -> Dict[str, Any]:
    text = _combined_result_text(result)
    preserved = [entity for entity in expected_entities if entity in text]
    missing = [entity for entity in expected_entities if entity not in text]
    return {
        "score": 1.0 if not expected_entities else len(preserved) / len(expected_entities),
        "passed": not missing,
        "preserved_entities": preserved,
        "missing_entities": missing,
    }


def compute_entity_propagation(
    eval_item: Dict[str, Any], tool_trace: List[Dict[str, Any]]
) -> Dict[str, Any]:
    expected_tools = eval_item.get("expected_tool_sequence") or eval_item.get(
        "expected_tools", []
    )
    if len(expected_tools) < 2:
        return {"applicable": False, "score": 1.0, "passed": True, "entities": []}

    entities = eval_item.get("propagation_entities")
    if entities is None:
        expected_entities = eval_item.get("expected_entities", [])
        first_result_entities = (
            _result_strings(tool_trace[0].get("result")) if tool_trace else []
        )
        entities = [
            entity for entity in expected_entities if entity in first_result_entities
        ]
        if not entities:
            question = eval_item.get("question", "")
            entities = [entity for entity in expected_entities if entity not in question]
    downstream_arguments = "\n".join(
        _json_text(item.get("arguments", {})) for item in tool_trace[1:]
    )
    propagated = [entity for entity in entities if entity in downstream_arguments]
    missing = [entity for entity in entities if entity not in downstream_arguments]
    return {
        "applicable": True,
        "score": 1.0 if not entities else len(propagated) / len(entities),
        "passed": not missing,
        "entities": entities,
        "propagated_entities": propagated,
        "missing_entities": missing,
    }


def compute_citation_presence(answer: str, requires_citation: bool) -> Dict[str, Any]:
    citations = CITATION_PATTERN.findall(answer or "")
    return {
        "required": requires_citation,
        "applicable": requires_citation,
        "passed": not requires_citation or bool(citations),
        "citations": citations,
    }


def compute_citation_validity(
    answer: str,
    tool_trace: List[Dict[str, Any]],
    requires_citation: bool,
) -> Dict[str, Any]:
    citations = CITATION_PATTERN.findall(answer or "")
    evidence_labels = set()
    tool_reported_invalid = set()
    rag_called = False
    for item in tool_trace:
        if item.get("tool") != "hybrid_rag_query":
            continue
        rag_called = True
        result = item.get("result") or {}
        if not isinstance(result, dict):
            continue
        evidence_labels.update(
            evidence.get("label", "")
            for evidence in result.get("evidence", [])
            if isinstance(evidence, dict)
        )
        tool_reported_invalid.update(result.get("invalid_citations", []))

    invalid = sorted(
        {citation for citation in citations if citation not in evidence_labels}
        | tool_reported_invalid
    )
    applicable = requires_citation or rag_called or bool(citations)
    passed = not invalid and (not requires_citation or bool(citations))
    return {
        "applicable": applicable,
        "passed": passed,
        "citations": citations,
        "evidence_labels": sorted(evidence_labels),
        "invalid_citations": invalid,
    }


def compute_answer_entity_accuracy(
    answer: str, expected_entities: List[str]
) -> Dict[str, Any]:
    present = [entity for entity in expected_entities if entity in (answer or "")]
    missing = [entity for entity in expected_entities if entity not in (answer or "")]
    return {
        "score": 1.0 if not expected_entities else len(present) / len(expected_entities),
        "passed": not missing,
        "present_entities": present,
        "missing_entities": missing,
    }


def compute_required_fact_accuracy(answer: str, expected_keywords: List[str]) -> Dict[str, Any]:
    normalized_answer = re.sub(r"[^\w]+", " ", (answer or "").lower()).strip()
    normalized_keywords = {
        keyword: re.sub(r"[^\w]+", " ", keyword.lower()).strip()
        for keyword in expected_keywords
    }
    matched = [
        keyword
        for keyword, normalized in normalized_keywords.items()
        if normalized in normalized_answer
    ]
    missing = [keyword for keyword in expected_keywords if keyword not in matched]
    return {
        "applicable": bool(expected_keywords),
        "score": 1.0 if not expected_keywords else len(matched) / len(expected_keywords),
        "passed": not missing,
        "matched_keywords": matched,
        "missing_keywords": missing,
    }


def compute_no_answer_accuracy(result: Optional[Dict[str, Any]], requires_no_answer: bool) -> Dict[str, Any]:
    answer = "" if not result else result.get("answer", "") or ""
    state = {} if not result else result.get("execution_state", {}) or {}
    markers = ("does not contain enough evidence", "not enough evidence", "insufficient evidence", "没有足够证据", "未查到")
    detected = state.get("status") == "NO_ANSWER" or any(marker in answer.lower() for marker in markers)
    return {"applicable": requires_no_answer, "required": requires_no_answer, "passed": not requires_no_answer or detected, "detected": detected, "reason": state.get("no_answer_reason", "")}


def evaluate_agent_result(
    eval_item: Dict[str, Any],
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    expected_tools = eval_item.get("expected_tools", [])
    expected_sequence = eval_item.get("expected_tool_sequence", expected_tools)
    expected_entities = eval_item.get("expected_entities", [])
    requires_citation = bool(eval_item.get("requires_citation", False))
    requires_no_answer = bool(eval_item.get("requires_no_answer", False))
    tool_trace = [] if result is None else result.get("tool_trace", [])
    answer = "" if result is None else result.get("answer", "")
    actual_tools = _tool_sequence(tool_trace)
    unnecessary_tools = [tool for tool in actual_tools if tool not in set(expected_tools)]

    sequence = compute_tool_sequence_exact_match(actual_tools, expected_sequence)
    selection_recall = compute_tool_selection_recall(actual_tools, expected_tools)
    selection_accuracy = compute_tool_selection_accuracy(actual_tools, expected_tools)
    unnecessary_rate = compute_unnecessary_tool_call_rate(actual_tools, expected_tools)
    entity_preservation = compute_entity_preservation(result, expected_entities)
    entity_propagation = compute_entity_propagation(eval_item, tool_trace)
    citation_presence = compute_citation_presence(answer, requires_citation)
    citation_validity = compute_citation_validity(answer, tool_trace, requires_citation)
    answer_entities = compute_answer_entity_accuracy(answer, expected_entities)
    required_facts = compute_required_fact_accuracy(
        answer, eval_item.get("expected_keywords", [])
    )
    no_answer = compute_no_answer_accuracy(result, requires_no_answer)
    task_completed = (
        error is None
        and selection_accuracy == 1.0
        and sequence == 1.0
        and unnecessary_rate == 0.0
        and entity_propagation["passed"]
        and citation_presence["passed"]
        and citation_validity["passed"]
        and (requires_no_answer or answer_entities["passed"])
        and (requires_no_answer or required_facts["passed"])
        and no_answer["passed"]
    )

    return {
        "id": eval_item.get("id", ""),
        "category": eval_item.get("category", ""),
        "expected_tools": expected_tools,
        "actual_tools": actual_tools,
        "tool_selection_accuracy": selection_accuracy,
        "tool_selection_recall": selection_recall,
        "tool_sequence_accuracy": sequence,
        "tool_sequence_exact_match": sequence,
        "unnecessary_tool_call_rate": unnecessary_rate,
        "unnecessary_tools": unnecessary_tools,
        "entity_preservation": entity_preservation,
        "entity_propagation": entity_propagation,
        "citation_presence": citation_presence,
        "citation_validity": citation_validity,
        "answer_entity_accuracy": answer_entities,
        "required_fact_accuracy": required_facts,
        "no_answer_accuracy": no_answer,
        "task_completed_rule": task_completed,
        "error": error,
    }


def _mean(per_query: List[Dict[str, Any]], path: List[str]) -> float:
    values = []
    for item in per_query:
        value: Any = item["automatic_evaluation"]
        for key in path:
            value = value[key]
        values.append(float(value))
    return sum(values) / len(values) if values else 0.0


def _applicable_mean(
    per_query: List[Dict[str, Any]], metric: str, value_key: str = "score"
) -> float:
    values = [
        float(item["automatic_evaluation"][metric][value_key])
        for item in per_query
        if item["automatic_evaluation"][metric].get("applicable", True)
    ]
    return sum(values) / len(values) if values else 1.0


def aggregate_agent_metrics(per_query: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not per_query:
        return {"query_count": 0}
    return {
        "query_count": len(per_query),
        "tool_selection_accuracy": _mean(per_query, ["tool_selection_accuracy"]),
        "tool_selection_recall": _mean(per_query, ["tool_selection_recall"]),
        "tool_sequence_accuracy": _mean(per_query, ["tool_sequence_accuracy"]),
        "tool_sequence_exact_match": _mean(per_query, ["tool_sequence_exact_match"]),
        "unnecessary_tool_call_rate": _mean(per_query, ["unnecessary_tool_call_rate"]),
        "entity_preservation": _mean(per_query, ["entity_preservation", "score"]),
        "entity_propagation_accuracy": _applicable_mean(per_query, "entity_propagation"),
        "citation_presence_accuracy": _applicable_mean(
            per_query, "citation_presence", "passed"
        ),
        "citation_validity_accuracy": _applicable_mean(
            per_query, "citation_validity", "passed"
        ),
        "answer_entity_accuracy": _mean(
            per_query, ["answer_entity_accuracy", "score"]
        ),
        "required_fact_accuracy": _applicable_mean(per_query, "required_fact_accuracy"),
        "no_answer_accuracy": _applicable_mean(per_query, "no_answer_accuracy", "passed"),
        "answer_accuracy": _mean(per_query, ["task_completed_rule"]),
        "task_completed_rule": _mean(per_query, ["task_completed_rule"]),
        "error_rate": sum(bool(item.get("error")) for item in per_query) / len(per_query),
    }


def summarize_agent_results(per_query: List[Dict[str, Any]]) -> Dict[str, Any]:
    grouped = defaultdict(list)
    for item in per_query:
        grouped[item["category"]].append(item)
    categories = [category for category in CATEGORY_ORDER if category in grouped]
    categories.extend(sorted(category for category in grouped if category not in CATEGORY_ORDER))
    return {
        "overall": aggregate_agent_metrics(per_query),
        "by_category": {
            category: aggregate_agent_metrics(grouped[category]) for category in categories
        },
    }
