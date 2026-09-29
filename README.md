# 其他流派抖音直播通知

檢查指定抖音直播間，在記錄狀態由未開播變成直播中時，透過 Discord Webhook 發送 `@everyone` 通知。

## 目前監測名單

| Key | 主播 | 直播間 |
| --- | --- | --- |
| yilan | 95高手｜抖音一岚 | https://live.douyin.com/759430282516 |
| mai | 無名高手｜埋 | https://live.douyin.com/265553120212 |
| chongjiu | 沖就 | https://live.douyin.com/713474936121 |

名單定義於 `monitor.py` 的 `STREAMERS`。

## 查詢與直播判定

- 同時查詢所有主播；通知與狀態更新仍按名單順序處理。
- 每位主播每次查詢限時 15 秒，最多嘗試 3 次，重試前分別等待 2、4 秒。
- 優先使用布林型別的 `is_live`；否則只接受整數 `status`：`2` 為直播中、`4` 為未開播。
- 非字典資料或無法辨識的直播狀態視為查詢失敗；三次皆失敗時保留舊狀態，並在 Actions 日誌記錄警告。

## 開播與通知規則

- 上次狀態為 `false`、本次判定直播中時，發送含 `@everyone`、主播名稱、直播標題與連結的 Discord 通知。
- Webhook 成功後才把狀態設為 `true`；發送失敗則保留原狀態，下輪若仍直播會再嘗試。
- 已記錄為直播中時不重複通知；判定未開播後改回 `false`，等待下一次開播，不發下播通知。
- 查詢拋出例外時保留上次狀態。第一次執行或新增主播預設未開播，因此若當時正在直播會立即通知。
- 去重依據是每次檢查記錄的布林狀態，沒有直播場次 ID；如果兩次檢查之間下播又重開，可能無法辨識為新一場。

Actions 在檢查步驟成功後，將有變更的 `state.json` 提交回執行分支；推送最多嘗試 3 次，遠端狀態衝突時中止。狀態未成功保存可能使後續執行再次通知。

## 錯誤處理

Workflow 的步驟失敗且有設定 Webhook 時，會傳送含 Actions 執行連結的失敗訊息。不過，程式已捕捉的單一主播查詢或通知錯誤只寫入日誌，不一定讓 workflow 失敗；綠色執行結果不代表所有主播都查詢成功。

## 排程與狀態保存

GitHub Actions 的 `.github/workflows/check-live.yml` 設有 `*/5 * * * *` 排程，也接受手動或外部 `workflow_dispatch`。這是每 5 分鐘的觸發設定，實際開始時間仍可能延遲或排隊。

程式庫另附獨立 Worker `other-styles-douyin-live-notify-scheduler`，Cron 同樣為每 5 分鐘，觸發本 repo `main` 分支。若 Cloudflare 與 GitHub 排程皆啟用，可能產生額外檢查。

Workflow 使用 Python 3.12，工作上限為 6 分鐘。套件安裝步驟上限 2 分鐘；`streamget install-node` 最多嘗試 3 次，每次限時 45 秒，重試前分別等待 5、10 秒。同一 concurrency group 不取消正在執行的工作。

## 必要 Secrets

- GitHub Repository Secret：`DISCORD_WEBHOOK_URL`。實際通知頻道由 Webhook 決定；通知嵌入訊息頁尾為「其他流派抖音直播通知」。
- Cloudflare Worker Secret：`GITHUB_TOKEN`。若使用 fine-grained PAT，只需授權本 repository 的 Actions **Read and write**。

## 部署排程器

在 `scheduler/` 目錄執行：

```sh
npx wrangler login
npx wrangler secret put GITHUB_TOKEN
npx wrangler deploy
```

`scheduler/wrangler.jsonc` 的 Cron 為 `*/5 * * * *`。Worker 對網路錯誤或 GitHub 5xx 最多嘗試 2 次，其他 HTTP 錯誤直接失敗。程式庫內的設定不代表 Cloudflare 線上部署已同步；部署狀態需以 Cloudflare 設定與日誌確認。

## 本機執行與新增主播

在 repo 根目錄使用 Python 3.12：

```powershell
python -m pip install --requirement requirements.txt
streamget install-node
$env:DISCORD_WEBHOOK_URL = "你的 Discord Webhook URL"
python monitor.py
```

在 `monitor.py` 的 `STREAMERS` 加入唯一 key、`name` 與 `url` 即可。程式自動把新 key 初始化為 `false`，保存時只保留目前名單中的 key，不必手動修改 `state.json`。
