import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORPUS_PATH = PROJECT_ROOT /"rag-agent-service" / "data" / "active_substance_docs.jsonl"
MODEL_NAME = "BAAI/bge-m3"


def load_documents(corpus_path):
    documents = []
    with corpus_path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                documents.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number}: {exc}") from exc

    if not documents:
        raise RuntimeError(f"No documents found in corpus: {corpus_path}")

    return documents


def print_results(title, results):
    print(title)
    for rank, document, score in results:
        print(f"{rank}. {document.get('name', '')}\t{score:.6f}")


def main():
    documents = load_documents(CORPUS_PATH)
    texts = [
        f"{document.get('name', '')}\n{document.get('content', '')}"
        for document in documents
    ]

    model = SentenceTransformer(
        MODEL_NAME,
        device="cuda",
        local_files_only=True,
    )

    embeddings = model.encode(
        texts,
        batch_size=8,
        normalize_embeddings=True,
        show_progress_bar=True,
    )
    embeddings = np.asarray(embeddings)

    print(f"document count: {len(documents)}")
    print(f"embedding shape: {embeddings.shape}")

    def search(query, top_k=3):
        query_embedding = model.encode(
            query,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        query_embedding = np.asarray(query_embedding)
        scores = embeddings @ query_embedding
        top_indices = np.argsort(scores)[::-1][:top_k]

        return [
            (rank, documents[index], float(scores[index]))
            for rank, index in enumerate(top_indices, start=1)
        ]

    query_1 = "What is the mode of action of abamectin?"
    query_1_results = search(query_1, top_k=3)
    print_results(f"\nQuery 1: {query_1}\nTop-3:", query_1_results)

    top_1_name = query_1_results[0][1].get("name", "").strip().lower()
    if top_1_name != "abamectin":
        raise AssertionError(
            f"Expected Top-1 to be abamectin, got {query_1_results[0][1].get('name', '')}"
        )

    query_2 = "acetylcholinesterase inhibitor"
    query_2_results = search(query_2, top_k=5)
    print_results(f"\nQuery 2: {query_2}\nTop-5:", query_2_results)

    print("\n验收通过: BGE-M3 Dense Retrieval smoke test 工作正常")


if __name__ == "__main__":
    main()
