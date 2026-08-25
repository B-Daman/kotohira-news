#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""assets/ の既存画像をWebPへ一括変換する一回性スクリプト。

fetch_notion.py は取得時に圧縮するようになったが、それ以前に保存された画像は
未圧縮のまま残る（数MBのPNG等）。このスクリプトはそれらをまとめて変換する。

対象は assets/thumbs/（Notion由来）と assets/manual/（手動配置）の2つ。

方針:
- 元ファイルは削除しない。<name>.png の隣に <name>.webp を作るだけ。
  変換後に不要になった元ファイルの一覧を scripts/unused-images.txt に書き出すので、
  中身を確認したうえで削除するかどうかは利用者が判断する。
- 参照側のパスも .webp に書き換える:
  - notion-data.js / site-widgets-data.js の画像パス
  - assets/image-overrides.json のファイル名（assets/manual/ の対応表）
  fetch_notion.py の find_local_thumb は .webp を優先するため、次回の自動更新でも
  同じパスが生成される（生成物と食い違わない）。
- 元から .webp のファイルは、長辺が MAX_EDGE を超えるものだけ同名のまま縮小する
  （元ファイルが残らないので削除の判断が不要。何度実行しても結果は同じ）。

使い方:
    python scripts/compress_thumbs.py --dry-run   # 変換せず結果だけ表示
    python scripts/compress_thumbs.py             # 実行
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from image_utils import MAX_EDGE, compress_to_webp, pillow_available  # noqa: E402

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
TARGET_DIRS = ("assets/thumbs", "assets/manual")
# 画像パスを持つデータファイル。notion-data.js は生成物だが、置換後のパスは
# find_local_thumb が返す値と一致するため次回生成でも変わらない。
DATA_FILES = ("notion-data.js", "site-widgets-data.js")
OVERRIDES_PATH = os.path.join(REPO_ROOT, "assets", "image-overrides.json")
UNUSED_LIST_PATH = os.path.join(SCRIPT_DIR, "unused-images.txt")

CONVERT_EXTENSIONS = (".jpg", ".jpeg", ".png")


def human(size: int) -> str:
    """バイト数を読みやすい単位にする。"""
    if size >= 1024 * 1024:
        return f"{size / 1024 / 1024:.1f}MB"
    return f"{size / 1024:.0f}KB"


def needs_resize(data: bytes) -> bool:
    """長辺が MAX_EDGE を超えているか（既に縮小済みなら False）。"""
    try:
        from PIL import Image

        with Image.open(io.BytesIO(data)) as img:
            return max(img.size) > MAX_EDGE
    except Exception:
        return False


def convert_one(path: str, dry_run: bool) -> tuple[int, int, str] | None:
    """1ファイルを変換する。(変換前, 変換後, 出力パス) を返す。

    変換しなかった場合は None。
    """
    base, ext = os.path.splitext(path)
    ext = ext.lower()

    if ext == ".webp":
        out_path = path  # 同名で上書きするので元ファイルは残らない
    elif ext in CONVERT_EXTENSIONS:
        out_path = base + ".webp"
        if os.path.exists(out_path):
            return None  # 変換済み
    else:
        return None

    with open(path, "rb") as f:
        data = f.read()

    # 既に縮小済みのWebPを再圧縮すると劣化するだけなので触らない
    if ext == ".webp" and not needs_resize(data):
        return None

    compressed = compress_to_webp(data)
    if compressed is None:
        return None

    if not dry_run:
        with open(out_path, "wb") as f:
            f.write(compressed)
    return len(data), len(compressed), out_path


def rewrite_data_files(renames: dict[str, str], dry_run: bool) -> int:
    """データファイル内の画像パスを .webp へ置き換える。置換件数を返す。"""
    if not renames:
        return 0
    replaced = 0
    for filename in DATA_FILES:
        path = os.path.join(REPO_ROOT, filename)
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        hits = 0
        for old_ref, new_ref in renames.items():
            count = text.count(old_ref)
            if count:
                text = text.replace(old_ref, new_ref)
                hits += count

        if hits and not dry_run:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
        replaced += hits
    return replaced


