import argparse
from pathlib import Path

from evaluation.fault_injection import run_fault_injection


DEFAULT_OUTPUT = Path(__file__).resolve().parent / "results" / "agent_fault_injection_v1.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic Agent fault injection benchmark.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = run_fault_injection(args.output)
    print("\nAgent Fault Injection Summary")
    print("-" * 56)
    for key, value in payload["summary"].items():
        print(f"{key:<44} {value:.4f}" if isinstance(value, float) else f"{key:<44} {value}")
    print(f"\nSaved: {args.output}")
    return 0 if all(case["passed"] for case in payload["cases"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
