import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional


CITATION_PATTERN = re.compile(r"\[D(\d+)\]")
BRACKET_PATTERN = re.compile(r"\[([^\]]+)\]")
INSUFFICIENT_PHRASE = "retrieved evidence is insufficient"
CATEGORY_ORDER = [
    "single_entity_fact",
    "multi_entity_or_mechanism",
    "cross_lingual_zh",
    "insufficient_evidence",
]


def load_generation_eval_queries(eval_path: Path) -> List[Dict]:
    eval_path = Path(eval_path)
    with eval_path.open("r", encoding="utf-8") as eval_file:
        queries = json.load(eval_file)

    if not isinstance(queries, list):
        raise ValueError(f"Generation eval queries must be a JSON array: {eval_path}")

    return queries


def evaluate_generation_result(eval_item: Dict, rag_result: Dict) -> Dict:
    answer = rag_result.get("answer", "") or ""
    evidence = rag_result.get("evidence", []) or []
    expected_behavior = eval_item["expected_behavior"]
    expected_entities = eval_item.get("expected_entities", []) or []

    citations = _extract_citation_labels(answer)
    evidence_labels = {item.get("label", "") for item in evidence}
    invalid_citations = [
        label for label in citations
        if label not in evidence_labels
    ]
    citations_valid = len(invalid_citations) == 0
    entity_as_citation_violation = _has_entity_as_citation(
        answer,
        expected_entities,
        evidence,
    )

    unexpected_insufficient = (
        expected_behavior == "answer"
        and INSUFFICIENT_PHRASE in answer.lower()
    )
    insufficient_success = None
    if expected_behavior == "insufficient":
        insufficient_success = INSUFFICIENT_PHRASE in answer.lower()

    citation_presence = None
    supported_expected_entities = []
    unretrieved_expected_entities = []
    retrieval_expected_entity_coverage = None
    matched_supported_entities = []
    missing_supported_entities = []
    evidence_conditioned_entity_recall = None
    generation_evaluable = None
    if expected_behavior == "answer":
        citation_presence = len(citations) > 0
        evidence_names = [
            item.get("name", "")
            for item in evidence
            if item.get("name")
        ]
        supported_expected_entities = [
            entity for entity in expected_entities
            if entity in evidence_names
        ]
        unretrieved_expected_entities = [
            entity for entity in expected_entities
            if entity not in evidence_names
        ]
        retrieval_expected_entity_coverage = (
            len(supported_expected_entities) / len(expected_entities)
            if expected_entities else 1.0
        )
        generation_evaluable = len(supported_expected_entities) > 0
        if generation_evaluable:
            matched_supported_entities = [
                entity for entity in supported_expected_entities
                if entity in answer
            ]
            missing_supported_entities = [
                entity for entity in supported_expected_entities
                if entity not in answer
            ]
            evidence_conditioned_entity_recall = (
                len(matched_supported_entities) / len(supported_expected_entities)
            )

    zh_language_match = None
    if eval_item.get("language") == "zh":
        zh_language_match = _count_cjk_chars(answer) >= 5

    automatic_metrics = {
        "citation_presence": citation_presence,
        "citations_valid": citations_valid,
        "invalid_citations": invalid_citations,
        "supported_expected_entities": supported_expected_entities,
        "unretrieved_expected_entities": unretrieved_expected_entities,
        "retrieval_expected_entity_coverage": retrieval_expected_entity_coverage,
        "matched_supported_entities": matched_supported_entities,
        "missing_supported_entities": missing_supported_entities,
        "evidence_conditioned_entity_recall": evidence_conditioned_entity_recall,
        "generation_evaluable": generation_evaluable,
        "entity_as_citation_violation": entity_as_citation_violation,
        "insufficient_success": insufficient_success,
        "unexpected_insufficient": unexpected_insufficient,
        "zh_language_match": zh_language_match,
    }
    automatic_metrics["automatic_rule_pass"] = _automatic_rule_pass(
        eval_item,
        automatic_metrics,
    )

    return {
        "id": eval_item["id"],
        "query": eval_item["query"],
        "category": eval_item["category"],
        "language": eval_item["language"],
        "expected_behavior": expected_behavior,
        "expected_entities": expected_entities,
        "source_retrieval_query_id": eval_item.get("source_retrieval_query_id"),
        "answer": answer,
        "evidence": evidence,
        "retrieval_trace": rag_result.get("retrieval_trace", []) or [],
        "invalid_citations": rag_result.get("invalid_citations", []) or [],
        "automatic_metrics": automatic_metrics,
        "manual_review": {
            "groundedness": None,
            "correctness": None,
            "completeness": None,
            "unsupported_claims": None,
            "notes": "",
        },
    }


