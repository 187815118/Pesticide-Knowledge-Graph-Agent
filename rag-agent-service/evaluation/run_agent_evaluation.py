import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent.agent_runner import run_agent
from evaluation.agent_evaluator import (
    evaluate_agent_result,
    load_agent_eval_queries,
    summarize_agent_results,
)


EVAL_QUERIES_PATH = ROOT / "data" / "agent_eval_queries.json"
DEFAULT_RESULTS_PATH = ROOT / "evaluation" / "results" / "agent_eval_results.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate the frozen Agent baseline.")
    parser.add_argument(
        "--input",
        type=Path,
        default=EVAL_QUERIES_PATH,
        help="Path to frozen agent evaluation queries JSON.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_RESULTS_PATH,
        help="Path for checkpointed agent evaluation results JSON.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional number of queries to run for smoke testing.",
    )
    return parser.parse_args()


def _write_checkpoint(
    output_path: Path,
    eval_queries_path: Path,
    per_query: List[Dict[str, Any]],
) -> None:
    output = {
        "metadata": {
            "eval_queries_path": str(eval_queries_path),
            "completed_query_count": len(per_query),
            "judge": "automatic_rules_only_no_llm_judge",
        },
        "summary": summarize_agent_results(per_query),
        "per_query": per_query,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    if args.limit is not None and args.limit <= 0:
        print("验收失败: --limit must be greater than 0.", file=sys.stderr)
        return 1

    eval_queries = load_agent_eval_queries(args.input)
    if args.limit is not None:
        eval_queries = eval_queries[: args.limit]

    per_query: List[Dict[str, Any]] = []
    for item in eval_queries:
        result = None
        error = None
        try:
            result = run_agent(item["question"])
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"

        automatic_evaluation = evaluate_agent_result(
            item,
            result=result,
            error=error,
        )
        record = {
            "id": item["id"],
            "category": item["category"],
            "question": item["question"],
            "expected_tools": item.get("expected_tools", []),
            "expected_entities": item.get("expected_entities", []),
            "requires_citation": item.get("requires_citation", False),
            "answer": "" if result is None else result.get("answer", ""),
            "tool_trace": [] if result is None else result.get("tool_trace", []),
            "automatic_evaluation": automatic_evaluation,
            "error": error,
        }
        per_query.append(record)
        _write_checkpoint(args.output, args.input, per_query)
        print(
            f"{record['id']}: task_completed_rule="
            f"{automatic_evaluation['task_completed_rule']}"
        )

    print(f"Saved agent evaluation results: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
