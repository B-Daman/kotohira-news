#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""金刀比羅宮の公開 Google カレンダー（ICS）→ Notion イベントDB の週次同期（2026-11-05）。

設計: docs/金刀比羅宮カレンダー同期_設計.md（要件: docs/金刀比羅宮カレンダー同期_要件定義.md）

- 公開 ICS を取得し、今日〜N日先（既定 90 日）の回に展開する（繰り返し・除外日・差し替えを処理）
- Notion の同じ日のページと「似た題名」または規則（docs/data/konpira-sync-rules.json）で突き合わせる
    同じ行事      → 空欄だけ補う（開始・終了時刻／カレンダー／主催／開催場所／ソース）。既存値は上書きしない
    同日に別の神社ページ → 要確認（規則で new と決めてあれば登録）
    それ以外      → 新規登録（登録スキル register_news.py・config-events-konpira.json）
- 結果を docs/data/konpira-sync-last.json / .md に残し、--apply のときは commit・push する
- 既定は dry-run（Notion に書かない・リポジトリのファイルも変えない）。--apply で実行

使い方:
    python -X utf8 scripts/konpira_sync.py                 # dry-run（内訳を表示）
    python -X utf8 scripts/konpira_sync.py --apply         # 実行（日曜の run_weekly.bat はこれ）
    python -X utf8 scripts/konpira_sync.py --ics path.ics  # 取得せずファイルで（オフライン検証）
