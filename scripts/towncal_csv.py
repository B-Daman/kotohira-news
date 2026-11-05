#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🗓 こんぴらカレンダーの誌面画像から行事CSVを転記する（日曜の週次ランから呼ぶ・半自動）。

対象: towncal-data.js の issues[] のうち、assets/towncal/<月>.webp があり
      assets/towncal/events-<月>.csv が無い号（通常 0〜1 件）。
手順: WebP→PNG（一時フォルダ）→ `claude -p`（sonnet・Read のみ）に誌面を読ませる
      → CSV本文を取り出して検証 → events-<月>.csv（UTF-8 BOM）を保存
      → kotohira-news に commit・pull --rebase・push。
失敗したら非ゼロで終了し何も書かない（次の日曜に同じ条件で自然に再試行される）。

使い方:
  python scripts/towncal_csv.py                      # 通常（週次ランから）
  python scripts/towncal_csv.py --month 2026-11 --out <dir> --no-git   # 検証用（対象を強制・git しない）

仕様の正本: docs/こんぴらカレンダー自動更新_要件定義.md 5章。プロンプト: scripts/prompts/towncal_csv.md
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_towncal import read_issues  # noqa: E402

CLAUDE_BIN = r"C:\Users\user\.local\bin\claude.exe"
PROMPT_PATH = REPO / "scripts" / "prompts" / "towncal_csv.md"
COLUMNS = ["date", "dow", "title", "time", "place", "booking", "category", "note", "source", "check"]
MIN_MONTH = "2026-10"  # これより前の号は遡って転記しない（要件定義 6章3の既定）
DOW = "月火水木金土日"  # date.weekday() の順
CLAUDE_TIMEOUT_SEC = 900


def fail(msg: str) -> "SystemExit":
    return SystemExit(f"towncal_csv: {msg}")


def pick_targets(data_path: Path, out_dir: Path, forced: str | None) -> list[str]:
    if forced:
        if not re.fullmatch(r"\d{4}-\d{2}", forced):
            raise fail(f"--month は YYYY-MM 形式で指定してください: {forced}")
        return [forced]
    months = [i["month"] for i in read_issues(data_path)]
    img_dir = REPO / "assets" / "towncal"
    return sorted(
        m for m in months
        if m >= MIN_MONTH and (img_dir / f"{m}.webp").exists() and not (out_dir / f"events-{m}.csv").exists()
    )


def webp_to_png(month: str, tmp: Path) -> Path:
    src = REPO / "assets" / "towncal" / f"{month}.webp"
    if not src.exists():
        raise fail(f"画像がありません: {src}")
    try:
        from PIL import Image
    except ImportError:
        raise fail("Pillow が見つかりません（pip install pillow）。")
    png = tmp / f"towncal-{month}.png"
    Image.open(src).convert("RGB").save(png, "PNG")
    return png


def call_claude(png: Path, month: str) -> str:
    y, mo = month.split("-")
    prompt = (
        PROMPT_PATH.read_text(encoding="utf-8")
        .replace("{IMAGE_PATH}", str(png))
        .replace("{YEAR}", str(int(y)))
        .replace("{MONTH_2}", mo)
        .replace("{MONTH}", str(int(mo)))
    )
    exe = CLAUDE_BIN if Path(CLAUDE_BIN).exists() else (shutil.which("claude") or "")
    if not exe:
        raise fail("claude の実行ファイルが見つかりません。")
    cmd = [
        exe, "-p", "--model", "sonnet",
        "--allowedTools", "Read",
        "--disallowedTools", "WebSearch,WebFetch,Bash,Write,Edit",
        "--add-dir", str(png.parent),
    ]
    # プロンプトは標準入力で渡す（長文・日本語・Windows の引数長制限を避ける）。画像のあるフォルダを cwd にする
    r = subprocess.run(
        cmd, input=prompt, capture_output=True, text=True, encoding="utf-8",
        cwd=str(png.parent), timeout=CLAUDE_TIMEOUT_SEC,
    )
    if r.returncode != 0:
        raise fail(f"claude が失敗しました (exit {r.returncode}): {(r.stderr or r.stdout)[-500:]}")
    return r.stdout


def extract_csv(text: str) -> str:
    """出力からCSV本文だけを取り出す。コードフェンスがあれば剥がし、ヘッダー行より前は捨てる。"""
    m = re.search(r"```(?:csv)?[ \t]*\n(.*?)```", text, re.S)
    if m:
        text = m.group(1)
    text = text.lstrip("\ufeff")
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if ln.strip().startswith("date,"):
            return "\n".join(lines[i:]).strip() + "\n"
    raise fail("出力にCSVのヘッダー行（date,...）がありません。")


