# Airtable 作品同步與手動更新教學

這個版本讓你繼續在 Airtable 維護作品，由 GitHub 自動取得已發布內容、壓縮照片、檢查網站並發布。流程名稱是 **Airtable Sync & Publish**。

程式已包含排程及手動按鈕，但**下載檔案不代表功能已啟用**。必須將新版程式碼與 `.github/workflows/airtable-sync.yml` 上傳到儲存庫的 `main`，完成下列首次設定。這份交付沒有替你更動 GitHub 設定、建立憑證或發布正式網站。

## 第一次設定：只需做一次

### 1. 建立 Airtable 唯讀 Token

1. 登入 Airtable，開啟 [Developer hub](https://airtable.com/create/tokens)。
2. 選擇 **Personal access tokens → Create token**。
3. 名稱可填 `Shyuan website sync`。
4. 在 **Scopes** 只加入 `data.records:read`。
5. 在 **Access / Resources** 只加入存放公司作品的 Base，不要選擇所有資料庫。
6. 建立 Token 後複製，直接貼到下一步的 GitHub Secret。不要貼進網頁、程式碼或聊天訊息。

原版 HTML 曾公開的 Token 請撤銷；若原版仍使用該 Token，撤銷會讓原版作品讀取失效，請配合新版發布安排處理。

### 2. 將 Token 存到 GitHub

1. 開啟 [shyuan1996/mywebsite](https://github.com/shyuan1996/mywebsite)。
2. 點 **Settings → Secrets and variables → Actions**。
3. 在 **Secrets** 分頁點 **New repository secret**。
4. **Name** 填 `AIRTABLE_TOKEN`（大小寫須相同）。
5. **Secret** 貼上剛建立的 Airtable Token，點 **Add secret**。

不用再建立 GitHub 個人 Token；工作流程使用 GitHub 內建的儲存庫 Token。

### 3. 切換網站發布來源

1. 點 **Settings → Pages**。
2. 在 **Build and deployment → Source** 選擇 **GitHub Actions**。
3. 保留原本的 **Custom domain：`www.shyuan.com.tw`** 及既有 HTTPS 設定，不要修改 DNS。

這一步必要：只靠機器人提交資料，不會自動觸發原本的「Deploy from a branch」發布；本版本會在同一個工作流程中直接部署 Pages。

### 4. 上傳最新版程式碼

將交付包中 `website/` 的內容放到儲存庫根目錄，`index.html` 與 `.github` 應在同一層。請包含 `.github/`、`scripts/`、`tests/`、`data/`、`images/`、`fonts/`、`js/` 等完整目錄。不要多包一層 `website/`，也不必上傳外層 `preview.html` 或 ZIP。

建議用 GitHub Desktop：先取得儲存庫、複製新版檔案、Commit，再 Push。若 GitHub Actions 頁面出現 **I understand my workflows, go ahead and enable them**，點選啟用。此工作流程只允許 `main` 發布。

如果你已經上傳前一版，請再覆蓋這次的完整版本；前一版尚未包含自動同步功能。

## 平常怎麼手動立即更新

1. 在 Airtable 編輯作品，確認照片已上傳完成。
2. 需要公開的作品，將 **狀態 (Status)** 設為 **發布 (Published)**。
3. 回到 GitHub 的 `shyuan1996/mywebsite`，點上方 **Actions**。
4. 點左側 **Airtable Sync & Publish**。
5. 點右上方 **Run workflow**。
6. **Branch** 選 `main`。一般更新不要勾選「允許清空全部作品」。
7. 再點一次綠色 **Run workflow**。
8. 等該次執行出現綠色勾選 **✓**，再開啟公司網站檢查作品。

第一次需要建立全部圖片快取，可能比後續更新慢。之後只有新增、變動或需要修復的照片會重新下載。每次手動更新都會重新部署，即使作品沒有變更。

一般新增、改名、改介紹、更換照片，或下架部分作品，都照上述步驟即可，不需要重新上傳程式碼。

若要下架**所有**作品，先在 Airtable 取消所有作品的發布狀態，再手動執行並勾選「允許清空全部作品」。自動排程遇到零件作品會保留既有快照並報錯，避免錯誤設定造成全部作品消失。

## 自動更新時間

每天台灣時間約 **00:17、04:17、08:17、12:17、16:17、20:17** 檢查一次。GitHub 排程可能延遲，這不是保證準點的即時服務。

作品沒有變動且上次執行成功時，不重複提交或部署；上次執行失敗時，下一輪會再次嘗試。你也可以立即按 **Run workflow** 重試。

GitHub 公開儲存庫若連續 60 天沒有活動，排程可能被自動停用。遇到停用提示，進入同一個 Actions 工作流程頁面點 **Enable workflow**，再按一次 **Run workflow**。正常更新作品會產生新提交；長期完全沒有更新時，請留意此提示。

## 哪些 Airtable 欄位會同步

| 欄位 | 用途 |
|---|---|
| 專案名稱 (ProjectName) | 作品名稱 |
| 專案簡介 (Description) | 圖片下方的客戶／地區說明 |
| 分類 (Category) | 作品篩選分類 |
| 專案主圖 (MainImage) | 多張相簿照片 |
| 狀態 (Status) | 僅「發布 (Published)」會公開 |

不要任意改動上述欄位名稱；若變更了名稱，需同步修改匯出器。已發布作品若沒有名稱或照片，會略過，數量會顯示在 Actions 摘要。

首頁已選定的案例會在發布時跟隨 Airtable 更新名稱、客戶說明、封面及相簿；下架的案例會從首頁精選卡片移除，重新發布後會回到原選定位置。**首頁主視覺及品牌照片仍是人工編排**，不會因為相簿照片順序改動而自動更換。若要更換首頁精選的三個案例，需要修改 `index.html` 中的選定案例 ID。

## 更新失敗時怎麼看

點進紅色 **✕** 的執行紀錄，再點 **build**，展開第一個紅色步驟查看原因。失敗時不會部署半套網站，正式網站保留上次成功版本。

| 狀況 | 處理方式 |
|---|---|
| `Missing AIRTABLE_TOKEN` | 檢查 GitHub Secret 名稱是否正確、是否填入內容 |
| `HTTP 401 / 403` | 檢查 Token、`data.records:read` 權限及 Base 資源範圍 |
| `HTTP 404 / 422` | 檢查 Base、資料表及欄位名稱 |
| 零件已發布作品 | 確認至少有一件完整作品已發布；若刻意全部下架，勾選允許清空 |
| `git push` 被拒絕 | 先檢查 Settings → Actions → General → Workflow permissions；必要時由管理者選 Read and write permissions。若仍被拒絕，再檢查 Rulesets／main 分支保護是否允許同步流程寫入資料快照 |
| `main 已有更新` | 執行期間有人修改程式碼；再按一次 Run workflow |
| Pages 設定錯誤 | 確認 Settings → Pages → Source 已選 GitHub Actions |
| 出現 Waiting / Review deployments | `github-pages` 環境設定了人工審核；依公司設定完成審核。若需要無人值守，管理者須調整該環境設定 |
| 綠色勾選但瀏覽器仍是舊畫面 | 等待 Pages 生效後按 Ctrl+F5；確認作品狀態、名稱及照片都完整 |
| 沒看到 Run workflow 按鈕 | 確認 workflow 已在 `main`，且使用有寫入權限的 GitHub 帳號 |

原本的 Base 與資料表已設為預設值。只有移動 Base 或改資料表名稱時，才需在 **Settings → Secrets and variables → Actions → Variables** 新增 `AIRTABLE_BASE_ID` 或 `AIRTABLE_TABLE`。

## 本次驗證範圍

已以離線測試驗證分頁、草稿排除、圖片快取、替換與重排、下載失敗保留舊資料、零作品保護、首頁案例更新及公開部署檔案不含憑證。尚未使用你新建立的 Token，也未在你的 GitHub 執行線上部署；首次啟用後請查看完整執行紀錄與網站。

官方說明：[手動執行工作流程](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow)、[GitHub Secrets](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets)、[Pages 自訂工作流程](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)、[Airtable Token](https://support.airtable.com/articles/9934989703-creating-personal-access-tokens)、[GitHub 排程](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)。
