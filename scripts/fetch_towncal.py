#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🗓 こんぴらカレンダーの月次更新スクリプト。

月次運用手順:
  1. 琴平町ホームページの広報バックナンバー（https://www.town.kotohira.kagawa.jp/site/kouhou/）
     から対象月の号のページを開き、掲載されているPDF（または個別のカレンダー画像）のURLを控える。
  2. 「こんぴらカレンダー」面が何ページ目かを確認する。単体の号は全ページ一体のPDFのみで配布
     されることが多く、その場合はPDF内でカレンダー面のページ番号を特定して --page で指定する
     （目視、または `python -c "import fitz; ..."` 等でページごとのテキストを抜き出し
     「こんぴらカレンダー」の文字列を検索すると早い）。個別に画像/PDFが分かれていれば --page は不要。
  3. 本スクリプトを実行する:
       python scripts/fetch_towncal.py <PDFまたは画像のURL> <YYYY-MM> [--page N]
     例:
       python scripts/fetch_towncal.py \
         https://www.town.kotohira.kagawa.jp/uploaded/attachment/6212.pdf 2026-09 --page 26
  4. assets/towncal/YYYY-MM.webp が生成され、towncal-data.js の month / image / sourceName が
     自動で書き換わる（sourceUrl はバックナンバー一覧ページに固定のため変更しない）。
  5. 生成された画像を目視で確認する（別ページを誤って取り込んでいないか、文字が判読できるか）。

安全のための制約:
  - ダウンロード先は town.kotohira.kagawa.jp のみを許可する（他ドメインは拒否する）。
  - PDFのページ画像化には PyMuPDF (fitz) が必要。無ければエラーで停止する
    （`pip install pymupdf` はこのスクリプトのための例外的な明示許可。他パッケージは追加しない）。
  - WebPへの圧縮・縮小は scripts/image_utils.py の共通処理（長辺1200px・quality 82）に委ねる。
"""
from __future__ import annotations

import argparse
import re
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

REPO = Path(__file__).resolve().parent.parent
ALLOWED_HOST = "www.town.kotohira.kagawa.jp"
RENDER_DPI = 200  # PDFページの画像化解像度。A4相当でも長辺1200pxへの縮小前提で十分な余裕がある

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


def pdf_page_to_png(pdf_bytes: bytes, page_no: int) -> bytes:
    """1始まりのページ番号でPDFの1ページをPNGバイト列にレンダリングする。"""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise SystemExit(
            "PyMuPDF (fitz) が見つかりません。`pip install pymupdf` を実行してから再度実行してください。"
        )
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    if not (1 <= page_no <= doc.page_count):
        raise SystemExit(f"ページ番号が範囲外です（1〜{doc.page_count}）: {page_no}")
    page = doc[page_no - 1]
    zoom = RENDER_DPI / 72
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    return pix.tobytes("png")


def update_towncal_data(month: str, source_name: str) -> None:
    """towncal-data.js の month / image / sourceName だけを書き換える（sourceUrl等は保持）。"""
    path = REPO / "towncal-data.js"
    text = path.read_text(encoding="utf-8")
    text, n1 = re.subn(r'(month:\s*)"[^"]*"', rf'\1"{month}"', text, count=1)
    text, n2 = re.subn(r'(image:\s*)"[^"]*"', rf'\1"assets/towncal/{month}.webp"', text, count=1)
    text, n3 = re.subn(r'(sourceName:\s*)"[^"]*"', rf'\1"{source_name}"', text, count=1)
    if not (n1 and n2 and n3):
        raise SystemExit("towncal-data.js の month/image/sourceName フィールドが見つかりませんでした。")
    path.write_text(text, encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url", help="カレンダー面のPDFまたは画像のURL（town.kotohira.kagawa.jpのみ許可）")
    ap.add_argument("month", help="対象月 YYYY-MM")
    ap.add_argument("--page", type=int, default=None, help="PDFの場合のページ番号（1始まり）")
    args = ap.parse_args()

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

    webp = compress_to_webp(raw)
    if webp is None:
        raise SystemExit("WebPへの変換に失敗しました（Pillow未導入、または元データが不正です）。")

    out_dir = REPO / "assets" / "towncal"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{args.month}.webp"
    out_path.write_bytes(webp)
    print(f"保存しました: {out_path} ({len(webp):,} bytes)")

    m = re.match(r"^(\d{4})-(\d{2})$", args.month)
    source_name = f"広報ことひら {int(m.group(1))}年{int(m.group(2))}月号"
    update_towncal_data(args.month, source_name)
    print(f"towncal-data.js を更新しました（month={args.month}, sourceName={source_name}）")


if __name__ == "__main__":
    main()
