import os

import requests
from requests.auth import HTTPBasicAuth


NEO4J_URL = "http://localhost:7474/db/data/transaction/commit"


def query_active_substance(pesticide_name: str) -> list[str]:
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    if not password:
        raise RuntimeError("环境变量 NEO4J_PASSWORD 未设置，无法连接 Neo4j。")

    payload = {
        "statements": [
            {
                "statement": (
                    "MATCH (p:Pesticide {name: {pesticide_name}})-[:INCLUDES3]-(a:ActiveSubstance) "
                    "RETURN DISTINCT a.name AS active_substance_name"
                ),
                "parameters": {"pesticide_name": pesticide_name},
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
        raise RuntimeError(f"HTTP 请求失败: {exc}") from exc

    if not response.ok:
        raise RuntimeError(f"Neo4j 返回 HTTP {response.status_code}: {response.text}")

    try:
        data = response.json()
    except ValueError as exc:
        raise RuntimeError(f"Neo4j 返回了非 JSON 响应: {response.text}") from exc

    errors = data.get("errors", [])
    if errors:
        raise RuntimeError(f"Neo4j 返回 errors: {errors}")

    results = data.get("results", [])
    if not results:
        return []

    rows = results[0].get("data", [])
    names: list[str] = []
    for item in rows:
        row = item.get("row", [])
        if row and isinstance(row[0], str):
            names.append(row[0])

    return names