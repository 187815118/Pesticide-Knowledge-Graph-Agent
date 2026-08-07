import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.pesticide_query import query_active_substance


def main() -> int:
    try:
        result = query_active_substance("Kenja 400 SC")
    except Exception as exc:
        print(f"验收失败: 查询执行异常: {exc}", file=sys.stderr)
        return 1

    lowered = [name.lower() for name in result]
    if "isofetamid" not in lowered:
        print(f"验收失败: 结果不包含 isofetamid，实际结果: {result}", file=sys.stderr)
        return 1

    print("验收通过: 查询结果包含 isofetamid")
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())