def validate(body: str, month: str) -> list[dict]:
    rows = list(csv.reader(io.StringIO(body)))
    header = [h.strip() for h in rows[0]]
    if header != COLUMNS:
        raise fail(f"列が想定と違います: {header}")
    out = []
    for n, r in enumerate(rows[1:], start=2):
        if not any(c.strip() for c in r):
            continue
        if len(r) != len(COLUMNS):
            raise fail(f"{n}行目の列数が{len(r)}です（{len(COLUMNS)}列が必要）: {r}")
        row = dict(zip(COLUMNS, (c.strip() for c in r)))
        try:
            d = dt.date.fromisoformat(row["date"])
        except ValueError:
            raise fail(f"{n}行目の日付が不正です: {row['date']!r}")
        if d.strftime("%Y-%m") != month:
            raise fail(f"{n}行目の日付が対象月 {month} の外です: {row['date']}")
        if not row["title"]:
            raise fail(f"{n}行目に title がありません")
        out.append(row)
    if not out:
        raise fail("行事が1行もありません。")
    return out


def finalize(rows: list[dict], month: str, prev_count: int | None) -> tuple[list[dict], bool]:
    y, mo = month.split("-")
    source = f"広報ことひら {int(y)}年{int(mo)}月号 こんぴらカレンダー"
    for r in rows:
        r["dow"] = DOW[dt.date.fromisoformat(r["date"]).weekday()]  # 曜日は日付から計算して上書き
        r["source"] = source
        r["check"] = "1" if r["check"].strip() in ("1", "1.0", "true", "True") else "0"
    rows.sort(key=lambda r: r["date"])  # 安定ソート（同日は出力順のまま）
    suspicious = prev_count is not None and len(rows) * 2 < prev_count
    if suspicious:
        for r in rows:
            r["check"] = "1"
    return rows, suspicious


def previous_row_count(out_dir: Path, month: str) -> int | None:
    y, mo = map(int, month.split("-"))
    py, pm = (y - 1, 12) if mo == 1 else (y, mo - 1)
    p = out_dir / f"events-{py}-{pm:02d}.csv"
    if not p.exists():
        return None
    with p.open(encoding="utf-8-sig", newline="") as f:
        return sum(1 for r in csv.reader(f) if any(c.strip() for c in r)) - 1


def write_csv(rows: list[dict], path: Path) -> None:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLUMNS, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\xef\xbb\xbf" + buf.getvalue().encode("utf-8"))


def git(*args: str) -> str:
    r = subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise fail(f"git {' '.join(args)} が失敗しました: {(r.stderr or r.stdout).strip()[-400:]}")
    return r.stdout


def push_pending() -> bool:
    """未 push の assets/towncal のコミットがあれば push する（前回 commit 後に push だけ失敗した週の再試行）。
    失敗すれば SystemExit（非ゼロ）。push を行ったら True。"""
    git("fetch", "origin", "main")
    if not git("log", "origin/main..HEAD", "--oneline", "--", "assets/towncal").strip():
        return False
    git("pull", "--rebase", "--autostash")
    git("push")
    return True


def commit_and_push(csv_path: Path, month: str) -> None:
    rel = csv_path.relative_to(REPO).as_posix()
    git("add", "--", rel)
    git("commit", "-m", f"chore: town calendar events CSV for {month}", "--", rel)  # このファイルだけをコミット
    git("pull", "--rebase", "--autostash")
    git("push")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--month", help="対象月 YYYY-MM を強制する（検証用）")
    ap.add_argument("--out", type=Path, default=REPO / "assets" / "towncal", help="CSVの保存先（検証用に差し替え可）")
    ap.add_argument("--no-git", action="store_true", help="commit・push をしない（検証用）")
    ap.add_argument("--data", type=Path, default=REPO / "towncal-data.js", help=argparse.SUPPRESS)
    args = ap.parse_args()

    if not args.no_git and push_pending():
        print("towncal_csv: 前回 push できなかったコミットを push しました")
    targets = pick_targets(args.data, args.out, args.month)
    if not targets:
        print("towncal_csv: 転記する号なし（全号に events CSV があります）")
        return
    for month in targets:
        print(f"towncal_csv: {month} を転記します")
        with tempfile.TemporaryDirectory(prefix="towncal-") as t:
            png = webp_to_png(month, Path(t))
            raw = call_claude(png, month)
        rows = validate(extract_csv(raw), month)
        rows, suspicious = finalize(rows, month, previous_row_count(args.out, month))
        path = args.out / f"events-{month}.csv"
        write_csv(rows, path)
        flagged = sum(1 for r in rows if r["check"] == "1")
        print(f"towncal_csv: 保存 {path}（{len(rows)}行・check=1 は{flagged}行）")
        if suspicious:
            print("towncal_csv: 警告 前月の半分未満の行数のため、全行を check=1 にしました（取りこぼしの疑い）")
        if not args.no_git:
            commit_and_push(path, month)
            print("towncal_csv: commit・push 完了")


if __name__ == "__main__":
    main()
