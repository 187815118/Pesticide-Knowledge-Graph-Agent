import json
import os
import re
import time
from typing import Any, Dict, List, Optional

from openai import OpenAI

from .agent_harness import AgentState, COMPLETED, FAILED, NO_ANSWER, RUNNING
from .tool_registry import TOOLS, execute_tool
from runtime.checkpoint_store import CheckpointStore


DEFAULT_LLM_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_LLM_MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"
TEMPERATURE = 0.0
MAX_AGENT_STEPS = 5
MAX_LLM_ATTEMPTS = 2
RETRY_DELAY_SECONDS = 5.0
MAX_TOOL_ATTEMPTS = 2
TOOL_RETRY_DELAY_SECONDS = 1.0

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
- 当一个 Tool 返回了具体实体，并且后续 Tool 需要使用该实体时，必须把 Tool 返回的精确实体字符串写入下一步 Tool arguments。
- 禁止使用 "its active substance"、"the active substance"、"the previous result"、"that substance" 等模糊指代表达作为下游检索问题中的实体。
- 例如 query_active_substance("Sparta") -> ["spinetoram"] 后，下一步必须调用 hybrid_rag_query({"question":"What is the mode of action of spinetoram?"})。
- 如果用户只询问“商品名 ↔ 活性成分”的结构化关系，在 Neo4j Tool 已经给出结果后应直接回答，不要额外调用 hybrid_rag_query。
- 只有问题明确要求 knowledge graph / structured category / structured target 时，才使用 chemical class、target site、结构化 mode-of-action Neo4j Tool。
- 普通的 mode of action、mechanism explanation、resistance、Introduction 或 corpus 问题必须使用 hybrid_rag_query，不要用结构化 KG Tool 替代。
- Tool 返回空结果或 unsupported 时，不要猜测，说明当前知识库没有足够证据。
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
- 如果所有 Tool observation 都为空或 unsupported，返回明确的 no-answer。
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


def _ground_tool_arguments(
    state: AgentState,
    tool_name: str,
    arguments: Dict[str, Any],
) -> Dict[str, Any]:
    active_substance_tools = {
        "query_pesticides_by_active_substance", "query_chemical_classes",
        "query_target_sites", "query_modes_of_action",
    }
    resolved_entities = state.latest_active_substances()
    if tool_name in active_substance_tools and resolved_entities:
        grounded_arguments = dict(arguments)
        grounded_arguments["active_substance_name"] = resolved_entities[0]
        return grounded_arguments
    if tool_name != "hybrid_rag_query":
        return arguments

    question = arguments.get("question")
    if not isinstance(question, str):
        return arguments

    resolved_entities = state.latest_active_substances()
    if not resolved_entities or any(entity in question for entity in resolved_entities):
        return arguments

    grounded_arguments = dict(arguments)
    grounded_arguments["question"] = (
        f"{question.rstrip()} Resolved active substance: {resolved_entities[0]}."
    )
    return grounded_arguments


def _apply_tool_dispatch_guard(
    state: AgentState,
    tool_name: str,
    arguments: Dict[str, Any],
) -> tuple[str, Dict[str, Any], Optional[str]]:
    query = state.original_query
    lowered = query.lower()
    structured_markers = (
        "knowledge graph", "structured", "知识图谱", "chemical class",
        "mode-of-action category", "mode of action category",
    )
    text_knowledge_markers = (
        "mode of action", "mechanism", "resistance", "introduction", "corpus",
        "作用机制", "抗性", "作用方式", "语料", "manufacturer", "market price",
        "current price", "application dose", "spray interval", "ld50",
    )
    active_lookup_markers = (
        "active substance of", "active substance in", "active substance does",
        "contains which active substance", "active substance is in",
        "identify the active substance", "'s active substance", "活性成分",
    )
    structured_tools = {
        "query_chemical_classes", "query_target_sites", "query_modes_of_action"
    }
    explicitly_structured = any(marker in lowered for marker in structured_markers)
    asks_text_knowledge = any(marker in lowered for marker in text_knowledge_markers)
    asks_active_lookup = any(marker in lowered for marker in active_lookup_markers)

    should_use_rag = tool_name in structured_tools and not explicitly_structured
    should_use_rag = should_use_rag or (
        tool_name == "query_active_substance"
        and asks_text_knowledge
        and not asks_active_lookup
    )
    if not should_use_rag:
        return tool_name, arguments, None

    entities = state.latest_active_substances()
    if not entities:
        entities = [
            value for value in arguments.values() if isinstance(value, str) and value.strip()
        ]
    rag_question = query
    if entities and entities[0] not in rag_question:
        rag_question = f"{rag_question.rstrip()} Resolved active substance: {entities[0]}."
    return (
        "hybrid_rag_query",
        {"question": rag_question},
        "text_knowledge_requires_hybrid_rag",
    )