def find_unused_originals() -> list[str]:
    """変換済みで参照されなくなった元画像を、ディスクの状態から洗い出す。

    同じ名前の .webp がある .jpg/.jpeg/.png が対象。実行履歴ではなく現在の
    ファイル配置から導くため、複数回に分けて実行しても一覧が欠けない。
    """
    unused: list[str] = []
    for rel_dir in TARGET_DIRS:
        abs_dir = os.path.join(REPO_ROOT, rel_dir)
        if not os.path.isdir(abs_dir):
            continue
        for name in sorted(os.listdir(abs_dir)):
            base, ext = os.path.splitext(name)
            if ext.lower() not in CONVERT_EXTENSIONS:
                continue
            if os.path.exists(os.path.join(abs_dir, base + ".webp")):
                unused.append(f"{rel_dir}/{name}")
    return unused


def rewrite_overrides(renames: dict[str, str], dry_run: bool) -> int:
    """image-overrides.json のファイル名を .webp へ置き換える。置換件数を返す。

    値は assets/manual/ 内のファイル名（パスなし）で持っているため、
    ファイル名だけを見て対応付ける。
    """
    if not renames or not os.path.exists(OVERRIDES_PATH):
        return 0
    manual_map = {
        os.path.basename(old): os.path.basename(new)
        for old, new in renames.items()
        if old.startswith("assets/manual/")
    }
    if not manual_map:
        return 0

    with open(OVERRIDES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    hits = 0
    for key, value in list(data.items()):
        if str(key).startswith("_"):
            continue
        if value in manual_map:
            data[key] = manual_map[value]
            hits += 1

    if hits and not dry_run:
        with open(OVERRIDES_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(description="assets の画像をWebPへ一括変換する")
    parser.add_argument(
        "--dry-run", action="store_true", help="変換せず結果の見込みだけ表示する"
    )
    args = parser.parse_args()

    if not pillow_available():
        print("[エラー] Pillow が必要です: python -m pip install Pillow")
        return 1

    total_before = 0
    total_after = 0
    converted = 0
    scanned = 0
    renames: dict[str, str] = {}

    for rel_dir in TARGET_DIRS:
        abs_dir = os.path.join(REPO_ROOT, rel_dir)
        if not os.path.isdir(abs_dir):
            continue
        for name in sorted(os.listdir(abs_dir)):
            ext = os.path.splitext(name)[1].lower()
            if ext not in CONVERT_EXTENSIONS + (".webp",):
                continue
            scanned += 1
            path = os.path.join(abs_dir, name)
            result = convert_one(path, args.dry_run)
            if result is None:
                size = os.path.getsize(path)
                total_before += size
                total_after += size
                continue
            before, after, out_path = result
            converted += 1
            total_before += before
            total_after += after
            out_name = os.path.basename(out_path)
            if out_name != name:
                renames[f"{rel_dir}/{name}"] = f"{rel_dir}/{out_name}"
            print(f"  {rel_dir}/{name:<44} {human(before):>8} -> {human(after):>8}")

    unused = find_unused_originals()

    replaced = rewrite_data_files(renames, args.dry_run)
    overrides_hits = rewrite_overrides(renames, args.dry_run)

    if unused and not args.dry_run:
        with open(UNUSED_LIST_PATH, "w", encoding="utf-8") as f:
            f.write(
                "# compress_thumbs.py の変換で使われなくなった元画像。\n"
                "# 中身を確認したうえで削除するかどうかを判断してください。\n"
            )
            for rel_path in unused:
                f.write(f"{rel_path}\n")

    prefix = "[dry-run] " if args.dry_run else ""
    print()
    print(f"{prefix}変換: {converted}件 / 対象 {scanned}件")
    print(
        f"{prefix}合計: {human(total_before)} -> {human(total_after)}"
        f"（{human(total_before - total_after)} 削減）"
    )
    print(f"{prefix}データファイルのパス置換: {replaced}件")
    print(f"{prefix}image-overrides.json の更新: {overrides_hits}件")
    if unused:
        print(
            f"{prefix}未使用になった元画像: {len(unused)}件"
            + ("" if args.dry_run else f" → 一覧: {UNUSED_LIST_PATH}")
        )
        print("  ※ このスクリプトはファイルを削除しません。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
