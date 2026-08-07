import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evaluation.rag_generation_evaluator import (
    aggregate_generation_metrics,
    evaluate_generation_result,
)


def _assert_close(actual, expected):
    if not math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-9):
        raise AssertionError(f"expected {expected}, got {actual}")


def _eval_item(
    expected_entities=None,
    expected_behavior="answer",
    language="en",
    category="single_entity_fact",
):
    return {
        "id": "gq-test",
        "query": "test query",
        "category": category,
        "language": language,
        "expected_behavior": expected_behavior,
        "expected_entities": expected_entities or [],
        "source_retrieval_query_id": "q-test",
    }


def _rag_result(answer, evidence=None):
    return {
        "answer": answer,
        "evidence": evidence if evidence is not None else [
            {
                "label": "D1",
                "id": "active_substance:fipronil",
                "name": "fipronil",
                "source": "test",
                "content": "test evidence",
                "retrieval_rank": 1,
                "retrieval_score": 0.1,
            }
        ],
        "retrieval_trace": [],
        "invalid_citations": [],
    }


def _evidence(label, name):
    return {
        "label": label,
        "id": f"active_substance:{name}",
        "name": name,
        "source": "test",
        "content": "test evidence",
        "retrieval_rank": int(label[1:]),
        "retrieval_score": 0.1,
    }