def _ground_final_citations(final_answer: str, state: AgentState) -> str:
    allowed = {
        f"[{item.get('label')}]"
        for item in state.evidence
        if isinstance(item, dict) and item.get("label")
    }

    def replace_citation(match):
        citation = match.group(0)
        return citation if citation in allowed else ""

    grounded_answer = re.sub(r"\[D[1-9]\d*\]", replace_citation, final_answer or "")
    if allowed and not re.search(r"\[D[1-9]\d*\]", grounded_answer):
        available = [citation for citation in state.citations if citation in allowed]
        if available:
            grounded_answer = f"{grounded_answer.rstrip()} {available[0]}"
    return grounded_answer


def _ground_final_entities(final_answer: str, state: AgentState) -> str:
    missing = [
        entity for entity in state.resolved_entities
        if entity and entity not in (final_answer or "")
    ]
    if not missing:
        return final_answer
    return f"{final_answer.rstrip()}\nGrounded entities: {'; '.join(missing)}."


def _execute_tool_with_retry(
    state: AgentState,
    tool_name: str,
    arguments: Dict[str, Any],
    checkpoint_store: Optional[CheckpointStore] = None,
    execute_fn=None,
) -> Any:
    if state.has_completed_result(tool_name, arguments):
        completed_result = state.completed_result(tool_name, arguments)
        state.record_success(
            tool_name,
            arguments,
            completed_result,
            latency_ms=0.0,
            attempts=0,
            reused=True,
            resumed=state.resumed,
        )
        if checkpoint_store is not None:
            checkpoint_store.save(state)
        return completed_result

    started_at = time.perf_counter()
    last_error = None
    tool_executor = execute_fn or execute_tool
    for attempt in range(1, MAX_TOOL_ATTEMPTS + 1):
        try:
            result = tool_executor(tool_name, arguments)
            state.record_success(
                tool_name,
                arguments,
                result,
                latency_ms=(time.perf_counter() - started_at) * 1000,
                attempts=attempt,
                resumed=state.resumed,
            )
            if checkpoint_store is not None:
                checkpoint_store.save(state)
            return result
        except Exception as exc:
            last_error = exc
            if attempt < MAX_TOOL_ATTEMPTS:
                time.sleep(TOOL_RETRY_DELAY_SECONDS)
                continue

    state.record_failure(
        tool_name,
        arguments,
        latency_ms=(time.perf_counter() - started_at) * 1000,
        attempts=MAX_TOOL_ATTEMPTS,
        error=last_error,
    )
    if checkpoint_store is not None:
        checkpoint_store.save(state)
    raise RuntimeError(
        f"执行 Tool {tool_name} 失败，已尝试 {MAX_TOOL_ATTEMPTS} 次，"
        f"此前成功的 Tool 结果保留在 AgentState 中: {last_error}"
    ) from last_error


def _compact_result_for_planning(tool_name: str, result: Any) -> Any:
    if tool_name == "hybrid_rag_query" and isinstance(result, dict):
        compact_result = {
            "answer": result.get("answer", ""),
            "invalid_citations": result.get("invalid_citations", []),
        }
        evidence = []
        for item in result.get("evidence", []):
            if isinstance(item, dict):
                evidence.append(
                    {
                        "label": item.get("label", ""),
                        "id": item.get("id", ""),
                        "name": item.get("name", ""),
                        "source": item.get("source", ""),
                        "retrieval_rank": item.get("retrieval_rank"),
                    }
                )
        if evidence:
            compact_result["evidence"] = evidence
        return compact_result

    return result


def _build_planning_state_message(planning_observations: List[Dict[str, Any]]) -> Dict[str, str]:
    payload = {
        "resolved_observations": planning_observations,
        "instruction": (
            "For any later tool call, use exact entity strings from resolved_observations "
            "inside tool arguments. Do not use vague references such as its active substance, "
            "the active substance, the previous result, or that substance."
        ),
    }
    return {
        "role": "user",
        "content": (
            "Structured execution state for subsequent tool planning:\n"
            f"{json.dumps(payload, ensure_ascii=False, indent=2, default=str)}"
        ),
    }


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


def _compact_execution_state_for_synthesis(state: AgentState) -> Dict[str, Any]:
    observations = [
        {
            "tool": item.get("tool"),
            "arguments": item.get("arguments", {}),
            "result": _compact_result_for_planning(
                item.get("tool", ""), item.get("result")
            ),
        }
        for item in state.observations
    ]
    return {
        "task_id": state.task_id,
        "original_query": state.original_query,
        "current_query": state.current_query,
        "resolved_entities": state.resolved_entities,
        "observations": observations,
        "evidence": state.evidence,
        "citations": state.citations,
        "step_count": state.step_count,
        "status": state.status,
    }


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


