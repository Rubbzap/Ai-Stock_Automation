const CSV_URL = 'https://raw.githubusercontent.com/Rubbzap/Ai-Stock_Automation/main/data/reports.csv';
const AI_SUMMARY_URL = 'https://raw.githubusercontent.com/Rubbzap/Ai-Stock_Automation/main/data/ai_summary.csv';

const SHEETS = {
  raw: 'RawData',
  latest: 'Latest',
  timeSeries: 'Chart_TimeSeries',
  latestMoves: 'Chart_LatestMoves',
  summary: 'Ticker_Summary',
  aiSummary: 'AI_Summary',
  config: 'Config',
};

const NUMBER_FIELDS = new Set([
  'regular_close',
  'extended_price',
  'regular_move_pct',
  'extended_move_pct',
]);

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('Stock Brief')
    .addItem('Refresh data now', 'refreshStockData')
    .addItem('Setup daily refresh trigger', 'setupDailyRefreshTrigger')
    .addToUi();
}

function setupStockBriefDashboard() {
  refreshStockData();
  setupDailyRefreshTrigger();
}

function refreshStockData() {
  const response = UrlFetchApp.fetch(CSV_URL, {
    muteHttpExceptions: true,
    followRedirects: true,
  });

  if (response.getResponseCode() >= 400) {
    throw new Error(`CSV fetch failed: ${response.getResponseCode()} ${response.getContentText()}`);
  }

  const csvText = response.getContentText('UTF-8');
  const rows = Utilities.parseCsv(csvText);
  if (rows.length < 2) {
    throw new Error('CSV has no data rows.');
  }

  const headers = rows[0];
  const records = rows.slice(1).map((row) => toRecord(headers, row));
  const latestDate = maxDate(records.map((record) => record.report_date));

  writeRows(SHEETS.raw, headers, rows.slice(1).map((row) => normalizeRow(headers, row)));
  writeLatest(records, latestDate);
  writeTimeSeries(records);
  writeLatestMoves(records, latestDate);
  writeTickerSummary(records);
  writeAiSummary();
  writeConfig(records.length, latestDate);

  SpreadsheetApp.flush();
}

function setupDailyRefreshTrigger() {
  ScriptApp.getProjectTriggers()
    .filter((trigger) => trigger.getHandlerFunction() === 'refreshStockData')
    .forEach((trigger) => ScriptApp.deleteTrigger(trigger));

  ScriptApp.newTrigger('refreshStockData')
    .timeBased()
    .everyDays(1)
    .atHour(9)
    .nearMinute(20)
    .create();
}

function toRecord(headers, row) {
  const record = {};
  headers.forEach((header, index) => {
    record[header] = normalizeValue(header, row[index] || '');
  });
  return record;
}

function normalizeRow(headers, row) {
  return headers.map((header, index) => normalizeValue(header, row[index] || ''));
}

function normalizeValue(header, value) {
  if (header === 'report_date' && value) {
    return parseReportDate(value);
  }
  if (NUMBER_FIELDS.has(header)) {
    const numeric = Number(String(value).replace(/,/g, ''));
    return Number.isFinite(numeric) ? numeric : '';
  }
  return value;
}

function parseReportDate(value) {
  const parts = String(value).split('-').map(Number);
  if (parts.length !== 3 || parts.some((part) => !Number.isFinite(part))) {
    return value;
  }
  return new Date(parts[0], parts[1] - 1, parts[2]);
}

function dateKey(value) {
  if (value instanceof Date) {
    return Utilities.formatDate(value, Session.getScriptTimeZone(), 'yyyy-MM-dd');
  }
  return String(value || '');
}

function maxDate(values) {
  return values
    .map(dateKey)
    .filter(Boolean)
    .sort()
    .pop();
}

function writeLatest(records, latestDate) {
  const headers = [
    'report_date',
    'ticker',
    'name',
    'regular_close',
    'extended_price',
    'regular_move_pct',
    'extended_move_pct',
    'source',
  ];

  const rows = records
    .filter((record) => dateKey(record.report_date) === latestDate)
    .map((record) => headers.map((header) => record[header] || ''));

  writeRows(SHEETS.latest, headers, rows);
}

function writeTimeSeries(records) {
  const headers = [
    'report_date',
    'ticker',
    'regular_close',
    'extended_price',
    'regular_move_pct',
    'extended_move_pct',
  ];

  const rows = records.map((record) => headers.map((header) => record[header] || ''));
  writeRows(SHEETS.timeSeries, headers, rows);
}

