#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🗓 こんぴらカレンダーの誌面CSVを Notion のイベントDBに登録する（日曜の週次ランから呼ぶ）。

対象: assets/towncal/events-YYYY-MM.csv があり、events-YYYY-MM.registered.json が無い号。
      自動で拾うのは 2026-12 号以降。2026-10・11 号は初回の本人承認待ちなので、
      --month YYYY-MM を明示したときだけ登録する（設計書 6章）。
手順: CSV → items（設計書 3章）→ register_news.py（config-events-towncal.json）で登録
      → 結果を解釈:
        created   … そのまま（カレンダー＝こんぴらカレンダーのみ）
        skipped   … 題名＋日付が一致する既存ページに「こんぴらカレンダー」を和集合で足す
        held      … 同日類似。一致率0.9以上または内包なら既存ページに足す。0.8〜0.9は足さず報告だけ
      → events-YYYY-MM.registered.json / .registered.md を書く（登録済みの印）
      → commit・pull --rebase・push（未 push の再試行つき）。

使い方:
  python -X utf8 scripts/towncal_register.py                           # 通常（週次ランから）
  python -X utf8 scripts/towncal_register.py --month 2026-11 --dry-run # 検証（Notion に書かない）
  python -X utf8 scripts/towncal_register.py --month 2026-10           # 初回の本登録（本人承認後）

--dry-run は registered.* を書かず、既存ページへの付与もしない（結果を標準出力に出すだけ）。
--no-git で commit・push を省く。仕様の正本: docs/統合カレンダー_Phase2_設計.md
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import time
import unicodedata
import urllib.error
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT_DIR = Path(__file__).resolve().parent
VENV_PY = Path(r"C:\Users\user\notion-event-formatter\.venv\Scripts\python.exe")
SKILL_DIR = Path.home() / ".claude" / "skills" / "kotohira-news-register"
REGISTER = SKILL_DIR / "register_news.py"
CONFIG = SKILL_DIR / "config-events-towncal.json"

# notion_client / keyring が無い素の python で呼ばれたら、専用 venv で自分自身を再実行する
if __name__ == "__main__" and importlib.util.find_spec("notion_client") is None:
    if not VENV_PY.exists():
        raise SystemExit(f"towncal_register: notion_client が無く、venv も見つかりません: {VENV_PY}")
    sys.exit(subprocess.call([str(VENV_PY), "-X", "utf8", str(Path(__file__).resolve()), *sys.argv[1:]]))

sys.path.insert(0, str(SKILL_DIR))
sys.path.insert(0, str(SCRIPT_DIR))
import register_news as rn  # noqa: E402  normalize_title / same_day_score を再利用（DRY）
import patch_calendar_values as pcv  # noqa: E402  api() / CAL を再利用（既存ページに値を足す処理）
import backfill_calendar as bc  # noqa: E402  load_write_token / MIN_INTERVAL
from towncal_csv import git, push_pending  # noqa: E402  git の呼び方と未 push 再試行は CSV の段と同じ

LAYER = "こんぴらカレンダー"
OUT_DIR = REPO / "assets" / "towncal"
MIN_MONTH = "2026-10"        # これより前の号は扱わない
AUTO_FROM = "2026-12"        # 自動で拾うのはこの号から（10・11月号は初回の本人承認待ち）
AUTO_TAG_SCORE = 0.9         # 同日類似でこの一致率以上（または内包）なら既存に自動で足す
BASE_WORDS = ("朝市", "マルシェ", "祭", "体育祭", "図書館一般開放", "マラソン")
DEFAULT_SOURCE_URL = "https://www.town.kotohira.kagawa.jp/site/kouhou/list18.html"
MIN_CONTAIN = rn.SAME_DAY_MIN_CONTAIN


def fail(msg: str) -> "SystemExit":
    return SystemExit(f"towncal_register: {msg}")


# ---------- CSV → items ----------

def source_url() -> str:
    try:
        text = (REPO / "towncal-data.js").read_text(encoding="utf-8")
        m = re.search(r'sourceUrl:\s*"([^"]+)"', text)
        if m:
            return m.group(1)
    except OSError:
        pass
    return DEFAULT_SOURCE_URL


