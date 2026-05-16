#!/usr/bin/env python3
"""Export watchlist price tables from Markdown reports to data/reports.csv."""

from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
OUTPUT = ROOT / "data" / "reports.csv"

FIELDNAMES = [
    "report_date",
    "ticker",
    "name",
    "regular_close",
    "regular_note",
    "extended_price",
    "extended_note",
    "regular_move_pct",
    "extended_move_pct",
    "latest_data_time",
    "source",
    "report_file",
]


def strip_markdown(value: str) -> str:
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"<[^>]+>", "", value)
    value = value.replace("**", "").replace("`", "")
    return " ".join(value.split())


def split_row(line: str) -> list[str]:
    line = line.strip()
    if not (line.startswith("|") and line.endswith("|")):
        return []
    return [cell.strip() for cell in line.strip("|").split("|")]


def is_separator(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells)


def extract_table(lines: list[str]) -> tuple[list[str], list[list[str]]] | None:
    for index, line in enumerate(lines):
        cells = split_row(line)
        if not cells or not cells[0].strip().lower().startswith("ticker"):
            continue
        if index + 1 >= len(lines):
            continue
        separator = split_row(lines[index + 1])
        if not is_separator(separator):
            continue

        rows: list[list[str]] = []
        for row_line in lines[index + 2 :]:
            row = split_row(row_line)
            if not row:
                break
            rows.append(row)
        return cells, rows
    return None


def first_number(value: str) -> str:
    cleaned = strip_markdown(value)
    if re.search(r"\bn/?a\b|ไม่พบ|ไม่มีข้อมูล", cleaned, flags=re.I):
        return ""
    match = re.search(r"[-+]?\d[\d,]*(?:\.\d+)?", cleaned)
    return match.group(0).replace(",", "") if match else ""


def first_pct(value: str) -> str:
    cleaned = strip_markdown(value)
    match = re.search(r"([-+]?\d+(?:\.\d+)?)\s*%", cleaned)
    return match.group(1).lstrip("+") if match else ""


def link_targets(value: str) -> str:
    links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", value)
    return "; ".join(links) if links else strip_markdown(value)


def normalize_generated_row(report_date: str, report_file: str, cells: list[str]) -> dict[str, str]:
    # Current generator format:
    # Ticker | Name | Regular close | Latest extended/overnight | Regular move |
    # Extended move | Latest data time | Source
    return {
        "report_date": report_date,
        "ticker": strip_markdown(cells[0]).upper(),
        "name": strip_markdown(cells[1]) if len(cells) > 1 else "",
        "regular_close": first_number(cells[2]) if len(cells) > 2 else "",
        "regular_note": strip_markdown(cells[2]) if len(cells) > 2 else "",
        "extended_price": first_number(cells[3]) if len(cells) > 3 else "",
        "extended_note": strip_markdown(cells[3]) if len(cells) > 3 else "",
        "regular_move_pct": first_pct(cells[4]) if len(cells) > 4 else "",
        "extended_move_pct": first_pct(cells[5]) if len(cells) > 5 else "",
        "latest_data_time": strip_markdown(cells[6]) if len(cells) > 6 else "",
        "source": link_targets(cells[7]) if len(cells) > 7 else "",
        "report_file": report_file,
    }


def normalize_legacy_row(report_date: str, report_file: str, cells: list[str]) -> dict[str, str]:
    # Legacy/manual formats:
    # Ticker | close | extended | change
    # Ticker | close | extended | source
    fourth = cells[3] if len(cells) > 3 else ""
    return {
        "report_date": report_date,
        "ticker": strip_markdown(cells[0]).upper(),
        "name": "",
        "regular_close": first_number(cells[1]) if len(cells) > 1 else "",
        "regular_note": strip_markdown(cells[1]) if len(cells) > 1 else "",
        "extended_price": first_number(cells[2]) if len(cells) > 2 else "",
        "extended_note": strip_markdown(cells[2]) if len(cells) > 2 else "",
        "regular_move_pct": first_pct(fourth),
        "extended_move_pct": first_pct(cells[2]) if len(cells) > 2 else "",
        "latest_data_time": "",
        "source": link_targets(fourth) if "](" in fourth else "",
        "report_file": report_file,
    }


def rows_from_report(path: Path) -> list[dict[str, str]]:
    report_date_match = re.match(r"(\d{4}-\d{2}-\d{2})-stock-brief\.md$", path.name)
    if not report_date_match:
        return []

    report_date = report_date_match.group(1)
    table = extract_table(path.read_text(encoding="utf-8").splitlines())
    if table is None:
        return []

    header, rows = table
    normalized: list[dict[str, str]] = []
    for cells in rows:
        if not cells or not strip_markdown(cells[0]):
            continue
        if len(header) >= 8 and len(cells) >= 8:
            normalized.append(normalize_generated_row(report_date, path.name, cells))
        else:
            normalized.append(normalize_legacy_row(report_date, path.name, cells))
    return normalized


def main() -> int:
    OUTPUT.parent.mkdir(exist_ok=True)
    rows: list[dict[str, str]] = []
    for report in sorted(REPORTS_DIR.glob("*-stock-brief.md")):
        rows.extend(rows_from_report(report))

    with OUTPUT.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {OUTPUT} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
