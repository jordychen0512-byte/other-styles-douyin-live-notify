import asyncio
import json
import os
from pathlib import Path

import requests
from streamget import DouyinLiveStream


STREAMERS = {
    "yilan": {
        "name": "95高手｜抖音一岚",
        "url": "https://live.douyin.com/759430282516",
    },
    "mai": {
        "name": "無名高手｜埋",
        "url": "https://live.douyin.com/265553120212",
    },
    "chongjiu": {
        "name": "沖就",
        "url": "https://live.douyin.com/713474936121",
    },
}

STATE_FILE = Path("state.json")
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")


def load_state():
    """讀取上次直播狀態；新加入的直播主預設為未開播。"""
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            return {
                streamer_id: bool(state.get(streamer_id, False))
                for streamer_id in STREAMERS
            }
        except (OSError, json.JSONDecodeError):
            pass

    return {streamer_id: False for streamer_id in STREAMERS}


def save_state(state):
    """儲存狀態，避免同一場直播重複通知。"""
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


async def check_stream(streamer):
    for attempt in range(1, 4):
        try:
            live = DouyinLiveStream()
            data = await asyncio.wait_for(
                live.fetch_web_stream_data(streamer["url"]), timeout=15
            )
            if not isinstance(data, dict):
                raise ValueError("抖音未回傳有效資料")
            if isinstance(data.get("is_live"), bool):
                is_live = data["is_live"]
            elif type(data.get("status")) is int and data["status"] in (2, 4):
                is_live = data["status"] == 2
            else:
                raise ValueError("抖音未回傳可辨識的直播狀態")
            return {
                "is_live": is_live,
                "title": data.get("title") or "抖音直播",
                "anchor_name": data.get("anchor_name") or streamer["name"],
            }
        except Exception as error:
            if attempt == 3:
                raise
            print(f"{streamer['name']} 查詢暫時失敗（{attempt}/3）：{type(error).__name__}，稍後重試")
            await asyncio.sleep(2 * attempt)


def send_discord_notification(streamer, info):
    if not WEBHOOK_URL:
        print("未設定 DISCORD_WEBHOOK_URL")
        return False

    payload = {
        "content": f"@everyone\n\n🔴 **{streamer['name']} 開播了！**",
        "embeds": [
            {
                "title": info["title"],
                "url": streamer["url"],
                "description": "點擊標題前往抖音直播間。",
                "color": 15158332,
                "footer": {"text": "其他流派抖音直播通知"},
            }
        ],
        "allowed_mentions": {"parse": ["everyone"]},
    }

    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=15)
        response.raise_for_status()
        print(f"已通知 Discord：{streamer['name']}")
        return True
    except requests.RequestException as error:
        print(f"Discord 通知失敗：{error}")
        return False


async def main():
    state = load_state()
    # Only read-only queries run concurrently; notifications and state updates stay ordered.
    results = await asyncio.gather(
        *(check_stream(streamer) for streamer in STREAMERS.values()),
        return_exceptions=True,
    )

    for (streamer_id, streamer), info in zip(STREAMERS.items(), results):
        previous_live = state.get(streamer_id, False)

        if isinstance(info, Exception):
            # 檢查失敗時保留上次狀態，避免暫時性錯誤造成重複通知。
            print(f"::warning::{streamer['name']} 重試 3 次仍檢查失敗，保留上次狀態：{type(info).__name__}")
            continue

        current_live = info["is_live"]
        print(f"{streamer['name']}：{'直播中' if current_live else '未開播'}")

        if current_live and not previous_live:
            if send_discord_notification(streamer, info):
                state[streamer_id] = True
        elif not current_live and previous_live:
            state[streamer_id] = False

    save_state(state)


if __name__ == "__main__":
    asyncio.run(main())
