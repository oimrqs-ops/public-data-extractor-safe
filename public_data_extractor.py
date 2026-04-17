#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse


@dataclass
class Record:
    title: str
    url: str
    category: str
    price_text: str
    price_amount: float | None
    summary: str
    source_file: str


@dataclass
class Reject:
    source_file: str
    reason: str
    raw_title: str
    raw_url: str


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def parse_price(value: str) -> float | None:
    match = re.search(r"(\d+(?:[.,]\d{1,2})?)", value or "")
    if not match:
        return None
    return float(match.group(1).replace(",", "."))


def safe_url(base_url: str, href: str) -> str:
    full_url = urljoin(base_url.rstrip("/") + "/", href)
    parsed = urlparse(full_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    return full_url


class ListingParser(HTMLParser):
    def __init__(self, source_file: str, base_url: str):
        super().__init__()
        self.source_file = source_file
        self.base_url = base_url
        self.current: dict[str, str] | None = None
        self.field: str | None = None
        self.records: list[Record] = []
        self.rejects: list[Reject] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key: value or "" for key, value in attrs}
        classes = set(attr.get("class", "").split())

        if tag == "article" and "listing" in classes:
            self.current = {
                "title": "",
                "url": "",
                "category": attr.get("data-category", "uncategorized"),
                "price_text": "",
                "summary": "",
            }
            self.field = None
            return

        if not self.current:
            return

        if tag == "a" and not self.current["title"]:
            self.field = "title"
            self.current["url"] = attr.get("href", "")
        elif tag == "span" and "price" in classes:
            self.field = "price_text"
        elif tag == "p" and "summary" in classes:
            self.field = "summary"

    def handle_data(self, data: str) -> None:
        if self.current and self.field:
            self.current[self.field] += data

    def handle_endtag(self, tag: str) -> None:
        if tag in {"a", "span", "p"}:
            self.field = None
        if tag == "article" and self.current:
            self._flush_current()
            self.current = None
            self.field = None

    def _flush_current(self) -> None:
        assert self.current is not None

        title = normalize_space(self.current["title"])
        raw_url = normalize_space(self.current["url"])
        url = safe_url(self.base_url, raw_url)
        summary = normalize_space(self.current["summary"])
        price_text = normalize_space(self.current["price_text"])
        category = normalize_space(self.current["category"]) or "uncategorized"

        missing = [
            name
            for name, value in {
                "title": title,
                "url": url,
                "summary": summary,
            }.items()
            if not value
        ]
        if missing:
            self.rejects.append(
                Reject(
                    source_file=self.source_file,
                    reason="missing " + ", ".join(missing),
                    raw_title=title,
                    raw_url=raw_url,
                )
            )
            return

        self.records.append(
            Record(
                title=title,
                url=url,
                category=category,
                price_text=price_text,
                price_amount=parse_price(price_text),
                summary=summary,
                source_file=self.source_file,
            )
        )


def extract_file(path: Path, base_url: str) -> tuple[list[Record], list[Reject]]:
    parser = ListingParser(source_file=path.name, base_url=base_url)
    parser.feed(path.read_text(encoding="utf-8"))
    return parser.records, parser.rejects


def extract_directory(input_dir: Path, base_url: str) -> tuple[list[Record], list[Reject]]:
    records: list[Record] = []
    rejects: list[Reject] = []

    for path in sorted(input_dir.glob("*.html")):
        file_records, file_rejects = extract_file(path, base_url)
        records.extend(file_records)
        rejects.extend(file_rejects)

    deduped: list[Record] = []
    seen_urls: set[str] = set()
    for record in records:
        if record.url in seen_urls:
            rejects.append(
                Reject(
                    source_file=record.source_file,
                    reason="duplicate url",
                    raw_title=record.title,
                    raw_url=record.url,
                )
            )
            continue
        seen_urls.add(record.url)
        deduped.append(record)

    return deduped, rejects


def write_csv(path: Path, rows: Iterable[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_outputs(records: list[Record], rejects: list[Reject], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    record_rows = [asdict(record) for record in records]
    reject_rows = [asdict(reject) for reject in rejects]

    (out_dir / "records.json").write_text(
        json.dumps(record_rows, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    write_csv(out_dir / "records.csv", record_rows, list(Record.__dataclass_fields__))
    write_csv(out_dir / "rejects.csv", reject_rows, list(Reject.__dataclass_fields__))

    categories: dict[str, int] = {}
    for record in records:
        categories[record.category] = categories.get(record.category, 0) + 1

    lines = [
        "# Extraction Report",
        "",
        f"- Clean records: {len(records)}",
        f"- Rejected rows: {len(rejects)}",
        "",
        "## Categories",
        "",
    ]
    for category, count in sorted(categories.items()):
        lines.append(f"- {category}: {count}")
    if not categories:
        lines.append("- none")

    (out_dir / "extraction-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract allowed public/exported HTML data.")
    parser.add_argument("input_dir", type=Path, help="Directory with saved .html files.")
    parser.add_argument("--out", type=Path, default=Path("out"), help="Output directory.")
    parser.add_argument("--base-url", default="https://example.com", help="Base URL for relative links.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records, rejects = extract_directory(args.input_dir, args.base_url)
    write_outputs(records, rejects, args.out)
    print(f"clean={len(records)} rejected={len(rejects)}")


if __name__ == "__main__":
    main()
