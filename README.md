# Daily Stock Brief

โปรเจกต์นี้สร้างรายงานข่าวหุ้นแบบสั้นรายวัน, export CSV สำหรับ BI, และสร้าง AI summary สำหรับใช้ใน Looker Studio

[![Open CSV](https://img.shields.io/badge/Data-reports.csv-34A853?logo=googlesheets&logoColor=white)](https://raw.githubusercontent.com/Rubbzap/Ai-Stock_Automation/main/data/reports.csv)
[![Open AI Summary](https://img.shields.io/badge/AI-ai_summary.csv-8E75B2?logo=googlegemini&logoColor=white)](https://raw.githubusercontent.com/Rubbzap/Ai-Stock_Automation/main/data/ai_summary.csv)
[![Open Looker Studio](https://img.shields.io/badge/Open-Looker%20Studio-4285F4?logo=looker&logoColor=white)](https://lookerstudio.google.com/)

GitHub Actions จะทำงานทุกวันเวลา 09:00 ตามเวลา Asia/Bangkok แล้วสร้าง/อัปเดตไฟล์:

```text
reports/YYYY-MM-DD-stock-brief.md
reports/YYYY-MM-DD-ai-summary.md
data/reports.csv
data/ai_summary.csv
visuals/YYYY-MM-DD-market-update.svg
```

## สิ่งที่รายงานควรมี

- ข่าวหุ้น/ตลาดแบบสั้น กระชับ อ่านเร็ว
- ราคาปิดล่าสุดของแต่ละตัวใน watchlist
- ราคาหลังตลาด/กลางคืน เช่น after-hours, pre-market, overnight หรือ session ล่าสุดที่หาได้
- ลิงก์แหล่งข้อมูลที่ใช้
- หมายเหตุถ้าราคากลางคืนของตัวใดไม่มีข้อมูล
- AI summary สำหรับ headline, market tone, key points, risks, actions
- ภาพ infographic รายวันใน `visuals/` สำหรับแชร์หรือฝังใน dashboard

## Visualize

ข้อมูลที่พร้อมต่อ BI:

- `data/reports.csv`: ราคาหุ้นและ metric แบบ structured
- `data/ai_summary.csv`: AI/rule-based summary สำหรับใส่ใน Looker Studio
- `visuals/YYYY-MM-DD-market-update.svg`: infographic สรุปตลาดรายวัน

> อย่าเลือก connector ชื่อ **Looker** ใน Looker Studio เพราะอันนั้นใช้ต่อ Looker instance ไม่ใช่ CSV นี้

วิธีที่เสถียรที่สุด:

1. เปิด Google Sheets ใหม่
2. ไปที่ `Extensions > Apps Script`
3. วางโค้ดจาก `apps-script/Code.gs`
4. รันฟังก์ชัน `setupStockBriefDashboard`
5. เปิด Looker Studio แล้วเลือก connector **Google Sheets**
6. เลือกชีตที่สร้างไว้ แล้วใช้ tab เหล่านี้เป็น data source:
   - `Chart_TimeSeries`
   - `Chart_LatestMoves`
   - `Ticker_Summary`
   - `Latest`
   - `AI_Summary`

หลังต่อข้อมูลแล้ว สามารถใช้ AI/Gemini ใน Looker Studio ด้วย prompt นี้:

```text
Create a stock dashboard with:
- time series of regular_close by report_date, filterable by ticker
- bar chart of regular_move_pct by ticker for latest report_date
- bar chart of extended_move_pct by ticker for latest report_date
- table with report_date, ticker, regular_close, extended_price, regular_move_pct, extended_move_pct, source
- text/table section from AI_Summary showing headline, market_tone, key_points, risks, actions
- filter controls for ticker and report_date
```

ถ้า Looker Studio account ไม่มี Gemini ให้ใช้ tab `AI_Summary` แสดง summary ที่ GitHub Actions สร้างไว้แทนได้เลย

ดูขั้นตอนเต็มได้ที่ `docs/looker-studio.md`

ดูวิธีตั้งค่า Google Sheets + Apps Script ได้ที่ `docs/google-sheets-apps-script.md`

ดูวิธีเปิด AI summary ผ่าน GitHub Actions ได้ที่ `docs/ai-summary.md`

## AI Summary

ระบบจะใช้ provider ตามลำดับนี้:

1. `OPENAI_API_KEY` ถ้ามี
2. `GEMINI_API_KEY` ถ้ามี
3. rule-based fallback ถ้าไม่มี API key

ถ้าใช้ Gemini ให้เพิ่ม GitHub Secret:

```text
GEMINI_API_KEY
```

หลัง workflow รันแล้ว เช็กได้ที่ `data/ai_summary.csv`:

- `provider = gemini` แปลว่าใช้ Gemini สำเร็จ
- `provider = rule_based` แปลว่ายังใช้ fallback

## Watchlist

แก้รายการหุ้น/ดัชนีที่ต้องติดตามได้ที่ `watchlist.md`

ใช้ ticker ตามแหล่งข้อมูลสากล เช่น Yahoo Finance:

- หุ้นไทยมักลงท้าย `.BK`
- หุ้นสหรัฐใช้ ticker ตรง ๆ เช่น `AAPL`
- ETF/ดัชนีอาจใช้สัญลักษณ์ตามแหล่งข้อมูล เช่น `SPY`, `QQQ`, `^GSPC`

## Manual Run

ไปที่ GitHub repo > `Actions` > `Daily Stock Brief` > `Run workflow`

Repo: `https://github.com/Rubbzap/Ai-Stock_Automation`
