import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evaluation.retrieval_evaluator import CATEGORY_ORDER, METRIC_KEYS, evaluate_retriever, load_eval_queries
from retrieval.bm25_retriever import BM25Retriever
from retrieval.vector_retriever import DEFAULT_MODEL_NAME, VectorRetriever


CORPUS_PATH = ROOT / "data" / "active_substance_docs.jsonl"
EVAL_QUERIES_PATH = ROOT / "data" / "retrieval_eval_queries.json"
DEFAULT_RESULTS_PATH = ROOT / "evaluation" / "results" / "retrieval_eval_results.json"


def _format_metric(value: float) -> str:
    return f"{value:.6f}"


def print_metric_block(title: str, metrics: dict) -> None:
    print(title)
    print(f"Queries: {metrics['query_count']}")
    for metric in METRIC_KEYS:
        print(f"{metric}: {_format_metric(metrics[metric])}")


def print_by_category(title: str, by_category: dict) -> None:
    print(title)
    categories = [category for category in CATEGORY_ORDER if category in by_category]
    categories.extend(
        sorted(category for category in by_category if category not in CATEGORY_ORDER)
    )

    for category in categories:
        metrics = by_category[category]
        print(f"{category}:")
        print(f"  Queries: {metrics['query_count']}")
        for metric in METRIC_KEYS:
            print(f"  {metric}: {_format_metric(metrics[metric])}")
        print()


def print_evaluation(name: str, summary: dict) -> None:
    print_metric_block(f"=== {name} Overall ===", summary["overall"])
    print()
    print_by_category(f"=== {name} By Category ===", summary["by_category"])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate BM25 and Vector retrieval.")
    parser.add_argument("--device", default="cpu", help="VectorRetriever device, e.g. cpu or cuda.")
    parser.add_argument("--top-k", type=int, default=10, help="Retrieval depth; must be at least 10.")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_RESULTS_PATH,
        help="Path for retrieval evaluation metrics JSON.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.top_k < 10:
        print("验收失败: --top-k must be at least 10.", file=sys.stderr)
        return 1

    eval_queries = load_eval_queries(EVAL_QUERIES_PATH)

    bm25_retriever = BM25Retriever(CORPUS_PATH)
    vector_retriever = VectorRetriever(
        model_name=DEFAULT_MODEL_NAME,
        corpus_path=CORPUS_PATH,
        device=args.device,
    )

    bm25_summary = evaluate_retriever(bm25_retriever, eval_queries, top_k=args.top_k)
    vector_summary = evaluate_retriever(vector_retriever, eval_queries, top_k=args.top_k)

    print_evaluation("BM25", bm25_summary)
    print_evaluation("Vector", vector_summary)

    output = {
        "metadata": {
            "evaluation_query_count": len(eval_queries),
            "retrieval_depth": args.top_k,
            "eval_queries_path": str(EVAL_QUERIES_PATH),
            "corpus_path": str(CORPUS_PATH),
            "vector_model_name": vector_retriever.model_name,
            "vector_device": args.device,
        },
        "bm25": bm25_summary,
        "vector": vector_summary,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Saved metrics JSON: {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
