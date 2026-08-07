import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent.tool_registry import execute_tool


def main() -> int:
    # Test active substance lookup by pesticide name
    try:
        res1 = execute_tool("query_active_substance", {"pesticide_name": "Sparta"})
    except Exception as exc:
        print(f"验收失败: 调用 query_active_substance 异常: {exc}")
        return 1

    lowered1 = [r.lower() for r in res1]
    if "spinetoram" not in lowered1:
        print(f"验收失败: query_active_substance 结果不包含 spinetoram，实际: {res1}")
        return 1

    # Test pesticide lookup by active substance
    try:
        res2 = execute_tool("query_pesticides_by_active_substance", {"active_substance_name": "spinetoram"})
    except Exception as exc:
        print(f"验收失败: 调用 query_pesticides_by_active_substance 异常: {exc}")
        return 1

    lowered2 = [r.lower() for r in res2]
    expected = ["sparta"]
    missing = [e for e in expected if e not in lowered2]
    if missing:
        print(f"验收失败: query_pesticides_by_active_substance 结果缺少: {missing}，实际: {res2}")
        return 1

    print("验收通过: tool registry 调用工作正常")
    print(res1)
    print(res2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())