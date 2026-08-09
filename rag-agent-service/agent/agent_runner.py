import json
import os
import time
from typing import Any, Dict, List

from openai import OpenAI

from .tool_registry import TOOLS, execute_tool


DEFAULT_LLM_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_LLM_MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"
TEMPERATURE = 0.0
MAX_AGENT_STEPS = 5
MAX_LLM_ATTEMPTS = 2
RETRY_DELAY_SECONDS = 5.0

SYSTEM_PROMPT = """你是一个农药知识查询助手。
- 农药事实必须优先通过提供的工具查询，不要凭模型自身知识猜测。
- 如果问题需要多个步骤，可以根据前一个 Tool 的结果继续调用其他 Tool。
- 最终答案必须基于 Tool 返回结果。
- Tool 返回的实体名称必须逐字原样使用。
- 不允许翻译、纠正、补全、变形、规范化或猜测实体名称。
- 最终答案中的事实和实体必须严格来自 Tool 返回结果。
- 如果需要引用某个 Tool 返回的名称，应直接复制该字符串，不自行修改。
- 当 hybrid_rag_query Tool 返回的 answer 包含 [D1]、[D2] 等 evidence citation 时，最终答案必须保留这些 citation。
- citation 应跟随它原本支持的 factual claim。
- 禁止删除 hybrid_rag_query Tool answer 中已有的 citation。
- 禁止自行创建 Tool 返回中不存在的 [D#] citation。
- 禁止修改 citation label，例如 [D1] 不能变成 [abamectin]、[1] 等。
- 如果最终答案使用了 hybrid_rag_query 返回的事实，则必须保留相应 Tool answer 中已有的 citation。
"""

FINAL_SYNTHESIS_SYSTEM_PROMPT = """你是一个农药知识查询助手，负责基于工具执行结果生成最终答案。
- 完整回答原始用户问题中的所有子问题。
- 必须保留 structured execution state 中重要的 KG 中间事实。
- 不得虚构 observations 中没有的信息。
- 如果使用 hybrid_rag_query 返回的事实，必须保留其 answer 中已有的 [D#] citation。
- 禁止创建 observation 中不存在的 [D#] citation。
- 禁止修改 citation label，例如 [D1] 不能变成 [abamectin]、[1] 等。
- KG 查询结果本身不强制添加 [D#] citation。
- 如果 Tool 返回空结果，明确说明没有查到，不自行猜测。
- 回答语言跟随用户问题语言。
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
    api_key = os.environ.get("LLM_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("缺少 LLM_API_KEY 或 OPENROUTER_API_KEY 环境变量，无法调用 LLM backend。")

    return OpenAI(
        base_url=os.environ.get("LLM_BASE_URL", DEFAULT_LLM_BASE_URL),
        api_key=api_key,
    )


def _get_llm_model() -> str:
    return os.environ.get("LLM_MODEL", DEFAULT_LLM_MODEL)


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


def _request_llm_message(
    client: OpenAI,
    messages: List[Dict[str, Any]],
    tools=None,
    tool_choice=None,
):
    last_error = None
    for attempt in range(1, MAX_LLM_ATTEMPTS + 1):
        try:
            completion_kwargs = {
                "model": _get_llm_model(),
                "messages": messages,
                "temperature": TEMPERATURE,
            }
            if tools is not None:
                completion_kwargs["tools"] = tools
            if tool_choice is not None:
                completion_kwargs["tool_choice"] = tool_choice

            response = client.chat.completions.create(**completion_kwargs)
            if response is None:
                raise RuntimeError("LLM/API 返回 response is None")
            if response.choices is None:
                raise RuntimeError("LLM/API 返回 response.choices is None")
            if not response.choices:
                raise RuntimeError("LLM/API 返回 response.choices 为空")

            return response.choices[0].message
        except Exception as exc:
            last_error = exc
            if attempt < MAX_LLM_ATTEMPTS:
                time.sleep(RETRY_DELAY_SECONDS)
                continue
            raise RuntimeError(
                f"LLM/API 请求失败，已尝试 {MAX_LLM_ATTEMPTS} 次: {last_error}"
            ) from exc


def _build_final_synthesis_messages(
    user_query: str,
    execution_state: Dict[str, Any],
    candidate_answer: str,
) -> List[Dict[str, Any]]:
    synthesis_payload = {
        "user_question": user_query,
        "execution_state": execution_state,
        "candidate_answer": candidate_answer,
    }
    return [
        {"role": "system", "content": FINAL_SYNTHESIS_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Use only this structured execution state and candidate answer "
                "to produce the final answer:\n"
                f"{json.dumps(synthesis_payload, ensure_ascii=False, indent=2, default=str)}"
            ),
        },
    ]


def _synthesize_final_answer(
    client: OpenAI,
    user_query: str,
    execution_state: Dict[str, Any],
    candidate_answer: str,
) -> str:
    synthesis_messages = _build_final_synthesis_messages(
        user_query,
        execution_state,
        candidate_answer,
    )
    message = _request_llm_message(client, synthesis_messages)
    return message.content or ""


def run_agent(user_query: str) -> Dict[str, Any]:
    client = _make_client()
    tools = _build_openai_tools_schema()
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_query},
    ]
    tool_trace: List[Dict[str, Any]] = []
    execution_state: Dict[str, Any] = {
        "user_question": user_query,
        "observations": [],
    }

    for _ in range(MAX_AGENT_STEPS):
        message = _request_llm_message(
            client,
            messages,
            tools=tools,
            tool_choice="auto",
        )

        tool_calls = message.tool_calls or []

        if not tool_calls:
            candidate_answer = message.content or ""
            final_answer = _synthesize_final_answer(
                client,
                user_query,
                execution_state,
                candidate_answer,
            )
            return {
                "answer": final_answer,
                "tool_trace": tool_trace,
                "execution_state": execution_state,
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
            execution_state["observations"].append(
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
