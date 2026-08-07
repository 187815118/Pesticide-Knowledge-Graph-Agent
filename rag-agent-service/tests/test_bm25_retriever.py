import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from retrieval.bm25_retriever import BM25Retriever


CORPUS_PATH = ROOT / "data" / "active_substance_docs.jsonl"


def _print_results(title, results):
    print(title)
    for result in results:
        print(
            f"{result['rank']}. {result['name']} "
            f"score={result['score']:.4f}"
        )


def main() -> int:
    if not CORPUS_PATH.exists():
        print(f"验收失败: 找不到语料文件: {CORPUS_PATH}", file=sys.stderr)
        return 1

    retriever = BM25Retriever(CORPUS_PATH)

    mode_query = "What is the mode of action of abamectin?"
    top3 = retriever.search(mode_query, top_k=3)
    _print_results("Query 1 Top-3:", top3)
    top3_names = {item["name"].lower() for item in top3}
    if "abamectin" not in top3_names:
        print(
            "验收失败: Top-3 中未包含 abamectin。实际结果: "
            + ", ".join(item["name"] for item in top3),
            file=sys.stderr,
        )
        return 1

    inhibitor_query = "acetylcholinesterase inhibitor"
    top5 = retriever.search(inhibitor_query, top_k=5)
    _print_results("Query 2 Top-5:", top5)
    if not top5:
        print("验收失败: acetylcholinesterase inhibitor 未返回结果", file=sys.stderr)
        return 1

    print("验收通过: BM25 检索模块工作正常")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
