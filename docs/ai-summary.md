# AI Summary Pipeline

The daily GitHub Action now creates:

- `data/ai_summary.csv`
- `reports/YYYY-MM-DD-ai-summary.md`

Looker Studio can display `AI_Summary` from the Google Sheet as a table/text section.

## Providers

The script tries providers in this order:

1. OpenAI if `OPENAI_API_KEY` is set
2. Gemini if `GEMINI_API_KEY` is set
3. Rule-based fallback if no API key is available

## GitHub Secrets

Add one of these repository secrets:

- `OPENAI_API_KEY`
- `GEMINI_API_KEY`

Optional repository variables:

- `OPENAI_MODEL`, default `gpt-5.2`
- `GEMINI_MODEL`, default `gemini-2.5-flash`

GitHub path:

```text
Settings > Secrets and variables > Actions
```

## Looker Studio

After updating the Apps Script in your Google Sheet and running `refreshStockData`, a new tab appears:

```text
AI_Summary
```

Use it for:

- headline cards
- market tone
- key points
- risks
- actions to watch

If no API key is configured, the tab still works with a deterministic rule-based summary.
