#!/usr/bin/env python3
"""Generate a daily SVG market-update infographic from CSV outputs."""

from __future__ import annotations

import csv
import html
import re
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
VISUALS = ROOT / "visuals"
REPORTS_CSV = DATA / "reports.csv"
AI_SUMMARY_CSV = DATA / "ai_summary.csv"


WIDTH = 1440
HEIGHT = 900


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def as_float(value: str) -> float | None:
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def latest_report_date(rows: list[dict[str, str]]) -> str:
    return sorted({row["report_date"] for row in rows if row.get("report_date")})[-1]


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def clean_bullets(value: str, limit: int = 4) -> list[str]:
    lines = []
    for line in str(value or "").splitlines():
        cleaned = re.sub(r"^\s*[-•]\s*", "", line).strip()
        if cleaned:
            lines.append(cleaned)
    return lines[:limit]


def wrap(value: str, width: int, max_lines: int) -> list[str]:
    lines: list[str] = []
    for paragraph in str(value or "").splitlines():
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        lines.extend(textwrap.wrap(paragraph, width=width, break_long_words=False))
    return lines[:max_lines]


def text_block(lines: list[str], x: int, y: int, size: int, line_height: int, fill: str = "#EAF6FF", weight: int = 500) -> str:
    parts = []
    for index, line in enumerate(lines):
        parts.append(
            f'<text x="{x}" y="{y + index * line_height}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}">{esc(line)}</text>'
        )
    return "\n".join(parts)


def panel(x: int, y: int, w: int, h: int, title: str, stroke: str = "#48E0FF") -> str:
    return f"""
    <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="26" fill="url(#panelGrad)" stroke="{stroke}" stroke-width="4"/>
    <rect x="{x + 2}" y="{y + 2}" width="{w - 4}" height="70" rx="24" fill="rgba(5,18,46,0.72)"/>
    <text x="{x + 28}" y="{y + 47}" font-size="32" font-weight="900" fill="#FFFFFF">{esc(title)}</text>
    """


def bar_chart(rows: list[tuple[str, float]], x: int, y: int, w: int, h: int, title: str, positive: bool) -> str:
    if not rows:
        return ""
    max_abs = max(abs(value) for _, value in rows) or 1
    bar_gap = 14
    bar_h = (h - 72 - bar_gap * (len(rows) - 1)) / len(rows)
    color = "#39F59B" if positive else "#FF5C7A"
    parts = [
        f'<text x="{x}" y="{y}" font-size="26" font-weight="900" fill="#FFFFFF">{esc(title)}</text>',
    ]
    chart_y = y + 42
    for i, (ticker, value) in enumerate(rows):
        yy = chart_y + i * (bar_h + bar_gap)
        bw = max(6, abs(value) / max_abs * (w - 130))
        parts.append(f'<text x="{x}" y="{yy + bar_h * 0.68:.1f}" font-size="20" font-weight="800" fill="#D9F7FF">{esc(ticker)}</text>')
        parts.append(f'<rect x="{x + 72}" y="{yy}" width="{w - 130}" height="{bar_h}" rx="10" fill="#123B63" opacity="0.75"/>')
        parts.append(f'<rect x="{x + 72}" y="{yy}" width="{bw:.1f}" height="{bar_h}" rx="10" fill="{color}"/>')
        parts.append(f'<text x="{x + w - 48}" y="{yy + bar_h * 0.68:.1f}" text-anchor="end" font-size="19" font-weight="800" fill="#FFFFFF">{value:+.2f}%</text>')
    return "\n".join(parts)


def metric_card(x: int, y: int, title: str, value: str, accent: str) -> str:
    return f"""
    <rect x="{x}" y="{y}" width="255" height="118" rx="22" fill="#071B36" stroke="{accent}" stroke-width="3"/>
    <text x="{x + 22}" y="{y + 38}" font-size="18" font-weight="800" fill="#A7E8FF">{esc(title)}</text>
    <text x="{x + 22}" y="{y + 86}" font-size="38" font-weight="950" fill="#FFFFFF">{esc(value)}</text>
    """


