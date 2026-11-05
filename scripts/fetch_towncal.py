#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🗓 こんぴらカレンダーの月次更新スクリプト。

自動（2026-11-05〜・GitHub Actions の update-notion-data.yml から呼ばれる）:
    python scripts/fetch_towncal.py --auto [--dry-run]
  広報一覧（https://www.town.kotohira.kagawa.jp/site/kouhou/）から「広報ことひら○月号」を拾い、
  towncal-data.js の issues[] に無い新しい号があれば、号のページのPDF/画像からカレンダー面を
  取り込んで issues[] に追加する。
    - 年は号のページの「YYYY年M月号」から決める（一覧に年が無いため）
    - リンク文字列に「カレンダー」を含む個別ファイルがあればそれを使い、無ければ全ページ一体のPDFを使う
    - 一体PDFでは、本文に「こんぴらカレンダー」と「相談日」の両方を含むページを探す。
      1ページに決まらなければ失敗（非ゼロ終了・何も取り込まない）
    - --dry-run は判定結果（号・PDF URL・ページ番号）だけ表示して何も書かない
  判定に迷う場合は取り込まずに失敗する。誤った面を載せた月は下の手動の手順で直す。

手動（従来どおり。自動が失敗した月の補修用）:
  1. 広報バックナンバー（https://www.town.kotohira.kagawa.jp/site/kouhou/）から対象月の号のページを開き、
     PDF（または個別のカレンダー画像）のURLを控える。
  2. 「こんぴらカレンダー」面が何ページ目かを確認する（`--auto --dry-run` の出力でも分かる）。
  3. 実行する:
       python scripts/fetch_towncal.py <PDFまたは画像のURL> <YYYY-MM> [--page N]
     例:
       python scripts/fetch_towncal.py \
         https://www.town.kotohira.kagawa.jp/uploaded/attachment/6212.pdf 2026-09 --page 26
  4. assets/towncal/YYYY-MM.webp が生成され、towncal-data.js の issues[] に同じ月があれば差し替え、
     無ければ追加される（sourceUrl はバックナンバー一覧ページに固定のため変更しない）。
  5. 生成された画像を目視で確認する（別ページを誤って取り込んでいないか、文字が判読できるか）。

安全のための制約:
  - ダウンロード先は town.kotohira.kagawa.jp のみを許可する（他ドメインは拒否する）。
  - PDFのページ画像化には PyMuPDF (fitz) が必要。無ければエラーで停止する
    （requirements-towncal.txt に pymupdf と pillow を置いている。他パッケージは追加しない）。
  - WebPへの圧縮・縮小は scripts/image_utils.py の共通処理（長辺1200px・quality 82）に委ねる。
