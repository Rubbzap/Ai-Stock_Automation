#!/usr/bin/env python3
"""Generate AI-ready stock summary outputs for Looker Studio.

Outputs:
- data/ai_summary.csv
- reports/YYYY-MM-DD-ai-summary.md

If OPENAI_API_KEY or GEMINI_API_KEY is present, the script asks the selected
model for a concise Thai summary. Without an API key it still writes a
deterministic rule-based summary so downstream dashboards keep working.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import os
import re
import statistics
import urllib.error
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REPORTS = ROOT / "reports"
REPORTS_CSV = DATA / "reports.csv"
AI_SUMMARY_CSV = DATA / "ai_summary.csv"
TZ = ZoneInfo("Asia/Bangkok")

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.2")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def read_rows() -> list[dict[str, str]]:
    with REPORTS_CSV.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def as_float(value: str) -> float | None:
    if value is None:
        return None
    cleaned = str(value).replace(",", "").strip()
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def fmt_pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:+.2f}%"


def fmt_price(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:,.2f}"


def latest_date(rows: list[dict[str, str]]) -> str:
    return sorted({row["report_date"] for row in rows if row.get("report_date")})[-1]


def latest_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    date = latest_date(rows)
    return [row for row in rows if row.get("report_date") == date]


def build_metrics(rows: list[dict[str, str]]) -> dict:
    latest = latest_rows(rows)
    regular = [(row["ticker"], as_float(row.get("regular_move_pct", ""))) for row in latest]
    extended = [(row["ticker"], as_float(row.get("extended_move_pct", ""))) for row in latest]
    regular = [(ticker, value) for ticker, value in regular if value is not None]
    extended = [(ticker, value) for ticker, value in extended if value is not None]

    closes = {
        row["ticker"]: as_float(row.get("regular_close", ""))
        for row in latest
        if row.get("ticker")
    }
    extended_prices = {
        row["ticker"]: as_float(row.get("extended_price", ""))
        for row in latest
        if row.get("ticker")
    }

    return {
        "report_date": latest_date(rows),
        "generated_at": dt.datetime.now(TZ).strftime("%Y-%m-%d %H:%M %Z"),
        "row_count": len(latest),
        "top_regular": sorted(regular, key=lambda item: item[1], reverse=True)[:5],
        "bottom_regular": sorted(regular, key=lambda item: item[1])[:5],
        "top_extended": sorted(extended, key=lambda item: item[1], reverse=True)[:5],
        "bottom_extended": sorted(extended, key=lambda item: item[1])[:5],
        "avg_regular_move": statistics.mean([value for _, value in regular]) if regular else None,
        "avg_extended_move": statistics.mean([value for _, value in extended]) if extended else None,
        "closes": closes,
        "extended_prices": extended_prices,
    }


def compact_list(items: list[tuple[str, float]]) -> str:
    return ", ".join(f"{ticker} {fmt_pct(value)}" for ticker, value in items) or "n/a"


def fallback_summary(metrics: dict) -> dict[str, str]:
    top_regular = metrics["top_regular"][0] if metrics["top_regular"] else (None, None)
    bottom_regular = metrics["bottom_regular"][0] if metrics["bottom_regular"] else (None, None)
    top_extended = metrics["top_extended"][0] if metrics["top_extended"] else (None, None)

    headline = (
        f"{metrics['report_date']}: watchlist average regular move "
        f"{fmt_pct(metrics['avg_regular_move'])}; strongest regular mover "
        f"{top_regular[0] or 'n/a'} {fmt_pct(top_regular[1])}."
    )
    market_tone = "risk-on" if (metrics["avg_regular_move"] or 0) > 0 else "risk-off / mixed"
    key_points = [
        f"Top regular movers: {compact_list(metrics['top_regular'])}.",
        f"Weakest regular movers: {compact_list(metrics['bottom_regular'])}.",
        f"Top extended-hours movers: {compact_list(metrics['top_extended'])}.",
        f"Average extended move is {fmt_pct(metrics['avg_extended_move'])}.",
    ]
    risks = [
        "Extended-hours prices can be thin and may reverse during the next regular session.",
        "Some symbols may have stale or missing extended-hours data depending on source coverage.",
    ]
    actions = [
        f"Watch whether {top_extended[0] or 'top extended movers'} can hold gains at the next open.",
        f"Check news for {bottom_regular[0] or 'weak names'} before treating the move as purely technical.",
    ]
    return {
        "provider": "rule_based",
        "model": "fallback",
        "headline": headline,
        "market_tone": market_tone,
        "key_points": "\n".join(f"- {point}" for point in key_points),
        "risks": "\n".join(f"- {risk}" for risk in risks),
        "actions": "\n".join(f"- {action}" for action in actions),
    }


def prompt_for(metrics: dict) -> str:
    payload = {
        "report_date": metrics["report_date"],
        "avg_regular_move_pct": metrics["avg_regular_move"],
        "avg_extended_move_pct": metrics["avg_extended_move"],
        "top_regular": metrics["top_regular"],
        "bottom_regular": metrics["bottom_regular"],
        "top_extended": metrics["top_extended"],
        "bottom_extended": metrics["bottom_extended"],
    }
    return (
        "You are writing for a Thai retail investor dashboard. "
        "Summarize this stock watchlist data in Thai. "
        "Return strict JSON with keys: headline, market_tone, key_points, risks, actions. "
        "Each value must be concise. key_points, risks, and actions should be arrays of strings. "
        "Do not give investment advice or buy/sell recommendations.\n\n"
        f"DATA:\n{json.dumps(payload, ensure_ascii=False)}"
    )


def post_json(url: str, headers: dict[str, str], body: dict) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={**headers, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def parse_jsonish(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def normalize_ai_payload(payload: dict, provider: str, model: str) -> dict[str, str]:
    def join_value(value) -> str:
        if isinstance(value, list):
            return "\n".join(f"- {str(item).strip()}" for item in value if str(item).strip())
        return str(value or "").strip()

    return {
        "provider": provider,
        "model": model,
        "headline": join_value(payload.get("headline")),
        "market_tone": join_value(payload.get("market_tone")),
        "key_points": join_value(payload.get("key_points")),
        "risks": join_value(payload.get("risks")),
        "actions": join_value(payload.get("actions")),
    }


def openai_summary(metrics: dict) -> dict[str, str]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    data = post_json(
        "https://api.openai.com/v1/responses",
        {"Authorization": f"Bearer {api_key}"},
        {
            "model": OPENAI_MODEL,
            "input": prompt_for(metrics),
            "text": {"format": {"type": "json_object"}},
        },
    )
    output_text = data.get("output_text")
    if not output_text:
        output_text = "".join(
            content.get("text", "")
            for item in data.get("output", [])
            for content in item.get("content", [])
            if content.get("type") == "output_text"
        )
    return normalize_ai_payload(parse_jsonish(output_text), "openai", OPENAI_MODEL)


def gemini_summary(metrics: dict) -> dict[str, str]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
        f"?key={api_key}"
    )
    data = post_json(
        url,
        {},
        {
            "contents": [{"parts": [{"text": prompt_for(metrics)}]}],
            "generationConfig": {"response_mime_type": "application/json"},
        },
    )
    output_text = data["candidates"][0]["content"]["parts"][0]["text"]
    return normalize_ai_payload(parse_jsonish(output_text), "gemini", GEMINI_MODEL)


def generate_summary(metrics: dict) -> dict[str, str]:
    if os.getenv("OPENAI_API_KEY"):
        try:
            return openai_summary(metrics)
        except Exception as exc:
            print(f"OpenAI summary failed, falling back: {exc}")
    if os.getenv("GEMINI_API_KEY"):
        try:
            return gemini_summary(metrics)
        except Exception as exc:
            print(f"Gemini summary failed, falling back: {exc}")
    return fallback_summary(metrics)


def write_csv(metrics: dict, summary: dict[str, str]) -> None:
    AI_SUMMARY_CSV.parent.mkdir(exist_ok=True)
    fieldnames = [
        "report_date",
        "generated_at",
        "provider",
        "model",
        "headline",
        "market_tone",
        "key_points",
        "risks",
        "actions",
        "avg_regular_move_pct",
        "avg_extended_move_pct",
        "top_regular",
        "bottom_regular",
        "top_extended",
        "bottom_extended",
    ]
    row = {
        "report_date": metrics["report_date"],
        "generated_at": metrics["generated_at"],
        "provider": summary["provider"],
        "model": summary["model"],
        "headline": summary["headline"],
        "market_tone": summary["market_tone"],
        "key_points": summary["key_points"],
        "risks": summary["risks"],
        "actions": summary["actions"],
        "avg_regular_move_pct": "" if metrics["avg_regular_move"] is None else f"{metrics['avg_regular_move']:.2f}",
        "avg_extended_move_pct": "" if metrics["avg_extended_move"] is None else f"{metrics['avg_extended_move']:.2f}",
        "top_regular": compact_list(metrics["top_regular"]),
        "bottom_regular": compact_list(metrics["bottom_regular"]),
        "top_extended": compact_list(metrics["top_extended"]),
        "bottom_extended": compact_list(metrics["bottom_extended"]),
    }
    with AI_SUMMARY_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(row)


def write_markdown(metrics: dict, summary: dict[str, str]) -> Path:
    REPORTS.mkdir(exist_ok=True)
    output = REPORTS / f"{metrics['report_date']}-ai-summary.md"
    output.write_text(
        "\n".join(
            [
                f"# AI Summary - {metrics['report_date']}",
                "",
                f"Generated at {metrics['generated_at']} using `{summary['provider']}` / `{summary['model']}`.",
                "",
                f"## Headline\n\n{summary['headline']}",
                "",
                f"## Market Tone\n\n{summary['market_tone']}",
                "",
                f"## Key Points\n\n{summary['key_points']}",
                "",
                f"## Risks\n\n{summary['risks']}",
                "",
                f"## Actions To Watch\n\n{summary['actions']}",
                "",
                "## Metrics",
                "",
                f"- Average regular move: {fmt_pct(metrics['avg_regular_move'])}",
                f"- Average extended move: {fmt_pct(metrics['avg_extended_move'])}",
                f"- Top regular: {compact_list(metrics['top_regular'])}",
                f"- Bottom regular: {compact_list(metrics['bottom_regular'])}",
                f"- Top extended: {compact_list(metrics['top_extended'])}",
                f"- Bottom extended: {compact_list(metrics['bottom_extended'])}",
                "",
            ]
        ),
        encoding="utf-8",
        newline="\n",
    )
    return output


def main() -> int:
    rows = read_rows()
    metrics = build_metrics(rows)
    summary = generate_summary(metrics)
    write_csv(metrics, summary)
    output = write_markdown(metrics, summary)
    print(f"Wrote {AI_SUMMARY_CSV}")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
