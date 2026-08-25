#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""サムネイル画像をWebPへ縮小・再エンコードする共通処理。

fetch_notion.py（取得時の圧縮）と compress_thumbs.py（既存画像の一括変換）
の両方から使う。

Pillow が無い環境では compress_to_webp が None を返し、呼び出し側は元データを
そのまま保存する。fetch_notion.py の「標準ライブラリのみで動く」性質を壊さず、
Pillow がある時だけ圧縮が効く形にしている。
"""

from __future__ import annotations

import io

# 表示は 16/9 の object-fit:cover で、最も大きいモーダルでも実寸1000px程度。
# 長辺1200pxの箱に収めれば高解像度ディスプレイでも足りる。
MAX_EDGE = 1200
WEBP_QUALITY = 82


def pillow_available() -> bool:
    """Pillow が import できるか。"""
    try:
        import PIL  # noqa: F401
    except ImportError:
        return False
    return True


def _to_supported_mode(img):  # type: ignore[no-untyped-def]
    """WebP で保存できるモード（RGB / RGBA）へ揃える。"""
    if img.mode in ("RGB", "RGBA"):
        return img
    has_alpha = img.mode in ("LA", "PA") or (
        img.mode == "P" and "transparency" in img.info
    )
    return img.convert("RGBA" if has_alpha else "RGB")


def compress_to_webp(
    data: bytes, max_edge: int = MAX_EDGE, quality: int = WEBP_QUALITY
) -> bytes | None:
    """画像バイト列を縮小してWebPへ再エンコードし、バイト列を返す。

    長辺が max_edge を超える場合だけ縮小する。次のいずれかに当てはまる場合は
    None を返し、呼び出し側は元データをそのまま使う:
    Pillow が無い／デコードできない／複数フレーム（アニメーション）／
    再エンコードしても元より小さくならない。
    """
    try:
        from PIL import Image, ImageOps
    except ImportError:
        return None

    try:
        img = Image.open(io.BytesIO(data))
        # アニメーションは1フレーム目だけになってしまうため対象外にする
        if getattr(img, "n_frames", 1) > 1:
            return None
        img = ImageOps.exif_transpose(img)
        img = _to_supported_mode(img)
        width, height = img.size
        longest = max(width, height)
        if longest > max_edge:
            scale = max_edge / longest
            img = img.resize(
                (max(1, round(width * scale)), max(1, round(height * scale))),
                Image.LANCZOS,
            )
        buf = io.BytesIO()
        img.save(buf, "WEBP", quality=quality, method=6)
    except Exception:
        return None

    out = buf.getvalue()
    if not out or len(out) >= len(data):
        return None
    return out
