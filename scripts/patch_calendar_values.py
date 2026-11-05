# -*- coding: utf-8 -*-
"""既存ページの「カレンダー」に値を足す（和集合）。featured が true の行は「大規模イベント」を true にする。

使い方:
  python scripts/patch_calendar_values.py [patch.json]            # 既定 --dry-run（読み取りのみ）
  python scripts/patch_calendar_values.py [patch.json] --apply    # 実際に更新

- 既にあるカレンダー値は消さない（基本のイベント等は残る）。featured が false のときは大規模イベントに触らない。
- 書き込みトークンは backfill_calendar.py と同じ方式（register_news.load_token）。値は出力しない。
- 書き込みは毎秒3件以内。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
import backfill_calendar as bc  # load_write_token / 定数を再利用（DRY）

DEFAULT_PATCH = os.path.join(os.path.dirname(SCRIPT_DIR), "docs", "data", "konpira-existing-patch.json")
CAL = "カレンダー"
BIG = "大規模イベント"


def api(token: str, method: str, page_id: str, body: dict | None = None) -> dict:
    req = urllib.request.Request(
        f"https://api.notion.com/v1/pages/{page_id}",
        data=json.dumps(body).encode("utf-8") if body is not None else None,
        method=method,
    )
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Notion-Version", bc.WRITE_NOTION_VERSION)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.loads(res.read().decode("utf-8"))


def main() -> None:
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="現在値→更新後を表示（既定・書かない）")
    mode.add_argument("--apply", action="store_true", help="実際に更新する")
    ap.add_argument("patch", nargs="?", default=DEFAULT_PATCH)
    args = ap.parse_args()

    with open(args.patch, encoding="utf-8") as f:
        rows = json.load(f)
    token = bc.load_write_token()

    last = 0.0
    done = failed = 0
    for row in rows:
        label = f"{row.get('start')} {row.get('title')}"
        pid = row.get("page_id")
        if not pid:
            print(f"[SKIP] {label}: page_id が空 ({row.get('note', '')})")
            continue
        try:
            props = api(token, "GET", pid)["properties"]
            cur = [o["name"] for o in props.get(CAL, {}).get("multi_select", [])]
            cur_big = bool(props.get(BIG, {}).get("checkbox", False))
            new = cur + [v for v in row.get("add_calendar", []) if v not in cur]
            set_big = bool(row.get("featured"))
            new_big = True if set_big else cur_big
            print(f"{label}\n    カレンダー: {cur} -> {new}\n    大規模イベント: {cur_big} -> {new_big}"
                  + ("" if (new != cur or new_big != cur_big) else "  (変更なし)"))
            if args.apply and (new != cur or new_big != cur_big):
                body = {"properties": {CAL: {"multi_select": [{"name": n} for n in new]}}}
                if set_big and not cur_big:
                    body["properties"][BIG] = {"checkbox": True}
                wait = bc.MIN_INTERVAL - (time.monotonic() - last)
                if wait > 0:
                    time.sleep(wait)
                api(token, "PATCH", pid, body)
                last = time.monotonic()
                done += 1
        except urllib.error.HTTPError as e:
            failed += 1
            print(f"[ERROR] {label}: HTTP {e.code}")
    print(f"\n{'APPLY' if args.apply else 'DRY-RUN'}: 更新{done}件 失敗{failed}件")


if __name__ == "__main__":
    main()
