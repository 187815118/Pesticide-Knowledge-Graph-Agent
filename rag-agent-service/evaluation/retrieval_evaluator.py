import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List


METRIC_KEYS = ["Hit@1", "Hit@3", "Hit@5", "MRR@10", "Recall@5", "Recall@10"]
CATEGORY_ORDER = [
    "entity_explicit",
    "semantic",
    "mechanism_or_resistance",
    "cross_lingual_zh",
]


def load_eval_queries(eval_path: Path) -> List[Dict]:
    eval_path = Path(eval_path)
    with eval_path.open("r", encoding="utf-8") as eval_file:
        queries = json.load(eval_file)

    if not isinstance(queries, list):
        raise ValueError(f"Evaluation queries must be a JSON array: {eval_path}")

    return queries


def compute_query_metrics(results: List[Dict], relevant_ids: Iterable[str]) -> Dict[str, float]:
    relevant_id_set = set(relevant_ids)
    if not relevant_id_set:
        raise ValueError("relevant_ids must not be empty.")

    ranked_ids = [result.get("id", "") for result in results]

    def hit_at(k: int) -> float:
        return 1.0 if any(doc_id in relevant_id_set for doc_id in ranked_ids[:k]) else 0.0

    def recall_at(k: int) -> float:
        retrieved_relevant_ids = set(ranked_ids[:k]) & relevant_id_set
        return len(retrieved_relevant_ids) / len(relevant_id_set)

    reciprocal_rank = 0.0
    for rank, doc_id in enumerate(ranked_ids[:10], start=1):
        if doc_id in relevant_id_set:
            reciprocal_rank = 1.0 / rank
            break

    return {
        "Hit@1": hit_at(1),
        "Hit@3": hit_at(3),
        "Hit@5": hit_at(5),
        "MRR@10": reciprocal_rank,
        "Recall@5": recall_at(5),
        "Recall@10": recall_at(10),
    }


def aggregate_metrics(query_metrics: List[Dict]) -> Dict[str, float]:
    query_count = len(query_metrics)
    if query_count == 0:
        return {"query_count": 0, **{metric: 0.0 for metric in METRIC_KEYS}}

    aggregated = {"query_count": query_count}
    for metric in METRIC_KEYS:
        aggregated[metric] = sum(item[metric] for item in query_metrics) / query_count

    return aggregated


def summarize_by_category(per_query_metrics: List[Dict]) -> Dict[str, Dict[str, float]]:
    grouped = defaultdict(list)
    for item in per_query_metrics:
        grouped[item["category"]].append(item["metrics"])

    categories = [category for category in CATEGORY_ORDER if category in grouped]
    categories.extend(
        sorted(category for category in grouped if category not in CATEGORY_ORDER)
    )

    return {
        category: aggregate_metrics(grouped[category])
        for category in categories
    }


def evaluate_retriever(retriever, eval_queries: List[Dict], top_k: int = 10) -> Dict:
    if top_k < 10:
        raise ValueError("top_k must be at least 10 to compute MRR@10 and Recall@10.")

    per_query_metrics = []
    for item in eval_queries:
        results = retriever.search(item["query"], top_k=top_k)
        metrics = compute_query_metrics(results, item["relevant_ids"])
        per_query_metrics.append(
            {
                "id": item["id"],
                "query": item["query"],
                "category": item["category"],
                "relevant_ids": item["relevant_ids"],
                "retrieved_ids": [result.get("id", "") for result in results],
                "metrics": metrics,
            }
        )

    return {
        "overall": aggregate_metrics([item["metrics"] for item in per_query_metrics]),
        "by_category": summarize_by_category(per_query_metrics),
        "per_query": per_query_metrics,
    }
