#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""イベントDBの重複監査（同日・類似の組を列挙する）。

規則の正本は docs/重複防止_設計.md の2章。登録スキル（register_news.py）と
konpie-bot（notion_register.py）の判定と同じ規則・同じ閾値で、実装は言語とリポジトリが
違うため複製している。規則を変えるときは3か所と設計書の表をそろえて直すこと。

- 読み取りだけ。Notion へ書き込まない。消さない（消すのは常に人）。
- 入力: イベントDB全件（scripts/fetch_notion.py の関数とトークンを再利用）
        docs/data/duplicate-allowlist.json  {"pairs": [[id1, id2], ...]}（無ければ空。
        「これは別の行事」と人が決めた組。手で追記する）
- 出力: docs/data/duplicate-candidates.json（生成物）
        docs/data/duplicate-candidates.md（開発ダッシュボード「現在地」に取り込む表）
- 終了コード: 常に 0（監査は助言。ワークフローを止めない）。標準出力に1行要約。

使い方:
    python scripts/audit_duplicates.py          # 開始日が今日の60日前以降のイベントだけ
    python scripts/audit_duplicates.py --all    # 全期間
環境変数は fetch_notion.py と同じ（KOTOHIRA_DASHBOARD_NOTION_TOKEN など）。
"""

from __future__ import annotations

import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from typing import Any

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(REPO_ROOT, "docs", "data")
ALLOWLIST_PATH = os.path.join(DATA_DIR, "duplicate-allowlist.json")
OUT_JSON = os.path.join(DATA_DIR, "duplicate-candidates.json")
OUT_MD = os.path.join(DATA_DIR, "duplicate-candidates.md")

JST = timezone(timedelta(hours=9))
RECENT_DAYS = 60  # 開始日が今日（JST）のこの日数前以降だけ監査する（--all で全期間）
EVENT_MAX = 5000
PAGE_URL = "https://www.notion.so/{}"

# ---- 判定（register_news.py と同じ規則。設計書2章） ----
_PART_RE = re.compile(r"午前|午後|第[0-9一二三四五六七八九十]+部|朝祭|夕祭|[0-9一二三四五六七八九十]+日目|昼|夜(?!市)")
SAME_DAY_RATIO = 0.80
SAME_DAY_MIN_CONTAIN = 3


def normalize_title(title: Any) -> str:
    """NFKC・小文字・空白と括弧と記号を除去。"""
    if not title:
        return ""
    t = unicodedata.normalize("NFKC", str(title)).lower()
    t = re.sub(r"\s+", "", t)
    t = re.sub(r"[【】\[\]「」『』（）()\"'’“”\-―ー~〜|｜/:：!！?？.,、。・…]", "", t)
    return t


def strip_part_markers(title: Any) -> tuple[str, set[str]]:
    s = unicodedata.normalize("NFKC", str(title or ""))
    markers = set(_PART_RE.findall(s))
    return normalize_title(_PART_RE.sub("", s)), markers


def same_day_score(a: Any, b: Any) -> float:
    """同日類似の一致率（0〜1）。類似でなければ 0.0。"""
    na, nb = normalize_title(a), normalize_title(b)
    if not na or not nb:
        return 0.0
    sa, ma = strip_part_markers(a)
    sb, mb = strip_part_markers(b)
    if sa == sb and ma and mb and ma != mb:
        return 0.0  # 午前/午後・朝祭/夕祭など、同日の別の回
    if na == nb:
        return 1.0
    ratio = SequenceMatcher(None, na, nb).ratio()
    shorter, longer = (na, nb) if len(na) <= len(nb) else (nb, na)
    if shorter in longer and len(shorter) >= SAME_DAY_MIN_CONTAIN:
        return round(max(ratio, len(shorter) / len(longer)), 3)
    if ratio >= SAME_DAY_RATIO:
        return round(ratio, 3)
    return 0.0


def is_same_day_similar(a: Any, b: Any) -> bool:
    return same_day_score(a, b) > 0.0


def dates_overlap(s1: str, e1: str, s2: str, e2: str) -> bool:
    if not s1 or not s2:
        return False
    e1, e2 = e1 or s1, e2 or s2
    return s1 <= e2 and s2 <= e1


# ---- 取得と列挙 ----
def load_allowlist() -> set[frozenset[str]]:
    if not os.path.exists(ALLOWLIST_PATH):
        return set()
    try:
        with open(ALLOWLIST_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {frozenset(p) for p in data.get("pairs", []) if isinstance(p, list) and len(p) == 2}
    except Exception as e:  # noqa: BLE001
        print(f"audit: allowlist を読めないため空として続行します（{e}）", file=sys.stderr)
        return set()


def fetch_event_pages(fn: Any, token: str) -> list[dict[str, Any]]:
    dsid = fn.get_data_source_id(fn.EVENT_DB_ID, token)
    sorts = [{"property": "開催日時（開始）", "direction": "descending"}]
    return fn.query_data_source(dsid, token, sorts, EVENT_MAX)


def to_event(fn: Any, page: dict[str, Any]) -> dict[str, Any]:
    props = page.get("properties", {})
    pid = page.get("id", "")
    return {
        "id": pid,
        "title": fn.get_title(props, "イベント名"),
        "start": fn.get_date_start(props, "開催日時（開始）")[:10],
        "end": fn.get_date_start(props, "開催日時（終了）")[:10],
        "created": (page.get("created_time") or "")[:10],
        "src": fn.get_url(props, "ソース"),
        "url": page.get("url") or PAGE_URL.format(pid.replace("-", "")),
    }


def find_pairs(events: list[dict[str, Any]], allow: set[frozenset[str]],
               since: str = "") -> list[dict[str, Any]]:
    """since（YYYY-MM-DD）が空でなければ、開始日がそれ以降のイベントだけを対象にする。"""
    dated = [e for e in events if e["start"] and e["title"] and e["start"] >= since]
    pairs = []
    for i, a in enumerate(dated):
        for b in dated[i + 1:]:
            if not dates_overlap(a["start"], a["end"], b["start"], b["end"]):
                continue
            if frozenset((a["id"], b["id"])) in allow:
                continue
            score = same_day_score(a["title"], b["title"])
            if not score:
                continue
            first, second = sorted((a, b), key=lambda e: (e["created"], e["id"]))
            pairs.append({"score": score, "pages": [first, second]})
    pairs.sort(key=lambda p: (p["pages"][0]["start"], -p["score"]))
    return pairs


# ---- 出力 ----
def _cell(text: str) -> str:
    return str(text or "").replace("|", "\\|").replace("[", "「").replace("]", "」")


def render_md(pairs: list[dict[str, Any]], total: int) -> str:
    # 日時は書かない（毎日の差分を出さず、内容が変わった日だけコミットされるようにする）
    lines = ["# 重複候補（同日・類似）", ""]
    if not pairs:
        lines.append(f"重複候補はありません（イベントDB {total}件を監査）。")
        return "\n".join(lines) + "\n"
    lines.append(
        f"{len(pairs)}組（イベントDB {total}件を監査）。同じ日に題名が似ている組です。"
        "別の行事なら `docs/data/duplicate-allowlist.json` に id の組を追記すると外れます。"
        "消すかどうかは人が決めます。"
    )
    lines += ["", "| 日付 | 題名A（作成日） | 題名B（作成日） | 一致率 | リンク |", "|---|---|---|---|---|"]
    for p in pairs:
        a, b = p["pages"]
        date = a["start"] if a["start"] == b["start"] else f"{a['start']} / {b['start']}"
        lines.append(
            f"| {date} | {_cell(a['title'])}（{a['created']}） | {_cell(b['title'])}（{b['created']}） "
            f"| {p['score']:.2f} | [A]({a['url']}) [B]({b['url']}) |"
        )
    return "\n".join(lines) + "\n"


def write_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    sys.path.insert(0, SCRIPT_DIR)
    import fetch_notion as fn  # .env の読み込み・Notion 読み取り関数を再利用

    token = fn.get_token()
    if not token:
        print("audit: トークンが未設定のため監査を行いません（前回の出力を残します）")
        return 0
    try:
        events = [to_event(fn, p) for p in fetch_event_pages(fn, token)]
    except Exception as e:  # noqa: BLE001
        print(f"audit: イベントDBを取得できません（{type(e).__name__}）。前回の出力を残します")
        return 0

    today = datetime.now(JST).date()
    since = "" if "--all" in sys.argv[1:] else (today - timedelta(days=RECENT_DAYS)).isoformat()
    pairs = find_pairs(events, load_allowlist(), since)
    result = {
        "generated_date": today.isoformat(),  # workflow の「1日1回」の門が読む。日付だけ
        "since": since or "all",
        "total_events": len(events),
        "count": len(pairs),
        "pairs": [
            {"score": p["score"],
             "pages": [{k: e[k] for k in ("id", "title", "start", "created", "src", "url")} for e in p["pages"]]}
            for p in pairs
        ],
    }
    write_text(OUT_JSON, json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    write_text(OUT_MD, render_md(pairs, len(events)))
    top = "・".join(f"{p['pages'][0]['start']} {p['pages'][0]['title']}" for p in pairs[:3])
    print(f"audit: 重複候補 {len(pairs)}組（イベント {len(events)}件）" + (f" 例: {top}" if pairs else ""))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # noqa: BLE001
        print(f"audit: 予期しないエラー（{type(e).__name__}）")
        sys.exit(0)
