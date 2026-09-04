#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""早明浦ダムの貯水状況を「川の防災情報」（国交省）から取得し、dam-data.js を生成するスクリプト。

- 標準ライブラリのみで動く（pip依存なし。fetch_notion.py と同じ流儀）。
- アクセス先は www1.river.go.jp のみに限定する（guard_url。他ドメインへは一切アクセスしない）。
- リアルタイム性は不要という判断（あっきーさん明示）のため、GitHub Actionsで1日2回のみ実行する
  （.github/workflows/update-dam-data.yml）。表示側は必ず「○月○日○時時点（速報値）」を明示し、
  リアルタイム値であるかのような誤解を避ける。

## ページ構成（2026-09-04調査。旧来のCGIシステムのため独特の作りになっている）
1. `https://www1.river.go.jp/cgi-bin/DspDamData.exe?ID=<観測所ID>&KIND=3&PAGE=0`
   （観測所ページ。文字コードは EUC-JP）。ここに以下の2つが載っている:
   - 「テキストデータ」ダウンロードリンク（`/dat/dload/download/....dat`。文字コードは
     Shift_JIS。CSV風のプレーンテキストで直近日数ぶんの10分値が並ぶ。**これを最優先で解析する**）
   - `<IFRAME>` 内に同じ期間のHTML表（文字コードは EUC-JP。最新時刻が先頭行）。
     .dat が取得できない時だけこちらをフォールバック解析する
   どちらのURLも観測ページを取得するたびに変わる動的パスなので、毎回まず観測ページ本体を
   取得してリンクを再取得する必要がある（固定URLとしてハードコードできない）。
2. .dat の列は
   `年月日,時刻,流域平均雨量,流域平均雨量属性,貯水量,貯水量属性,流入量,流入量属性,放流量,放流量属性,貯水率,貯水率属性`
   の12列。属性列は `$`=欠測 `-`=未受信（未受信はまだこのタイミングでは値が確定していないだけで、
   0ではない）。**欠測・未受信をそのまま0として扱わないこと**が要件。
   実際に調べた早明浦ダムのデータでは、貯水量・流入量・放流量は10分おきに更新されるが、
   **貯水率だけは毎時00分にしか確定しない**（それ以外の10分刻みの行は `0.0,-` という
   プレースホルダになる）。そのため本スクリプトは「貯水率の属性が有効（未受信/欠測でない）な
   直近の行」を1行選び、その行の日時・貯水量・流入量・放流量・貯水率をまとめて採用する
   （行をまたいで値を混ぜると、表示時刻と値の実体がズレるため）。
3. 貯水率の列は早明浦ダムでは「貯水率」の1列のみ（常時満水位比・制限水位比等の別列は無かった）。
   ただし他ダムやシステム改修で列名が変わる可能性があるため、rateLabel はヘッダー行から
   動的に読み取る（ハードコードしない）。
4. 貯水量の単位はページの単位画像（`tani_1000000m3.png`、alt「×10^3m3」）から千m³
   （＝10^3 m³）と判断した。早明浦ダムの有効貯水容量（約2.89億m³）に対し、観測値
   （例: 29,060 → 29.06百万m³ ≒ 有効容量の約10%）と、同じ行の貯水率（8.3%）がほぼ
   一致することでも裏取りした。万一ページ側の単位表記が変わった場合に備え、この換算は
   本スクリプトでは行わず、.dat に出ている生の数値をそのまま storage に出力する
   （表示側で「千m³」等の単位ラベルを付けるかはindex.html側の判断に委ねる）。

使い方:
    python scripts/fetch_dam.py

失敗時（ネットワークエラー・想定外のページ構造など）は既存の dam-data.js を上書きせず、
非0で終了する。
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urljoin, urlparse

JST = timezone(timedelta(hours=9))

DAM_ID = "1368080700010"
DAM_NAME = "早明浦ダム"
SOURCE_URL = f"https://www1.river.go.jp/cgi-bin/DspDamData.exe?ID={DAM_ID}&KIND=3&PAGE=0"
ALLOWED_HOST = "www1.river.go.jp"
# 貯水量の単位。ページの単位画像(tani_1000000m3.png, alt文字は文字化けしていて機械的に確定
# できない)から千m³（×10^3 m³）と判断した根拠はファイル冒頭のコメント参照。動的抽出が
# 信頼できないため定数として持ち、正しさの判断材料として dam-data.js にも書き出す。
STORAGE_UNIT = "千m³"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
OUTPUT_PATH = os.path.join(REPO_ROOT, "dam-data.js")

