import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from retrieval.hybrid_retriever import HybridRetriever


REQUIRED_KEYS = {
    "rank",
    "id",
    "name",
    "score",
    "content",
    "source",
    "bm25_rank",
    "vector_rank",
    "bm25_score",
    "vector_score",
}


def _result(doc_id, rank, score=None):
    return {
        "rank": rank,
        "id": doc_id,
        "name": f"name-{doc_id}",
        "score": float(rank) if score is None else score,
        "content": f"content-{doc_id}",
        "source": f"source-{doc_id}",
    }


class StubRetriever:
    def __init__(self, doc_ids):
        self.doc_ids = doc_ids
        self.requested_top_ks = []

    def search(self, query, top_k=3):
        self.requested_top_ks.append(top_k)
        return [
            _result(doc_id, rank)
            for rank, doc_id in enumerate(self.doc_ids[:top_k], start=1)
        ]


def _assert_close(actual, expected):
    if not math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-9):
        raise AssertionError(f"expected {expected}, got {actual}")


def _assert_raises_value_error(func):
    try:
        func()
    except ValueError:
        return
    raise AssertionError("预期抛出 ValueError，但没有抛出。")


def _assert_result_shape(results):
    for result in results:
        missing_keys = REQUIRED_KEYS - set(result)
        if missing_keys:
            raise AssertionError(f"结果缺少字段: {sorted(missing_keys)}")


def main() -> int:
    bm25 = StubRetriever(["A", "B"])
    vector = StubRetriever(["B", "A"])
    retriever = HybridRetriever(bm25, vector, rrf_k=60, candidate_k=10)
    results = retriever.search("test query", top_k=2)

    _assert_result_shape(results)
    if [item["id"] for item in results] != ["A", "B"]:
        raise AssertionError("tie-breaking 应按 best rank 后再按 document id 稳定排序")
    expected_score = 1.0 / 61.0 + 1.0 / 62.0
    _assert_close(results[0]["score"], expected_score)
    _assert_close(results[1]["score"], expected_score)
    if results[0]["bm25_rank"] != 1 or results[0]["vector_rank"] != 2:
        raise AssertionError("A 的诊断 rank 不正确")
    if results[1]["bm25_rank"] != 2 or results[1]["vector_rank"] != 1:
        raise AssertionError("B 的诊断 rank 不正确")

    bm25 = StubRetriever(["A", "B"])
    vector = StubRetriever(["C", "A"])
    retriever = HybridRetriever(bm25, vector, rrf_k=60, candidate_k=10)
    results = retriever.search("test query", top_k=3)
    result_ids = [item["id"] for item in results]
    if result_ids != ["A", "C", "B"]:
        raise AssertionError(f"RRF union 或排序不正确: {result_ids}")
    if len(result_ids) != len(set(result_ids)):
        raise AssertionError("同一 document 在最终结果中重复出现")

    by_id = {item["id"]: item for item in results}
    if by_id["B"]["vector_rank"] is not None or by_id["B"]["vector_score"] is not None:
        raise AssertionError("单路缺失候选的 vector 诊断字段应为 None")
    if by_id["C"]["bm25_rank"] is not None or by_id["C"]["bm25_score"] is not None:
        raise AssertionError("单路缺失候选的 bm25 诊断字段应为 None")
    if [item["score"] for item in results] != sorted(
        [item["score"] for item in results],
        reverse=True,
    ):
        raise AssertionError("score 未按 RRF 降序排列")

    _assert_raises_value_error(lambda: retriever.search("test query", top_k=0))
    _assert_raises_value_error(lambda: retriever.search("", top_k=3))

    bm25 = StubRetriever([str(index) for index in range(20)])
    vector = StubRetriever([str(index) for index in range(20)])
    retriever = HybridRetriever(bm25, vector, rrf_k=60, candidate_k=10)
    retriever.search("test query", top_k=15)
    if bm25.requested_top_ks[-1] != 15 or vector.requested_top_ks[-1] != 15:
        raise AssertionError("top_k > candidate_k 时底层请求深度应至少等于 top_k")

    print("验收通过: HybridRetriever RRF 工作正常")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
