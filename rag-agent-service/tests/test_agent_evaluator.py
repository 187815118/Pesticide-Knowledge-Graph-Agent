import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evaluation.agent_evaluator import evaluate_agent_result


def _eval_item(requires_citation=False):
    return {
        "id": "test",
        "category": "kg_to_rag_multistep",
        "expected_tools": ["query_active_substance", "hybrid_rag_query"],
        "expected_entities": ["Sparta", "spinetoram"],
        "requires_citation": requires_citation,
    }


def _result(tool_names, answer):
    trace = []
    for tool_name in tool_names:
        if tool_name == "query_active_substance":
            trace.append(
                {
                    "tool": "query_active_substance",
                    "arguments": {"pesticide_name": "Sparta"},
                    "result": ["spinetoram"],
                }
            )
        elif tool_name == "hybrid_rag_query":
            trace.append(
                {
                    "tool": "hybrid_rag_query",
                    "arguments": {
                        "question": "What is the mode of action of spinetoram?"
                    },
                    "result": {
                        "answer": "spinetoram affects insect nervous systems. [D1]",
                        "evidence": [{"label": "D1", "name": "spinetoram"}],
                    },
                }
            )
        else:
            trace.append(
                {
                    "tool": tool_name,
                    "arguments": {"active_substance_name": "spinetoram"},
                    "result": ["Sparta"],
                }
            )
    return {"answer": answer, "tool_trace": trace}


def main() -> int:
    passed = evaluate_agent_result(
        _eval_item(requires_citation=True),
        _result(
            ["query_active_substance", "hybrid_rag_query"],
            "spinetoram affects insect nervous systems. [D1]",
        ),
    )
    if not passed["task_completed_rule"]:
        raise AssertionError("正确 tool sequence 和 citation 应通过")
    if passed["tool_sequence_exact_match"] != 1.0:
        raise AssertionError("正确顺序应 exact match")

    wrong_order = evaluate_agent_result(
        _eval_item(requires_citation=True),
        _result(
            ["hybrid_rag_query", "query_active_substance"],
            "spinetoram affects insect nervous systems. [D1]",
        ),
    )
    if wrong_order["task_completed_rule"]:
        raise AssertionError("顺序错误不应通过")
    if wrong_order["tool_selection_recall"] != 1.0:
        raise AssertionError("顺序错误但工具都调用时 recall 应为 1")

    extra_tool = evaluate_agent_result(
        _eval_item(requires_citation=True),
        _result(
            [
                "query_active_substance",
                "query_pesticides_by_active_substance",
                "hybrid_rag_query",
            ],
            "spinetoram affects insect nervous systems. [D1]",
        ),
    )
    if extra_tool["unnecessary_tool_call_rate"] <= 0.0:
        raise AssertionError("多调用一个 Tool 应被识别")
    if "query_pesticides_by_active_substance" not in extra_tool["unnecessary_tools"]:
        raise AssertionError("unnecessary_tools 缺少额外 Tool")

    missing_citation = evaluate_agent_result(
        _eval_item(requires_citation=True),
        _result(
            ["query_active_substance", "hybrid_rag_query"],
            "spinetoram affects insect nervous systems.",
        ),
    )
    if missing_citation["citation_presence"]["passed"]:
        raise AssertionError("requires_citation=true 但无 [D#] 不应通过")
    if missing_citation["task_completed_rule"]:
        raise AssertionError("缺 citation 不应 task_completed_rule 通过")

    citation_ok = evaluate_agent_result(
        _eval_item(requires_citation=True),
        _result(
            ["query_active_substance", "hybrid_rag_query"],
            "spinetoram affects insect nervous systems. [D12]",
        ),
    )
    if not citation_ok["citation_presence"]["passed"]:
        raise AssertionError("合法 [D#] citation 应通过")

    print("验收通过: Agent evaluator 规则工作正常")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
