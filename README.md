# 寵物美容店家 GitHub Pages

使用 `google-2025-12-28.csv` 與 `寵物美容detail.csv` 產生靜態網站，為每間寵物美容店建立獨立介紹頁面，可直接部署到 GitHub Pages（`docs/` 目錄）。

## 如何重新產生網站
1. 確保使用 Python 3，無需額外套件。
2. 執行：
   ```bash
   python generate_sites.py
   ```
   會在 `docs/` 產出首頁（含搜尋/篩選）與 `docs/stores/<slug>/index.html` 的店家頁面，以及共用樣式與腳本。
3. 將 `docs/` 推送到啟用 GitHub Pages 的分支即可公開瀏覽。

## 資料來源
- `google-2025-12-28.csv`：店名、評分、地址、營業資訊、網站等。
- `寵物美容detail.csv`：店家地圖連結對應的封面圖片網址。

目前資料共 9 間店家，生成腳本會自動跳過空白列並確保網址 slug 唯一。
