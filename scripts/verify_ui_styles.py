#!/usr/bin/env python3
"""UI変更の検証用: 390px幅で index.html を描画し、指定セレクタの算出スタイルを実測する。

CSSの宣言が無効だと書いた値は反映されない（2026-08-28の font:...inherit 事件）。
スクリーンショットの見た目ではなく getComputedStyle の実測値で、
「書いた値 = ブラウザが実際に使う値」を確認するためのスクリプト。

使い方:
  python scripts/verify_ui_styles.py ".drawer-link" ".drawer-group-toggle"
  python scripts/verify_ui_styles.py --props font-size,font-weight,display ".carousel-arrow"

前提: Google Chrome がローカルにあること。ネットワーク不要（file://で描画）。
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
REPO = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("selectors", nargs="+", help="計測するCSSセレクタ")
    ap.add_argument("--props", default="font-size,font-weight,font-family,line-height,display",
                    help="カンマ区切りの計測プロパティ")
    ap.add_argument("--width", type=int, default=390, help="ビューポート幅（既定390）")
    ap.add_argument("--page", default="index.html", help="対象ページ（リポジトリ相対）")
    args = ap.parse_args()

    props = [p.strip() for p in args.props.split(",") if p.strip()]
    probe = f"""
<script>
setTimeout(() => {{
  const sels = {json.dumps(args.selectors)};
  const props = {json.dumps(props)};
  const out = {{}};
  for (const sel of sels) {{
    const el = document.querySelector(sel);
    if (!el) {{ out[sel] = null; continue; }}
    const cs = getComputedStyle(el);
    out[sel] = Object.fromEntries(props.map(p => [p, cs.getPropertyValue(p)]));
  }}
  document.title = "STYLEPROBE:" + JSON.stringify(out);
}}, 3000);
</script>"""

    html = (REPO / args.page).read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as td:
        # 相対パスのデータJSを確実に解決するため、プローブ用コピーはリポジトリ直下に置く
        # （tmp-プレフィックスは.gitignore外の使い捨てファイル。毎回上書きされる）
        probe_page = REPO / "tmp-style-probe.html"
        probe_page.write_text(html.replace("</body>", probe + "</body>", 1), encoding="utf-8")
        frame = REPO / "tmp-style-frame.html"
        frame.write_text(
            f'<!DOCTYPE html><html><head><meta charset="UTF-8"></head><body style="margin:0">'
            f'<iframe src="{probe_page.as_uri()}" width="{args.width}" height="800" '
            f'onload="var f=this;setInterval(()=>{{try{{document.title=f.contentDocument.title}}catch(e){{}}}},500)">'
            f"</iframe></body></html>", encoding="utf-8")
        result = subprocess.run(
            [CHROME, "--headless=new", "--disable-gpu", "--allow-file-access-from-files",
             f"--user-data-dir={td}\\profile", "--virtual-time-budget=15000",
             "--dump-dom", frame.as_uri()],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        m = re.search(r"STYLEPROBE:(\{.*?\})</title>", result.stdout)
        if not m:
            print("計測失敗: プローブ結果がタイトルに載っていません。", file=sys.stderr)
            sys.exit(2)
        data = json.loads(m.group(1))
        for sel, vals in data.items():
            if vals is None:
                print(f"[NOT FOUND] {sel}")
                continue
            print(f"{sel}")
            for k, v in vals.items():
                print(f"  {k}: {v}")
        # 要素が見つからなかったセレクタがあれば異常終了にする
        sys.exit(1 if any(v is None for v in data.values()) else 0)


if __name__ == "__main__":
    main()
