# -*- coding: utf-8 -*-
"""金刀比羅宮の年間行事JSON → register_news.py 用の items 配列JSON に変換する。

使い方: python scripts/konpira_items.py [出力先]
  入力: docs/data/konpira-events-2026.json
  出力: docs/data/konpira-register-items.json（既定）
Notion には触れない（変換のみ）。
"""
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, "docs", "data", "konpira-events-2026.json")
DST = os.path.join(BASE, "docs", "data", "konpira-register-items.json")

SOURCE_LABEL = "出典: 金刀比羅宮公式サイト（令和8年年間行事）"
TIME_RE = re.compile(r"^(\d{1,2}):(\d{2})$")


def convert(ev):
    title = ev["title"]
    if ev.get("category") == "例大祭":
        title = "例大祭 " + title

    start = ev["date"]
    comment_parts = []
    if ev.get("place"):
        comment_parts.append(f"場所: {ev['place']}")
    t = (ev.get("time") or "").strip()
    if t:
        m = TIME_RE.match(t)
        if m:
            # 時刻付きは日本時間として送る（タイムゾーン無しだとUTC扱いになるため）
            start = f"{ev['date']}T{int(m.group(1)):02d}:{m.group(2)}:00+09:00"
        else:
            comment_parts.append(f"時刻: {t}")  # 「午前中」「深夜」「1:00頃」等は日付のみ＋コメント
    if ev.get("note"):
        comment_parts.append(ev["note"])
    comment_parts.append(SOURCE_LABEL)
    comment = " / ".join(comment_parts)
    if ev.get("check"):
        comment = "【要確認】" + comment

    date_val = {"start": start}
    if ev.get("end"):
        date_val["end"] = ev["end"]

    item = {
        "イベント名": title,
        "開催日時（開始）": date_val["start"],
        "市町村": "琴平町",
        "主催/運営": "金刀比羅宮",
        "ソース": ev.get("source_url", ""),
        "コメント": comment,
    }
    if date_val.get("end"):
        item["開催日時（終了）"] = date_val["end"]
    if ev.get("featured_candidate"):
        item["カレンダー"] = "基本のイベント,金刀比羅宮"
        item["大規模イベント"] = True
    return item


def main():
    dst = sys.argv[1] if len(sys.argv) > 1 else DST
    with open(SRC, "r", encoding="utf-8") as f:
        events = json.load(f)["events"]
    items = [convert(e) for e in events]
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"{len(items)}件 -> {dst}")


if __name__ == "__main__":
    main()