# 属性コード（.dat・HTML共通の意味）。$=欠測、-=未受信。どちらも「値が確定していない」ので欠測扱いにする。
INVALID_ATTRS = {"$", "-"}


def guard_url(url: str) -> str:
    """www1.river.go.jp 以外へのアクセスを拒否する。相対URLは絶対URLへ解決してから検証する。"""
    absolute = urljoin(SOURCE_URL, url)
    host = urlparse(absolute).hostname or ""
    if host != ALLOWED_HOST:
        raise SystemExit(f"許可されていないドメインです: {host}（{ALLOWED_HOST} のみ許可）")
    return absolute


def fetch_bytes(url: str) -> bytes:
    url = guard_url(url)
    req = urllib.request.Request(url, headers={"User-Agent": "kotohira-news-dam-fetch/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def decode_fallback(raw: bytes) -> str:
    """旧システムのためページごとに文字コードが違う（EUC-JP・Shift_JISの両方が実在する）。
    複数の候補を順に試し、最初にデコードできたものを使う。"""
    for enc in ("euc-jp", "shift_jis", "utf-8"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    # 最終手段：文字化けを許容してでも処理を継続する（正規表現での数値抽出自体は影響を受けにくい）
    return raw.decode("shift_jis", errors="replace")


def find_dat_link(page_html: str) -> str | None:
    m = re.search(r'href="(/dat/dload/download/[^"]+\.dat)"', page_html)
    return m.group(1) if m else None


def find_iframe_link(page_html: str) -> str | None:
    m = re.search(r'<IFRAME\s+src="([^"]+)"', page_html, re.IGNORECASE)
    return m.group(1) if m else None


def parse_dat(text: str) -> dict[str, Any] | None:
    """テキストデータ(.dat)を解析し、最新の有効な観測値を返す。

    列は年月日,時刻,流域平均雨量,流域平均雨量属性,貯水量,貯水量属性,流入量,流入量属性,
    放流量,放流量属性,貯水率,貯水率属性 の12列（ヘッダーは # 始まりの行に載っている）。
    """
    lines = text.splitlines()
    header_cols: list[str] | None = None
    rows: list[list[str]] = []
    row_re = re.compile(r"^\d{4}/\d{2}/\d{2},\d{2}:\d{2},")
    for line in lines:
        if line.startswith("#年月日"):
            header_cols = line.lstrip("#").split(",")
        elif row_re.match(line):
            rows.append(line.split(","))
    if not rows or not header_cols or len(header_cols) < 12:
        return None

    rate_label = header_cols[10].strip()

    def col(parts: list[str], value_idx: int, attr_idx: int) -> float | None:
        if attr_idx < len(parts) and parts[attr_idx].strip() in INVALID_ATTRS:
            return None
        try:
            return float(parts[value_idx].strip())
        except (ValueError, IndexError):
            return None

    # 貯水率の属性が有効な直近の行を1つ選ぶ（貯水量等より更新頻度が低いため、
    # 単純に最終行を使うと「時刻はあるが貯水率だけ古いプレースホルダ」になってしまう）。
    for parts in reversed(rows):
        if len(parts) < 12:
            continue
        if parts[11].strip() in INVALID_ATTRS:
            continue
        date_part = parts[0].strip().replace("/", "-")
        time_part = parts[1].strip()
        try:
            datetime.strptime(f"{date_part}T{time_part}", "%Y-%m-%dT%H:%M")
        except ValueError:
            continue
        return {
            "observedAt": f"{date_part}T{time_part}",
            "storage": col(parts, 4, 5),
            "inflow": col(parts, 6, 7),
            "outflow": col(parts, 8, 9),
            "rate": col(parts, 10, 11),
            "rateLabel": rate_label,
        }
    return None


def parse_html_table(text: str) -> dict[str, Any] | None:
    """.dat が取得できない場合のフォールバック：IFRAME内のHTML表を解析する。

    表は最新時刻が先頭行。値は <FONT COLOR="#0000FF">値</FONT> で囲まれ、未受信/欠測は
    セルの中身がそのまま "-" になる（別列の属性コードは無い）。
    """
    row_re = re.compile(
        r"<TR>\s*"
        r"<TD[^>]*>(\d{4}/\d{2}/\d{2})</TD>\s*"
        r"<TD[^>]*>(\d{2}:\d{2})</TD>\s*"
        r"<TD[^>]*>(.*?)</TD>\s*"  # 雨量（未使用）
        r"<TD[^>]*>(.*?)</TD>\s*"  # 貯水量
        r"<TD[^>]*>(.*?)</TD>\s*"  # 流入量
        r"<TD[^>]*>(.*?)</TD>\s*"  # 放流量
        r"<TD[^>]*>(.*?)</TD>\s*"  # 貯水率
        r"</TR>",
        re.IGNORECASE | re.DOTALL,
    )

    def cell_value(cell: str) -> float | None:
        cell = cell.strip()
        if cell == "-" or not cell:
            return None
        m = re.search(r">([\d.]+)<", cell) or re.match(r"^([\d.]+)$", cell)
        if not m:
            return None
        try:
            return float(m.group(1))
        except ValueError:
            return None

    for m in row_re.finditer(text):
        date_part, time_part, _rain, storage_cell, inflow_cell, outflow_cell, rate_cell = m.groups()
        rate = cell_value(rate_cell)
        if rate is None:
            continue  # 貯水率が未受信の行はスキップし、値が揃っている直近行を採用する
        try:
            datetime.strptime(f"{date_part}T{time_part}", "%Y/%m/%dT%H:%M")
        except ValueError:
            continue
        return {
            "observedAt": f"{date_part.replace('/', '-')}T{time_part}",
            "storage": cell_value(storage_cell),
            "inflow": cell_value(inflow_cell),
            "outflow": cell_value(outflow_cell),
            "rate": rate,
            "rateLabel": "貯水率",  # HTML表には列見出しテキストが同一ページ内にあるが、
            # フォールバック経路の単純化のため固定値にする（.dat経路が動的取得の主系統）
        }
    return None


def fetch_dam_observation() -> dict[str, Any]:
    page_raw = fetch_bytes(SOURCE_URL)
    page_html = decode_fallback(page_raw)

    dat_link = find_dat_link(page_html)
    if dat_link:
        try:
            dat_raw = fetch_bytes(dat_link)
            parsed = parse_dat(decode_fallback(dat_raw))
            if parsed:
                return parsed
            print("[警告] .datの解析に失敗しました。HTML表のフォールバックを試みます。")
        except Exception as e:
            print(f"[警告] .datの取得に失敗しました（{type(e).__name__}）。HTML表のフォールバックを試みます。")

    iframe_link = find_iframe_link(page_html)
    if not iframe_link:
        raise RuntimeError("観測ページからテキストデータ・IFRAMEのどちらも見つかりませんでした")
    iframe_raw = fetch_bytes(iframe_link)
    parsed = parse_html_table(decode_fallback(iframe_raw))
    if not parsed:
        raise RuntimeError("HTML表の解析にも失敗しました（ページ構造が変わった可能性があります）")
    return parsed


def load_existing() -> str | None:
    if not os.path.exists(OUTPUT_PATH):
        return None
    with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def main() -> None:
    try:
        obs = fetch_dam_observation()
    except Exception as e:
        print(f"[エラー] 早明浦ダムのデータ取得に失敗しました（{type(e).__name__}: {e}）")
        existing = load_existing()
        if existing is not None:
            print("既存の dam-data.js は変更せず保持します。")
        sys.exit(1)

    data = {
        "name": DAM_NAME,
        "observedAt": obs["observedAt"],
        "rate": obs["rate"],
        "rateLabel": obs["rateLabel"],
        "storage": obs["storage"],
        "storageUnit": STORAGE_UNIT,
        "inflow": obs["inflow"],
        "outflow": obs["outflow"],
        "fetchedAt": datetime.now(JST).strftime("%Y-%m-%d %H:%M"),
        "sourceUrl": SOURCE_URL,
    }

    js = "/* 自動生成: scripts/fetch_dam.py が1日2回（GitHub Actions）再生成します。手編集しないでください。\n"
    js += "   早明浦ダムの貯水状況（国交省「川の防災情報」より）。速報値のため、観測時刻を必ず併記して表示すること。 */\n"
    js += "window.DAM_DATA = " + json.dumps(data, ensure_ascii=False, indent=2)
    js += ";\n"

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(js)

    print(f"dam-data.js を書き出しました: {OUTPUT_PATH}")
    print(
        f"観測時刻={obs['observedAt']} 貯水量={obs['storage']} 流入量={obs['inflow']} "
        f"放流量={obs['outflow']} {obs['rateLabel']}={obs['rate']}"
    )


if __name__ == "__main__":
    main()