function writeLatestMoves(records, latestDate) {
  const headers = [
    'ticker',
    'regular_move_pct',
    'extended_move_pct',
    'regular_close',
    'extended_price',
    'source',
  ];

  const rows = records
    .filter((record) => dateKey(record.report_date) === latestDate)
    .map((record) => headers.map((header) => record[header] || ''));

  writeRows(SHEETS.latestMoves, headers, rows);
}

function writeTickerSummary(records) {
  const byTicker = new Map();

  records.forEach((record) => {
    const ticker = record.ticker;
    if (!ticker) return;
    if (!byTicker.has(ticker)) byTicker.set(ticker, []);
    byTicker.get(ticker).push(record);
  });

  const headers = [
    'ticker',
    'first_report_date',
    'latest_report_date',
    'observations',
    'latest_regular_close',
    'latest_extended_price',
    'avg_regular_move_pct',
    'avg_extended_move_pct',
    'max_regular_move_pct',
    'min_regular_move_pct',
  ];

  const rows = Array.from(byTicker.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([ticker, tickerRows]) => {
      const sortedRows = tickerRows
        .slice()
        .sort((a, b) => dateKey(a.report_date).localeCompare(dateKey(b.report_date)));
      const latest = sortedRows[sortedRows.length - 1];
      const regularMoves = sortedRows.map((row) => row.regular_move_pct).filter(isNumber);
      const extendedMoves = sortedRows.map((row) => row.extended_move_pct).filter(isNumber);

      return [
        ticker,
        sortedRows[0].report_date,
        latest.report_date,
        sortedRows.length,
        latest.regular_close || '',
        latest.extended_price || '',
        average(regularMoves),
        average(extendedMoves),
        regularMoves.length ? Math.max(...regularMoves) : '',
        regularMoves.length ? Math.min(...regularMoves) : '',
      ];
    });

  writeRows(SHEETS.summary, headers, rows);
}

function writeConfig(rowCount, latestDate) {
  const rows = [
    ['csv_url', CSV_URL],
    ['ai_summary_url', AI_SUMMARY_URL],
    ['last_refresh', new Date()],
    ['latest_report_date', latestDate],
    ['row_count', rowCount],
    ['looker_data_tabs', `${SHEETS.latest}, ${SHEETS.timeSeries}, ${SHEETS.latestMoves}, ${SHEETS.summary}, ${SHEETS.aiSummary}`],
  ];
  writeRows(SHEETS.config, ['key', 'value'], rows);
}

function writeAiSummary() {
  const response = UrlFetchApp.fetch(AI_SUMMARY_URL, {
    muteHttpExceptions: true,
    followRedirects: true,
  });

  if (response.getResponseCode() >= 400) {
    writeRows(SHEETS.aiSummary, ['status', 'message'], [[
      'missing',
      `AI summary CSV is not available yet: ${response.getResponseCode()}`,
    ]]);
    return;
  }

  const rows = Utilities.parseCsv(response.getContentText('UTF-8'));
  if (rows.length < 2) {
    writeRows(SHEETS.aiSummary, ['status', 'message'], [['empty', 'AI summary CSV has no data rows.']]);
    return;
  }

  const headers = rows[0];
  const normalizedRows = rows.slice(1).map((row) => normalizeRow(headers, row));
  writeRows(SHEETS.aiSummary, headers, normalizedRows);
}

function writeRows(sheetName, headers, rows) {
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = spreadsheet.getSheetByName(sheetName) || spreadsheet.insertSheet(sheetName);
  sheet.clearContents();

  const values = [headers].concat(rows);
  sheet.getRange(1, 1, values.length, headers.length).setValues(values);
  sheet.setFrozenRows(1);
  sheet.autoResizeColumns(1, headers.length);
  sheet.getRange(1, 1, 1, headers.length).setFontWeight('bold');

  formatSheet(sheet, headers, values.length);
}

function formatSheet(sheet, headers, rowCount) {
  headers.forEach((header, index) => {
    const column = index + 1;
    if (header.includes('date')) {
      sheet.getRange(2, column, Math.max(rowCount - 1, 1), 1).setNumberFormat('yyyy-mm-dd');
    }
    if (NUMBER_FIELDS.has(header) || header.includes('avg_') || header.includes('max_') || header.includes('min_')) {
      sheet.getRange(2, column, Math.max(rowCount - 1, 1), 1).setNumberFormat('0.00');
    }
  });
}

function average(values) {
  return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : '';
}

function isNumber(value) {
  return typeof value === 'number' && Number.isFinite(value);
}
