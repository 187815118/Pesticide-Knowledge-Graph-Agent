import csv
import json
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from retrieval.build_active_substance_docs import build_docs


def _write_test_csv(path):
    rows = [
        {
            "Active Substance": "abamectin",
            "Introduction": "Abamectin intro.",
            "Mode of action": "",
            "The way of action": "-",
            "Resistance": "--",
        },
        {
            "Active Substance": "abamectin",
            "Introduction": "Abamectin intro.",
            "Mode of action": "",
            "The way of action": "-",
            "Resistance": "--",
        },
        {
            "Active Substance": "emptytext",
            "Introduction": "",
            "Mode of action": "-",
            "The way of action": "--",
            "Resistance": "",
        },
    ]
    fieldnames = [
        "Active Substance",
        "Introduction",
        "Mode of action",
        "The way of action",
        "Resistance",
    ]
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        input_path = temp_dir / "input.csv"
        output_path = temp_dir / "active_substance_docs.jsonl"
        _write_test_csv(input_path)

        stats = build_docs(input_path, output_path)
        docs = [
            json.loads(line)
            for line in output_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    if stats["scanned_rows"] != 3:
        print(f"验收失败: 扫描行数不正确: {stats}", file=sys.stderr)
        return 1

    if len(docs) != 1:
        print(f"验收失败: 预期只生成 1 篇文档，实际: {docs}", file=sys.stderr)
        return 1

    doc = docs[0]
    if doc["name"] != "abamectin":
        print(f"验收失败: 文档 name 不正确: {doc}", file=sys.stderr)
        return 1

    content = doc["content"]
    if content.count("Active Substance: abamectin") != 1:
        print(f"验收失败: abamectin 内容重复或缺失: {content}", file=sys.stderr)
        return 1

    if "Introduction: Abamectin intro." not in content:
        print(f"验收失败: Introduction 未写入 content: {content}", file=sys.stderr)
        return 1

    empty_fields = ["Mode of action:", "The way of action:", "Resistance:"]
    leaked = [field for field in empty_fields if field in content]
    if leaked:
        print(f"验收失败: 空字段被写入 content: {leaked}", file=sys.stderr)
        return 1

    print("验收通过: Active Substance 文档生成逻辑工作正常")
    print(json.dumps(doc, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
