#!/usr/bin/env python3
"""根据商城邮箱列表，从源数据中匹配并导出完整记录。"""

from pathlib import Path

DIR = Path(__file__).resolve().parent
SOURCE_FILE = DIR / "源数据.txt"
MALL_FILE = DIR / "商城数据.txt"
OUTPUT_FILE = DIR / "导出结果.txt"
NOT_FOUND_FILE = DIR / "未匹配.txt"


def load_source_index(path: Path) -> dict[str, str]:
    index: dict[str, str] = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            email = line.split("----", 1)[0].strip().lower()
            index[email] = line
    return index


def load_mall_emails(path: Path) -> list[str]:
    emails: list[str] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            email = line.strip()
            if email:
                emails.append(email)
    return emails


def main() -> None:
    source_index = load_source_index(SOURCE_FILE)
    mall_emails = load_mall_emails(MALL_FILE)

    matched: list[str] = []
    not_found: list[str] = []

    for email in mall_emails:
        key = email.lower()
        record = source_index.get(key)
        if record:
            matched.append(record)
        else:
            not_found.append(email)

    with OUTPUT_FILE.open("w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(matched))
        if matched:
            f.write("\n")

    with NOT_FOUND_FILE.open("w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(not_found))
        if not_found:
            f.write("\n")

    print(f"商城数据: {len(mall_emails)} 条")
    print(f"匹配成功: {len(matched)} 条 -> {OUTPUT_FILE.name}")
    print(f"未匹配:   {len(not_found)} 条 -> {NOT_FOUND_FILE.name}")


if __name__ == "__main__":
    main()
