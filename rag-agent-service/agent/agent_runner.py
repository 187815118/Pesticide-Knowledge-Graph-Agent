import json
import os
from typing import Any, Dict, List

from openai import OpenAI

from .tool_registry import TOOLS, execute_tool


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL = "openrouter/free"
MAX_AGENT_STEPS = 5

SYSTEM_PROMPT = """你是一个农药知识查询助手。
- 农药事实必须优先通过提供的工具查询，不要凭模型自身知识猜测。
- 如果问题需要多个步骤，可以根据前一个 Tool 的结果继续调用其他 Tool。
- 最终答案必须基于 Tool 返回结果。
- Tool 返回的实体名称必须逐字原样使用。
- 不允许翻译、纠正、补全、变形、规范化或猜测实体名称。
- 最终答案中的事实和实体必须严格来自 Tool 返回结果。
- 如果需要引用某个 Tool 返回的名称，应直接复制该字符串，不自行修改。
"""


def _build_openai_tools_schema() -> List[Dict[str, Any]]:
    """Expose only model-safe tool metadata to the LLM."""
    schemas: List[Dict[str, Any]] = []
    for tool in TOOLS.values():
        schemas.append(
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"],
                },
            }
        )
    return schemas


def _make_client() -> OpenAI:
    if not os.environ.get("OPENROUTER_API_KEY"):
        raise RuntimeError("缺少 OPENROUTER_API_KEY 环境变量，无法调用 OpenRouter。")

    return OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=os.environ["OPENROUTER_API_KEY"],
    )


def _decode_tool_arguments(tool_name: str, raw_arguments: str) -> Dict[str, Any]:
    try:
        arguments = json.loads(raw_arguments or "{}")
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Tool {tool_name} 的 arguments 不是合法 JSON: {raw_arguments}"
        ) from exc

    if not isinstance(arguments, dict):
        raise ValueError(f"Tool {tool_name} 的 arguments 必须是 JSON object。")

    return arguments


def _to_tool_content(result: Any) -> str:
    return json.dumps(result, ensure_ascii=False, default=str)


def run_agent(user_query: str) -> Dict[str, Any]:
    client = _make_client()
    tools = _build_openai_tools_schema()
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_query},
    ]
    tool_trace: List[Dict[str, Any]] = []

    for _ in range(MAX_AGENT_STEPS):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=tools,
                tool_choice="auto",
            )
        except Exception as exc:
            raise RuntimeError(f"LLM/API 请求失败: {exc}") from exc

        message = response.choices[0].message
        tool_calls = message.tool_calls or []

        if not tool_calls:
            return {
                "answer": message.content or "",
                "tool_trace": tool_trace,
            }

        messages.append(message.model_dump(exclude_none=True))

        for tool_call in tool_calls:
            if tool_call.type != "function":
                raise ValueError(f"不支持的 tool_call 类型: {tool_call.type}")

            tool_name = tool_call.function.name
            if tool_name not in TOOLS:
                raise KeyError(f"模型请求了未知 Tool: {tool_name}")

            arguments = _decode_tool_arguments(
                tool_name,
                tool_call.function.arguments,
            )

            try:
                result = execute_tool(tool_name, arguments)
            except Exception as exc:
                raise RuntimeError(
                    f"执行 Tool {tool_name} 失败，arguments={arguments}: {exc}"
                ) from exc

            tool_trace.append(
                {
                    "tool": tool_name,
                    "arguments": arguments,
                    "result": result,
                }
            )
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": _to_tool_content(result),
                }
            )

    raise RuntimeError(f"超过最大 Agent 步数限制: {MAX_AGENT_STEPS}")