def parse_time(raw: str) -> tuple[str | None, str | None, bool]:
    """time 列 → (開始 HH:MM, 終了 HH:MM, 原文をコメントにも残すか)。時刻が読めなければ (None, None, 原文あり)。"""
    s = unicodedata.normalize("NFKC", raw or "").replace("~", "〜").strip()
    if not s:
        return None, None, False

    def ok(h: str, m: str) -> bool:
        return int(h) < 24 and int(m) < 60

    m = re.fullmatch(r"(\d{1,2}):(\d{2})〜(\d{1,2}):(\d{2})", s)
    if m and ok(m[1], m[2]) and ok(m[3], m[4]):
        start, end = f"{int(m[1]):02d}:{m[2]}", f"{int(m[3]):02d}:{m[4]}"
        return start, (end if end > start else None), False
    m = re.fullmatch(r"(\d{1,2}):(\d{2})〜?", s)
    if m and ok(m[1], m[2]):
        return f"{int(m[1]):02d}:{m[2]}", None, False
    m = re.search(r"(\d{1,2}):(\d{2})", s)  # 「開会式9:30〜・スタート10:00」等は先頭の時刻を開始にし、原文はコメントへ
    if m and ok(m[1], m[2]):
        return f"{int(m[1]):02d}:{m[2]}", None, True
    return None, None, True


def row_to_item(row: dict, month: str, src_url: str) -> dict:
    y, mo = month.split("-")
    source = (row.get("source") or "").strip() or f"広報ことひら {int(y)}年{int(mo)}月号 こんぴらカレンダー"
    date = row["date"].strip()
    start_t, end_t, keep_raw = parse_time(row.get("time", ""))

    parts = []
    if (row.get("place") or "").strip():
        parts.append(f"場所: {row['place'].strip()}")
    if keep_raw:
        parts.append(f"時間: {row['time'].strip()}")
    if (row.get("booking") or "").strip():
        parts.append("要予約")
    if (row.get("note") or "").strip():
        parts.append(f"備考: {row['note'].strip()}")
    if (row.get("category") or "").strip():
        parts.append(f"区分: {row['category'].strip()}（誌面の色分けから推定）")
    parts.append(f"出典: {source}")
    comment = " / ".join(parts)
    if is_check(row):
        comment = "【要確認】誌面の読み取りに自信がない行 " + comment

    item = {
        "イベント名": row["title"].strip(),
        "開催日時（開始）": f"{date}T{start_t}:00+09:00" if start_t else date,
        "市町村": "琴平町",
        "ソース": src_url,
        "コメント": comment,
    }
    if start_t and end_t:
        item["開催日時（終了）"] = f"{date}T{end_t}:00+09:00"
    return item


def is_check(row: dict) -> bool:
    return (row.get("check") or "0").strip() in ("1", "1.0", "true", "True")  # check 列が無い号は 0 扱い


def read_rows(csv_path: Path) -> list[dict]:
    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f) if any((v or "").strip() for v in r.values())]
    for n, r in enumerate(rows, start=2):
        if not (r.get("date") or "").strip() or not (r.get("title") or "").strip():
            raise fail(f"{csv_path.name} の{n}行目に date か title がありません")
    return rows


def is_base_candidate(title: str) -> bool:
    return any(w in title for w in BASE_WORDS)


# ---------- 登録（register_news.py） ----------

def run_register(items: list[dict], dry_run: bool) -> list[dict]:
    with tempfile.TemporaryDirectory(prefix="towncal-reg-") as t:
        p = Path(t) / "items.json"
        p.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
        cmd = [str(VENV_PY), "-X", "utf8", str(REGISTER), str(p), "--config", str(CONFIG)]
        if dry_run:
            cmd.append("--dry-run")
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=1800)
    if r.returncode != 0:
        raise fail(f"register_news.py が失敗しました (exit {r.returncode}): {(r.stderr or r.stdout)[-500:]}")
    m = re.search(r"^\[", r.stdout, re.M)  # dry-run はスキーマ表示が先に出るので JSON の頭から読む
    if not m:
        raise fail(f"register_news.py の出力に結果 JSON がありません: {r.stdout[-300:]}")
    results = json.loads(r.stdout[m.start():])
    if len(results) != len(items):
        raise fail(f"結果 {len(results)} 件が items {len(items)} 件と合いません")
    return results