"""
from __future__ import annotations

import argparse
import re
import sys
import urllib.request
from html import unescape
from pathlib import Path
from urllib.parse import urljoin, urlparse

REPO = Path(__file__).resolve().parent.parent
ALLOWED_HOST = "www.town.kotohira.kagawa.jp"
INDEX_URL = "https://www.town.kotohira.kagawa.jp/site/kouhou/"
RENDER_DPI = 200  # PDFページの画像化解像度。A4相当でも長辺1200pxへの縮小前提で十分な余裕がある
KEYWORDS = ("こんぴらカレンダー", "相談日")  # 一体PDFでカレンダー面を決める語（全部を含むページ）
MAX_ISSUE_PAGES = 4  # 一覧から号のページを開く最大数（一覧の上から）

sys.path.insert(0, str(Path(__file__).resolve().parent))
from image_utils import compress_to_webp  # noqa: E402


def guard_url(url: str) -> None:
    """town.kotohira.kagawa.jp 以外のURLへのダウンロードを拒否する。"""
    host = urlparse(url).hostname or ""
    if host != ALLOWED_HOST:
        raise SystemExit(f"許可されていないドメインです: {host}（{ALLOWED_HOST} のみ許可）")


def download(url: str) -> bytes:
    guard_url(url)
    req = urllib.request.Request(url, headers={"User-Agent": "kotohira-news-towncal-fetch/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def download_text(url: str) -> str:
    return download(url).decode("utf-8", errors="replace")


def open_pdf(pdf_bytes: bytes):  # type: ignore[no-untyped-def]
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise SystemExit(
            "PyMuPDF (fitz) が見つかりません。`pip install -r requirements-towncal.txt` を実行してから再度実行してください。"
        )
    return fitz.open(stream=pdf_bytes, filetype="pdf")


def render_page(doc, page_no: int) -> bytes:  # type: ignore[no-untyped-def]
    """1始まりのページ番号でPDFの1ページをPNGバイト列にレンダリングする。"""
    import fitz

    if not (1 <= page_no <= doc.page_count):
        raise SystemExit(f"ページ番号が範囲外です（1〜{doc.page_count}）: {page_no}")
    zoom = RENDER_DPI / 72
    pix = doc[page_no - 1].get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    return pix.tobytes("png")


def pdf_page_to_png(pdf_bytes: bytes, page_no: int) -> bytes:
    return render_page(open_pdf(pdf_bytes), page_no)


# ---- towncal-data.js の issues[] ----------------------------------------------------------
ISSUE_RE = re.compile(
    r'\{\s*month:\s*"(\d{4}-\d{2})"\s*,\s*image:\s*"([^"]*)"\s*,\s*sourceName:\s*"([^"]*)"\s*\}'
)
ISSUES_BLOCK_RE = re.compile(r"(issues:\s*\[)(.*?)(\n\s*\])", re.S)


def read_issues(data_path: Path) -> list[dict]:
    text = data_path.read_text(encoding="utf-8")
    m = ISSUES_BLOCK_RE.search(text)
    if not m:
        raise SystemExit(f"{data_path.name} の issues[] が見つかりませんでした。")
    return [{"month": a, "image": b, "sourceName": c} for a, b, c in ISSUE_RE.findall(m.group(2))]


def source_name_for(month: str) -> str:
    y, mo = month.split("-")
    return f"広報ことひら {int(y)}年{int(mo)}月号"


def upsert_issue(data_path: Path, month: str) -> None:
    """issues[] に号を追加（同じ月があれば差し替え）。新しい順に並べ直して書き戻す。sourceUrl等は保持。"""
    text = data_path.read_text(encoding="utf-8")
    m = ISSUES_BLOCK_RE.search(text)
    if not m:
        raise SystemExit(f"{data_path.name} の issues[] が見つかりませんでした。")
    issues = {i["month"]: i for i in read_issues(data_path)}
    issues[month] = {"month": month, "image": f"assets/towncal/{month}.webp", "sourceName": source_name_for(month)}
    lines = [
        f'    {{ month: "{i["month"]}", image: "{i["image"]}", sourceName: "{i["sourceName"]}" }}'
        for i in sorted(issues.values(), key=lambda x: x["month"], reverse=True)
    ]
    block = m.group(1) + "\n" + ",\n".join(lines) + m.group(3)
    data_path.write_text(text[: m.start()] + block + text[m.end():], encoding="utf-8")


# ---- 画像の保存 ---------------------------------------------------------------------------
def save_webp(raw_image: bytes, month: str, out_dir: Path) -> Path:
    webp = compress_to_webp(raw_image)
    if webp is None:
        raise SystemExit("WebPへの変換に失敗しました（Pillow未導入、または元データが不正です）。")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{month}.webp"
    out_path.write_bytes(webp)
    print(f"保存しました: {out_path} ({len(webp):,} bytes)")
    return out_path


# ---- 自動取り込み -------------------------------------------------------------------------
def strip_tags(s: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", "", s))).strip()


def anchors(html: str) -> list[tuple[str, str]]:
    """(href, 表示文字列) の一覧。"""
    return [(unescape(h), strip_tags(t)) for h, t in re.findall(r'<a\s[^>]*?href="([^"]*)"[^>]*>(.*?)</a>', html, re.S)]


def list_issue_links(index_html: str) -> list[tuple[int, str]]:
    """広報一覧から (月, 号ページURL) を一覧の出現順に返す（URLの重複は除く）。"""
    seen: set[str] = set()
    out: list[tuple[int, str]] = []
    for href, label in anchors(index_html):
        m = re.search(r"広報ことひら\s*(\d{1,2})月号", label)
        if not m:
            continue
        url = urljoin(INDEX_URL, href)
        if url in seen:
            continue
        seen.add(url)
        out.append((int(m.group(1)), url))
    return out


def resolve_issue_month(link_month: int, page_html: str) -> str:
    """号のページ本文の「YYYY年M月号」から YYYY-MM を決める。リンクの月と一致する表記だけを採る。"""
    years = {int(y) for y, mo in re.findall(r"(\d{4})年\s*(\d{1,2})月号", strip_tags(page_html)) if int(mo) == link_month}
    if len(years) != 1:
        raise SystemExit(f"号のページから{link_month}月号の年を一意に決められません（候補: {sorted(years)}）。")
    return f"{years.pop()}-{link_month:02d}"


def find_file_link(page_html: str, page_url: str, month: str) -> tuple[str, str]:
    """号のページから取り込むファイルを選ぶ。戻り値は (URL, 種別 'cal'=個別カレンダー / 'whole'=一体PDF)。"""
    files = [(urljoin(page_url, h), t) for h, t in anchors(page_html) if re.search(r"\.(pdf|jpe?g|png)(\?|$)", h, re.I)]
    files = [(u, t) for u, t in files if urlparse(u).hostname == ALLOWED_HOST]
    cal = [u for u, t in files if "カレンダー" in t]
    if len(set(cal)) == 1:
        return cal[0], "cal"
    if len(set(cal)) > 1:
        raise SystemExit(f"{month}: 「カレンダー」を含むファイルが複数あり決められません: {sorted(set(cal))}")
    pdfs = sorted({u for u, t in files if u.lower().split("?")[0].endswith(".pdf")})
    if len(pdfs) == 1:
        return pdfs[0], "whole"
    if not pdfs:
        raise SystemExit(f"{month}: 号のページにPDF/画像のリンクが見つかりません。")
    raise SystemExit(f"{month}: PDFが複数あり一体PDFを決められません: {pdfs}")


def find_calendar_page(doc) -> int:  # type: ignore[no-untyped-def]
    """本文に KEYWORDS を全部含むページ（1始まり）を返す。1ページに決まらなければ失敗。"""
    hits = []
    for i in range(doc.page_count):
        text = re.sub(r"\s+", "", doc[i].get_text())
        if all(k in text for k in KEYWORDS):
            hits.append(i + 1)
    if len(hits) != 1:
        raise SystemExit(f"カレンダー面のページを一意に決められません（{'・'.join(KEYWORDS)} を含むページ: {hits or 'なし'}）。")
    return hits[0]


def auto(data_path: Path, out_dir: Path, dry_run: bool, index_url: str) -> None:
    existing = [i["month"] for i in read_issues(data_path)]
    latest = max(existing) if existing else ""
    links = list_issue_links(download_text(index_url))
    if not links:
        raise SystemExit("広報一覧から「広報ことひら○月号」のリンクが1つも見つかりません（ページ構造が変わった可能性）。")

    candidates: list[tuple[str, str]] = []  # (YYYY-MM, 号ページURL)
    for link_month, page_url in links[:MAX_ISSUE_PAGES]:
        candidates.append((resolve_issue_month(link_month, download_text(page_url)), page_url))
    candidates.sort(reverse=True)

    targets = [(m, u) for m, u in candidates if m not in existing and m > latest]
    if not targets:
        print(f"新しい号なし（最新 {latest or 'なし'} は保存済み）")
        return

    for month, page_url in targets:  # 新しい号から
        print(f"対象: {month}  号ページ: {page_url}")
        file_url, kind = find_file_link(download_text(page_url), page_url, month)
        raw = download(file_url)
        page_no = None
        if raw[:4] == b"%PDF":
            doc = open_pdf(raw)
            if kind == "cal" and doc.page_count == 1:
                page_no = 1
            else:
                page_no = find_calendar_page(doc)
            print(f"  ファイル: {file_url}  種別: {'個別カレンダー' if kind == 'cal' else '一体PDF'}  全{doc.page_count}ページ  カレンダー面: p{page_no}")
            if dry_run:
                continue
            image = render_page(doc, page_no)
        else:
            print(f"  ファイル: {file_url}  種別: 画像")
            if dry_run:
                continue
            image = raw
        save_webp(image, month, out_dir)
        upsert_issue(data_path, month)
        print(f"{data_path.name} の issues[] に {month} を追加しました（sourceName={source_name_for(month)}）")
    if dry_run:
        print("（--dry-run: 何も書いていません）")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url", nargs="?", help="[手動] カレンダー面のPDFまたは画像のURL（town.kotohira.kagawa.jpのみ許可）")
    ap.add_argument("month", nargs="?", help="[手動] 対象月 YYYY-MM")
    ap.add_argument("--page", type=int, default=None, help="[手動] PDFの場合のページ番号（1始まり）")
    ap.add_argument("--auto", action="store_true", help="広報一覧から新しい号を見つけて取り込む")
    ap.add_argument("--dry-run", action="store_true", help="[--auto] 判定結果だけ表示して何も書かない")
    ap.add_argument("--data", type=Path, default=REPO / "towncal-data.js", help="towncal-data.js のパス（検証用に差し替え可）")
    ap.add_argument("--out-dir", type=Path, default=REPO / "assets" / "towncal", help="画像の保存先（検証用に差し替え可）")
    ap.add_argument("--index-url", default=INDEX_URL, help=argparse.SUPPRESS)
    args = ap.parse_args()

    if args.auto:
        auto(args.data, args.out_dir, args.dry_run, args.index_url)
        return

    if not args.url or not args.month:
        ap.error("手動実行は <url> <YYYY-MM> が必要です（自動は --auto）。")
    if not re.match(r"^\d{4}-\d{2}$", args.month):
        raise SystemExit(f"month は YYYY-MM 形式で指定してください: {args.month}")

    print(f"ダウンロード中: {args.url}")
    raw = download(args.url)

    is_pdf = args.url.lower().endswith(".pdf") or raw[:4] == b"%PDF"
    if is_pdf:
        if args.page is None:
            raise SystemExit("PDFの場合は --page でカレンダー面のページ番号を指定してください。")
        print(f"PDF {args.page}ページ目を画像化中...")
        raw = pdf_page_to_png(raw, args.page)

    save_webp(raw, args.month, args.out_dir)
    upsert_issue(args.data, args.month)
    print(f"{args.data.name} を更新しました（month={args.month}, sourceName={source_name_for(args.month)}）")


if __name__ == "__main__":
    main()
