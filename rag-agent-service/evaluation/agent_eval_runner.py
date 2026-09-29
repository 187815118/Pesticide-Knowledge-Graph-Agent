import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.agent_runner import run_agent
from evaluation.agent_evaluator import (
    evaluate_agent_result,
    load_agent_eval_queries,
    summarize_agent_results,
)


EVAL_QUERIES_PATH = ROOT / "data" / "agent_eval_queries.json"
RETRIEVAL_RESULTS_PATH = ROOT / "evaluation" / "results" / "retrieval_eval_results.json"
DEFAULT_RESULTS_PATH = ROOT / "evaluation" / "results" / "agent_eval_frozen_v3.json"


def _load_retrieval_metrics(path: Path) -> Dict[str, float]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    overall = (
        payload.get("hybrid_rrf", {}).get("overall", {})
        or payload.get("hybrid", {}).get("overall", {})
    )
    return {
        "retrieval_hit1": overall.get("Hit@1"),
        "retrieval_hit3": overall.get("Hit@3"),
        "retrieval_hit5": overall.get("Hit@5"),
    }


def _summary_payload(
    cases: List[Dict[str, Any]], retrieval_results_path: Path
) -> Dict[str, Any]:
    agent_summary = summarize_agent_results(cases)
    overall = agent_summary["overall"]
    return {
        "num_cases": overall.get("query_count", 0),
        **_load_retrieval_metrics(retrieval_results_path),
        "tool_selection_accuracy": overall.get("tool_selection_accuracy", 0.0),
        "tool_sequence_accuracy": overall.get("tool_sequence_accuracy", 0.0),
        "entity_propagation_accuracy": overall.get(
            "entity_propagation_accuracy", 0.0
        ),
        "citation_presence_accuracy": overall.get(
            "citation_presence_accuracy", 0.0
        ),
        "citation_validity_accuracy": overall.get(
            "citation_validity_accuracy", 0.0
        ),
        "answer_entity_accuracy": overall.get("answer_entity_accuracy", 0.0),
        "required_fact_accuracy": overall.get("required_fact_accuracy", 0.0),
        "no_answer_accuracy": overall.get("no_answer_accuracy", 1.0),
        "answer_accuracy": overall.get("answer_accuracy", 0.0),
        "error_rate": overall.get("error_rate", 0.0),
    }


def _write_results(
    output_path: Path,
    eval_path: Path,
    retrieval_results_path: Path,
    cases: List[Dict[str, Any]],
) -> Dict[str, Any]:
    category_summary = summarize_agent_results(cases).get("by_category", {})
    version_path = eval_path.with_name("agent_eval_queries.version.json")
    version = {}
    if version_path.exists():
        version = json.loads(version_path.read_text(encoding="utf-8"))
    payload = {
        "metadata": {
            "dataset_version": version.get("dataset_version", "unversioned"),
            "eval_queries_path": str(eval_path),
            "retrieval_results_path": str(retrieval_results_path),
            "completed_query_count": len(cases),
            "answer_evaluation": "deterministic_entities_and_required_keywords",
            "llm_judge": "disabled",
        },
        "summary": _summary_payload(cases, retrieval_results_path),
        "by_category": category_summary,
        "cases": cases,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return payload


def run_evaluation(
    eval_queries: List[Dict[str, Any]],
    agent_fn: Callable[[str], Dict[str, Any]],
    output_path: Optional[Path] = None,
    eval_path: Path = EVAL_QUERIES_PATH,
    retrieval_results_path: Path = RETRIEVAL_RESULTS_PATH,
) -> Dict[str, Any]:
    cases: List[Dict[str, Any]] = []
    for item in eval_queries:
        result = None
        error = None
        try:
            result = agent_fn(item["question"])
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"

        automatic_evaluation = evaluate_agent_result(item, result=result, error=error)
        record = {
            "id": item["id"],
            "category": item["category"],
            "question": item["question"],
            "expected_tools": item.get("expected_tools", []),
            "expected_tool_sequence": item.get(
                "expected_tool_sequence", item.get("expected_tools", [])
            ),
            "expected_entities": item.get("expected_entities", []),
            "expected_keywords": item.get("expected_keywords", []),
            "requires_citation": item.get("requires_citation", False),
            "requires_no_answer": item.get("requires_no_answer", False),
            "answer": "" if result is None else result.get("answer", ""),
            "tool_trace": [] if result is None else result.get("tool_trace", []),
            "execution_state": (
                {} if result is None else result.get("execution_state", {})
            ),
            "automatic_evaluation": automatic_evaluation,
            "error": error,
        }
        cases.append(record)
        if output_path is not None:
            _write_results(
                output_path, eval_path, retrieval_results_path, cases
            )
        print(
            f"{record['id']}: tools={automatic_evaluation['actual_tools']} "
            f"pass={automatic_evaluation['task_completed_rule']} error={error or '-'}"
        )

    if output_path is None:
        return {
            "summary": _summary_payload(cases, retrieval_results_path),
            "by_category": summarize_agent_results(cases).get("by_category", {}),
            "cases": cases,
        }
    return _write_results(output_path, eval_path, retrieval_results_path, cases)


def _print_summary(summary: Dict[str, Any]) -> None:
    print("\nAgent Eval Summary")
    print("-" * 56)
    for key, value in summary.items():
        rendered = f"{value:.4f}" if isinstance(value, float) else str(value)
        print(f"{key:<38} {rendered:>16}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the unified Agent Eval Harness.")
    parser.add_argument("--input", type=Path, default=EVAL_QUERIES_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_RESULTS_PATH)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--retrieval-results", type=Path, default=RETRIEVAL_RESULTS_PATH
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.limit is not None and args.limit <= 0:
        print("--limit must be greater than 0", file=sys.stderr)
        return 1
    eval_queries = load_agent_eval_queries(args.input)
    if args.limit is not None:
        eval_queries = eval_queries[: args.limit]
    payload = run_evaluation(
        eval_queries,
        run_agent,
        output_path=args.output,
        eval_path=args.input,
        retrieval_results_path=args.retrieval_results,
    )
    _print_summary(payload["summary"])
    print(f"\nSaved: {args.output}")
    return 1 if payload["summary"].get("error_rate", 0.0) > 0.0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
