# Daily Stock Brief Automation Prompt

Create a concise Thai-language daily stock market brief as a Markdown file.

Read `watchlist.md` from the repository and use its tickers as the primary coverage list. For each ticker, gather reliable current market data from public sources such as Yahoo Finance, Nasdaq, exchange pages, broker market pages, or other reputable financial data providers. Include the latest regular-session close and the latest available after-hours, pre-market, overnight, or extended-hours price. If extended-hours or overnight data is not available for a ticker, state that clearly.

Also gather short, current market/news context relevant to the watchlist and major indices. Prefer primary or reputable financial/news sources and include Markdown links to sources used. Keep the brief short and scannable.

Write the report to `reports/YYYY-MM-DD-stock-brief.md`, using the local date for the filename. The report should include:

- Title with date
- Market snapshot
- Watchlist price table with close and overnight/extended-hours price
- Short bullet summary of important news
- Source links
- Data caveats where needed

After writing the file, run Git commands to add the new report and any project metadata changes, commit with a message like `Add stock brief YYYY-MM-DD`, and push to the configured GitHub remote. If no remote is configured or push fails, still commit locally when possible and include the reason in the run output.
