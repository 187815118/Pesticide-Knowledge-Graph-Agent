import json
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer


DEFAULT_MODEL_NAME = "BAAI/bge-m3"
DEFAULT_CORPUS_PATH = Path(__file__).resolve().parents[1] / "data" / "active_substance_docs.jsonl"


class VectorRetriever:
    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        corpus_path: Optional[Path] = None,
        device: str = "cpu",
        batch_size: int = 8,
    ):
        self.model_name = model_name
        self.corpus_path = Path(corpus_path) if corpus_path is not None else DEFAULT_CORPUS_PATH
        self.device = device
        self.batch_size = batch_size

        self.documents = self._load_documents(self.corpus_path)
        self.model = SentenceTransformer(
            self.model_name,
            device=self.device,
            local_files_only=True,
        )
        self.embeddings = self.model.encode(
            [
                (doc.get("name") or "") + "\n" + (doc.get("content") or "")
                for doc in self.documents
            ],
            batch_size=self.batch_size,
            normalize_embeddings=True,
            show_progress_bar=True,
        )
        self.embeddings = np.asarray(self.embeddings)

    @property
    def document_count(self) -> int:
        return len(self.documents)

    def _load_documents(self, corpus_path: Path) -> List[Dict]:
        documents = []
        with corpus_path.open("r", encoding="utf-8") as jsonl_file:
            for line_number, line in enumerate(jsonl_file, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    doc = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"JSONL 解析失败: {corpus_path} 第 {line_number} 行"
                    ) from exc

                documents.append(
                    {
                        "id": doc.get("id", ""),
                        "name": doc.get("name", ""),
                        "content": doc.get("content", ""),
                        "source": doc.get("source", ""),
                    }
                )

        if not documents:
            raise RuntimeError(f"语料为空: {corpus_path}")

        return documents

    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query 必须是非空字符串。")
        if top_k <= 0:
            raise ValueError("top_k 必须大于 0。")

        query_embedding = self.model.encode(
            query,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        query_embedding = np.asarray(query_embedding)

        scores = self.embeddings @ query_embedding
        top_k = min(top_k, len(self.documents))
        ranked_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for rank, doc_index in enumerate(ranked_indices, start=1):
            doc = self.documents[doc_index]
            results.append(
                {
                    "rank": rank,
                    "id": doc.get("id", ""),
                    "name": doc.get("name", ""),
                    "score": float(scores[doc_index]),
                    "content": doc.get("content", ""),
                    "source": doc.get("source", ""),
                }
            )

        return results