def contains(a: str, b: str) -> bool:
    na, nb = rn.normalize_title(a), rn.normalize_title(b)
    shorter, longer = (na, nb) if len(na) <= len(nb) else (nb, na)
    return len(shorter) >= MIN_CONTAIN and shorter in longer


def page_id_of(url: str) -> str | None:
    m = re.search(r"([0-9a-fA-F]{32})(?:[?#].*)?$", url or "")
    return m.group(1) if m else None


def classify(row: dict, res: dict) -> dict:
    """register の1結果 → 行の記録。status: created / tagged_existing / held / skipped（付与の実行は別）。"""
    base = {
        "date": row["date"].strip(),
        "title": row["title"].strip(),
        "check": is_check(row),
        "base_candidate": is_base_candidate(row["title"]),
        "page_url": res.get("page_url"),
        "reason": None, "score": None,
        "existing_title": None, "existing_date": None, "existing_page": None,
    }
    st = res.get("status")
    if st == "created":
        return {**base, "status": "created"}
    if st == "skipped_dup":
        ex = res.get("existing_page")
        if not page_id_of(ex):  # 同じ CSV 内の重複行（既存ページが無い）
            return {**base, "status": "skipped", "reason": "csv_batch_dup"}
        return {**base, "status": "tagged_existing", "reason": "title_date", "score": 1.0,
                "existing_title": row["title"].strip(), "existing_date": base["date"], "existing_page": ex}
    sim = res.get("similar_to") or {}
    if st in ("held_title_dup",) or res.get("dup_status") == "possible_title_dup":
        score = float(sim.get("score") or 0)
        inc = contains(row["title"], sim.get("見出し", ""))
        info = {"score": score, "existing_title": sim.get("見出し"), "existing_date": sim.get("開始日"),
                "existing_page": sim.get("existing_page")}
        if score >= AUTO_TAG_SCORE or inc:
            return {**base, **info, "status": "tagged_existing", "reason": "similar_contain" if inc else "similar"}
        return {**base, **info, "status": "held", "reason": "similar_review"}
    return {**base, "status": "new"}  # dry-run で新規になる行（本実行では created）


def add_layer(token: str, page_url: str, state: dict) -> dict:
    """既存ページの「カレンダー」に LAYER を和集合で足す。他の値は消さない。"""
    pid = page_id_of(page_url)
    props = pcv.api(token, "GET", pid)["properties"]
    cur = [o["name"] for o in props.get(pcv.CAL, {}).get("multi_select", [])]
    if LAYER in cur:
        return {"before": cur, "after": cur, "changed": False}
    new = cur + [LAYER]
    wait = bc.MIN_INTERVAL - (time.monotonic() - state.get("last", 0.0))
    if wait > 0:
        time.sleep(wait)
    pcv.api(token, "PATCH", pid, {"properties": {pcv.CAL: {"multi_select": [{"name": n} for n in new]}}})
    state["last"] = time.monotonic()
    return {"before": cur, "after": new, "changed": True}


def sibling_conflicts(rows: list[dict], recs: list[dict]) -> list[int]:
    """誌面内の同日類似（先の行が新規になる場合、後の行は登録スキルが「同日類似」で止める）。index を返す。"""
    out = []
    for j, rj in enumerate(recs):
        if rj["status"] not in ("new", "created"):
            continue
        for i in range(j):
            if recs[i]["status"] in ("new", "created") and recs[i]["date"] == rj["date"] \
                    and rn.same_day_score(recs[i]["title"], rj["title"]) > 0:
                out.append(j)
                break
    return out


# ---------- 報告 ----------

def md_cell(s) -> str:
    return str(s if s is not None else "").replace("|", "／").replace("\n", " ")


def table(header: list[str], rows: list[list]) -> str:
    if not rows:
        return "（なし）\n"
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(md_cell(c) for c in r) + " |" for r in rows]
    return "\n".join(lines) + "\n"


