from typing import Any, Dict
import sys
from pathlib import Path

# Ensure rag-agent-service is importable when running from project root or tests
SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from tools.pesticide_query import (
    query_active_substance,
    query_pesticides_by_active_substance,
)
from tools.rag_query import hybrid_rag_query


def _make_tool(name: str, description: str, params_schema: Dict[str, Any], func):
    return {
        "name": name,
        "description": description,
        "parameters": params_schema,
        "callable": func,
    }


TOOLS = {
    "query_active_substance": _make_tool(
        name="query_active_substance",
        description="根据农药商品名查询其活性成分。",
        params_schema={
            "type": "object",
            "properties": {"pesticide_name": {"type": "string"}},
            "required": ["pesticide_name"],
        },
        func=query_active_substance,
    ),
    "query_pesticides_by_active_substance": _make_tool(
        name="query_pesticides_by_active_substance",
        description="根据活性成分名称查询使用该成分的农药产品。",
        params_schema={
            "type": "object",
            "properties": {"active_substance_name": {"type": "string"}},
            "required": ["active_substance_name"],
        },
        func=query_pesticides_by_active_substance,
    ),
    "hybrid_rag_query": _make_tool(
        name="hybrid_rag_query",
        description=(
            "使用 Hybrid RAG 回答语料中的长文本知识问题，适合活性成分 Introduction、"
            "mode of action、way of action、resistance 以及其他需要从文档证据生成答案的问题。"
            "不用于“农药商品名 ↔ 活性成分”的结构化关系查询；这类关系查询仍应使用 Neo4j tools。"
        ),
        params_schema={
            "type": "object",
            "properties": {"question": {"type": "string"}},
            "required": ["question"],
        },
        func=hybrid_rag_query,
    ),
}


def get_tools() -> Dict[str, Dict[str, Any]]:
    """返回所有注册的 tools 字典，按 name 索引。"""
    return TOOLS


def execute_tool(tool_name: str, arguments: Dict[str, Any]):
    """执行指定的 tool。

    简单行为：
    - 查找 tool 定义
    - 校验必填参数存在
    - 调用底层函数并返回结果
    """
    tool = TOOLS.get(tool_name)
    if not tool:
        raise KeyError(f"未知的 tool: {tool_name}")

    params_schema = tool.get("parameters", {})
    required = params_schema.get("required", [])
    for r in required:
        if r not in arguments:
            raise ValueError(f"缺少必要参数: {r}")

    func = tool.get("callable")
    # Call with keyword args only
    return func(**arguments)
