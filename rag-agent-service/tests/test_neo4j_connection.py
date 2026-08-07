import os
import sys

import requests
from requests.auth import HTTPBasicAuth


NEO4J_URL = "http://localhost:7474/db/data/transaction/commit"
QUERY = """
MATCH (p:Pesticide)-[:INCLUDES3]-(a:ActiveSubstance)
RETURN p.name, a.name
LIMIT 10
""".strip()


def main() -> int:
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")

    if not password:
        print("错误: 环境变量 NEO4J_PASSWORD 未设置，无法连接 Neo4j。", file=sys.stderr)
        return 1

    payload = {
        "statements": [
            {
                "statement": QUERY,
                "resultDataContents": ["row"],
            }
        ]
    }

    try:
        response = requests.post(
            NEO4J_URL,
            json=payload,
            auth=HTTPBasicAuth(user, password),
            timeout=10,
        )
    except requests.RequestException as exc:
        print(f"错误: HTTP 请求失败: {exc}", file=sys.stderr)
        return 1

    if not response.ok:
        print(f"错误: Neo4j 返回 HTTP {response.status_code}: {response.text}", file=sys.stderr)
        return 1

    try:
        data = response.json()
    except ValueError:
        print(f"错误: Neo4j 返回了非 JSON 响应: {response.text}", file=sys.stderr)
        return 1

    errors = data.get("errors", [])
    if errors:
        print(f"错误: Neo4j 返回 errors: {errors}", file=sys.stderr)
        return 1

    results = data.get("results", [])
    if not results:
        print("未查询到任何结果。")
        return 0

    rows = results[0].get("data", [])
    if not rows:
        print("未查询到任何结果。")
        return 0

    for item in rows:
        row = item.get("row", [])
        if len(row) >= 2:
            print(f"{row[0]} -> {row[1]}")
        else:
            print(row)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())