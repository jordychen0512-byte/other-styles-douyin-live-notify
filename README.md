# 其他流派抖音直播通知

每 10 分鐘檢查指定的抖音直播間。只有直播狀態從「未開播」變成「直播中」時，才會在 Discord 的「其他流派抖音直播通知」頻道發送 `@everyone` 通知。

## 目前監測名單

- 95高手｜抖音一岚：https://v.douyin.com/a8aESt_i6HE/
- 無名高手｜埋：https://live.douyin.com/265553120212
- 沖就：https://live.douyin.com/713474936121

## 運作方式

Cloudflare Worker Cron 每 10 分鐘呼叫 GitHub 的 `workflow_dispatch` API。GitHub Actions 執行 `monitor.py`，檢查直播狀態並更新 `state.json`。

## 必要 Secrets

- GitHub Repository Secret：`DISCORD_WEBHOOK_URL`
- Cloudflare Worker Secret：`GITHUB_TOKEN`

`GITHUB_TOKEN` 建議使用只限本 repository 的 fine-grained personal access token，並給予 Actions `Read and write` 權限。

## 部署排程器

在 `scheduler` 目錄執行：

```sh
npx wrangler login
npx wrangler secret put GITHUB_TOKEN
npx wrangler deploy
```

Cron 設定在 `scheduler/wrangler.jsonc`，目前為每 10 分鐘執行一次。

## 新增直播主

在 `monitor.py` 的 `STREAMERS` 加入一筆資料，並在 `state.json` 加入相同 key、值設為 `false`。
