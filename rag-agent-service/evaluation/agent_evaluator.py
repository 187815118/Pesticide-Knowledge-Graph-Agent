import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


CITATION_PATTERN = re.compile(r"\[D[1-9]\d*\]")
CATEGORY_ORDER = [
    "single_kg_forward",
    "single_kg_reverse",
    "single_rag",
    "kg_to_rag_multistep",
    "kg_to_kg_multistep",
    "cross_lingual_zh",
    "empty_or_unknown",
]


def load_agent_eval_queries(eval_path: Path) -> List[Dict[str, Any]]:
    eval_path = Path(eval_path)
    with eval_path.open("r", encoding="utf-8") as eval_file:
        queries = json.load(eval_file)

    if not isinstance(queries, list):
        raise ValueError(f"Agent evaluation queries must be a JSON array: {eval_path}")

    return queries


def _tool_sequence(tool_trace: Iterable[Dict[str, Any]]) -> List[str]:
    return [item.get("tool", "") for item in tool_trace]


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def _combined_result_text(result: Optional[Dict[str, Any]]) -> str:
    if not result:
        return ""

    parts = [result.get("answer", "")]
    for item in result.get("tool_trace", []):
        parts.append(_json_text(item.get("arguments", {})))
        parts.append(_json_text(item.get("result", "")))
    return "\n".join(parts)


def compute_tool_sequence_exact_match(
    actual_tools: List[str],
    expected_tools: List[str],
) -> float:
    return 1.0 if actual_tools == expected_tools else 0.0


def compute_tool_selection_recall(
    actual_tools: List[str],
    expected_tools: List[str],
) -> float:
    if not expected_tools:
        return 1.0

    actual_set = set(actual_tools)
    expected_set = set(expected_tools)
    return len(actual_set & expected_set) / len(expected_set)


def compute_unnecessary_tool_call_rate(
    actual_tools: List[str],
    expected_tools: List[str],
) -> float:
    if not actual_tools:
        return 0.0

    expected_set = set(expected_tools)
    unnecessary_count = sum(1 for tool in actual_tools if tool not in expected_set)
    return unnecessary_count / len(actual_tools)


def compute_entity_preservation(
    result: Optional[Dict[str, Any]],
    expected_entities: List[str],
) -> Dict[str, Any]:
    if not expected_entities:
        return {
            "score": 1.0,
            "passed": True,
            "preserved_entities": [],
            "missing_entities": [],
        }

    text = _combined_result_text(result)
    preserved = [entity for entity in expected_entities if entity in text]
    missing = [entity for entity in expected_entities if entity not in text]
    return {
        "score": len(preserved) / len(expected_entities),
        "passed": not missing,
        "preserved_entities": preserved,
        "missing_entities": missing,
    }


def compute_citation_presence(answer: str, requires_citation: bool) -> Dict[str, Any]:
    citations = CITATION_PATTERN.findall(answer or "")
    passed = True if not requires_citation else bool(citations)
    return {
        "required": requires_citation,
        "passed": passed,
        "citations": citations,
    }


def evaluate_agent_result(
    eval_item: Dict[str, Any],
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    expected_tools = eval_item.get("expected_tools", [])
    expected_entities = eval_item.get("expected_entities", [])
    requires_citation = bool(eval_item.get("requires_citation", False))

    tool_trace = [] if result is None else result.get("tool_trace", [])
    answer = "" if result is None else result.get("answer", "")
    actual_tools = _tool_sequence(tool_trace)
    unnecessary_tools = [
        tool for tool in actual_tools if tool not in set(expected_tools)
    ]

    tool_sequence_exact_match = compute_tool_sequence_exact_match(
        actual_tools,
        expected_tools,
    )
    tool_selection_recall = compute_tool_selection_recall(
        actual_tools,
        expected_tools,
    )
    unnecessary_tool_call_rate = compute_unnecessary_tool_call_rate(
        actual_tools,
        expected_tools,
    )
    entity_preservation = compute_entity_preservation(result, expected_entities)
    citation_presence = compute_citation_presence(answer, requires_citation)

    task_completed_rule = (
        error is None
        and tool_sequence_exact_match == 1.0
        and entity_preservation["passed"]
        and citation_presence["passed"]
        and unnecessary_tool_call_rate == 0.0
    )

    return {
        "id": eval_item.get("id", ""),
        "category": eval_item.get("category", ""),
        "expected_tools": expected_tools,
        "actual_tools": actual_tools,
        "tool_sequence_exact_match": tool_sequence_exact_match,
        "tool_selection_recall": tool_selection_recall,
        "unnecessary_tool_call_rate": unnecessary_tool_call_rate,
        "unnecessary_tools": unnecessary_tools,
        "entity_preservation": entity_preservation,
        "citation_presence": citation_presence,
        "task_completed_rule": task_completed_rule,
        "error": error,
    }


def aggregate_agent_metrics(per_query: List[Dict[str, Any]]) -> Dict[str, Any]:
    count = len(per_query)
    if count == 0:
        return {
            "query_count": 0,
            "tool_sequence_exact_match": 0.0,
            "tool_selection_recall": 0.0,
            "unnecessary_tool_call_rate": 0.0,
            "entity_preservation": 0.0,
            "citation_presence": 0.0,
            "task_completed_rule": 0.0,
            "error_rate": 0.0,
        }

    return {
        "query_count": count,
        "tool_sequence_exact_match": sum(
            item["automatic_evaluation"]["tool_sequence_exact_match"]
            for item in per_query
        )
        / count,
        "tool_selection_recall": sum(
            item["automatic_evaluation"]["tool_selection_recall"]
            for item in per_query
        )
        / count,
        "unnecessary_tool_call_rate": sum(
            item["automatic_evaluation"]["unnecessary_tool_call_rate"]
            for item in per_query
        )
        / count,
        "entity_preservation": sum(
            item["automatic_evaluation"]["entity_preservation"]["score"]
            for item in per_query
        )
        / count,
        "citation_presence": sum(
            1.0
            if item["automatic_evaluation"]["citation_presence"]["passed"]
            else 0.0
            for item in per_query
        )
        / count,
        "task_completed_rule": sum(
            1.0
            if item["automatic_evaluation"]["task_completed_rule"]
            else 0.0
            for item in per_query
        )
        / count,
        "error_rate": sum(1.0 if item.get("error") else 0.0 for item in per_query)
        / count,
    }


def summarize_agent_results(per_query: List[Dict[str, Any]]) -> Dict[str, Any]:
    grouped = defaultdict(list)
    for item in per_query:
        grouped[item["category"]].append(item)

    categories = [category for category in CATEGORY_ORDER if category in grouped]
    categories.extend(
        sorted(category for category in grouped if category not in CATEGORY_ORDER)
    )

    return {
        "overall": aggregate_agent_metrics(per_query),
        "by_category": {
            category: aggregate_agent_metrics(grouped[category])
            for category in categories
        },
    }
