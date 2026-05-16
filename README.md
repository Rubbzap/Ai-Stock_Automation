# Daily Stock Brief

โปรเจกต์นี้เก็บรายงานข่าวหุ้นแบบสั้นรายวันเป็นไฟล์ Markdown ใน `reports/`

[![Visualize in Looker Studio](https://img.shields.io/badge/Visualize-Looker%20Studio-4285F4?logo=looker&logoColor=white)](https://lookerstudio.google.com/reporting/create?r.reportName=Daily%20Stock%20Brief%20Dashboard)
[![Open CSV](https://img.shields.io/badge/Data-reports.csv-34A853?logo=googlesheets&logoColor=white)](https://raw.githubusercontent.com/Rubbzap/Automations1/main/data/reports.csv)

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

- กดปุ่ม **Visualize - Looker Studio** ด้านบนเพื่อเปิดหน้า create report ของ Looker Studio พร้อมชื่อ dashboard
- ใช้ CSV URL นี้เป็นแหล่งข้อมูล: `https://raw.githubusercontent.com/Rubbzap/Automations1/main/data/reports.csv`
- ถ้าใช้ Looker Studio โดยตรง แนะนำนำ CSV เข้า Google Sheets ก่อนด้วยสูตร `=IMPORTDATA("https://raw.githubusercontent.com/Rubbzap/Automations1/main/data/reports.csv")` แล้วต่อ Looker Studio กับ Google Sheets นั้น

ดูขั้นตอนสั้น ๆ ได้ที่ `docs/looker-studio.md`

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
