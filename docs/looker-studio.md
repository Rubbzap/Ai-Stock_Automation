# Looker Studio / Google Data Studio

[![Open Raw CSV](https://img.shields.io/badge/Open-raw%20reports.csv-34A853?logo=googlesheets&logoColor=white)](https://raw.githubusercontent.com/Rubbzap/Automations1/main/data/reports.csv)
[![Open Looker Studio](https://img.shields.io/badge/Open-Looker%20Studio-4285F4?logo=looker&logoColor=white)](https://lookerstudio.google.com/)

## Data Source

Raw CSV:

```text
https://raw.githubusercontent.com/Rubbzap/Automations1/main/data/reports.csv
```

## Recommended Setup

Looker Studio does not reliably create a report directly from a GitHub raw CSV URL in one click. The most stable setup is Google Sheets + Apps Script:

1. Create a Google Sheet.
2. Open `Extensions > Apps Script`.
3. Paste `apps-script/Code.gs`.
4. Run `setupStockBriefDashboard`.
5. Open Looker Studio.
6. Add data source: Google Sheets.
7. Select the sheet created in step 1.

Do not choose the connector named `Looker`; that connector is for connecting to a Looker instance, not this CSV dataset.

Full setup guide: `docs/google-sheets-apps-script.md`

## AI Prompt

After adding the Google Sheets data source, use this prompt with Gemini/AI in Looker Studio if your account has the feature:

```text
Create a stock dashboard with:
- time series of regular_close by report_date, filterable by ticker
- bar chart of regular_move_pct by ticker for latest report_date
- bar chart of extended_move_pct by ticker for latest report_date
- table with report_date, ticker, regular_close, extended_price, regular_move_pct, extended_move_pct, source
- filter controls for ticker and report_date
Use a clean finance dashboard style.
```

## Suggested Charts

- Time series: `report_date` by `regular_close`
- Bar chart: `ticker` by `regular_move_pct`
- Bar chart: `ticker` by `extended_move_pct`
- Filter controls: `ticker`, `report_date`
- Table: `ticker`, `regular_close`, `extended_price`, `source`
