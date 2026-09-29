import os
from typing import Any, Dict, List
import requests
from requests.auth import HTTPBasicAuth

NEO4J_URL = os.getenv("NEO4J_HTTP_URL", "http://localhost:7474/db/data/transaction/commit")


def _query_names(statement: str, parameters: Dict[str, Any], column: str) -> List[str]:
    password = os.getenv("NEO4J_PASSWORD")
    if not password:
        raise RuntimeError("环境变量 NEO4J_PASSWORD 未设置，无法连接 Neo4j。")
    payload = {"statements": [{"statement": statement, "parameters": parameters, "resultDataContents": ["row"]}]}
    try:
        response = requests.post(NEO4J_URL, json=payload, auth=HTTPBasicAuth(os.getenv("NEO4J_USER", "neo4j"), password), timeout=10)
    except requests.RequestException as exc:
        raise RuntimeError(f"HTTP 请求失败: {exc}") from exc
    if not response.ok:
        raise RuntimeError(f"Neo4j 返回 HTTP {response.status_code}: {response.text}")
    try:
        data = response.json()
    except ValueError as exc:
        raise RuntimeError(f"Neo4j 返回了非 JSON 响应: {response.text}") from exc
    if data.get("errors"):
        raise RuntimeError(f"Neo4j 返回 errors: {data['errors']}")
    results = data.get("results", [])
    if not results:
        return []
    columns = results[0].get("columns", [])
    index = columns.index(column) if column in columns else 0
    names: List[str] = []
    for item in results[0].get("data", []):
        row = item.get("row", [])
        if len(row) > index and isinstance(row[index], str) and row[index] not in names:
            names.append(row[index])
    return names


def query_active_substance(pesticide_name: str) -> List[str]:
    return _query_names("MATCH (p:Pesticide {name: {pesticide_name}})-[:INCLUDES3]-(a:ActiveSubstance) RETURN DISTINCT a.name AS active_substance_name", {"pesticide_name": pesticide_name}, "active_substance_name")


def query_pesticides_by_active_substance(active_substance_name: str) -> List[str]:
    return _query_names("MATCH (p:Pesticide)-[:INCLUDES3]-(a:ActiveSubstance) WHERE toLower(a.name) = toLower({active_substance_name}) RETURN DISTINCT p.name AS pesticide_name", {"active_substance_name": active_substance_name}, "pesticide_name")


def query_chemical_classes(active_substance_name: str) -> List[str]:
    return _query_names("MATCH (cc:ChemicalClasses)-[:INCLUDES2]->(a:ActiveSubstance) WHERE toLower(a.name) = toLower({active_substance_name}) AND cc.name <> '--' RETURN DISTINCT cc.name AS chemical_class_name", {"active_substance_name": active_substance_name}, "chemical_class_name")


def query_target_sites(active_substance_name: str) -> List[str]:
    return _query_names("MATCH (cc:ChemicalClasses)-[:INCLUDES2]->(a:ActiveSubstance), (cc)-[:DETERMINES1]->(t:TargetSite) WHERE toLower(a.name) = toLower({active_substance_name}) AND cc.name <> '--' AND t.name <> '--' RETURN DISTINCT t.name AS target_site_name", {"active_substance_name": active_substance_name}, "target_site_name")


def query_modes_of_action(active_substance_name: str) -> List[str]:
    return _query_names("MATCH (cc:ChemicalClasses)-[:INCLUDES2]->(a:ActiveSubstance), (cc)-[:DETERMINES1]->(t:TargetSite), (t)-[:DETERMINES2]->(m:ModeOfAction) WHERE toLower(a.name) = toLower({active_substance_name}) AND cc.name <> '--' AND t.name <> '--' AND m.name <> '--' RETURN DISTINCT m.name AS mode_of_action_name", {"active_substance_name": active_substance_name}, "mode_of_action_name")
