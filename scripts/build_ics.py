#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""notion-data.js の events から、レイヤー別の ICS（iCalendar）をサイト直下に生成する。

  events-all.ics      全件
  events-base.ics     「基本のイベント」を持つ件（カレンダー未分類＝空も含む）
  events-konpira.ics  「金刀比羅宮」を持つ件
  events-towncal.ics  「こんぴらカレンダー」を持つ件

Google カレンダーの「URL で追加」で購読する用（書き込み権限を持たない）。
元データは fetch_notion.py が作る notion-data.js（終了から60日以内と今後・上限200件）。ここでも念のため
終了から60日より前の件は入れない。DTSTAMP は notion-data.js の fetched を使い、内容が同じなら
出力も同じバイト列になる（毎時の workflow で無駄なコミットを出さないため）。外部ライブラリは使わない。

使い方: python scripts/build_ics.py [--data notion-data.js] [--out <dir>]
仕様の正本: docs/統合カレンダー_Phase3_設計.md
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
JST = dt.timezone(dt.timedelta(hours=9))
SITE = "https://kotohilife.com/"
EVENTS_URL = SITE + "#events"
RECENT_WINDOW_DAYS = 60
BASE = "基本のイベント"

# ファイル名 → (表示名, 属する条件)
LAYERS = {
    "events-all.ics": ("ことひらいふ すべてのイベント", lambda cals: True),
    "events-base.ics": ("ことひらいふ 基本のイベント", lambda cals: BASE in cals),
    "events-konpira.ics": ("ことひらいふ 金刀比羅宮", lambda cals: "金刀比羅宮" in cals),
    "events-towncal.ics": ("ことひらいふ こんぴらカレンダー", lambda cals: "こんぴらカレンダー" in cals),
}

VTIMEZONE = [
    "BEGIN:VTIMEZONE",
    "TZID:Asia/Tokyo",
    "X-LIC-LOCATION:Asia/Tokyo",
    "BEGIN:STANDARD",
    "TZOFFSETFROM:+0900",
    "TZOFFSETTO:+0900",
    "TZNAME:JST",
    "DTSTART:19700101T000000",
    "END:STANDARD",
    "END:VTIMEZONE",
]

DT_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2}))?")


def load_events(path: Path) -> tuple[list[dict], str]:
    text = path.read_text(encoding="utf-8")
    data = json.loads(text[text.index("{"): text.rindex("}") + 1])
    return data.get("events", []), str(data.get("fetched", ""))


def calendars_of(ev: dict) -> list[str]:
    cals = [c for c in (ev.get("calendar") or []) if c]
    return cals or [BASE]  # 未分類は基本のイベント扱い（サイトと同じ）


def parse(value: str):
    """'YYYY-MM-DD' or 'YYYY-MM-DDTHH:MM' → (date, 'HHMM' or None)。読めなければ None。"""
    m = DT_RE.match(value or "")
    if not m:
        return None
    try:
        d = dt.date(int(m[1]), int(m[2]), int(m[3]))
    except ValueError:
        return None
    return d, (f"{m[4]}{m[5]}" if m[4] else None)


def esc_text(s: str) -> str:
    """TEXT 値のエスケープ（RFC 5545 3.3.11）。"""
    s = str(s).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")
    return s.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\\n")


def fold(line: str) -> list[str]:
    """75 オクテット（UTF-8）で折り返す。継続行は先頭に空白1つ（それも75に数える）。文字の途中では切らない。"""
    out, cur, size, limit = [], "", 0, 75
    for ch in line:
        n = len(ch.encode("utf-8"))
        if size + n > limit:
            out.append(cur)
            cur, size, limit = " ", 1, 75
        cur += ch
        size += n
    out.append(cur)
    return out


def fee_text(fee: str) -> str:
    f = str(fee or "").strip()
    if not f:
        return ""
    if re.fullmatch(r"0+(\.0+)?", f):
        return "参加費: 無料"
    if re.fullmatch(r"[\d,]+(\.\d+)?", f):
        return f"参加費: {f}円"
    return f"参加費: {f}"


