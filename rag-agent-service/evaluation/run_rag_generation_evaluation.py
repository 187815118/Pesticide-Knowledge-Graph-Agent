import argparse
import json
import os
import sys
import time
from pathlib import Path

from openai import OpenAI


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evaluation.rag_generation_evaluator import (
    aggregate_generation_metrics,
    evaluate_generation_result,
    load_generation_eval_queries,
)


OPENROUTER_BASE_URL = "https:" + "//" + "openrouter.ai/api/v1"
DEFAULT_MODEL = 'nvidia/nemotron-3-ultra-550b-a55b:free'
DEFAULT_RRF_K = 60
DEFAULT_CANDIDATE_K = 10
DEFAULT_TOP_K = 5
DEFAULT_DELAY_SECONDS = 3.2
DEFAULT_TEMPERATURE = 0.0
DEFAULT_MAX_ATTEMPTS = 2
DEFAULT_RETRY_DELAY_SECONDS = 5.0

CORPUS_PATH = ROOT / "data" / "active_substance_docs.jsonl"
DATASET_PATH = ROOT / "data" / "rag_generation_eval_queries.json"
DEFAULT_OUTPUT_PATH = ROOT / "evaluation" / "results" / "rag_generation_eval_results.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run grounded RAG generation evaluation.")
    parser.add_argument("--device", default="cpu", help="VectorRetriever device, e.g. cpu or cuda.")
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K, help="GroundedRAG evidence top-k.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="OpenRouter model id.")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Path for RAG generation evaluation results JSON.",
    )
    parser.add_argument(
        "--delay-seconds",
        type=float,
        default=DEFAULT_DELAY_SECONDS,
        help="Sleep time between adjacent LLM queries.",
    )
    return parser.parse_args()


def _make_client() -> OpenAI:
    if not os.environ.get("OPENROUTER_API_KEY"):
        raise RuntimeError("缺少 OPENROUTER_API_KEY 环境变量，无法调用 OpenRouter。")

    return OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=os.environ["OPENROUTER_API_KEY"],
    )


def _print_metric(name: str, value) -> None:
    if value is None:
        print(f"{name}: null")
    elif isinstance(value, float):
        print(f"{name}: {value:.6f}")
    else:
        print(f"{name}: {value}")


def print_summary(overall: dict) -> None:
    print("=== RAG Generation Evaluation Overall ===")
    for key in [
        "total_queries",
        "answer_queries",
        "insufficient_queries",
        "citation_presence_rate",
        "valid_citation_rate",
        "retrieval_expected_entity_coverage_macro",
        "evidence_conditioned_entity_recall_macro",
        "generation_evaluable_rate",
        "entity_as_citation_violation_rate",
        "insufficient_accuracy",
        "zh_language_match_rate",
        "automatic_rule_pass_rate",
    ]:
        _print_metric(key, overall[key])


def main() -> int:
    args = parse_args()
    if args.top_k <= 0:
        print("验收失败: --top-k must be greater than 0.", file=sys.stderr)
        return 1
    if args.delay_seconds < 0:
        print("验收失败: --delay-seconds must be non-negative.", file=sys.stderr)
        return 1

    try:
        client = _make_client()
    except RuntimeError as exc:
        print(f"验收失败: {exc}", file=sys.stderr)
        return 1

    from rag.grounded_rag import GroundedRAG
    from retrieval.bm25_retriever import BM25Retriever
    from retrieval.hybrid_retriever import HybridRetriever
    from retrieval.vector_retriever import DEFAULT_MODEL_NAME, VectorRetriever

    eval_queries = load_generation_eval_queries(DATASET_PATH)

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
        model=args.model,
        top_k=args.top_k,
        temperature=DEFAULT_TEMPERATURE,
    )

    per_query = []
    for index, item in enumerate(eval_queries):
        if index > 0 and args.delay_seconds > 0:
            time.sleep(args.delay_seconds)
        rag_result = _answer_with_retry(rag, item)
        if rag_result is None:
            return 1
        per_query.append(evaluate_generation_result(item, rag_result))
        _write_results(
            args.output,
            _build_output(args, eval_queries, per_query),
        )
        print(f"Evaluated {item['id']}: automatic_rule_pass={per_query[-1]['automatic_metrics']['automatic_rule_pass']}")

    output = _build_output(args, eval_queries, per_query)
    _write_results(args.output, output)

    print_summary(output["overall"])
    print(f"Saved results JSON: {args.output}")

    return 0


def _build_output(args, eval_queries, per_query):
    overall = aggregate_generation_metrics(per_query)
    category_breakdown = _category_breakdown(per_query)
    return {
        "metadata": {
            "dataset": str(DATASET_PATH),
            "requested_model": args.model,
            "top_k": args.top_k,
            "retrieval_method": "RRF Hybrid",
            "rrf_k": DEFAULT_RRF_K,
            "candidate_k": DEFAULT_CANDIDATE_K,
            "temperature": DEFAULT_TEMPERATURE,
            "max_attempts": DEFAULT_MAX_ATTEMPTS,
            "retry_delay_seconds": DEFAULT_RETRY_DELAY_SECONDS,
            "query_count": len(eval_queries),
            "completed_query_count": len(per_query),
        },
        "overall": overall,
        "category_breakdown": category_breakdown,
        "per_query": per_query,
    }


def _write_results(output_path: Path, output: dict) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _answer_with_retry(rag, item):
    last_exception = None
    for attempt in range(1, DEFAULT_MAX_ATTEMPTS + 1):
        try:
            return rag.answer(item["query"])
        except Exception as exc:
            last_exception = exc
            if attempt < DEFAULT_MAX_ATTEMPTS:
                print(
                    f"Attempt {attempt} failed for {item['id']}: {exc}",
                    file=sys.stderr,
                )
                time.sleep(DEFAULT_RETRY_DELAY_SECONDS)
            else:
                print(
                    f"Evaluation failed at {item['id']} after {DEFAULT_MAX_ATTEMPTS} attempts: {last_exception}",
                    file=sys.stderr,
                )
    return None


def _category_breakdown(per_query):
    from evaluation.rag_generation_evaluator import summarize_generation_by_category

    return summarize_generation_by_category(per_query)


if __name__ == "__main__":
    raise SystemExit(main())
