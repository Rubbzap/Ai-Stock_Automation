#!/usr/bin/env python3
"""Generate a daily stock brief Markdown file from watchlist.md.

This script intentionally uses only the Python standard library so it can run
inside GitHub Actions without dependency installation.
"""

from __future__ import annotations

import datetime as dt
import email.utils
import html
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
WATCHLIST = ROOT / "watchlist.md"
REPORTS = ROOT / "reports"
TZ = ZoneInfo("Asia/Bangkok")
USER_AGENT = "Mozilla/5.0 (compatible; daily-stock-brief/1.0)"


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=25) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=25) as response:
        return response.read().decode("utf-8", errors="replace")


def read_watchlist() -> list[str]:
    text = WATCHLIST.read_text(encoding="utf-8")
    block = re.search(r"```text\s*(.*?)```", text, flags=re.S)
    source = block.group(1) if block else text
    tickers: list[str] = []
    for line in source.splitlines():
        symbol = line.strip().upper()
        if not symbol or symbol.startswith("#"):
            continue
        if re.fullmatch(r"[A-Z0-9.^=-]{1,12}", symbol):
            tickers.append(symbol)
    return list(dict.fromkeys(tickers))


def yahoo_chart(symbol: str, range_: str = "5d", interval: str = "5m", include_prepost: bool = True) -> dict:
    encoded = urllib.parse.quote(symbol, safe="")
    prepost = "true" if include_prepost else "false"
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded}"
        f"?range={range_}&interval={interval}&includePrePost={prepost}"
    )
    data = fetch_json(url)
    error = data.get("chart", {}).get("error")
    if error:
        raise RuntimeError(error.get("description") or str(error))
    results = data.get("chart", {}).get("result") or []
    if not results:
        raise RuntimeError("No Yahoo chart result")
    return results[0]


def fmt_price(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:,.2f}"


def fmt_pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.2f}%"


def ts_label(timestamp: int | None, timezone_name: str | None) -> str:
    if not timestamp:
        return "n/a"
    try:
        zone = ZoneInfo(timezone_name or "America/New_York")
    except Exception:
        zone = dt.timezone.utc
    return dt.datetime.fromtimestamp(timestamp, zone).strftime("%Y-%m-%d %H:%M %Z")


def quote_for(symbol: str) -> dict:
    chart = yahoo_chart(symbol, range_="5d", interval="5m", include_prepost=True)
    daily_chart = yahoo_chart(symbol, range_="5d", interval="1d", include_prepost=False)
    meta = chart.get("meta", {})
    timestamps = chart.get("timestamp") or []
    quote = (chart.get("indicators", {}).get("quote") or [{}])[0]
    closes = quote.get("close") or []
    daily_quote = (daily_chart.get("indicators", {}).get("quote") or [{}])[0]
    daily_closes = [float(value) for value in daily_quote.get("close", []) if value is not None]

    latest_price = None
    latest_ts = None
    for timestamp, close in reversed(list(zip(timestamps, closes))):
        if close is not None:
            latest_price = float(close)
            latest_ts = int(timestamp)
            break

    close_price = daily_closes[-1] if daily_closes else meta.get("regularMarketPrice")
    previous_close = daily_closes[-2] if len(daily_closes) >= 2 else meta.get("chartPreviousClose")
    close_price = float(close_price) if close_price is not None else latest_price
    previous_close = float(previous_close) if previous_close is not None else None

    change_pct = None
    if close_price is not None and previous_close:
        change_pct = (close_price - previous_close) / previous_close * 100

    extended_pct = None
    if latest_price is not None and close_price:
        extended_pct = (latest_price - close_price) / close_price * 100

    return {
        "symbol": symbol,
        "name": meta.get("shortName") or meta.get("longName") or symbol,
        "currency": meta.get("currency") or "",
        "close": close_price,
        "latest": latest_price,
        "change_pct": change_pct,
        "extended_pct": extended_pct,
        "close_time": ts_label(meta.get("regularMarketTime"), meta.get("exchangeTimezoneName")),
        "latest_time": ts_label(latest_ts, meta.get("exchangeTimezoneName")),
        "source": f"https://finance.yahoo.com/quote/{urllib.parse.quote(symbol, safe='')}/",
        "error": None,
    }


