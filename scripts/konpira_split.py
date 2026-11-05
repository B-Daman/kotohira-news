# -*- coding: utf-8 -*-
"""register-items.json を「新規登録分(final)」と「既存ページに値を足す分(patch)」に分ける。

既存ページの page_id はイベントDBを読み取りで引いて、日付＋タイトルの一致で解決する。
Notion への書き込みはしない。
"""
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "docs", "data")
SKILL_DIR = os.path.join(os.path.expanduser("~"), ".claude", "skills", "kotohira-news-register")

# (items側のイベント名, 日付, 既存ページ側タイトルに含まれる語)
EXISTING = [
    ("元始祭", "2026-01-03", "元始祭"),
    ("とんど焼き神事", "2026-01-18", "とんど焼"),
    ("節分祭", "2026-02-03", "節分祭"),
    ("祈年祭", "2026-02-17", "祈年祭"),
    ("天長祭", "2026-02-23", "天長祭"),
    ("例大祭 宵宮祭", "2026-10-09", "宵宮祭"),
    ("例大祭 例祭(御本宮例祭)", "2026-10-10", "例祭"),
    ("例大祭 御神輿 御本宮発御", "2026-10-10", "御本宮発御"),
    ("例大祭 御神輿 御旅所発御(還御)", "2026-10-11", "御旅所発御"),
]
UMBRELLA = ("令和8年 金刀比羅宮例大祭", "2026-10-09", "令和8年 金刀比羅宮例大祭")


def main():
    sys.path.insert(0, SKILL_DIR)
    import register_news as r

    with open(os.path.join(DATA, "konpira-register-items.json"), encoding="utf-8") as f:
        items = json.load(f)
    by_name = {i["イベント名"]: i for i in items}

    with open(os.path.join(SKILL_DIR, "config-events-konpira.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    client = r.Client(auth=r.load_token(cfg))
    existing = r.fetch_existing(client, r.resolve_database_id(cfg), None, "イベント名", "開催日時（開始）")

    patch, skip_names = [], set()
    for name, date, key in EXISTING + [UMBRELLA]:
        is_umbrella = (name, date, key) == UMBRELLA
        if not is_umbrella:
            if name not in by_name:
                raise SystemExit(f"items に無い: {name}")
            skip_names.add(name)
            featured = bool(by_name[name].get("大規模イベント"))
        else:
            featured = True
        hits = [p for p in existing if p["start_date"] == date and key in p["title"]
                and not p["title"].startswith(("大井八幡", "櫛梨", "春日"))]
        row = {"page_id": "", "title": name if is_umbrella else "", "start": date,
               "add_calendar": ["金刀比羅宮"], "featured": featured}
        if len(hits) == 1:
            row["page_id"] = re.sub(r"[^0-9a-f]", "", hits[0]["page_url"].rsplit("/", 1)[-1])[-32:]
            row["title"] = hits[0]["title"]
        else:
            row["title"] = name
            row["note"] = f"既存ページが{len(hits)}件ヒット: " + " / ".join(h["title"] for h in hits)
        patch.append(row)

    final = [i for i in items if i["イベント名"] not in skip_names]
    with open(os.path.join(DATA, "konpira-register-items.final.json"), "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)
    with open(os.path.join(DATA, "konpira-existing-patch.json"), "w", encoding="utf-8") as f:
        json.dump(patch, f, ensure_ascii=False, indent=2)
    print(f"final={len(final)}件 patch={len(patch)}行 page_id未解決={sum(1 for p in patch if not p['page_id'])}")


if __name__ == "__main__":
    main()
