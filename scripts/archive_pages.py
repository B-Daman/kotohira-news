#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重複したイベントページを Notion のゴミ箱へ移す（archived=true。Notion 側で30日以内なら復元できる）。

入力: docs/data/dedup-cleanup-YYYY-MM-DD.json の archive[]（page_id・title・start・keep_instead）
既定は --dry-run（何も書かない）。--apply で1件ずつ PATCH /v1/pages/{id} {"archived": true}。
書き込みトークンは backfill_calendar.py と同じ探し方。トークンの値は出力しない。
本人の明示の承認が出てから --apply する（削除に相当する操作のため）。
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
import backfill_calendar as bc  # noqa: E402


def archive_page(token: str, page_id: str) -> None:
    req = urllib.request.Request(
        f"https://api.notion.com/v1/pages/{page_id}",
        data=json.dumps({"archived": True}).encode("utf-8"),
        method="PATCH",
    )
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Notion-Version", bc.WRITE_NOTION_VERSION)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as res:
        res.read()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("spec", help="dedup-cleanup JSON（archive[] を持つ）")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="一覧を表示するだけ（既定）")
    mode.add_argument("--apply", action="store_true", help="実際にゴミ箱へ移す")
    args = ap.parse_args()

    with open(args.spec, "r", encoding="utf-8") as f:
        spec = json.load(f)
    rows = spec.get("archive") or []
    print(f"対象: {len(rows)}件")
    for r in rows:
        print(f"  {r.get('start','')}  {r.get('title','')}  （残す: {r.get('keep_title') or r.get('keep_instead','')[:8]}）")
    if not args.apply:
        print("-- dry-run（何も書き込みません）")
        return
    token = bc.load_write_token()
    ok = ng = 0
    for r in rows:
        try:
            archive_page(token, r["page_id"])
            ok += 1
        except urllib.error.HTTPError as e:
            ng += 1
            print(f"失敗: {r['page_id']} HTTP {e.code} {r.get('title','')}")
        time.sleep(bc.MIN_INTERVAL)
    print(f"完了: ゴミ箱へ {ok}件 / 失敗 {ng}件")


if __name__ == "__main__":
    main()