def rss_news(symbols: list[str], limit: int = 8) -> list[dict]:
    joined = ",".join(symbols[:12])
    url = (
        "https://feeds.finance.yahoo.com/rss/2.0/headline?"
        + urllib.parse.urlencode({"s": joined, "region": "US", "lang": "en-US"})
    )
    try:
        root = ET.fromstring(fetch_text(url))
    except Exception:
        return []

    items: list[dict] = []
    for item in root.findall("./channel/item"):
        title = html.unescape((item.findtext("title") or "").strip())
        link = (item.findtext("link") or "").strip()
        published = item.findtext("pubDate") or ""
        if not title or not link:
            continue
        try:
            parsed_date = email.utils.parsedate_to_datetime(published)
            date_label = parsed_date.astimezone(TZ).strftime("%Y-%m-%d %H:%M")
        except Exception:
            date_label = ""
        items.append({"title": title, "link": link, "date": date_label})
        if len(items) >= limit:
            break
    return items


def mermaid_chart(title: str, y_label: str, values: list[tuple[str, float]], lower: float, upper: float) -> str:
    if not values:
        return "_Not enough data for chart._"
    labels = ", ".join(json.dumps(label) for label, _ in values)
    nums = ", ".join(f"{value:.2f}" for _, value in values)
    return (
        "```mermaid\n"
        "xychart-beta\n"
        f"    title {json.dumps(title)}\n"
        f"    x-axis [{labels}]\n"
        f"    y-axis {json.dumps(y_label)} {lower:.0f} --> {upper:.0f}\n"
        f"    bar [{nums}]\n"
        "```"
    )


def group_heatmap(rows: list[dict]) -> str:
    groups = {
        "Mega-cap tech": {"AAPL", "GOOG", "GOOGL", "TSLA", "NVDA", "AVGO"},
        "Semis / memory": {"INTC", "AMD", "MU", "SNDK", "DRAM", "ASML"},
        "Space / high beta": {"RKLB", "ASTS", "IREN", "EOSE"},
        "ETFs": {"SPY", "QQQ", "JEPQ"},
    }
    lines = ["| Group | Names in watchlist | Avg regular move | Avg extended move |", "|---|---|---:|---:|"]
    for group, symbols in groups.items():
        matches = [row for row in rows if row["symbol"] in symbols and row.get("error") is None]
        if not matches:
            continue
        regular = [row["change_pct"] for row in matches if row["change_pct"] is not None]
        extended = [row["extended_pct"] for row in matches if row["extended_pct"] is not None]
        lines.append(
            "| {group} | {names} | {regular} | {extended} |".format(
                group=group,
                names=", ".join(row["symbol"] for row in matches),
                regular=fmt_pct(sum(regular) / len(regular)) if regular else "n/a",
                extended=fmt_pct(sum(extended) / len(extended)) if extended else "n/a",
            )
        )
    return "\n".join(lines)


