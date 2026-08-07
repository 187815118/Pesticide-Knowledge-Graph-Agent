import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rag.grounded_rag import GroundedRAG


class StubRetriever:
    def __init__(self, results):
        self.results = results
        self.last_question = None
        self.last_top_k = None

    def search(self, question, top_k=3):
        self.last_question = question
        self.last_top_k = top_k
        return self.results[:top_k]


class FakeMessage:
    def __init__(self, content):
        self.content = content


class FakeChoice:
    def __init__(self, content):
        self.message = FakeMessage(content)


class FakeResponse:
    def __init__(self, content):
        self.choices = [FakeChoice(content)]


class FakeCompletions:
    def __init__(self, parent):
        self.parent = parent

    def create(self, model, messages, temperature=None):
        self.parent.called = True
        self.parent.model = model
        self.parent.messages = messages
        self.parent.temperature = temperature
        return FakeResponse(self.parent.answer_text)


class FakeChat:
    def __init__(self, parent):
        self.completions = FakeCompletions(parent)


class FakeClient:
    def __init__(self, answer_text):
        self.answer_text = answer_text
        self.called = False
        self.model = None
        self.messages = None
        self.temperature = None
        self.chat = FakeChat(self)


def _sample_result(doc_id, rank):
    return {
        "rank": rank,
        "id": doc_id,
        "name": "abamectin" if rank == 1 else "emamectin benzoate",
        "score": 0.123 / rank,
        "content": "Glutamate-gated chloride channel modulator.",
        "source": "New Zealand pesticide dataset",
        "bm25_rank": rank,
        "vector_rank": rank + 1,
        "bm25_score": 7.0 / rank,
        "vector_score": 0.9 / rank,
    }


def _assert_raises_value_error(func):
    try:
        func()
    except ValueError:
        return
    raise AssertionError("预期抛出 ValueError，但没有抛出。")


def main() -> int:
    retriever = StubRetriever(
        [
            _sample_result("active_substance:abamectin", 1),
            _sample_result("active_substance:emamectin benzoate", 2),
        ]
    )
    fake_client = FakeClient("Abamectin acts on glutamate-gated chloride channels. [D1]")
    rag = GroundedRAG(
        retriever=retriever,
        llm_client=fake_client,
        model="openrouter/free",
        top_k=2,
    )

    result = rag.answer("What is the mode of action of abamectin?")

    if retriever.last_question != "What is the mode of action of abamectin?":
        raise AssertionError("Retriever 没有收到正确 question")
    if retriever.last_top_k != 2:
        raise AssertionError("Retriever 没有收到正确 top_k")
    if not fake_client.called:
        raise AssertionError("LLM client 应该被调用")
    if result["answer"] != "Abamectin acts on glutamate-gated chloride channels. [D1]":
        raise AssertionError("answer 返回不正确")
    if result["invalid_citations"]:
        raise AssertionError("合法 [D1] 不应产生 invalid_citations")
    if fake_client.temperature is not None:
        raise AssertionError("未传 temperature 时不应向 fake client 传 temperature")

    evidence = result["evidence"]
    if evidence[0]["label"] != "D1" or evidence[1]["label"] != "D2":
        raise AssertionError("Evidence label 应为 D1/D2")
    for key in ["id", "name", "source", "content", "retrieval_rank", "retrieval_score"]:
        if key not in evidence[0]:
            raise AssertionError(f"evidence 缺少字段: {key}")

    trace = result["retrieval_trace"][0]
    for key in ["rank", "id", "name", "score", "bm25_rank", "vector_rank"]:
        if key not in trace:
            raise AssertionError(f"retrieval_trace 缺少字段: {key}")

    system_prompt = fake_client.messages[0]["content"].lower()
    user_prompt = fake_client.messages[1]["content"]
    for expected in [
        "only use the retrieved evidence",
        "insufficient",
        "copy active substance",
        "[d1]",
        "do not cite evidence labels that were not provided",
        "absence of evidence",
        "negative claim",
        "explicitly supported",
        "do not evaluate unrelated/distractor evidence",
        "literal evidence labels",
        "do not use entity names as citations",
        "factual claim",
        "factual sentence",
    ]:
        if expected not in system_prompt:
            raise AssertionError(f"system prompt 缺少 grounding 约束: {expected}")
    if "[D1]" not in user_prompt or "[D2]" not in user_prompt:
        raise AssertionError("user prompt 未包含 D1/D2 evidence")
    if "Retrieved Evidence:" not in user_prompt:
        raise AssertionError("user prompt 未包含 Retrieved Evidence")
    user_prompt_lower = user_prompt.lower()
    for expected in [
        "literal evidence labels",
        "do not put entity names inside square brackets",
        "factual sentences",
    ]:
        if expected not in user_prompt_lower:
            raise AssertionError(f"user prompt 缺少 citation 约束: {expected}")

    invalid_client = FakeClient("Unsupported citation. [D99]")
    invalid_rag = GroundedRAG(retriever=retriever, llm_client=invalid_client, top_k=2)
    invalid_result = invalid_rag.answer("What is the mode of action of abamectin?")
    if invalid_result["invalid_citations"] != ["D99"]:
        raise AssertionError("非法 citation [D99] 未被识别")

    d0_client = FakeClient("Unsupported citation. [D0]")
    d0_rag = GroundedRAG(retriever=retriever, llm_client=d0_client, top_k=2)
    d0_result = d0_rag.answer("What is the mode of action of abamectin?")
    if d0_result["invalid_citations"] != ["D0"]:
        raise AssertionError("非法 citation [D0] 未被识别")

    temperature_client = FakeClient("Abamectin acts on glutamate-gated chloride channels. [D1]")
    temperature_rag = GroundedRAG(
        retriever=retriever,
        llm_client=temperature_client,
        top_k=2,
        temperature=0.0,
    )
    temperature_rag.answer("What is the mode of action of abamectin?")
    if temperature_client.temperature != 0.0:
        raise AssertionError("temperature=0.0 未传递给 LLM client")

    empty_client = FakeClient("This should not be called.")
    empty_rag = GroundedRAG(
        retriever=StubRetriever([]),
        llm_client=empty_client,
        top_k=2,
    )
    empty_result = empty_rag.answer("What is missing?")
    if empty_client.called:
        raise AssertionError("无检索结果时不应调用 LLM")
    if empty_result["evidence"] != [] or empty_result["retrieval_trace"] != []:
        raise AssertionError("无检索结果时 evidence 和 retrieval_trace 应为空")
    if empty_result["invalid_citations"] != []:
        raise AssertionError("无检索结果时 invalid_citations 应为空")
    if "Insufficient retrieved evidence" not in empty_result["answer"]:
        raise AssertionError("无检索结果时应返回 insufficient context")

    _assert_raises_value_error(lambda: rag.answer(""))

    print("验收通过: GroundedRAG 工作正常")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
