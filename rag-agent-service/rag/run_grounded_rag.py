import argparse
import os
import sys
from pathlib import Path

from openai import OpenAI


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rag.grounded_rag import GroundedRAG
from retrieval.bm25_retriever import BM25Retriever
from retrieval.hybrid_retriever import HybridRetriever
from retrieval.vector_retriever import DEFAULT_MODEL_NAME, VectorRetriever


OPENROUTER_BASE_URL = 'https://openrouter.ai/api/v1'
MODEL = "openrouter/free"
CORPUS_PATH = ROOT / "data" / "active_substance_docs.jsonl"
DEFAULT_RRF_K = 60
DEFAULT_CANDIDATE_K = 10


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run grounded RAG over the pesticide corpus.")
    parser.add_argument("--question", required=True, help="User question to answer.")
    parser.add_argument("--device", default="cpu", help="VectorRetriever device, e.g. cpu or cuda.")
    parser.add_argument("--top-k", type=int, default=5, help="Number of evidence documents.")
    return parser.parse_args()


def _make_client() -> OpenAI:
    if not os.environ.get("OPENROUTER_API_KEY"):
        raise RuntimeError("缺少 OPENROUTER_API_KEY 环境变量，无法调用 OpenRouter。")

    return OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=os.environ["OPENROUTER_API_KEY"],
    )


def _print_evidence(evidence, retrieval_trace) -> None:
    print("=== Evidence ===")
    for item, trace in zip(evidence, retrieval_trace):
        print(f"[{item['label']}]")
        print(f"name: {item['name']}")
        print(f"id: {item['id']}")
        print(f"source: {item['source']}")
        print(f"hybrid rank: {item['retrieval_rank']}")
        print(f"hybrid score: {item['retrieval_score']}")
        print(f"bm25 rank: {trace.get('bm25_rank')}")
        print(f"vector rank: {trace.get('vector_rank')}")
        print()


def main() -> int:
    args = parse_args()
    if args.top_k <= 0:
        print("验收失败: --top-k must be greater than 0.", file=sys.stderr)
        return 1

    try:
        client = _make_client()
    except RuntimeError as exc:
        print(f"验收失败: {exc}", file=sys.stderr)
        return 1

    bm25_retriever = BM25Retriever(CORPUS_PATH)
    vector_retriever = VectorRetriever(
        model_name=DEFAULT_MODEL_NAME,
        corpus_path=CORPUS_PATH,
        device=args.device,
    )
    hybrid_retriever = HybridRetriever(
        bm25_retriever,
        vector_retriever,
        rrf_k=DEFAULT_RRF_K,
        candidate_k=DEFAULT_CANDIDATE_K,
    )
    rag = GroundedRAG(
        retriever=hybrid_retriever,
        llm_client=client,
        model=MODEL,
        top_k=args.top_k,
    )

    result = rag.answer(args.question)

    print("=== Answer ===")
    print(result["answer"])
    print()
    _print_evidence(result["evidence"], result["retrieval_trace"])
    invalid_citations = result.get("invalid_citations") or []
    if invalid_citations:
        print(f"Invalid citations: {', '.join(invalid_citations)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