def _no_answer_text(user_query: str) -> str:
    return "当前知识库中没有足够证据回答该问题。" if re.search(r"[\u4e00-\u9fff]", user_query) else "The current knowledge base does not contain enough evidence to answer this question."


def _result_payload(state: AgentState) -> Dict[str, Any]:
    return {"task_id": state.task_id, "answer": state.final_answer, "tool_trace": state.tool_history, "execution_state": state.to_dict()}


def run_agent(user_query: Optional[str] = None, task_id: Optional[str] = None, checkpoint_store: Optional[CheckpointStore] = None, resume: bool = False) -> Dict[str, Any]:
    store = checkpoint_store or CheckpointStore()
    if resume:
        if not task_id:
            raise ValueError("resume=True 时必须提供 task_id。")
        state = store.load(task_id)
        if state.status in {COMPLETED, NO_ANSWER}:
            return _result_payload(state)
        previous_status = state.status
        start_step = max(1, state.step_count + (0 if previous_status == FAILED else 1))
        state.record_resume()
        store.save(state)
        user_query = state.original_query
    else:
        if not isinstance(user_query, str) or not user_query.strip():
            raise ValueError("user_query 必须是非空字符串。")
        state = AgentState(original_query=user_query.strip())
        if task_id:
            state.task_id = task_id
        user_query, start_step = state.original_query, 1
        store.save(state)
    client = _make_client()
    tools = _build_openai_tools_schema()
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_query},
    ]
    planning_observations: List[Dict[str, Any]] = [
        {"tool": item.get("tool"), "arguments": item.get("arguments", {}), "result": _compact_result_for_planning(item.get("tool", ""), item.get("result"))}
        for item in state.observations
    ]
    if planning_observations:
        messages.append(_build_planning_state_message(planning_observations))

    for step in range(start_step, MAX_AGENT_STEPS + 1):
        state.step_count = step
        state.status = RUNNING
        store.save(state)
        try:
            message = _request_llm_message(client, messages, tools=tools, tool_choice="auto")
        except Exception:
            state.status = FAILED
            store.save(state)
            raise

        tool_calls = message.tool_calls or []

        if not tool_calls:
            candidate_answer = message.content or ""
            if state.all_observations_empty():
                state.final_answer = _no_answer_text(user_query)
                state.record_no_answer("all_tool_results_empty_or_unsupported")
                store.save(state)
                return _result_payload(state)
            final_answer = _ground_final_entities(_ground_final_citations(
                _synthesize_final_answer(
                    client,
                    user_query,
                    _compact_execution_state_for_synthesis(state),
                    candidate_answer,
                ),
                state,
            ), state)
            state.final_answer = final_answer
            state.status = COMPLETED
            store.save(state)
            return _result_payload(state)

        messages.append(message.model_dump(exclude_none=True))

        new_planning_observations = []
        for tool_call in tool_calls:
            if tool_call.type != "function":
                raise ValueError(f"不支持的 tool_call 类型: {tool_call.type}")

            requested_tool_name = tool_call.function.name
            if requested_tool_name not in TOOLS:
                raise KeyError(f"模型请求了未知 Tool: {requested_tool_name}")

            try:
                arguments = _decode_tool_arguments(requested_tool_name, tool_call.function.arguments)
            except Exception as exc:
                state.record_failure(requested_tool_name, {}, 0.0, 0, exc)
                store.save(state)
                raise
            tool_name = requested_tool_name
            arguments = _ground_tool_arguments(state, tool_name, arguments)
            tool_name, arguments, guard_reason = _apply_tool_dispatch_guard(
                state, tool_name, arguments
            )

            result = _execute_tool_with_retry(state, tool_name, arguments, store)
            if guard_reason:
                state.tool_history[-1]["model_requested_tool"] = requested_tool_name
                state.tool_history[-1]["routing_guard"] = guard_reason
                store.save(state)
            planning_observation = {
                "tool": tool_name,
                "arguments": arguments,
                "result": _compact_result_for_planning(tool_name, result),
            }
            planning_observations.append(planning_observation)
            new_planning_observations.append(planning_observation)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": _to_tool_content(
                        _compact_result_for_planning(tool_name, result)
                    ),
                }
            )

        if new_planning_observations:
            messages.append(_build_planning_state_message(planning_observations))

    state.status = FAILED
    store.save(state)
    raise RuntimeError(f"超过最大 Agent 步数限制: {MAX_AGENT_STEPS}")


def resume_agent(task_id: str, checkpoint_store: Optional[CheckpointStore] = None) -> Dict[str, Any]:
    return run_agent(task_id=task_id, checkpoint_store=checkpoint_store, resume=True)
