import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.pesticide_query import query_pesticides_by_active_substance


def main() -> int:
    try:
        result = query_pesticides_by_active_substance("spinetoram")
    except Exception as exc:
        print(f"验收失败: 查询执行异常: {exc}", file=sys.stderr)
        return 1

    lowered = [name.lower() for name in result]
    expected = [
        "yates success ultra insect control",
        "sparta",
    ]
    missing = [e for e in expected if e not in lowered]
    if missing:
        print(f"验收失败: 结果缺少预期项目: {missing}，实际结果: {result}", file=sys.stderr)
        return 1

    print("验收通过: 查询结果包含预期农药")
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())