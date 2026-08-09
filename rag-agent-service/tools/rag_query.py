import os
import time
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_LLM_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_LLM_MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"
TEMPERATURE = 0.0
SERVICE_ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = SERVICE_ROOT / "data" / "active_substance_docs.jsonl"
DEFAULT_RRF_K = 60
DEFAULT_CANDIDATE_K = 10
DEFAULT_TOP_K = 5
DEFAULT_DEVICE = "cuda"
MAX_RAG_ATTEMPTS = 2
RAG_RETRY_DELAY_SECONDS = 5.0

_RAG_INSTANCE = None


def _make_client():
    api_key = os.environ.get("LLM_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("缺少 LLM_API_KEY 或 OPENROUTER_API_KEY 环境变量，无法调用 LLM backend。")

    from openai import OpenAI

    return OpenAI(
        base_url=os.environ.get("LLM_BASE_URL", DEFAULT_LLM_BASE_URL),
        api_key=api_key,
    )


def _get_llm_model() -> str:
    return os.environ.get("LLM_MODEL", DEFAULT_LLM_MODEL)


def _get_rag() -> Any:
    global _RAG_INSTANCE

    if _RAG_INSTANCE is None:
        from rag.grounded_rag import GroundedRAG
        from retrieval.bm25_retriever import BM25Retriever
        from retrieval.hybrid_retriever import HybridRetriever
        from retrieval.vector_retriever import DEFAULT_MODEL_NAME, VectorRetriever

        bm25_retriever = BM25Retriever(CORPUS_PATH)
        vector_retriever = VectorRetriever(
            model_name=DEFAULT_MODEL_NAME,
            corpus_path=CORPUS_PATH,
            device=DEFAULT_DEVICE,
        )
        hybrid_retriever = HybridRetriever(
            bm25_retriever,
            vector_retriever,
            rrf_k=DEFAULT_RRF_K,
            candidate_k=DEFAULT_CANDIDATE_K,
        )
        _RAG_INSTANCE = GroundedRAG(
            retriever=hybrid_retriever,
            llm_client=_make_client(),
            model=_get_llm_model(),
            top_k=DEFAULT_TOP_K,
            temperature=TEMPERATURE,
        )

    return _RAG_INSTANCE


def _compact_evidence(evidence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    compact = []
    for item in evidence:
        compact.append(
            {
                "label": item.get("label", ""),
                "id": item.get("id", ""),
                "name": item.get("name", ""),
                "source": item.get("source", ""),
                "retrieval_rank": item.get("retrieval_rank"),
            }
        )
    return compact


def hybrid_rag_query(question: str) -> Dict[str, Any]:
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question 必须是非空字符串。")

    rag = _get_rag()
    last_error = None
    for attempt in range(1, MAX_RAG_ATTEMPTS + 1):
        try:
            result = rag.answer(question)
            break
        except Exception as exc:
            last_error = exc
            if attempt < MAX_RAG_ATTEMPTS:
                time.sleep(RAG_RETRY_DELAY_SECONDS)
                continue
            raise RuntimeError(
                f"GroundedRAG answer 调用失败，已尝试 {MAX_RAG_ATTEMPTS} 次: {last_error}"
            ) from exc

    return {
        "answer": result.get("answer", ""),
        "evidence": _compact_evidence(result.get("evidence", [])),
        "retrieval_trace": result.get("retrieval_trace", []),
        "invalid_citations": result.get("invalid_citations", []),
    }
