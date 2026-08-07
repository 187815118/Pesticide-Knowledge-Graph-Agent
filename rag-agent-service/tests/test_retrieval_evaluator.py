import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evaluation.retrieval_evaluator import compute_query_metrics, evaluate_retriever


def _results(*doc_ids):
    return [{"id": doc_id} for doc_id in doc_ids]


def _assert_close(actual, expected):
    if not math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-9):
        raise AssertionError(f"expected {expected}, got {actual}")


class FakeRetriever:
    def __init__(self, ranked_ids_by_query):
        self.ranked_ids_by_query = ranked_ids_by_query

    def search(self, query, top_k=10):
        return _results(*self.ranked_ids_by_query[query][:top_k])


def main() -> int:
    top1 = compute_query_metrics(
        _results("doc-a", "doc-b", "doc-c"),
        ["doc-a"],
    )
    _assert_close(top1["Hit@1"], 1.0)
    _assert_close(top1["Hit@3"], 1.0)
    _assert_close(top1["MRR@10"], 1.0)

    top3 = compute_query_metrics(
        _results("doc-a", "doc-b", "doc-c", "doc-d"),
        ["doc-c"],
    )
    _assert_close(top3["Hit@1"], 0.0)
    _assert_close(top3["Hit@3"], 1.0)
    _assert_close(top3["MRR@10"], 1.0 / 3.0)

    no_hit = compute_query_metrics(
        _results("doc-a", "doc-b", "doc-c", "doc-d", "doc-e"),
        ["doc-z"],
    )
    _assert_close(no_hit["Hit@1"], 0.0)
    _assert_close(no_hit["Hit@3"], 0.0)
    _assert_close(no_hit["Hit@5"], 0.0)
    _assert_close(no_hit["MRR@10"], 0.0)
    _assert_close(no_hit["Recall@5"], 0.0)
    _assert_close(no_hit["Recall@10"], 0.0)

    multi_relevant = compute_query_metrics(
        _results("doc-a", "doc-b", "doc-c", "doc-d", "doc-e"),
        ["doc-b", "doc-d", "doc-x", "doc-y"],
    )
    _assert_close(multi_relevant["Recall@5"], 0.5)

    eval_queries = [
        {
            "id": "q1",
            "query": "query one",
            "relevant_ids": ["doc-a"],
            "category": "entity_explicit",
        },
        {
            "id": "q2",
            "query": "query two",
            "relevant_ids": ["doc-z"],
            "category": "semantic",
        },
    ]
    fake_retriever = FakeRetriever(
        {
            "query one": ["doc-a", "doc-b", "doc-c"],
            "query two": ["doc-a", "doc-b", "doc-z"],
        }
    )
    summary = evaluate_retriever(fake_retriever, eval_queries, top_k=10)

    _assert_close(summary["overall"]["Hit@1"], 0.5)
    _assert_close(summary["overall"]["Hit@3"], 1.0)
    _assert_close(summary["overall"]["MRR@10"], (1.0 + 1.0 / 3.0) / 2.0)
    if summary["by_category"]["entity_explicit"]["query_count"] != 1:
        raise AssertionError("entity_explicit category aggregation failed")
    if summary["by_category"]["semantic"]["query_count"] != 1:
        raise AssertionError("semantic category aggregation failed")
    _assert_close(summary["by_category"]["semantic"]["MRR@10"], 1.0 / 3.0)

    print("验收通过: RetrievalEvaluator 指标计算正常")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