def generate_svg() -> tuple[str, str]:
    reports = read_csv(REPORTS_CSV)
    ai_rows = read_csv(AI_SUMMARY_CSV)
    ai = ai_rows[-1]
    report_date = ai.get("report_date") or latest_report_date(reports)
    latest_rows = [row for row in reports if row.get("report_date") == report_date]

    avg_regular = as_float(ai.get("avg_regular_move_pct", ""))
    avg_extended = as_float(ai.get("avg_extended_move_pct", ""))
    regular = [
        (row["ticker"], as_float(row.get("regular_move_pct", "")))
        for row in latest_rows
        if row.get("ticker") and as_float(row.get("regular_move_pct", "")) is not None
    ]
    extended = [
        (row["ticker"], as_float(row.get("extended_move_pct", "")))
        for row in latest_rows
        if row.get("ticker") and as_float(row.get("extended_move_pct", "")) is not None
    ]
    top_regular = sorted(regular, key=lambda item: item[1], reverse=True)[:6]
    weak_regular = sorted(regular, key=lambda item: item[1])[:6]
    top_extended = sorted(extended, key=lambda item: item[1], reverse=True)[:6]

    headline = ai.get("headline", f"Market update {report_date}")
    market_tone = ai.get("market_tone", "n/a")
    key_points = clean_bullets(ai.get("key_points", ""))
    risks = clean_bullets(ai.get("risks", ""), limit=3)
    actions = clean_bullets(ai.get("actions", ""), limit=3)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#05264F"/>
      <stop offset="45%" stop-color="#087B9E"/>
      <stop offset="100%" stop-color="#0A1942"/>
    </linearGradient>
    <linearGradient id="panelGrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0B315F" stop-opacity="0.94"/>
      <stop offset="100%" stop-color="#07132E" stop-opacity="0.94"/>
    </linearGradient>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="10" stdDeviation="8" flood-color="#00152A" flood-opacity="0.55"/>
    </filter>
    <style>
      text {{ font-family: Inter, Arial, 'Noto Sans Thai', sans-serif; letter-spacing: 0; }}
      .tiny {{ opacity: 0.76; }}
    </style>
  </defs>
  <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#bg)"/>
  <g opacity="0.22">
    <path d="M40 670 C170 570, 240 640, 360 500 S580 410, 700 480 S940 620, 1110 380 S1290 280, 1400 330" fill="none" stroke="#7BFFF2" stroke-width="5"/>
    <path d="M10 760 L130 700 L240 735 L360 620 L470 650 L600 540 L735 580 L850 430 L980 465 L1090 350 L1260 390 L1410 230" fill="none" stroke="#B6FF66" stroke-width="4"/>
    <g fill="#FFFFFF">
      <circle cx="1180" cy="90" r="5"/><circle cx="1320" cy="170" r="4"/><circle cx="210" cy="110" r="4"/><circle cx="92" cy="210" r="3"/>
    </g>
  </g>

  <text x="720" y="74" text-anchor="middle" font-size="56" font-weight="950" fill="#FFFFFF" stroke="#001B35" stroke-width="6" paint-order="stroke">FINANCIAL MARKET UPDATE</text>
  <text x="720" y="112" text-anchor="middle" font-size="24" font-weight="800" fill="#A7F3FF">{esc(report_date)} | Provider: {esc(ai.get("provider"))} / {esc(ai.get("model"))}</text>

  <g filter="url(#shadow)">
    {metric_card(70, 142, "Average regular move", "n/a" if avg_regular is None else f"{avg_regular:+.2f}%", "#48E0FF")}
    {metric_card(350, 142, "Average extended move", "n/a" if avg_extended is None else f"{avg_extended:+.2f}%", "#9BFF6A")}
    {metric_card(630, 142, "Market tone", market_tone[:22], "#FFD84D")}
    {metric_card(910, 142, "Tickers tracked", str(len(latest_rows)), "#FF78A6")}
  </g>

  <g filter="url(#shadow)">
    {panel(70, 290, 760, 300, "AI MARKET BRIEF", "#48E0FF")}
    {text_block(wrap(headline, 58, 2), 105, 390, 29, 38, "#FFFFFF", 900)}
    {text_block([f"• {line}" for line in key_points], 105, 465, 22, 34, "#DDFBFF", 650)}

    {panel(860, 290, 510, 300, "TOP MOVERS", "#9BFF6A")}
    {bar_chart(top_regular, 895, 392, 440, 170, "Regular session leaders", True)}

    {panel(70, 630, 625, 210, "RISKS", "#FFCE4D")}
    {text_block([f"• {line}" for line in risks], 105, 725, 21, 34, "#FFF4C7", 650)}

    {panel(725, 630, 645, 210, "WATCH NEXT", "#FF78A6")}
    {text_block([f"• {line}" for line in actions], 760, 725, 21, 34, "#FFE4EF", 650)}
  </g>

  <g filter="url(#shadow)">
    <rect x="70" y="198" width="1300" height="58" rx="18" fill="#03172E" opacity="0.72" stroke="#49E0FF" stroke-width="2"/>
    <text x="105" y="236" font-size="24" font-weight="850" fill="#EAFBFF">Weakest: {esc(', '.join(f'{t} {v:+.2f}%' for t, v in weak_regular[:5]))}</text>
    <text x="930" y="236" font-size="24" font-weight="850" fill="#EAFBFF">Extended: {esc(', '.join(f'{t} {v:+.2f}%' for t, v in top_extended[:3]))}</text>
  </g>
</svg>
"""
    return report_date, svg


def main() -> int:
    report_date, svg = generate_svg()
    VISUALS.mkdir(exist_ok=True)
    output = VISUALS / f"{report_date}-market-update.svg"
    output.write_text(svg, encoding="utf-8", newline="\n")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
