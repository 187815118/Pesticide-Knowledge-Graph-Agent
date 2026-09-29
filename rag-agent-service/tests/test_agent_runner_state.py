import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import agent.agent_runner as agent_runner


class FakeFunction:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments


class FakeToolCall:
    def __init__(self, call_id, name, arguments):
        self.id = call_id
        self.type = "function"
        self.function = FakeFunction(name, json.dumps(arguments))


class FakeMessage:
    def __init__(self, content="", tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls

    def model_dump(self, exclude_none=True):
        payload = {"role": "assistant"}
        if self.content:
            payload["content"] = self.content
        if self.tool_calls:
            payload["tool_calls"] = [
                {
                    "id": item.id,
                    "type": item.type,
                    "function": {
                        "name": item.function.name,
                        "arguments": item.function.arguments,
                    },
                }
                for item in self.tool_calls
            ]
        return payload


class FakeChoice:
    def __init__(self, message):
        self.message = message


class FakeResponse:
    def __init__(self, message):
        self.choices = [FakeChoice(message)]


class FakeCompletions:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        call_number = len(self.calls)
        if call_number == 1:
            return FakeResponse(
                FakeMessage(
                    tool_calls=[
                        FakeToolCall(
                            "call_1",
                            "query_active_substance",
                            {"pesticide_name": "Sparta"},
                        )
                    ]
                )
            )
        if call_number == 2:
            planning_context = kwargs["messages"][-1]["content"]
            if "Structured execution state for subsequent tool planning" not in planning_context:
                raise AssertionError("后续 Tool planning 缺少 structured execution state")
            if "spinetoram" not in planning_context:
                raise AssertionError("后续 Tool planning 看不到第一步 resolved entity: spinetoram")
            return FakeResponse(
                FakeMessage(
                    tool_calls=[
                        FakeToolCall(
                            "call_2",
                            "hybrid_rag_query",
                            {"question": "What is the mode of action of spinetoram?"},
                        )
                    ]
                )
            )
        if call_number == 3:
            return FakeResponse(
                FakeMessage("spinetoram affects insect nervous systems. [D1]")
            )

        final_user_prompt = kwargs["messages"][1]["content"]
        if "Sparta" not in final_user_prompt:
            raise AssertionError("final synthesis prompt 缺少 KG product entity")
        if "query_active_substance" not in final_user_prompt:
            raise AssertionError("final synthesis prompt 缺少 KG observation")
        if "hybrid_rag_query" not in final_user_prompt:
            raise AssertionError("final synthesis prompt 缺少 RAG observation")
        if "spinetoram affects insect nervous systems. [D1]" not in final_user_prompt:
            raise AssertionError("final synthesis prompt 缺少 RAG answer citation")

        return FakeResponse(
            FakeMessage(
                "Sparta's active substance is spinetoram. "
                "spinetoram affects insect nervous systems. [D1]"
            )
        )


class FakeChat:
    def __init__(self):
        self.completions = FakeCompletions()


class FakeClient:
    def __init__(self):
        self.chat = FakeChat()


def fake_execute_tool(tool_name, arguments):
    if tool_name == "query_active_substance":
        return ["spinetoram"]
    if tool_name == "hybrid_rag_query":
        question = arguments.get("question", "")
        if "spinetoram" not in question:
            raise AssertionError("hybrid_rag_query 的 question 必须显式包含 spinetoram")
        vague_terms = [
            "its active substance",
            "the active substance",
            "the previous result",
            "that substance",
        ]
        if any(term in question.lower() for term in vague_terms):
            raise AssertionError("hybrid_rag_query 的 question 不应使用模糊指代")
        return {
            "answer": "spinetoram affects insect nervous systems. [D1]",
            "evidence": [
                {
                    "label": "D1",
                    "id": "active_substance:spinetoram",
                    "name": "spinetoram",
                    "source": "active_substance_docs",
                    "retrieval_rank": 1,
                }
            ],
            "retrieval_trace": [],
            "invalid_citations": [],
        }
    raise AssertionError(f"unexpected tool: {tool_name}")


def main() -> int:
    fake_client = FakeClient()
    original_make_client = agent_runner._make_client
    original_tools_schema = agent_runner._build_openai_tools_schema
    original_execute_tool = agent_runner.execute_tool
    try:
        agent_runner._make_client = lambda: fake_client
        agent_runner._build_openai_tools_schema = lambda: []
        agent_runner.execute_tool = fake_execute_tool

        result = agent_runner.run_agent(
            "What is the active substance of Sparta, and what is its mode of action?"
        )
    finally:
        agent_runner._make_client = original_make_client
        agent_runner._build_openai_tools_schema = original_tools_schema
        agent_runner.execute_tool = original_execute_tool

    observations = result["execution_state"]["observations"]
    if len(observations) != 2:
        raise AssertionError("structured execution state 应包含两个 observations")
    if observations[0]["tool"] != "query_active_substance":
        raise AssertionError("第一个 observation 应来自 KG forward tool")
    if observations[1]["tool"] != "hybrid_rag_query":
        raise AssertionError("第二个 observation 应来自 RAG tool")
    if observations[0]["result"] != ["spinetoram"]:
        raise AssertionError("KG result 未进入 structured state")
    if "[D1]" not in result["answer"]:
        raise AssertionError("final synthesis 丢失 RAG citation [D1]")
    if "Sparta's active substance is spinetoram" not in result["answer"]:
        raise AssertionError("final synthesis 未保留 KG 中间事实")

    calls = fake_client.chat.completions.calls
    if len(calls) != 4:
        raise AssertionError("应有三次 Agent loop LLM 调用和一次 final synthesis 调用")
    if "tools" in calls[-1]:
        raise AssertionError("final synthesis 不应携带 tool schema")

    print("验收通过: Agent structured state 和 final synthesis 工作正常")
    return 0


def test_structured_state_and_grounded_final_synthesis():
    assert main() == 0


if __name__ == "__main__":
    raise SystemExit(main())
