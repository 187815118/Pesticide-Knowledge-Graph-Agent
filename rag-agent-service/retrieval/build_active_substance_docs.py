import argparse
import csv
import json
from pathlib import Path


ACTIVE_SUBSTANCE_FIELD = "Active Substance"
TEXT_FIELDS = [
    "Introduction",
    "Mode of action",
    "The way of action",
    "Resistance",
]
INVALID_VALUES = {"", "-", "--"}
SOURCE_NAME = "New Zealand pesticide dataset"


def _clean(value):
    return (value or "").strip()


def _is_valid_text(value):
    return _clean(value) not in INVALID_VALUES


def _doc_id(name):
    return "active_substance:" + name.strip().lower()


def _build_content(name, fields):
    parts = ["Active Substance: " + name]
    for field in TEXT_FIELDS:
        value = fields.get(field)
        if value:
            parts.append(field + ": " + value)
    return "\n\n".join(parts)


def build_docs(input_path, output_path):
    input_path = Path(input_path)
    output_path = Path(output_path)

    substances = {}
    scanned_rows = 0
    conflict_count = 0

    with input_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            scanned_rows += 1
            name = _clean(row.get(ACTIVE_SUBSTANCE_FIELD))
            if name in INVALID_VALUES:
                continue

            fields = substances.setdefault(name, {})
            for field in TEXT_FIELDS:
                value = _clean(row.get(field))
                if not _is_valid_text(value):
                    continue

                existing = fields.get(field)
                if existing is None:
                    fields[field] = value
                elif existing != value:
                    conflict_count += 1
                    print(
                        "warning: Active Substance "
                        + repr(name)
                        + " field "
                        + repr(field)
                        + " has multiple values; keeping first."
                    )

    docs = []
    for name, fields in substances.items():
        if not fields:
            continue
        docs.append(
            {
                "id": _doc_id(name),
                "entity_type": "Active Substance",
                "name": name,
                "source": SOURCE_NAME,
                "content": _build_content(name, fields),
            }
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as jsonl_file:
        for doc in docs:
            jsonl_file.write(json.dumps(doc, ensure_ascii=False) + "\n")

    stats = {
        "scanned_rows": scanned_rows,
        "unique_active_substances": len(substances),
        "generated_docs": len(docs),
        "conflict_fields": conflict_count,
    }
    print("扫描 CSV 行数:", stats["scanned_rows"])
    print("唯一 Active Substance 数量:", stats["unique_active_substances"])
    print("最终生成文档数量:", stats["generated_docs"])
    print("冲突字段数量:", stats["conflict_fields"])
    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Build deduplicated Active Substance RAG JSONL docs."
    )
    parser.add_argument("--input", required=True, help="Input CSV path.")
    parser.add_argument("--output", required=True, help="Output JSONL path.")
    args = parser.parse_args()

    build_docs(args.input, args.output)


if __name__ == "__main__":
    main()
