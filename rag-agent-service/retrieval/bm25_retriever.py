import json
import re
from pathlib import Path
from typing import Dict, List

from rank_bm25 import BM25Okapi


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> List[str]:
    return TOKEN_PATTERN.findall((text or "").lower())


class BM25Retriever:
    def __init__(self, corpus_path):
        self.corpus_path = Path(corpus_path)
        self.documents = self._load_documents(self.corpus_path)
        tokenized_corpus = [
            tokenize((doc.get("name") or "") + "\n" + (doc.get("content") or ""))
            for doc in self.documents
        ]
        self.index = BM25Okapi(tokenized_corpus)

    def _load_documents(self, corpus_path: Path) -> List[Dict]:
        documents = []
        with corpus_path.open("r", encoding="utf-8") as jsonl_file:
            for line_number, line in enumerate(jsonl_file, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    documents.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"JSONL 解析失败: {corpus_path} 第 {line_number} 行"
                    ) from exc
        return documents

    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        if top_k <= 0:
            raise ValueError("top_k 必须大于 0。")

        query_tokens = tokenize(query)
        scores = self.index.get_scores(query_tokens)
        ranked = sorted(
            enumerate(scores),
            key=lambda item: item[1],
            reverse=True,
        )[:top_k]

        results = []
        for rank, (doc_index, score) in enumerate(ranked, start=1):
            doc = self.documents[doc_index]
            results.append(
                {
                    "rank": rank,
                    "id": doc.get("id", ""),
                    "name": doc.get("name", ""),
                    "score": float(score),
                    "content": doc.get("content", ""),
                    "source": doc.get("source", ""),
                }
            )
        return results
