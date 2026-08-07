import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent.agent_runner import run_agent


QUERY = "Sparta 的活性成分是什么？还有哪些农药使用相同的活性成分？"


def main() -> int:
    try:
        result = run_agent(QUERY)
    except Exception as exc:
        print(f"验收失败: Agent 执行异常: {exc}", file=sys.stderr)
        return 1

    print("最终答案:")
    print(result["answer"])
    print()
    print("tool_trace:")
    print(json.dumps(result["tool_trace"], ensure_ascii=False, indent=2))

    called_tools = [item["tool"] for item in result["tool_trace"]]
    expected_tools = [
        "query_active_substance",
        "query_pesticides_by_active_substance",
    ]
    missing = [tool for tool in expected_tools if tool not in called_tools]
    if missing:
        print(f"验收失败: tool_trace 缺少真实调用: {missing}", file=sys.stderr)
        return 1

    print("验收通过: Agent 真实调用了两个必需 Tool。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
