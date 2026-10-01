# 祥鉞餐飲設備網站

以「把每一寸，做到剛好」為設計主軸的五頁靜態網站。保留既有網址、公司資訊與 Formspree 表單，不需要前端框架或 CDN JavaScript。

## 預覽與檢查

需要 Node.js 22 或更新版本。網站本身沒有 npm 依賴。

```sh
npm run dev
npm run check
```

開啟 `http://localhost:5173/review`，可切換五頁與桌面、390px、320px、768px 尺寸。這個開發伺服器會標記預覽模式，攔截表單送出；預覽也不會在停用 JavaScript 時寄出資料。`scripts/review.html` 只用於審閱，請透過 `/review` 開啟，以確保 iframe 內相對路徑正確。

## 網站內容

- `index.html`：品牌首頁、設備細節探索、服務、精選作品與合作流程。
- `about.html`：公司故事、工藝價值與招募聯繫。
- `services.html`：服務說明、實品細節、流程與 FAQ。
- `portfolio.html`：作品分類、搜尋、分頁、鍵盤可操作的相簿。
- `contact.html`：電話、LINE、地圖與需求表單。
- `data/projects.json`：僅含 Airtable 已發布作品的公開快照。
- `images/projects/`：作品照片 WebP 快照，避免附件網址到期。
- `fonts/`：本機供應 Noto Sans TC Variable，授權見 `OFL.txt`。

相簿支援左右方向鍵、Escape 關閉與焦點返回；手機選單支援焦點循環與 Escape；動畫尊重系統減少動態偏好。頁面保留不執行 JavaScript 時的主要內容和導覽。

## 更新作品：每 4 小時＋手動立即更新

自動化程式已備妥，尚未在 GitHub 啟用。首次設定及手動操作請見 **[Airtable 更新教學](docs/AIRTABLE-UPDATE-GUIDE.md)**。

- 工作流程：`.github/workflows/airtable-sync.yml`，名稱 **Airtable Sync & Publish**。
- 台灣時間每天約 00:17、04:17、08:17、12:17、16:17、20:17 同步；排程可能延遲。
- 手動：GitHub → Actions → Airtable Sync & Publish → Run workflow → main → Run workflow。
- 首次設定：Airtable 唯讀 Token 存為 GitHub Secret `AIRTABLE_TOKEN`；Settings → Pages → Source 改為 **GitHub Actions**，保留原網域。
- 只公開「發布 (Published)」作品。正常新增、修改或部分下架，不需要重新上傳程式碼。
- 首次同步會建立圖片快取；後續只處理新增、變動或損壞照片。快取不存下載網址或憑證。
- 無變動且上次執行成功時不重複部署；同步、檢查或提交失敗時保留正式網站。
- 若刻意下架全部作品，手動執行時勾選允許清空。一般情況不要勾選。

首頁選定案例在部署時同步名稱、封面、說明與相簿，下架後隱藏；主視覺與品牌照片仍人工編排。公開網站由 `scripts/build_site.py` 產生到 `_site/`，不包含工作流程、同步程式、測試、快取或憑證。

若開發者要在本機同步：先 `python3 -m pip install -r scripts/requirements.txt`，在環境變數提供 `AIRTABLE_TOKEN`，再執行 `python3 scripts/sync_projects.py`、`npm run check`、`python3 scripts/build_site.py`。沒有提供 Token 時不會發出 API 請求。

## 正式發布

目前改版在本機的獨立 `design/craft-preview` 分支。GitHub 建立分支回傳 403（Resource not accessible by integration），尚未成功推送或建立 PR。**未核准前，不合併 main、不修改 DNS/CNAME、不觸發正式部署。** GitHub Pages 仍使用原靜態檔案結構。設計已獲確認；實際上傳後需依更新教學將 Pages 發布來源改為 GitHub Actions，沒有引入新主機。

正式 HTML 仍送至原本的 `https://formspree.io/f/mvgwrvwv`，保留電話、LINE、社群與地圖連結。審閱時僅驗證預覽攔截，沒有送出測試信；正式上線前需由管理者確認 Formspree 收件與額度設定。

## 離線交付

交付包根目錄的 `preview.html` 含全部五頁、字型和作品照片，解壓縮後可直接以瀏覽器開啟，不需伺服器。內部導航、搜尋、相簿與尺寸切換可離線使用；Google 位置地圖需要連網。表單永久為預覽模式。可用 `python3 scripts/build_offline.py` 重新產生預覽檔。離線資料功能已在 HTTP 預覽環境驗證；本次雲端瀏覽器禁止 file:// 協定，因此未直接測試本機檔案開啟。`website/` 是可維護的網站程式碼，與離線預覽檔分開。

## 品質紀錄

2026-09-30：完成桌面／手機視覺迭代、99 件案例與 410 張照片檢查。`npm run check` 驗證 5 頁、98 個本機引用、主要標題、結構資料、案例唯一性與公開憑證缺漏。瀏覽器已驗證分類／搜尋、無結果狀態、9 頁分頁、相簿換圖／Escape／焦點返回與預覽表單。320px、390px、768px 與桌面排版另有瀏覽器檢查紀錄。

視覺以國際網站獎項作品為目標；自我檢查不是評審認證，也不保證獲獎。若要正式參賽，建議再規劃專業工藝攝影與完整案例故事，強化品牌獨特性。

## 審閱修訂（2026-09-30）

依公司確認，頁首顯示全名「祥鉞餐飲設備股份有限公司」；首頁右側設備更正為電磁爐台。頁尾公司中文全名增加 10pt，其餘文字增加 5pt，聯絡欄新增可撥號電話；作品副標題增加 2pt。服務頁移除配置示意圖及切換控制。聯絡頁改為 Google 嵌入式位置地圖（不需額外 API 金鑰），地圖需連網。全站文案以不鏽鋼製品、客製製作與可靠支援為主，不再宣稱全面後場廚房規劃能力；CTA 改為「你的不鏽鋼需求，我們全力支持」。

頁尾排版追加修訂：電話與傳真移至中欄同排，統一編號獨立下一排。右欄社群固定兩排（LINE／Facebook、Instagram／Threads），移除 CTA 下方的電話按鈕。

## 同步驗證（2026-09-30）

9 項離線測試通過，涵蓋分頁、草稿排除、簽名網址更新不重複下載、附件重排與替換、快取修復、失敗保留快照、清空保護、首頁資料更新與公開檔案白名單。工作流程的排程、手動入口、分支限制、部署依賴及六個官方 action 的 commit 固定引用已檢查；尚未使用新 Token 或實際部署。
