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

## 更新作品

此版本不再讓瀏覽器直接持有 Airtable 存取權，**Airtable 編輯不會自動即時出現在網站上**。使用公開快照發布，更新方式如下：

1. 撤銷原本出現在公開來源中的 Airtable token，建立僅能讀取所需資料表的新 token。
2. 安裝 Python 3.10+ 與 Pillow，將新 token 放在終端環境變數 `AIRTABLE_TOKEN`，不要寫入 HTML、JS、Git 或本文件。
3. 執行 `python3 scripts/sync_projects.py`，再執行 `npm run check`。
4. 在審閱分支確認新增、下架、圖片與首頁精選作品，再透過 PR 核准發布。

匯出器支援 Airtable offset 分頁，完整下載完成後才替換 JSON；錯誤時保留既有資料。只匯出公開必要欄位。首頁照片和標題是人工編排，若精選案件變動，需一併更新首頁，不會由匯出器自動改動。

## 正式發布

目前改版在本機的獨立 `design/craft-preview` 分支。GitHub 建立分支回傳 403（Resource not accessible by integration），尚未成功推送或建立 PR。**未核准前，不合併 main、不修改 DNS/CNAME、不觸發正式部署。** GitHub Pages 仍使用原靜態檔案結構。核准合併後再依既有 Pages 設定發布，沒有引入新主機。

正式 HTML 仍送至原本的 `https://formspree.io/f/mvgwrvwv`，保留電話、LINE、社群與地圖連結。審閱時僅驗證預覽攔截，沒有送出測試信；正式上線前需由管理者確認 Formspree 收件與額度設定。

## 離線交付

交付包根目錄的 `preview.html` 含全部五頁、字型和作品照片，解壓縮後可直接以瀏覽器開啟，不需伺服器。內部導航、搜尋、相簿與尺寸切換可離線使用；Google 位置地圖需要連網。表單永久為預覽模式。可用 `python3 scripts/build_offline.py` 重新產生預覽檔。離線資料功能已在 HTTP 預覽環境驗證；本次雲端瀏覽器禁止 file:// 協定，因此未直接測試本機檔案開啟。`website/` 是可維護的網站程式碼，與離線預覽檔分開。

## 品質紀錄

2026-09-30：完成桌面／手機視覺迭代、99 件案例與 410 張照片檢查。`npm run check` 驗證 5 頁、98 個本機引用、主要標題、結構資料、案例唯一性與公開憑證缺漏。瀏覽器已驗證分類／搜尋、無結果狀態、9 頁分頁、相簿換圖／Escape／焦點返回與預覽表單。320px、390px、768px 與桌面排版另有瀏覽器檢查紀錄。

視覺以國際網站獎項作品為目標；自我檢查不是評審認證，也不保證獲獎。若要正式參賽，建議再規劃專業工藝攝影與完整案例故事，強化品牌獨特性。

## 審閱修訂（2026-09-30）

依公司確認，頁首顯示全名「祥鉞餐飲設備股份有限公司」；首頁右側設備更正為電磁爐台。頁尾公司中文全名增加 10pt，其餘文字增加 5pt，聯絡欄新增可撥號電話；作品副標題增加 2pt。服務頁移除配置示意圖及切換控制。聯絡頁改為 Google 嵌入式位置地圖（不需額外 API 金鑰），地圖需連網。全站文案以不鏽鋼製品、客製製作與可靠支援為主，不再宣稱全面後場廚房規劃能力；CTA 改為「你的不鏽鋼需求，我們全力支持」。

頁尾排版追加修訂：電話與傳真移至中欄同排，統一編號獨立下一排。右欄社群固定兩排（LINE／Facebook、Instagram／Threads），移除 CTA 下方的電話按鈕。
