import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = ROOT / "data" / "active_substance_docs.jsonl"
EVAL_PATH = ROOT / "data" / "retrieval_eval_queries.json"

REQUIRED_KEYS = {"id", "query", "relevant_ids", "category", "notes"}
REQUIRED_CATEGORIES = {
    "entity_explicit",
    "semantic",
    "mechanism_or_resistance",
    "cross_lingual_zh",
}


def _load_corpus_ids():
    corpus_ids = set()
    with CORPUS_PATH.open("r", encoding="utf-8") as jsonl_file:
        for line_number, line in enumerate(jsonl_file, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                document = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"JSONL 解析失败: {CORPUS_PATH} 第 {line_number} 行") from exc
            corpus_ids.add(document.get("id", ""))
    return corpus_ids


def _has_chinese(text):
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def main() -> int:
    with EVAL_PATH.open("r", encoding="utf-8") as eval_file:
        queries = json.load(eval_file)

    if not isinstance(queries, list):
        print("验收失败: retrieval_eval_queries.json 必须是 JSON array", file=sys.stderr)
        return 1

    if len(queries) != 30:
        print(f"验收失败: query 数量应为 30，实际为 {len(queries)}", file=sys.stderr)
        return 1

    corpus_ids = _load_corpus_ids()
    seen_ids = set()
    categories = set()
    chinese_count = 0

    for item in queries:
        missing_keys = REQUIRED_KEYS - set(item)
        if missing_keys:
            print(f"验收失败: {item.get('id', '<unknown>')} 缺少字段 {sorted(missing_keys)}", file=sys.stderr)
            return 1

        query_id = item["id"]
        if query_id in seen_ids:
            print(f"验收失败: query id 重复: {query_id}", file=sys.stderr)
            return 1
        seen_ids.add(query_id)

        if not isinstance(item["query"], str) or not item["query"].strip():
            print(f"验收失败: {query_id} query 为空", file=sys.stderr)
            return 1

        relevant_ids = item["relevant_ids"]
        if not isinstance(relevant_ids, list) or not relevant_ids:
            print(f"验收失败: {query_id} relevant_ids 为空", file=sys.stderr)
            return 1

        missing_relevant_ids = [doc_id for doc_id in relevant_ids if doc_id not in corpus_ids]
        if missing_relevant_ids:
            print(
                f"验收失败: {query_id} relevant_ids 不存在于 corpus: {missing_relevant_ids}",
                file=sys.stderr,
            )
            return 1

        categories.add(item["category"])
        if _has_chinese(item["query"]):
            chinese_count += 1

    missing_categories = REQUIRED_CATEGORIES - categories
    if missing_categories:
        print(f"验收失败: 缺少 category: {sorted(missing_categories)}", file=sys.stderr)
        return 1

    if chinese_count < 5:
        print(f"验收失败: 中文 query 至少 5 条，实际为 {chinese_count}", file=sys.stderr)
        return 1

    print("验收通过: Retrieval evaluation dataset 工作正常")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
