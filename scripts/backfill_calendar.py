#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""イベントDBの「カレンダー」(multi-select) が空の件に「基本のイベント」を一括付与する（一度きりの道具）。

- 読み: fetch_notion.py の関数（読み取りトークン・data_sources API）で全件取得
- 書き: 登録スキルと同じ探し方の書き込みトークンで PATCH /v1/pages/{id}
  送るのは「カレンダー」プロパティだけ。他のプロパティ・削除は一切しない
- 既定は --dry-run（何も書かない）。--apply で毎秒3件以内で更新
- トークンの値は出力しない

使い方:
    python -X utf8 scripts/backfill_calendar.py --dry-run
    python -X utf8 scripts/backfill_calendar.py --apply
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
SKILL_DIR = os.path.join(
    os.path.expanduser("~"), ".claude", "skills", "kotohira-news-register"
)
CONFIG_PATH = os.path.join(SKILL_DIR, "config-events.json")

PROP_NAME = "カレンダー"
VALUE = "基本のイベント"
MAX_EVENTS = 5000
MIN_INTERVAL = 0.4  # 秒。毎秒3件以内（0.4秒間隔＝2.5件/秒）
WRITE_NOTION_VERSION = "2022-06-28"


def load_write_token() -> str:
    """書き込みトークンを register_news.load_token と同じ順で探す。

    fetch_notion を import すると kotohira-news の .env が環境変数に取り込まれ、
    読み取り専用トークンが書き込み側の探索に混ざりうるため、必ず先に解決する。
    """
    sys.path.insert(0, SKILL_DIR)
    import register_news  # noqa: E402

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    return register_news.load_token(cfg)


def collect_targets(read_token: str, fn) -> tuple[int, list[dict]]:
    """イベントDB全件を取り、「カレンダー」が空の件を返す。(全件数, 対象リスト)"""
    dsid = fn.get_data_source_id(fn.EVENT_DB_ID, read_token)
    sorts = [{"property": "開催日時（開始）", "direction": "descending"}]
    pages = fn.query_data_source(dsid, read_token, sorts, MAX_EVENTS)
    targets = []
    for p in pages:
        props = p.get("properties", {})
        if fn.get_multi_select(props, PROP_NAME):
            continue
        targets.append(
            {
                "id": p.get("id", ""),
                "title": fn.get_title(props, "イベント名"),
                "start": fn.get_date_start(props, "開催日時（開始）"),
            }
        )
    return len(pages), targets


def patch_calendar(write_token: str, page_id: str) -> None:
    body = {"properties": {PROP_NAME: {"multi_select": [{"name": VALUE}]}}}
    req = urllib.request.Request(
        f"https://api.notion.com/v1/pages/{page_id}",
        data=json.dumps(body).encode("utf-8"),
        method="PATCH",
    )
    req.add_header("Authorization", f"Bearer {write_token}")
    req.add_header("Notion-Version", WRITE_NOTION_VERSION)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as res:
        res.read()


def main() -> None:
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="件数と先頭10件を表示（既定・何も書かない）")
    mode.add_argument("--apply", action="store_true", help="実際に更新する")
    args = ap.parse_args()
    apply = args.apply

    # 書き込みトークンを先に解決（fetch_notion の .env 取り込みより前）
    try:
        write_token = load_write_token()
        print("トークン: あり")
    except SystemExit as e:
        print(f"トークン: なし（{e}）")
        write_token = None
    except Exception as e:
        print(f"トークン: 取得エラー（{type(e).__name__}）")
        write_token = None

    sys.path.insert(0, SCRIPT_DIR)
    import fetch_notion as fn  # noqa: E402

    read_token = fn.get_token()
    if not read_token:
        print("読み取りトークンが未設定です。")
        sys.exit(1)

    total, targets = collect_targets(read_token, fn)
    print(f"イベントDB全件: {total}件 / 「{PROP_NAME}」が空の対象: {len(targets)}件")

    if not apply:
        print("-- dry-run（何も書き込みません）。先頭10件 --")
        for t in targets[:10]:
            print(f"  {t['start'] or '(日付なし)'}  {t['title']}")
        return

    if not write_token:
        print("書き込みトークンが無いため中止します。")
        sys.exit(1)

    ok = 0
    ng = 0
    last = 0.0
    for t in targets:
        wait = MIN_INTERVAL - (time.monotonic() - last)
        if wait > 0:
            time.sleep(wait)
        last = time.monotonic()
        try:
            patch_calendar(write_token, t["id"])
            ok += 1
        except urllib.error.HTTPError as e:
            ng += 1
            print(f"失敗: {t['id']} HTTP {e.code} {t['title']}")
        except Exception as e:
            ng += 1
            print(f"失敗: {t['id']} {type(e).__name__} {t['title']}")
    print(f"完了: 成功 {ok}件 / 失敗 {ng}件")


if __name__ == "__main__":
    main()