def summarize(recs: list[dict]) -> dict:
    c = lambda s: sum(1 for r in recs if r["status"] == s)  # noqa: E731
    return {
        "created": c("created") + c("new"),
        "tagged_existing": c("tagged_existing"),
        "held": c("held"),
        "skipped": c("skipped"),
        "check": sum(1 for r in recs if r["check"]),
        "base_candidates": sum(1 for r in recs if r["base_candidate"] and r["status"] in ("created", "new")),
    }


def build_md(month: str, recs: list[dict], counts: dict, dry: bool) -> str:
    y, mo = month.split("-")
    mark = lambda r: "★基本候補" if r["base_candidate"] else ""  # noqa: E731
    created = [r for r in recs if r["status"] in ("created", "new")]
    tagged = [r for r in recs if r["status"] == "tagged_existing"]
    held = [r for r in recs if r["status"] == "held"]
    skipped = [r for r in recs if r["status"] == "skipped"]
    checks = [r for r in recs if r["check"]]
    head = "（dry-run: Notion には書いていません）\n\n" if dry else ""
    s = f"# こんぴらカレンダー {int(y)}年{int(mo)}月号 登録結果\n\n{head}"
    s += (f"- 登録 {counts['created']}件／既存に付与 {counts['tagged_existing']}件／"
          f"要判断 {counts['held']}件／要確認 {counts['check']}件"
          + (f"／CSV内の重複 {counts['skipped']}件" if counts["skipped"] else "") + "\n")
    s += "- 新規は カレンダー＝こんぴらカレンダー のみ。町外の人も来られる行事に `基本のイベント` を足すかは Notion で判断する（★基本候補は題名からの目安）\n\n"
    s += "## 要判断（同日に似た既存あり・一致率0.8〜0.9・足していない）\n\n"
    s += table(["日付", "誌面の題名", "既存ページの題名", "一致率", "既存ページ"],
               [[r["date"], r["title"], r["existing_title"], f"{r['score']:.2f}", r["existing_page"]] for r in held])
    s += f"\n## 既存に付与（こんぴらカレンダーを{'足す予定' if dry else '足した'}）\n\n"
    s += table(["日付", "誌面の題名", "既存ページの題名", "一致率", "理由"],
               [[r["date"], r["title"], r["existing_title"], f"{r['score']:.2f}",
                 {"title_date": "題名と日付が一致", "similar": "同日類似0.9以上", "similar_contain": "同日類似（内包）"}.get(r["reason"], r["reason"])]
                for r in tagged])
    s += "\n## 要確認（誌面の読み取りに自信がない行）\n\n"
    s += table(["日付", "題名", "状態"], [[r["date"], r["title"], r["status"]] for r in checks])
    s += "\n## 登録（新規）\n\n"
    s += table(["日付", "題名", "印"], [[r["date"], r["title"], mark(r)] for r in created])
    if skipped:
        s += "\n## CSV内の重複（登録していない）\n\n"
        s += table(["日付", "題名"], [[r["date"], r["title"]] for r in skipped])
    return s


# ---------- 本体 ----------

def pick_targets(forced: str | None, out_dir: Path) -> list[str]:
    if forced:
        if not re.fullmatch(r"\d{4}-\d{2}", forced):
            raise fail(f"--month は YYYY-MM 形式で指定してください: {forced}")
        if forced < MIN_MONTH:
            raise fail(f"{MIN_MONTH} より前の号は扱いません: {forced}")
        if not (out_dir / f"events-{forced}.csv").exists():
            raise fail(f"CSV がありません: events-{forced}.csv")
        if (out_dir / f"events-{forced}.registered.json").exists():
            raise fail(f"{forced} 号は登録済みです（events-{forced}.registered.json あり）")
        return [forced]
    months = []
    for p in sorted(out_dir.glob("events-????-??.csv")):
        m = p.stem.removeprefix("events-")
        if m >= AUTO_FROM and not (out_dir / f"events-{m}.registered.json").exists():
            months.append(m)
    return months


