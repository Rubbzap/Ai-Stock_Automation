# Google Sheets + Apps Script Setup

This setup turns `data/reports.csv` into a Looker Studio-ready Google Sheet.

## What It Creates

The Apps Script in `apps-script/Code.gs` creates and refreshes these tabs:

- `RawData`: all rows from `data/reports.csv`
- `Latest`: latest report date only
- `Chart_TimeSeries`: clean time-series fields for line charts
- `Chart_LatestMoves`: latest ticker moves for bar charts
- `Ticker_Summary`: ticker-level summary metrics
- `AI_Summary`: AI/rule-based narrative summary for Looker Studio text tables
- `Config`: refresh metadata

## Setup

1. Create a new Google Sheet.
2. Open `Extensions > Apps Script`.
3. Replace `Code.gs` with the contents of `apps-script/Code.gs`.
4. Open Project Settings and set the timezone to `Asia/Bangkok`.
5. Run `setupStockBriefDashboard`.
6. Approve permissions.

After setup, the sheet will refresh from:

```text
https://raw.githubusercontent.com/Rubbzap/Ai-Stock_Automation/main/data/reports.csv
```

It also fetches the AI/rule-based summary from:

```text
https://raw.githubusercontent.com/Rubbzap/Ai-Stock_Automation/main/data/ai_summary.csv
```

## Daily Refresh

`setupStockBriefDashboard` also creates a daily trigger around `09:20` Bangkok time.

You can refresh manually from the Google Sheet menu:

```text
Stock Brief > Refresh data now
```

## Looker Studio

In Looker Studio, add data with the **Google Sheets** connector and select this spreadsheet.

Recommended tabs:

- `Chart_TimeSeries` for line charts by date
- `Chart_LatestMoves` for latest daily movers
- `Ticker_Summary` for scorecards and summary tables
- `Latest` for the newest report table
- `AI_Summary` for narrative headline, key points, risks, and actions

Do not choose the connector named `Looker`; that is for a Looker instance, not this Google Sheet.

## Suggested AI Prompt

Use this with Gemini/AI in Looker Studio after adding the Google Sheets data source:

```text
Create a stock dashboard using the Google Sheets data source.

Use Chart_TimeSeries for a time series of regular_close by report_date, filterable by ticker.
Use Chart_LatestMoves for bar charts of regular_move_pct and extended_move_pct by ticker.
Use Ticker_Summary for scorecards and a summary table.
Use AI_Summary for headline text, market tone, key points, risks, and actions.
Add filter controls for ticker and report_date.
Use a clean finance dashboard style.
```
