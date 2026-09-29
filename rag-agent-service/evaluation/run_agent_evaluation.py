"""Backward-compatible entry point for the unified Agent Eval Harness."""

try:
    from .agent_eval_runner import main
except ImportError:
    from agent_eval_runner import main


if __name__ == "__main__":
    raise SystemExit(main())
