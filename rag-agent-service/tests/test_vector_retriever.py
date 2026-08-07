import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from retrieval.vector_retriever import VectorRetriever


EXPECTED_RESULT_KEYS = {"rank", "id", "name", "score", "content", "source"}


def _print_results(title, results):
    print(title)
    for result in results:
        print(
            f"{result['rank']}. {result['name']} "
            f"score={result['score']:.6f}"
        )


def _assert_result_shape(results):
    for result in results:
        missing_keys = EXPECTED_RESULT_KEYS - set(result)
        if missing_keys:
            raise AssertionError(f"结果缺少字段: {sorted(missing_keys)}")


def _assert_raises_value_error(func):
    try:
        func()
    except ValueError:
        return
    raise AssertionError("预期抛出 ValueError，但没有抛出。")


def main() -> int:
    retriever = VectorRetriever(device="cuda")

    if retriever.document_count != 259:
        print(
            f"验收失败: corpus 数量应为 259，实际为 {retriever.document_count}",
            file=sys.stderr,
        )
        return 1

    mode_query = "What is the mode of action of abamectin?"
    top3 = retriever.search(mode_query, top_k=3)
    _print_results("Query 1 Top-3:", top3)
    _assert_result_shape(top3)

    top1_name = top3[0]["name"].strip().lower()
    if top1_name != "abamectin":
        print(
            f"验收失败: Top-1 应为 abamectin，实际为 {top3[0]['name']}",
            file=sys.stderr,
        )
        return 1

    inhibitor_query = "acetylcholinesterase inhibitor"
    top5 = retriever.search(inhibitor_query, top_k=5)
    _print_results("Query 2 Top-5:", top5)
    _assert_result_shape(top5)

    _assert_raises_value_error(lambda: retriever.search(mode_query, top_k=0))
    _assert_raises_value_error(lambda: retriever.search("", top_k=3))

    print("验收通过: VectorRetriever 工作正常")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