def process(month: str, out_dir: Path, dry: bool, no_git: bool) -> int:
    rows = read_rows(out_dir / f"events-{month}.csv")
    src_url = source_url()
    items = [row_to_item(r, month, src_url) for r in rows]
    results = run_register(items, dry_run=dry)
    recs = [classify(r, res) for r, res in zip(rows, results)]

    failures = 0
    if dry:
        sib = sibling_conflicts(rows, recs)
    else:
        # 誌面内の同日類似で、先に作った新規ページと「同日類似」になって保留された行は、別の行事なので許可して作る
        created_urls = {r["page_url"] for r in recs if r["status"] == "created"}
        again = [i for i, r in enumerate(recs)
                 if r["status"] in ("held", "tagged_existing") and r["existing_page"] in created_urls]
        if again:
            re_items = [{**items[i], "_allow_dup": True} for i in again]
            for i, res in zip(again, run_register(re_items, dry_run=False)):
                recs[i] = classify(rows[i], res)
                if recs[i]["reason"] == "title_date":  # この実行で作ったページと題名・日付が同じ＝CSV内の重複行
                    recs[i].update(status="skipped", reason="csv_batch_dup", existing_page=None)
        token = bc.load_write_token()
        state: dict = {}
        for r in recs:
            if r["status"] != "tagged_existing":
                continue
            for attempt in (1, 2):
                try:
                    r.update(add_layer(token, r["existing_page"], state))
                    break
                except urllib.error.HTTPError as e:
                    if attempt == 2:
                        failures += 1
                        r["status"], r["reason"] = "held", f"tag_failed_http_{e.code}"
                        print(f"towncal_register: 付与に失敗 {r['date']} {r['title']} (HTTP {e.code})")
                    else:
                        time.sleep(2)
        sib = []

    counts = summarize(recs)
    md = build_md(month, recs, counts, dry)
    if dry:
        print(md)
        if sib:
            print("参考: 誌面内で同日に似た題名の行（本実行では許可して両方作る）:")
            for j in sib:
                print(f"  {recs[j]['date']} {recs[j]['title']}")
        print(f"towncal_register: dry-run {month}: 登録(新規) {counts['created']}・既存に付与 {counts['tagged_existing']}・"
              f"要判断 {counts['held']}・要確認 {counts['check']}・CSV内重複 {counts['skipped']}")
        return 0

    jpath = out_dir / f"events-{month}.registered.json"
    mpath = out_dir / f"events-{month}.registered.md"
    doc = {"month": month, "generated": dt.datetime.now().isoformat(timespec="seconds"),
           "layer": LAYER, "counts": counts, "rows": recs}
    jpath.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    mpath.write_text(md, encoding="utf-8", newline="\n")
    print(f"towncal_register: {month} 登録 {counts['created']}・既存に付与 {counts['tagged_existing']}・"
          f"要判断 {counts['held']}・要確認 {counts['check']}")
    if not no_git:
        rels = [p.relative_to(REPO).as_posix() for p in (jpath, mpath)]
        git("add", "--", *rels)
        git("commit", "-m", f"chore: register town calendar events for {month}", "--", *rels)
        git("pull", "--rebase", "--autostash")
        git("push")
        print("towncal_register: commit・push 完了")
    return 1 if failures else 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--month", help="対象月 YYYY-MM を明示する（2026-10・11 号の本登録や検証用）")
    ap.add_argument("--dry-run", action="store_true", help="Notion に書かず、結果を標準出力に出す")
    ap.add_argument("--no-git", action="store_true", help="commit・push をしない")
    ap.add_argument("--out", type=Path, default=OUT_DIR, help=argparse.SUPPRESS)
    args = ap.parse_args()

    if not args.no_git and not args.dry_run and push_pending():
        print("towncal_register: 前回 push できなかったコミットを push しました")
    targets = pick_targets(args.month, args.out)
    if not targets:
        print("towncal_register: 登録する号なし")
        return
    rc = 0
    for month in targets:
        print(f"towncal_register: {month} を{'dry-run' if args.dry_run else '登録'}します")
        rc |= process(month, args.out, args.dry_run, args.no_git)
    sys.exit(rc)


if __name__ == "__main__":
    main()