def main() -> int:
    normal = evaluate_generation_result(
        _eval_item(expected_entities=["fipronil"]),
        _rag_result("fipronil blocks GABA-gated chloride channels [D1]."),
    )
    metrics = normal["automatic_metrics"]
    if metrics["citation_presence"] is not True:
        raise AssertionError("citation_presence should be True")
    if metrics["citations_valid"] is not True:
        raise AssertionError("citations_valid should be True")
    _assert_close(metrics["evidence_conditioned_entity_recall"], 1.0)
    if metrics["automatic_rule_pass"] is not True:
        raise AssertionError("normal answer should pass automatic rules")

    invalid = evaluate_generation_result(
        _eval_item(expected_entities=["fipronil"]),
        _rag_result("fipronil blocks GABA-gated chloride channels [D99]."),
    )
    if invalid["automatic_metrics"]["citations_valid"] is not False:
        raise AssertionError("[D99] should be invalid")

    d0 = evaluate_generation_result(
        _eval_item(expected_entities=["fipronil"]),
        _rag_result("fipronil blocks GABA-gated chloride channels [D0]."),
    )
    if d0["automatic_metrics"]["citations_valid"] is not False:
        raise AssertionError("[D0] should be invalid")

    entity_as_citation = evaluate_generation_result(
        _eval_item(expected_entities=["fipronil"]),
        _rag_result("[fipronil] blocks GABA-gated chloride channels."),
    )
    if entity_as_citation["automatic_metrics"]["entity_as_citation_violation"] is not True:
        raise AssertionError("entity-as-citation violation should be True")
    if entity_as_citation["automatic_metrics"]["citation_presence"] is not False:
        raise AssertionError("[fipronil] is not a valid [D#] citation")

    missing_entity = evaluate_generation_result(
        _eval_item(expected_entities=["fipronil", "abamectin"]),
        _rag_result("fipronil blocks GABA-gated chloride channels [D1]."),
    )
    _assert_close(missing_entity["automatic_metrics"]["retrieval_expected_entity_coverage"], 0.5)
    _assert_close(missing_entity["automatic_metrics"]["evidence_conditioned_entity_recall"], 1.0)
    if missing_entity["automatic_metrics"]["matched_supported_entities"] != ["fipronil"]:
        raise AssertionError("matched_supported_entities incorrect")
    if missing_entity["automatic_metrics"]["unretrieved_expected_entities"] != ["abamectin"]:
        raise AssertionError("unretrieved_expected_entities incorrect")

    insufficient = evaluate_generation_result(
        _eval_item(
            expected_behavior="insufficient",
            expected_entities=[],
            category="insufficient_evidence",
        ),
        _rag_result("retrieved evidence is insufficient to answer the question."),
    )
    if insufficient["automatic_metrics"]["insufficient_success"] is not True:
        raise AssertionError("insufficient_success should be True")

    wrong_refusal = evaluate_generation_result(
        _eval_item(expected_entities=["fipronil"]),
        _rag_result("retrieved evidence is insufficient to answer the question."),
    )
    if wrong_refusal["automatic_metrics"]["unexpected_insufficient"] is not True:
        raise AssertionError("answer case refusal should set unexpected_insufficient")

    zh = evaluate_generation_result(
        _eval_item(
            expected_entities=["fipronil"],
            language="zh",
            category="cross_lingual_zh",
        ),
        _rag_result("fipronil 是 GABA 门控氯离子通道阻断剂 [D1]。"),
    )
    if zh["automatic_metrics"]["zh_language_match"] is not True:
        raise AssertionError("zh_language_match should be True")

    partial_retrieval = evaluate_generation_result(
        _eval_item(expected_entities=["a", "b", "c", "d"]),
        _rag_result(
            "a and b are relevant [D1] [D2].",
            evidence=[_evidence("D1", "a"), _evidence("D2", "b")],
        ),
    )
    partial_metrics = partial_retrieval["automatic_metrics"]
    if partial_metrics["supported_expected_entities"] != ["a", "b"]:
        raise AssertionError("supported_expected_entities incorrect")
    if partial_metrics["unretrieved_expected_entities"] != ["c", "d"]:
        raise AssertionError("unretrieved_expected_entities incorrect")
    _assert_close(partial_metrics["retrieval_expected_entity_coverage"], 0.5)
    _assert_close(partial_metrics["evidence_conditioned_entity_recall"], 1.0)
    if partial_metrics["generation_evaluable"] is not True:
        raise AssertionError("partial retrieval should be generation evaluable")
    if partial_metrics["automatic_rule_pass"] is not True:
        raise AssertionError("unretrieved expected entities must not fail generation")

    missing_supported = evaluate_generation_result(
        _eval_item(expected_entities=["a", "b", "c"]),
        _rag_result(
            "a is relevant [D1].",
            evidence=[_evidence("D1", "a"), _evidence("D2", "b")],
        ),
    )
    missing_supported_metrics = missing_supported["automatic_metrics"]
    _assert_close(missing_supported_metrics["evidence_conditioned_entity_recall"], 0.5)
    if missing_supported_metrics["missing_supported_entities"] != ["b"]:
        raise AssertionError("missing_supported_entities incorrect")
    if missing_supported_metrics["automatic_rule_pass"] is not False:
        raise AssertionError("missing supported evidence entity should fail generation")

    unevaluable = evaluate_generation_result(
        _eval_item(expected_entities=["a", "b"]),
        _rag_result(
            "x and y are relevant [D1] [D2].",
            evidence=[_evidence("D1", "x"), _evidence("D2", "y")],
        ),
    )
    unevaluable_metrics = unevaluable["automatic_metrics"]
    if unevaluable_metrics["generation_evaluable"] is not False:
        raise AssertionError("case without target evidence should be unevaluable")
    if unevaluable_metrics["evidence_conditioned_entity_recall"] is not None:
        raise AssertionError("unevaluable case recall should be None")
    if unevaluable_metrics["automatic_rule_pass"] is not None:
        raise AssertionError("unevaluable case automatic_rule_pass should be None")

    aggregate = aggregate_generation_metrics([
        partial_retrieval,
        missing_supported,
        unevaluable,
        insufficient,
    ])
    if aggregate["total_queries"] != 4:
        raise AssertionError("total_queries should be 4")
    if aggregate["answer_queries"] != 3:
        raise AssertionError("answer_queries should be 3")
    if aggregate["insufficient_queries"] != 1:
        raise AssertionError("insufficient_queries should be 1")
    _assert_close(aggregate["citation_presence_rate"], 1.0)
    _assert_close(aggregate["valid_citation_rate"], 1.0)
    _assert_close(aggregate["retrieval_expected_entity_coverage_macro"], (0.5 + (2.0 / 3.0) + 0.0) / 3.0)
    _assert_close(aggregate["evidence_conditioned_entity_recall_macro"], (1.0 + 0.5) / 2.0)
    _assert_close(aggregate["generation_evaluable_rate"], 2.0 / 3.0)
    _assert_close(aggregate["entity_as_citation_violation_rate"], 0.0)
    _assert_close(aggregate["insufficient_accuracy"], 1.0)
    _assert_close(aggregate["automatic_rule_pass_rate"], 2.0 / 3.0)

    print("验收通过: RAG generation evaluator 工作正常")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
