# Daily Stock Brief

โปรเจกต์นี้เก็บรายงานข่าวหุ้นแบบสั้นรายวันเป็นไฟล์ Markdown ใน `reports/`

[![Open CSV](https://img.shields.io/badge/Data-reports.csv-34A853?logo=googlesheets&logoColor=white)](https://raw.githubusercontent.com/Rubbzap/Automations1/main/data/reports.csv)
[![Open Looker Studio](https://img.shields.io/badge/Open-Looker%20Studio-4285F4?logo=looker&logoColor=white)](https://lookerstudio.google.com/)

Automation ที่ผูกไว้จะทำงานทุกวันเวลา 09:00 ตามเวลา Asia/Bangkok แล้วสร้างไฟล์:

```text
reports/YYYY-MM-DD-stock-brief.md
```

## สิ่งที่รายงานควรมี

- ข่าวหุ้น/ตลาดแบบสั้น กระชับ อ่านเร็ว
- ราคาปิดล่าสุดของแต่ละตัวใน watchlist
- ราคาหลังตลาด/กลางคืน เช่น after-hours, pre-market, overnight หรือ session ล่าสุดที่หาได้
- ลิงก์แหล่งข้อมูลที่ใช้
- หมายเหตุถ้าราคากลางคืนของตัวใดไม่มีข้อมูล

## Visualize

ข้อมูลที่พร้อมต่อ BI อยู่ที่ `data/reports.csv`

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

หลังต่อข้อมูลแล้ว สามารถใช้ AI/Gemini ใน Looker Studio ด้วย prompt นี้:

```text
Create a stock dashboard with:
- time series of regular_close by report_date, filterable by ticker
- bar chart of regular_move_pct by ticker for latest report_date
- bar chart of extended_move_pct by ticker for latest report_date
- table with report_date, ticker, regular_close, extended_price, regular_move_pct, extended_move_pct, source
- filter controls for ticker and report_date
```

ดูขั้นตอนเต็มได้ที่ `docs/looker-studio.md`

ดูวิธีตั้งค่า Google Sheets + Apps Script ได้ที่ `docs/google-sheets-apps-script.md`

## Watchlist

แก้รายการหุ้น/ดัชนีที่ต้องติดตามได้ที่ `watchlist.md`

ใช้ ticker ตามแหล่งข้อมูลสากล เช่น Yahoo Finance:

- หุ้นไทยมักลงท้าย `.BK`
- หุ้นสหรัฐใช้ ticker ตรง ๆ เช่น `AAPL`
- ETF/ดัชนีอาจใช้สัญลักษณ์ตามแหล่งข้อมูล เช่น `SPY`, `QQQ`, `^GSPC`

## GitHub

โฟลเดอร์นี้ถูกตั้งเป็น Git repo แล้ว แต่ยังไม่มี remote GitHub

เมื่อสร้าง repo บน GitHub แล้วให้รัน:

```powershell
git remote add origin https://github.com/<user>/<repo>.git
git branch -M main
git push -u origin main
```

หลังจากมี remote แล้ว automation จะพยายาม commit และ push รายงานใหม่ให้ทุกครั้ง
