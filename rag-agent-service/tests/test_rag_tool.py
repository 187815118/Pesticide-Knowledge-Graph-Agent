import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent.tool_registry import execute_tool, get_tools
from tools import rag_query


class FakeRAG:
    def __init__(self):
        self.questions = []

    def answer(self, question):
        self.questions.append(question)
        return {
            "answer": "Abamectin affects glutamate-gated chloride channels. [D1]",
            "evidence": [
                {
                    "label": "D1",
                    "id": "active_substance:abamectin",
                    "name": "abamectin",
                    "source": "active_substance_docs",
                    "content": "Full evidence content should stay internal.",
                    "retrieval_rank": 1,
                    "retrieval_score": 0.032,
                }
            ],
            "retrieval_trace": [
                {
                    "rank": 1,
                    "id": "active_substance:abamectin",
                    "name": "abamectin",
                    "score": 0.032,
                    "bm25_rank": 2,
                    "vector_rank": 1,
                }
            ],
            "invalid_citations": [],
        }


def _assert_raises_value_error(func):
    try:
        func()
    except ValueError:
        return
    raise AssertionError("预期抛出 ValueError，但没有抛出。")


def main() -> int:
    fake_rag = FakeRAG()
    rag_query._RAG_INSTANCE = fake_rag

    result = rag_query.hybrid_rag_query("What is the mode of action of abamectin?")

    if fake_rag.questions != ["What is the mode of action of abamectin?"]:
        raise AssertionError("hybrid_rag_query 没有调用 RAG.answer")
    if result["answer"] != "Abamectin affects glutamate-gated chloride channels. [D1]":
        raise AssertionError("answer 返回不正确")
    if "content" in result["evidence"][0]:
        raise AssertionError("Tool evidence 不应返回完整 content")
    for key in ["label", "id", "name", "source", "retrieval_rank"]:
        if key not in result["evidence"][0]:
            raise AssertionError(f"compact evidence 缺少字段: {key}")
    if result["retrieval_trace"][0]["vector_rank"] != 1:
        raise AssertionError("retrieval_trace 未正确透传")
    if result["invalid_citations"] != []:
        raise AssertionError("invalid_citations 未正确透传")

    tools = get_tools()
    if "hybrid_rag_query" not in tools:
        raise AssertionError("tool_registry 缺少 hybrid_rag_query")
    schema = tools["hybrid_rag_query"]["parameters"]
    if schema.get("required") != ["question"]:
        raise AssertionError("hybrid_rag_query schema required 不正确")
    if schema.get("properties", {}).get("question", {}).get("type") != "string":
        raise AssertionError("hybrid_rag_query question schema 不正确")

    dispatched = execute_tool(
        "hybrid_rag_query",
        {"question": "Explain abamectin resistance."},
    )
    if fake_rag.questions[-1] != "Explain abamectin resistance.":
        raise AssertionError("execute_tool 没有正确分发到 hybrid_rag_query")
    if "content" in dispatched["evidence"][0]:
        raise AssertionError("execute_tool 返回 evidence 不应包含 content")

    _assert_raises_value_error(lambda: rag_query.hybrid_rag_query(""))
    if fake_rag.questions[-1] != "Explain abamectin resistance.":
        raise AssertionError("空 question 不应触发 RAG 调用")

    reused = rag_query._get_rag()
    if reused is not fake_rag:
        raise AssertionError("lazy singleton 未复用现有 RAG 实例")

    print("验收通过: hybrid_rag_query Tool 工作正常")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
