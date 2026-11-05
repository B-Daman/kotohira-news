#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""「カレンダー」に指定の値を持つイベントページの DiscordイベントURL を一括で入れる。

本人案（2026-11-05）: 金刀比羅宮の行事は Discord にイベント用フォーラムを用意し、その URL を
DiscordイベントURL に入れておく（週間スケジュール kotohira_weekly_schedule.py の行がリンクになる）。

- 読み: fetch_notion.py（読み取りトークン・data_sources API）で全件取得
- 書き: patch_calendar_values.api()（登録スキルと同じ書き込みトークン）で PATCH /v1/pages/{id}
  送るのは DiscordイベントURL だけ。他のプロパティ・削除は一切しない
- 既定は --dry-run（何も書かない）。--apply で毎秒3件以内で更新
- DiscordイベントURL が既に入っている件は触らない（--overwrite で上書き）
- トークンの値は出力しない

使い方:
    python -X utf8 scripts/patch_discord_url.py --url https://discord.com/channels/... --dry-run
    python -X utf8 scripts/patch_discord_url.py --url https://discord.com/channels/... --apply
    python -X utf8 scripts/patch_discord_url.py --calendar こんぴらカレンダー --url ... --apply
"""
from __future__ import annotations

import argparse
import os
import sys
import time
import urllib.error

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
import backfill_calendar as bc  # noqa: E402  load_write_token / MIN_INTERVAL
import fetch_notion as fn  # noqa: E402  読み取り（data_sources API）
import patch_calendar_values as pcv  # noqa: E402  api() / CAL

URL_PROP = "DiscordイベントURL"
ALLOWED_PREFIXES = ("https://discord.com/", "https://discordapp.com/")


def collect(read_token: str, calendar: str, overwrite: bool) -> tuple[int, list[dict]]:
    """イベントDB全件から、カレンダーに calendar を持つ件を返す。(該当数, 対象リスト)"""
    dsid = fn.get_data_source_id(fn.EVENT_DB_ID, read_token)
    sorts = [{"property": "開催日時（開始）", "direction": "ascending"}]
    pages = fn.query_data_source(dsid, read_token, sorts, bc.MAX_EVENTS)
    hit = 0
    targets = []
    for p in pages:
        props = p.get("properties", {})
        if calendar not in fn.get_multi_select(props, pcv.CAL):
            continue
        hit += 1
        current = (props.get(URL_PROP) or {}).get("url") or ""
        if current and not overwrite:
            continue
        targets.append(
            {
                "id": p.get("id", ""),
                "title": fn.get_title(props, "イベント名"),
                "start": fn.get_date_start(props, "開催日時（開始）"),
                "current": current,
            }
        )
    return hit, targets


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True, help="入れる Discord の URL（フォーラム・スレッド・イベント）")
    ap.add_argument("--calendar", default="金刀比羅宮", help="対象にするカレンダー値（既定: 金刀比羅宮）")
    ap.add_argument("--overwrite", action="store_true", help="既に URL がある件も上書きする")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="対象を表示するだけ（既定）")
    mode.add_argument("--apply", action="store_true", help="実際に書き込む")
    args = ap.parse_args()

    if not args.url.startswith(ALLOWED_PREFIXES):
        raise SystemExit(f"Discord の URL ではありません: {args.url}")

    read_token = fn.get_token()
    if not read_token:
        raise SystemExit("読み取りトークンが見つかりません（kotohira-news の .env）")
    hit, targets = collect(read_token, args.calendar, args.overwrite)
    print(f"カレンダー「{args.calendar}」: {hit}件 / うち対象 {len(targets)}件"
          + ("" if args.overwrite else "（URL 済みは除く）"))
    for t in targets:
        mark = f"  ← 上書き: {t['current']}" if t["current"] else ""
        print(f"  {t['start'] or '----------'}  {t['title']}{mark}")
    if not args.apply:
        print("-- dry-run（何も書き込みません）")
        return

    token = bc.load_write_token()
    ok = ng = 0
    last = 0.0
    for t in targets:
        wait = bc.MIN_INTERVAL - (time.monotonic() - last)
        if wait > 0:
            time.sleep(wait)
        try:
            pcv.api(token, "PATCH", t["id"], {"properties": {URL_PROP: {"url": args.url}}})
            ok += 1
        except urllib.error.HTTPError as e:
            ng += 1
            print(f"失敗: {t['id']} HTTP {e.code} {t['title']}")
        last = time.monotonic()
    print(f"完了: 更新 {ok}件 / 失敗 {ng}件")


if __name__ == "__main__":
    main()
