#!/usr/bin/env python3
"""拉取梅李飞书私聊里最近发的作业/试卷照片到 ~/math-plan/inbox/。

用法：python3 fetch_photos.py [--hours 24]
只取她本人发的 image 消息和图片/PDF 文件消息；重复运行按 message_id 去重（已存在的文件跳过）。
"""
import argparse
import json
import os
import pathlib
import time
import urllib.request

APP_ID = "cli_a927d084e0f8dbcc"
CHAT_ID = "oc_1c0caf8af68c56d6c7eab58fa87816d1"  # 梅李 ↔ 机器人私聊
LIMEI_OPEN_ID = "ou_03512becb5ed9156090a1f2662097bd1"
INBOX = pathlib.Path.home() / "math-plan" / "inbox"
FILE_EXTS = (".jpg", ".jpeg", ".png", ".heic", ".webp", ".pdf")


def api(url, data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data else None, headers=headers)
    return urllib.request.urlopen(req)


def tenant_token():
    resp = api("https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
               {"app_id": APP_ID, "app_secret": os.environ["FEISHU_APP_SECRET"]})
    return json.load(resp)["tenant_access_token"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=24)
    args = ap.parse_args()

    tok = tenant_token()
    start = str(int(time.time() - args.hours * 3600))
    INBOX.mkdir(parents=True, exist_ok=True)

    saved, page_token = [], ""
    while True:
        url = ("https://open.feishu.cn/open-apis/im/v1/messages"
               f"?container_id_type=chat&container_id={CHAT_ID}"
               f"&start_time={start}&sort_type=ByCreateTimeAsc&page_size=50"
               + (f"&page_token={page_token}" if page_token else ""))
        data = json.load(api(url, token=tok))["data"]
        for m in data.get("items") or []:
            if m["sender"].get("sender_type") != "user" or m["sender"].get("id") != LIMEI_OPEN_ID:
                continue
            body = json.loads(m["body"]["content"])
            if m["msg_type"] == "image":
                key, rtype, ext = body["image_key"], "image", ".jpg"
            elif m["msg_type"] == "file" and body.get("file_name", "").lower().endswith(FILE_EXTS):
                key, rtype = body["file_key"], "file"
                ext = pathlib.Path(body["file_name"]).suffix.lower()
            else:
                continue
            ts = time.strftime("%Y%m%d-%H%M%S", time.localtime(int(m["create_time"]) / 1000))
            out = INBOX / f"{ts}-{m['message_id'][-6:]}{ext}"
            if out.exists():
                continue
            blob = api(f"https://open.feishu.cn/open-apis/im/v1/messages/{m['message_id']}"
                       f"/resources/{key}?type={rtype}", token=tok).read()
            out.write_bytes(blob)
            saved.append((str(out), len(blob)))
        if not data.get("has_more"):
            break
        page_token = data.get("page_token", "")

    for path, size in saved:
        print(f"{path}\t{size / 1024:.0f}KB")
    if not saved:
        print(f"(近 {args.hours:g} 小时无新图片)")


if __name__ == "__main__":
    main()