def evaluate_generation_results(eval_items: List[Dict], rag_results: List[Dict]) -> Dict:
    if len(eval_items) != len(rag_results):
        raise ValueError("eval_items and rag_results must have the same length.")

    per_query = [
        evaluate_generation_result(eval_item, rag_result)
        for eval_item, rag_result in zip(eval_items, rag_results)
    ]

    return {
        "overall": aggregate_generation_metrics(per_query),
        "category_breakdown": summarize_generation_by_category(per_query),
        "per_query": per_query,
    }


def aggregate_generation_metrics(per_query: List[Dict]) -> Dict:
    answer_items = [
        item for item in per_query
        if item["expected_behavior"] == "answer"
    ]
    insufficient_items = [
        item for item in per_query
        if item["expected_behavior"] == "insufficient"
    ]
    zh_items = [
        item for item in per_query
        if item["language"] == "zh"
    ]

    return {
        "total_queries": len(per_query),
        "answer_queries": len(answer_items),
        "insufficient_queries": len(insufficient_items),
        "citation_presence_rate": _mean_bool(
            item["automatic_metrics"]["citation_presence"]
            for item in answer_items
        ),
        "valid_citation_rate": _mean_bool(
            item["automatic_metrics"]["citations_valid"]
            for item in per_query
        ),
        "retrieval_expected_entity_coverage_macro": _mean_float(
            item["automatic_metrics"]["retrieval_expected_entity_coverage"]
            for item in answer_items
        ),
        "evidence_conditioned_entity_recall_macro": _mean_float(
            item["automatic_metrics"]["evidence_conditioned_entity_recall"]
            for item in answer_items
        ),
        "generation_evaluable_rate": _mean_bool(
            item["automatic_metrics"]["generation_evaluable"]
            for item in answer_items
        ),
        "entity_as_citation_violation_rate": _mean_bool(
            item["automatic_metrics"]["entity_as_citation_violation"]
            for item in per_query
        ),
        "insufficient_accuracy": _mean_bool(
            item["automatic_metrics"]["insufficient_success"]
            for item in insufficient_items
        ),
        "zh_language_match_rate": _mean_bool(
            item["automatic_metrics"]["zh_language_match"]
            for item in zh_items
        ),
        "automatic_rule_pass_rate": _mean_bool(
            item["automatic_metrics"]["automatic_rule_pass"]
            for item in per_query
        ),
    }


def summarize_generation_by_category(per_query: List[Dict]) -> Dict[str, Dict]:
    grouped = defaultdict(list)
    for item in per_query:
        grouped[item["category"]].append(item)

    categories = [category for category in CATEGORY_ORDER if category in grouped]
    categories.extend(
        sorted(category for category in grouped if category not in CATEGORY_ORDER)
    )

    return {
        category: aggregate_generation_metrics(grouped[category])
        for category in categories
    }


def _extract_citation_labels(answer: str) -> List[str]:
    return [f"D{match.group(1)}" for match in CITATION_PATTERN.finditer(answer)]


def _has_entity_as_citation(answer: str, expected_entities: List[str], evidence: List[Dict]) -> bool:
    entity_names = set(expected_entities)
    entity_names.update(
        item.get("name", "")
        for item in evidence
        if item.get("name")
    )
    bracketed_values = [match.group(1) for match in BRACKET_PATTERN.finditer(answer)]
    return any(value in entity_names for value in bracketed_values)


def _count_cjk_chars(text: str) -> int:
    return sum(1 for char in text if "\u4e00" <= char <= "\u9fff")


def _automatic_rule_pass(eval_item: Dict, metrics: Dict) -> bool:
    if eval_item["expected_behavior"] == "answer":
        if metrics["generation_evaluable"] is False:
            return None
        if not metrics["citation_presence"]:
            return False
        if not metrics["citations_valid"]:
            return False
        if metrics["evidence_conditioned_entity_recall"] != 1.0:
            return False
        if metrics["entity_as_citation_violation"]:
            return False
        if metrics["unexpected_insufficient"]:
            return False
        if eval_item.get("language") == "zh" and metrics["zh_language_match"] is not True:
            return False
        return True

    if eval_item["expected_behavior"] == "insufficient":
        return (
            metrics["insufficient_success"] is True
            and metrics["citations_valid"] is True
            and metrics["entity_as_citation_violation"] is False
        )

    raise ValueError(f"Unknown expected_behavior: {eval_item['expected_behavior']}")


def _mean_bool(values) -> Optional[float]:
    filtered = [value for value in values if value is not None]
    if not filtered:
        return None
    return sum(1.0 if value else 0.0 for value in filtered) / len(filtered)


def _mean_float(values) -> Optional[float]:
    filtered = [value for value in values if value is not None]
    if not filtered:
        return None
    return sum(filtered) / len(filtered)