def date_str(d: dt.date) -> str:
    return d.strftime("%Y%m%d")


def event_lines(ev: dict, stamp: str) -> list[str] | None:
    s = parse(ev.get("start", ""))
    if not s:
        return None  # 日付未定は購読カレンダーに出せない
    sd, st = s
    e = parse(ev.get("end", ""))
    ed, et = e if e else (None, None)
    if ed and ed < sd:
        ed, et = None, None

    L = ["BEGIN:VEVENT", f"UID:{ev['id']}@kotohilife.com", f"DTSTAMP:{stamp}"]
    if st:
        L.append(f"DTSTART;TZID=Asia/Tokyo:{date_str(sd)}T{st}00")
        if ed:
            L.append(f"DTEND;TZID=Asia/Tokyo:{date_str(ed)}T{(et or '2359')}00")
    else:
        L.append(f"DTSTART;VALUE=DATE:{date_str(sd)}")
        L.append(f"DTEND;VALUE=DATE:{date_str((ed or sd) + dt.timedelta(days=1))}")  # 終日は終了日の翌日

    L.append(f"SUMMARY:{esc_text(ev.get('title', '(無題)'))}")
    loc = ev.get("place") or ev.get("city") or ""
    if loc:
        L.append(f"LOCATION:{esc_text(loc)}")
    desc = [x for x in (
        (ev.get("comment") or "").strip(),
        fee_text(ev.get("fee")),
        f"主催: {ev['organizer']}" if ev.get("organizer") else "",
        f"ことひらいふ イベント: {EVENTS_URL}",
    ) if x]
    L.append(f"DESCRIPTION:{esc_text(chr(10).join(desc))}")
    if str(ev.get("url", "")).startswith("http"):
        L.append(f"URL:{ev['url']}")
    L.append("CATEGORIES:" + ",".join(esc_text(c) for c in calendars_of(ev)))
    L.append("END:VEVENT")
    return L


def build_calendar(name: str, events: list[dict], stamp: str) -> tuple[bytes, int]:
    L = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//kotohilife.com//events//JA",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{esc_text(name)}",
        "X-WR-TIMEZONE:Asia/Tokyo",
        *VTIMEZONE,
    ]
    n = 0
    for ev in events:
        lines = event_lines(ev, stamp)
        if lines:
            L += lines
            n += 1
    L.append("END:VCALENDAR")
    folded = [piece for line in L for piece in fold(line)]
    return ("\r\n".join(folded) + "\r\n").encode("utf-8"), n


def stamp_from(fetched: str) -> str:
    """notion-data.js の fetched（JST 'YYYY-MM-DD HH:MM'）→ DTSTAMP（UTC）。読めなければ固定の過去日時。"""
    try:
        t = dt.datetime.strptime(fetched, "%Y-%m-%d %H:%M").replace(tzinfo=JST)
    except ValueError:
        t = dt.datetime(2026, 1, 1, tzinfo=JST)
    return t.astimezone(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def recent(events: list[dict], today: dt.date) -> list[dict]:
    cutoff = today - dt.timedelta(days=RECENT_WINDOW_DAYS)
    keep = []
    for ev in events:
        s = parse(ev.get("start", ""))
        if not s:
            continue
        e = parse(ev.get("end", ""))
        last = e[0] if e and e[0] >= s[0] else s[0]
        if last >= cutoff:
            keep.append(ev)
    return sorted(keep, key=lambda ev: (ev.get("start", ""), ev.get("id", "")))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, default=REPO / "notion-data.js")
    ap.add_argument("--out", type=Path, default=REPO)
    args = ap.parse_args()

    events, fetched = load_events(args.data)
    events = recent(events, dt.datetime.now(JST).date())
    stamp = stamp_from(fetched)
    for fname, (name, pred) in LAYERS.items():
        body, n = build_calendar(name, [ev for ev in events if pred(calendars_of(ev))], stamp)
        (args.out / fname).write_bytes(body)
        print(f"build_ics: {fname} {n}件")


if __name__ == "__main__":
    main()