def build_report(rows: list[dict], news: list[dict], report_date: dt.date) -> str:
    valid = [row for row in rows if row.get("error") is None]
    top_regular = sorted(
        [(row["symbol"], row["change_pct"]) for row in valid if row["change_pct"] is not None],
        key=lambda item: item[1],
        reverse=True,
    )[:10]
    top_extended = sorted(
        [(row["symbol"], row["extended_pct"]) for row in valid if row["extended_pct"] is not None],
        key=lambda item: item[1],
        reverse=True,
    )[:10]

    regular_values = [value for _, value in top_regular]
    extended_values = [value for _, value in top_extended]
    regular_upper = max(5, int(max(regular_values or [5])) + 2)
    extended_lower = min(-5, int(min(extended_values or [-1])) - 1)
    extended_upper = max(5, int(max(extended_values or [1])) + 1)

    lines = [
        f"# Stock Brief - {report_date.isoformat()}",
        "",
        f"Generated at {dt.datetime.now(TZ).strftime('%Y-%m-%d %H:%M %Z')} from `watchlist.md`.",
        "Prices are snapshots from Yahoo Finance public chart data. Extended/overnight is the latest available pre/post-market datapoint from the same feed.",
        "",
        "## Market Snapshot",
        "",
    ]

    for symbol in ("SPY", "QQQ", "JEPQ"):
        row = next((item for item in valid if item["symbol"] == symbol), None)
        if row:
            lines.append(
                f"- {symbol}: close {fmt_price(row['close'])}, latest extended {fmt_price(row['latest'])}, "
                f"regular move {fmt_pct(row['change_pct'])}, extended move {fmt_pct(row['extended_pct'])}"
            )
    if not any(line.startswith("- ") for line in lines[-3:]):
        lines.append("- Broad market ETFs were not found in the watchlist.")

    lines += [
        "",
        "## Watchlist Prices",
        "",
        "| Ticker | Name | Regular close | Latest extended/overnight | Regular move | Extended move | Latest data time | Source |",
        "|---|---|---:|---:|---:|---:|---|---|",
    ]
    for row in rows:
        if row.get("error"):
            lines.append(f"| {row['symbol']} | n/a | n/a | n/a | n/a | n/a | n/a | Error: {row['error']} |")
            continue
        lines.append(
            f"| {row['symbol']} | {row['name']} | {fmt_price(row['close'])} {row['currency']} | "
            f"{fmt_price(row['latest'])} {row['currency']} | {fmt_pct(row['change_pct'])} | "
            f"{fmt_pct(row['extended_pct'])} | {row['latest_time']} | [Yahoo]({row['source']}) |"
        )

    lines += [
        "",
        "## Charts",
        "",
        "### Top Movers - Regular Session",
        "",
        mermaid_chart("Top movers by regular-session change (%)", "Change %", top_regular, 0, regular_upper),
        "",
        "### Extended / Overnight Move",
        "",
        mermaid_chart("Latest extended move from regular close (%)", "Extended %", top_extended, extended_lower, extended_upper),
        "",
        "### Quick Heatmap",
        "",
        group_heatmap(rows),
        "",
        "## News Headlines",
        "",
    ]
    if news:
        for item in news:
            date = f" ({item['date']} Bangkok)" if item["date"] else ""
            lines.append(f"- [{item['title']}]({item['link']}){date}")
    else:
        lines.append("- No Yahoo Finance RSS headlines were available during this run.")

    errors = [row for row in rows if row.get("error")]
    lines += [
        "",
        "## Caveats",
        "",
        "- This is not investment advice. Extended-hours prices can be thin and volatile.",
        "- Yahoo public endpoints may lag official exchange data.",
    ]
    if errors:
        lines.append("- Tickers with fetch errors: " + ", ".join(f"{row['symbol']} ({row['error']})" for row in errors))

    return "\n".join(lines) + "\n"


def main() -> int:
    report_date = dt.datetime.now(TZ).date()
    symbols = read_watchlist()
    if not symbols:
        print("No tickers found in watchlist.md", file=sys.stderr)
        return 1

    rows = []
    for symbol in symbols:
        try:
            rows.append(quote_for(symbol))
        except Exception as exc:
            rows.append({"symbol": symbol, "error": str(exc)})

    news = rss_news(symbols)
    REPORTS.mkdir(exist_ok=True)
    output = REPORTS / f"{report_date.isoformat()}-stock-brief.md"
    output.write_text(build_report(rows, news, report_date), encoding="utf-8", newline="\n")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
