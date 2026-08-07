from typing import Dict, List, Optional


class HybridRetriever:
    def __init__(
        self,
        bm25_retriever,
        vector_retriever,
        rrf_k: int = 60,
        candidate_k: int = 10,
    ):
        if rrf_k <= 0:
            raise ValueError("rrf_k 必须大于 0。")
        if candidate_k <= 0:
            raise ValueError("candidate_k 必须大于 0。")

        self.bm25_retriever = bm25_retriever
        self.vector_retriever = vector_retriever
        self.rrf_k = rrf_k
        self.candidate_k = candidate_k

    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query 必须是非空字符串。")
        if top_k <= 0:
            raise ValueError("top_k 必须大于 0。")

        candidate_depth = max(self.candidate_k, top_k)
        bm25_results = self.bm25_retriever.search(query, top_k=candidate_depth)
        vector_results = self.vector_retriever.search(query, top_k=candidate_depth)

        fused = {}
        self._add_results(fused, bm25_results, "bm25")
        self._add_results(fused, vector_results, "vector")

        ranked = sorted(
            fused.values(),
            key=lambda item: (
                -item["score"],
                item["best_rank"],
                item["id"],
            ),
        )[:top_k]

        results = []
        for rank, item in enumerate(ranked, start=1):
            results.append(
                {
                    "rank": rank,
                    "id": item["id"],
                    "name": item.get("name", ""),
                    "score": float(item["score"]),
                    "content": item.get("content", ""),
                    "source": item.get("source", ""),
                    "bm25_rank": item.get("bm25_rank"),
                    "vector_rank": item.get("vector_rank"),
                    "bm25_score": item.get("bm25_score"),
                    "vector_score": item.get("vector_score"),
                }
            )

        return results

    def _add_results(self, fused: Dict, results: List[Dict], source: str) -> None:
        rank_key = f"{source}_rank"
        score_key = f"{source}_score"

        for fallback_rank, result in enumerate(results, start=1):
            doc_id = result.get("id", "")
            if not doc_id:
                continue
            if doc_id in fused and fused[doc_id].get(rank_key) is not None:
                continue

            source_rank = result.get("rank")
            if source_rank is None:
                source_rank = fallback_rank

            item = fused.setdefault(
                doc_id,
                {
                    "id": doc_id,
                    "name": result.get("name", ""),
                    "content": result.get("content", ""),
                    "source": result.get("source", ""),
                    "score": 0.0,
                    "best_rank": source_rank,
                    "bm25_rank": None,
                    "vector_rank": None,
                    "bm25_score": None,
                    "vector_score": None,
                },
            )

            item["best_rank"] = min(item["best_rank"], source_rank)
            item["score"] += 1.0 / (self.rrf_k + source_rank)
            item[rank_key] = source_rank
            item[score_key] = (
                None if result.get("score") is None else float(result.get("score"))
            )

            if not item.get("name") and result.get("name"):
                item["name"] = result.get("name", "")
            if not item.get("content") and result.get("content"):
                item["content"] = result.get("content", "")
            if not item.get("source") and result.get("source"):
                item["source"] = result.get("source", "")
