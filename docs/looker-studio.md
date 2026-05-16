# Looker Studio / Google Data Studio

[![Visualize in Looker Studio](https://img.shields.io/badge/Visualize-Looker%20Studio-4285F4?logo=looker&logoColor=white)](https://lookerstudio.google.com/reporting/create?r.reportName=Daily%20Stock%20Brief%20Dashboard)
[![Open Raw CSV](https://img.shields.io/badge/Open-raw%20reports.csv-34A853?logo=googlesheets&logoColor=white)](https://raw.githubusercontent.com/Rubbzap/Automations1/main/data/reports.csv)

## Data Source

Raw CSV:

```text
https://raw.githubusercontent.com/Rubbzap/Automations1/main/data/reports.csv
```

## Recommended Setup

Looker Studio does not reliably create a report directly from a GitHub raw CSV URL in one click. The most stable setup is:

1. Create a Google Sheet.
2. Put this formula in cell `A1`:

```text
=IMPORTDATA("https://raw.githubusercontent.com/Rubbzap/Automations1/main/data/reports.csv")
```

3. Open the Looker Studio button above.
4. Add data source: Google Sheets.
5. Select the sheet created in step 1.

## Suggested Charts

- Time series: `report_date` by `regular_close`
- Bar chart: `ticker` by `regular_move_pct`
- Bar chart: `ticker` by `extended_move_pct`
- Filter controls: `ticker`, `report_date`
- Table: `ticker`, `regular_close`, `extended_price`, `source`