終了コード: 0=正常 / 1=一部失敗 / 2=ICS 取得失敗（何も変えない）
"""
from __future__ import annotations

import argparse
import calendar
import collections
import datetime as dt
import difflib
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT_DIR = Path(__file__).resolve().parent
VENV_PY = Path(r"C:\Users\user\notion-event-formatter\.venv\Scripts\python.exe")
SKILL_DIR = Path.home() / ".claude" / "skills" / "kotohira-news-register"
REGISTER = SKILL_DIR / "register_news.py"
CONFIG = SKILL_DIR / "config-events-konpira.json"
DATA_DIR = REPO / "docs" / "data"
RULES_PATH = DATA_DIR / "konpira-sync-rules.json"
ICS_PATH = DATA_DIR / "konpira-calendar.ics"
LAST_JSON = DATA_DIR / "konpira-sync-last.json"
LAST_MD = DATA_DIR / "konpira-sync-last.md"
GIT_PATHS = ["docs/data/konpira-calendar.ics", "docs/data/konpira-sync-last.json", "docs/data/konpira-sync-last.md"]

# notion_client / keyring が無い素の python で呼ばれたら、専用 venv で自分自身を再実行する（towncal_register と同じ）
if __name__ == "__main__" and importlib.util.find_spec("notion_client") is None:
    if not VENV_PY.exists():
        raise SystemExit(f"konpira_sync: notion_client が無く、venv も見つかりません: {VENV_PY}")
    sys.exit(subprocess.call([str(VENV_PY), "-X", "utf8", str(Path(__file__).resolve()), *sys.argv[1:]]))

sys.path.insert(0, str(SKILL_DIR))
sys.path.insert(0, str(SCRIPT_DIR))
import register_news as rn  # noqa: E402  normalize_title を再利用（登録スキルと同じ正規化）
import patch_calendar_values as pcv  # noqa: E402  api() / CAL
import backfill_calendar as bc  # noqa: E402  load_write_token / MIN_INTERVAL / MAX_EVENTS
from towncal_csv import git  # noqa: E402  git の呼び方は CSV の段と同じ

LAYER = "金刀比羅宮"
ORG_PROP = "主催/運営"
PLACE_PROP = "開催場所"
SOURCE_PROP = "ソース"
START_PROP = "開催日時（開始）"
END_PROP = "開催日時（終了）"
JST = dt.timezone(dt.timedelta(hours=9))
WEEKDAY = {"MO": 0, "TU": 1, "WE": 2, "TH": 3, "FR": 4, "SA": 5, "SU": 6}
SIMILAR_RATIO = 0.80
MIN_CONTAIN = 3
COMMENT_MAX = 1900


def fail(msg: str) -> SystemExit:
    print(f"konpira_sync: {msg}", file=sys.stderr)
    return SystemExit(1)


# ---------- ICS ----------

def unescape(s: str) -> str:
    return (s or "").replace("\\n", "\n").replace("\\N", "\n").replace("\\,", ",").replace("\\;", ";").replace("\\\\", "\\")


def unfold(text: str) -> list[str]:
    return re.sub(r"\r?\n[ \t]", "", text).splitlines()


def parse_dt(key: str, val: str) -> tuple[dt.date, str | None]:
    """DTSTART/DTEND/RECURRENCE-ID/UNTIL の値 → (日付, 'HH:MM' か None)。UTC(Z) は JST に直す。"""
    val = val.strip()
    if "VALUE=DATE" in key or len(val) == 8:
        return dt.date(int(val[:4]), int(val[4:6]), int(val[6:8])), None
    t = dt.datetime.strptime(val.rstrip("Z"), "%Y%m%dT%H%M%S")
    if val.endswith("Z"):
        t = t + dt.timedelta(hours=9)
    return t.date(), t.strftime("%H:%M")


def parse_events(text: str) -> list[dict]:
    events: list[dict] = []
    cur: dict = {}
    in_ev = False
    for ln in unfold(text):
        if ln == "BEGIN:VEVENT":
            cur, in_ev = {"EXDATE": []}, True
        elif ln == "END:VEVENT":
            events.append(cur)
            in_ev = False
        elif in_ev and ":" in ln:
            k, v = ln.split(":", 1)
            name = k.split(";")[0]
            if name in ("DTSTART", "DTEND", "RECURRENCE-ID"):
                cur[name] = parse_dt(k, v)
            elif name == "EXDATE":
                for part in v.split(","):
                    cur["EXDATE"].append(parse_dt(k, part)[0])
            else:
                cur[name] = v
    return events


def rrule_dates(ev: dict, w_from: dt.date, w_to: dt.date) -> list[dt.date]:
    start, _ = ev["DTSTART"]
    rule = ev.get("RRULE")
    if not rule:
        return [start] if w_from <= start <= w_to else []
    parts = dict(p.split("=", 1) for p in rule.split(";"))
    until = parse_dt("DTSTART", parts["UNTIL"])[0] if "UNTIL" in parts else None
    freq = parts.get("FREQ")
    out: list[dt.date] = []
    for y in range(w_from.year, w_to.year + 1):
        if freq == "YEARLY":
            if "BYDAY" in parts and "BYMONTH" in parts:  # 例: 3MO;BYMONTH=7（7月第3月曜）
                n, wd = int(parts["BYDAY"][:-2]), WEEKDAY[parts["BYDAY"][-2:]]
                m = int(parts["BYMONTH"])
                days = [d for d in range(1, calendar.monthrange(y, m)[1] + 1) if dt.date(y, m, d).weekday() == wd]
                cands = [dt.date(y, m, days[n - 1])] if len(days) >= n else []
            else:
                try:
                    cands = [dt.date(y, start.month, start.day)]
                except ValueError:
                    cands = []
        elif freq == "MONTHLY" and "BYMONTHDAY" in parts:
            d = int(parts["BYMONTHDAY"])
            cands = [dt.date(y, m, d) for m in range(1, 13) if d <= calendar.monthrange(y, m)[1]]
        else:
            raise ValueError(f"未対応の RRULE: {rule}（{ev.get('SUMMARY')}）")
        for c in cands:
            if c < start or c < w_from or c > w_to or (until and c > until):
                continue
            out.append(c)
    return out


def monthly_days(events: list[dict]) -> dict[str, list[int]]:
    """題名ごとに MONTHLY;BYMONTHDAY の日を集める（「毎月1・6・10・26日に斎行」の文に使う）。"""
    days: dict[str, set[int]] = collections.defaultdict(set)
    for ev in events:
        rule = ev.get("RRULE") or ""
        m = re.search(r"BYMONTHDAY=(\d+)", rule)
        if "FREQ=MONTHLY" in rule and m and "RECURRENCE-ID" not in ev:
            days[unescape(ev.get("SUMMARY", ""))].add(int(m.group(1)))
    return {k: sorted(v) for k, v in days.items()}


def clean_text(s: str, limit: int) -> str:
    s = re.sub(r"<[^>]+>", "", unescape(s))
    s = re.sub(r"\s+", " ", s).strip()
    return s[:limit]


def expand(events: list[dict], w_from: dt.date, w_to: dt.date) -> list[dict]:
    """窓内の回に展開する。EXDATE は除き、RECURRENCE-ID の差し替えを適用し、同じ (日付, 題名) は畳む。"""
    overrides = {(ev.get("UID"), ev["RECURRENCE-ID"][0]): ev for ev in events if "RECURRENCE-ID" in ev}
    mdays = monthly_days(events)
    rows: dict[tuple[str, str], dict] = {}
    for ev in events:
        if "RECURRENCE-ID" in ev:
            continue
        for d in rrule_dates(ev, w_from, w_to):
            if d in ev["EXDATE"]:
                continue
            src = overrides.get((ev.get("UID"), d), ev)
            sd, st = src["DTSTART"]
            ed, et = src.get("DTEND", (sd, None))
            if src is not ev:
                d = sd
                if not (w_from <= d <= w_to):
                    continue
            end_date = d + (ed - sd)  # 繰り返しの回では DTEND は初回の日付なので、その回の日付にずらす
            title = unescape(src.get("SUMMARY", "")).strip()
            key = (d.isoformat(), title)
            if key in rows:
                continue
            rows[key] = {
                "date": d.isoformat(), "start": st, "end": et, "end_date": end_date.isoformat(),
                "title": title, "uid": ev.get("UID"),
                "location": clean_text(src.get("LOCATION", ""), 200).split(",")[0].strip(),  # 住所部分は落とす
                "desc": clean_text(src.get("DESCRIPTION", ""), COMMENT_MAX),
                "monthly": mdays.get(title) if "FREQ=MONTHLY" in (ev.get("RRULE") or "") else None,
            }
    return sorted(rows.values(), key=lambda r: (r["date"], r["start"] or ""))


def fetch_ics(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "kotohilife-konpira-sync/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    text = data.decode("utf-8", errors="replace")
    if "BEGIN:VCALENDAR" not in text:
        raise ValueError("ICS ではない応答")
    return text


# ---------- 規則 ----------

def norm(s: str) -> str:
    t = rn.normalize_title(s)
    return re.sub(r"^\d+月\d+日", "", t)


def similar(a: str, b: str) -> str | None:
    """同じ行事とみなせるなら根拠（exact / contain / ratio）を返す。
    判定は登録スキルの same_day_score と同じ（朝祭/夕祭/竟祭 など「別の回」の語が違えば別の行事）。"""
    if rn.same_day_score(a, b) <= 0.0:
        return None
    na, nb = norm(a), norm(b)
    if na == nb:
        return "exact"
    shorter, longer = (na, nb) if len(na) <= len(nb) else (nb, na)
    if len(shorter) >= MIN_CONTAIN and shorter in longer:
        return "contain"
    return "ratio"


def load_rules() -> dict:
    d = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    d["_titles"] = {t["ics"]: t for t in d.get("titles", [])}
    d["_skip"] = set(d.get("skip_titles", []))
    return d


def place_for(location: str, rules: dict) -> dict | None:
    """LOCATION の先頭語（「金刀比羅宮 」を外し、・（( で区切った最初の語）で場所DBのページを引く。"""
    loc = (location or "").strip()
    if not loc:
        return None
    if loc.startswith("金刀比羅宮 "):
        loc = loc[len("金刀比羅宮 "):]
    head = re.split(r"[ ・（(,、]", loc)[0].strip()
    for pl in rules.get("places", []):
        if head in pl["match"] or loc in pl["match"]:
            return pl
    return None


# ---------- Notion ----------

def load_notion_pages(w_from: str, w_to: str) -> list[dict]:
    """窓内に開始日を持つ全ページ。※書き込みトークンの解決後に呼ぶ（fetch_notion が .env を取り込むため）。"""
    import fetch_notion as fn  # noqa: E402

    tok = fn.get_token()
    if not tok:
        raise fail("読み取りトークンが見つかりません（kotohira-news の .env）")
    ds = fn.get_data_source_id(fn.EVENT_DB_ID, tok)
    pages = fn.query_data_source(ds, tok, [{"property": START_PROP, "direction": "ascending"}], bc.MAX_EVENTS)
    out = []
    for p in pages:
        props = p.get("properties", {})
        s = fn.get_date_start(props, START_PROP)
        if not s or not (w_from <= s[:10] <= w_to):
            continue
        e = fn.get_date_start(props, END_PROP)
        out.append({
            "id": p["id"], "title": fn.get_title(props, "イベント名"), "date": s[:10],
            "start": s[11:16] if len(s) > 10 else None,
            "end": e[11:16] if len(e) > 10 else None, "has_end": bool(e),
            "calendars": fn.get_multi_select(props, pcv.CAL), "orgs": fn.get_multi_select(props, ORG_PROP),
            "place_ids": fn.get_relation_ids(props, PLACE_PROP),
            "source": (props.get(SOURCE_PROP) or {}).get("url") or "",
            "discord_url": (props.get("DiscordイベントURL") or {}).get("url") or "",
        })
    return out


def is_shrine(p: dict) -> bool:
    return LAYER in p["calendars"] or LAYER in p["orgs"]


def jst_iso(date: str, hhmm: str) -> str:
    return f"{date}T{hhmm}:00+09:00"


def plan_fills(page: dict, occ: dict, rules: dict) -> tuple[dict, bool]:
    """補うプロパティ（PATCH の断片）と、時刻の食い違いの有無。既存値は触らない。"""
    fills: dict = {}
    conflict = bool(page["start"] and occ["start"] and page["start"] != occ["start"])
    if occ["start"] and not page["start"]:
        fills[START_PROP] = {"date": {"start": jst_iso(occ["date"], occ["start"]), "end": None}}
    if occ["end"] and not page["has_end"] and not conflict:
        fills[END_PROP] = {"date": {"start": jst_iso(occ["end_date"], occ["end"]), "end": None}}
    if LAYER not in page["calendars"]:
        fills[pcv.CAL] = {"multi_select": [{"name": n} for n in page["calendars"] + [LAYER]]}
    if not page["orgs"]:
        fills[ORG_PROP] = {"multi_select": [{"name": LAYER}]}
    if not page["place_ids"]:
        pl = place_for(occ["location"], rules)
        if pl:
            fills[PLACE_PROP] = {"relation": [{"id": pl["page"]}]}
    if not page["source"]:
        fills[SOURCE_PROP] = {"url": rules["source_url"]}
    return fills, conflict


def describe_fills(fills: dict, rules: dict) -> list[str]:
    out = []
    for k, v in fills.items():
        if k in (START_PROP, END_PROP):
            out.append(f"{'開始' if k == START_PROP else '終了'} {v['date']['start'][11:16]}")
        elif k == pcv.CAL:
            out.append(f"カレンダー+{LAYER}")
        elif k == ORG_PROP:
            out.append(f"主催 {LAYER}")
        elif k == PLACE_PROP:
            pid = v["relation"][0]["id"]
            name = next((p["name"] for p in rules.get("places", []) if p["page"] == pid), pid)
            out.append(f"開催場所 {name}")
        elif k == SOURCE_PROP:
            out.append("ソース")
    return out


def new_item(occ: dict, rules: dict) -> dict:
    parts = []
    if occ["desc"]:
        parts.append(occ["desc"])
    if occ["location"] and not place_for(occ["location"], rules):
        parts.append(f"場所: {occ['location']}")
    if occ["monthly"]:
        parts.append("毎月" + "・".join(str(d) for d in occ["monthly"]) + "日に斎行")
    parts.append("出典: 金刀比羅宮公式カレンダー（こんぴらさんカレンダー）")
    item = {
        "イベント名": occ["title"],
        START_PROP: jst_iso(occ["date"], occ["start"]) if occ["start"] else occ["date"],
        ORG_PROP: LAYER,
        SOURCE_PROP: rules["source_url"],
        "コメント": " / ".join(parts)[:COMMENT_MAX],
    }
    if occ["end"]:
        item[END_PROP] = jst_iso(occ["end_date"], occ["end"])
    return item


def run_register(items: list[dict], dry_run: bool) -> list[dict]:
    with tempfile.TemporaryDirectory(prefix="konpira-reg-") as t:
        p = Path(t) / "items.json"
        p.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
        cmd = [str(VENV_PY), "-X", "utf8", str(REGISTER), str(p), "--config", str(CONFIG)]
        if dry_run:
            cmd.append("--dry-run")
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=1800)
    if r.returncode != 0:
        raise fail(f"register_news.py が失敗しました (exit {r.returncode}): {(r.stderr or r.stdout)[-500:]}")
    m = re.search(r"^\[", r.stdout, re.M)
    if not m:
        raise fail(f"register_news.py の出力に結果 JSON がありません: {r.stdout[-300:]}")
    results = json.loads(r.stdout[m.start():])
    if len(results) != len(items):
        raise fail(f"結果 {len(results)} 件が items {len(items)} 件と合いません")
    return results


def page_id_of(url: str) -> str | None:
    m = re.search(r"([0-9a-fA-F]{32})(?:[?#].*)?$", url or "")
    return m.group(1) if m else None


class Writer:
    """PATCH を MIN_INTERVAL 間隔で送る。失敗は例外のまま返す。"""

    def __init__(self, token: str | None):
        self.token = token
        self.last = 0.0
        self._place_ok: dict[str, bool] = {}

    def _throttle(self) -> None:
        wait = bc.MIN_INTERVAL - (time.monotonic() - self.last)
        if wait > 0:
            time.sleep(wait)

    def patch(self, page_id: str, props: dict) -> None:
        self._throttle()
        try:
            pcv.api(self.token, "PATCH", page_id, {"properties": props})
        finally:
            self.last = time.monotonic()

    def place_writable(self, place_page_id: str) -> bool:
        """場所DBのページに書き込みトークンが届くか（届かないと relation の PATCH が 404 になる）。1件1回だけ確かめる。"""
        if place_page_id not in self._place_ok:
            self._throttle()
            try:
                pcv.api(self.token, "GET", place_page_id)
                self._place_ok[place_page_id] = True
            except urllib.error.HTTPError as e:
                if e.code != 404:
                    raise
                self._place_ok[place_page_id] = False
            finally:
                self.last = time.monotonic()
        return self._place_ok[place_page_id]

    def strip_unwritable_place(self, props: dict) -> tuple[dict, bool]:
        """relation 先に届かないなら 開催場所 を外して返す。(残りの props, 外したか)"""
        rel = props.get(PLACE_PROP)
        if not rel or self.place_writable(rel["relation"][0]["id"]):
            return props, False
        return {k: v for k, v in props.items() if k != PLACE_PROP}, True


# ---------- 突合 ----------

def classify(occs: list[dict], pages: list[dict], rules: dict) -> list[dict]:
    by_date: dict[str, list[dict]] = collections.defaultdict(list)
    for p in pages:
        by_date[p["date"]].append(p)
    used: set[str] = set()
    rows: list[dict] = []
    pending: list[dict] = []
    for occ in occs:
        rule = rules["_titles"].get(occ["title"])
        base = {"date": occ["date"], "title": occ["title"], "start": occ["start"], "end": occ["end"],
                "location": occ["location"], "notion_id": None, "notion_title": None, "fills": [], "reason": None,
                "_occ": occ}
        if occ["title"] in rules["_skip"] or (rule and rule.get("action") == "ignore"):
            rows.append({**base, "status": "skipped", "reason": "rule_ignore"})
            continue
        cands = [p for p in by_date[occ["date"]] if p["id"] not in used]
        hit, how = None, None
        if rule and rule.get("action") == "same":
            target = norm(rule.get("notion", ""))
            hit = next((p for p in cands if norm(p["title"]) == target), None)
            how = "rule_same" if hit else None
        if not hit:
            best = None
            for p in cands:
                s = similar(p["title"], occ["title"])
                if s:
                    rank = {"exact": 0, "contain": 1, "ratio": 2}[s]
                    if best is None or rank < best[0]:
                        best = (rank, p, s)
            if best:
                _, hit, how = best
        if hit:
            used.add(hit["id"])
            fills, conflict = plan_fills(hit, occ, rules)
            status = "conflict" if conflict else ("filled" if fills else "ok")
            rows.append({**base, "status": status, "reason": how, "notion_id": hit["id"], "notion_title": hit["title"],
                         "fills": describe_fills(fills, rules), "_patch": fills,
                         "notion_start": hit["start"]})
        else:
            pending.append(base)
    for base in pending:
        occ = base["_occ"]
        rule = rules["_titles"].get(occ["title"])
        blockers = [p for p in by_date[occ["date"]] if p["id"] not in used and is_shrine(p)]
        if blockers and not (rule and rule.get("action") == "new"):
            rows.append({**base, "status": "held", "reason": "same_day_other",
                         "same_day": [{"title": p["title"], "start": p["start"], "id": p["id"]} for p in blockers]})
        else:
            rows.append({**base, "status": "new", "reason": "rule_new" if rule else None})
    return sorted(rows, key=lambda r: (r["date"], r["start"] or "", r["title"]))


# ---------- 実行 ----------

def apply_changes(rows: list[dict], rules: dict, token: str | None, dry_run: bool) -> None:
    writer = Writer(token)
    # 補完
    for r in rows:
        if r["status"] in ("filled", "conflict") and r.get("_patch") and not dry_run:
            props, dropped = writer.strip_unwritable_place(r["_patch"])
            if dropped:
                r["place_pending"] = True
                r["fills"] = describe_fills(props, rules)
                if not props:
                    if r["status"] == "filled":
                        r["status"] = "ok"
                    continue
            try:
                writer.patch(r["notion_id"], props)
                r["applied"] = True
            except urllib.error.HTTPError as e:
                r["status"], r["reason"] = "failed", f"patch_http_{e.code}"
    # 新規登録
    news = [r for r in rows if r["status"] == "new"]
    if not news:
        return
    items = [new_item(r["_occ"], rules) for r in news]
    results = run_register(items, dry_run)
    for r, res in zip(news, results):
        st = res.get("status")
        sim = res.get("similar_to") or {}
        if st == "created":
            r["status"], r["page_url"] = "created", res.get("page_url")
            pl = place_for(r["_occ"]["location"], rules)
            pid = page_id_of(r["page_url"] or "")
            if pl and pid and not dry_run:
                if not writer.place_writable(pl["page"]):
                    r["place_pending"] = True
                else:
                    try:
                        writer.patch(pid, {PLACE_PROP: {"relation": [{"id": pl["page"]}]}})
                        r["fills"] = [f"開催場所 {pl['name']}"]
                    except urllib.error.HTTPError as e:
                        r["reason"] = f"place_patch_http_{e.code}"
        elif st == "held_title_dup" or res.get("dup_status") == "possible_title_dup":
            r["status"], r["reason"] = "held", "skill_same_day"
            r["same_day"] = [{"title": sim.get("見出し"), "start": None, "id": page_id_of(sim.get("existing_page") or "")}]
        elif st == "skipped_dup":
            r["status"], r["reason"] = "skipped", "title_date_exists"
        elif st == "dup_check":
            r["status"] = "new"  # dry-run: 登録される見込み
        else:
            r["status"], r["reason"] = "failed", f"register_{st}"


def counts_of(rows: list[dict]) -> dict:
    c = collections.Counter(r["status"] for r in rows)
    out = {k: c.get(k, 0) for k in ("created", "new", "filled", "ok", "held", "conflict", "skipped", "failed")}
    out["place_pending"] = sum(1 for r in rows if r.get("place_pending"))
    return out


def build_md(doc: dict) -> str:
    c, rows = doc["counts"], doc["rows"]
    mode = "apply" if doc["apply"] else "dry-run"
    L = [f"# 金刀比羅宮カレンダー同期 結果（{doc['generated'][:16].replace('T', ' ')}・{mode}）", ""]
    L.append(f"- 窓: {doc['window']['from']} 〜 {doc['window']['to']}（{doc['days']}日）／ ICS 展開 {doc['ics_rows']} 回 ／ Notion 窓内 {doc['notion_rows']} 件")
    L.append(f"- 登録 {c['created'] + c['new']}・補完 {c['filled']}・変更なし {c['ok']}・要確認 {c['held']}・時刻相違 {c['conflict']}・除外 {c['skipped']}・失敗 {c['failed']}")
    L.append("- 規則: docs/data/konpira-sync-rules.json（要確認は規則に1行足すと次回から自動で決まる）")

    def sec(title: str, status: tuple[str, ...], fmt) -> None:
        sel = [r for r in rows if r["status"] in status]
        if not sel:
            return
        L.extend(["", f"## {title}（{len(sel)}）", ""])
        L.extend(fmt(r) for r in sel)

    def span(r: dict) -> str:
        return f"{r['start'] or '--:--'}{'〜' + r['end'] if r['end'] else ''}"

    sec("要確認", ("held",), lambda r: (
        f"- {r['date']} 「{r['title']}」 {span(r)} … 同日の既存: "
        + " / ".join(f"「{s['title']}」({s['start'] or '時刻なし'})" for s in r.get("same_day", []))
        + f"\n  規則の例: {{\"ics\": \"{r['title']}\", \"action\": \"same\", \"notion\": \"{(r.get('same_day') or [{}])[0].get('title', '')}\"}} "
        + f"または {{\"ics\": \"{r['title']}\", \"action\": \"new\"}}"))
    sec("登録", ("created", "new"), lambda r: (
        f"- {r['date']} {span(r)} {r['title']}" + (f"（{r['location']}）" if r["location"] else "")
        + (f" → {r['page_url']}" if r.get("page_url") else "") + (f"  {' / '.join(r['fills'])}" if r["fills"] else "")))
    sec("補完", ("filled",), lambda r: f"- {r['date']} {r['notion_title']}: " + " / ".join(r["fills"]))
    sec("時刻相違（書いていない）", ("conflict",), lambda r: (
        f"- {r['date']} {r['notion_title']}: Notion {r.get('notion_start')} / 公式 {r['start']}"
        + (f"  （他の補完: {' / '.join(r['fills'])}）" if r["fills"] else "")))
    sec("失敗", ("failed",), lambda r: f"- {r['date']} {r['title']}: {r['reason']}")
    sec("除外", ("skipped",), lambda r: f"- {r['date']} {r['title']}: {r['reason']}")
    sec("変更なし", ("ok",), lambda r: f"- {r['date']} {r['notion_title']}")
    place_ng = [r for r in rows if r.get("place_pending")]
    if place_ng:
        L.extend(["", f"## 注意: 開催場所を付けられなかった（{len(place_ng)}）", "",
                  "場所DB（会場名・住所）が書き込みインテグレーションに接続されていないため。"
                  "Notion で場所DBを開き「…」→「接続」から、登録スキル用の書き込みインテグレーション"
                  "（イベントDBに接続してあるもの）を追加すると、次回の同期で自動で付く。", ""])
        L.extend(f"- {r['date']} {r['title']}" for r in place_ng)
    return "\n".join(L) + "\n"


def push_pending() -> bool:
    git("fetch", "origin", "main")
    if not git("log", "origin/main..HEAD", "--oneline", "--", *GIT_PATHS).strip():
        return False
    git("pull", "--rebase", "--autostash")
    git("push")
    return True


def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Notion に書き、記録を commit・push する（既定は dry-run）")
    ap.add_argument("--days", type=int, default=90, help="今日から何日先まで見るか（既定 90）")
    ap.add_argument("--no-git", action="store_true", help="commit・push しない")
    ap.add_argument("--ics", help="取得せずこのファイルを使う（オフライン検証）")
    args = ap.parse_args()
    dry_run = not args.apply

    rules = load_rules()
    token = bc.load_write_token() if not dry_run else None  # fetch_notion の import より先に解決する
    if not dry_run and not args.no_git:
        push_pending()

    today = dt.datetime.now(JST).date()
    w_from, w_to = today, today + dt.timedelta(days=args.days)
    if args.ics:
        text = Path(args.ics).read_text(encoding="utf-8", errors="replace")
    else:
        try:
            text = fetch_ics(rules["ics_url"])
        except (urllib.error.URLError, OSError, ValueError) as e:
            print(f"konpira_sync: ICS を取得できませんでした（{type(e).__name__}）。何も変えません")
            return 2
    events = parse_events(text)
    occs = expand(events, w_from, w_to)
    pages = load_notion_pages(w_from.isoformat(), w_to.isoformat())
    rows = classify(occs, pages, rules)
    apply_changes(rows, rules, token, dry_run)

    doc = {
        "generated": dt.datetime.now(JST).replace(microsecond=0).isoformat(),
        "apply": not dry_run, "days": args.days,
        "window": {"from": w_from.isoformat(), "to": w_to.isoformat()},
        "ics_events": len(events), "ics_rows": len(occs), "notion_rows": len(pages),
        "counts": counts_of(rows),
        "rows": [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows],
    }
    md = build_md(doc)
    print(md)
    if dry_run:
        print("-- dry-run（Notion にもリポジトリにも書いていません）")
        return 0

    if not args.ics:
        old = ICS_PATH.read_text(encoding="utf-8", errors="replace") if ICS_PATH.exists() else None
        if old != text:
            ICS_PATH.write_text(text, encoding="utf-8", newline="\n")
    LAST_JSON.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    LAST_MD.write_text(md, encoding="utf-8", newline="\n")
    if not args.no_git:
        git("add", "--", *GIT_PATHS)
        if git("status", "--porcelain", "--", *GIT_PATHS).strip():
            git("commit", "-m", f"chore: sync Konpira shrine calendar {today.isoformat()}", "--", *GIT_PATHS)
            git("pull", "--rebase", "--autostash")
            git("push")
    return 1 if doc["counts"]["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
