# -*- coding: utf-8 -*-
"""
SNS 導線の中継ページ生成（pip依存なし・2026-11-03 追加）

  routes.json                 … 正本（行き先・出どころ・置いた導線の一覧）。手で編集する
  go/{dest}/{src}/index.html  … 生成物（直接編集しない。次回ビルドで上書きされる）

中継ページは「{行き先} へ移動します」の1画面で、1.2秒後に行き先へ自動で転送する。
出どころをパスで分けているので、Cloudflare Web Analytics のページ別閲覧数がそのまま
「その出どころから何人押したか」になる（sns-hub collectors/site.mjs の topPages で集計）。
即時の 302 転送（_redirects）だと計測ビーコンが飛ばないので、静的 HTML ＋ JS の遅延転送にしている。

設計: SecondBrain/03_Resources/agent-outputs/activity-os-map/plan/2026-10-31_SNS導線設計_v1.md §3・§7-3

使い方:
  python scripts/build_routes.py          生成（既存ファイルは上書き。削除はしない）
  python scripts/build_routes.py --list   生成せず、置き場ごとの URL 一覧を表で出す（本人作業用）
"""
import json
import os
import sys
from html import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROUTES_PATH = os.path.join(ROOT, "routes.json")
OUT_DIR = os.path.join(ROOT, "go")

TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<!-- 生成物: scripts/build_routes.py が routes.json から作る。直接編集しない。
     出どころ: {src_label} → 行き先: {dest_name}
     {delay_ms} ms 後に自動転送（Cloudflare Web Analytics のビーコンが先に飛ぶ時間を確保）。 -->
<meta name="robots" content="noindex, nofollow">
<meta name="referrer" content="origin">
<title>{dest_name} へ移動します｜ことひらいふ</title>
<meta property="og:type" content="website">
<meta property="og:site_name" content="ことひらいふ">
<meta property="og:title" content="{og_title}">
<meta property="og:description" content="{who} {what}">
<meta property="og:url" content="{page_url}">
<meta property="og:image" content="{og_image}">
<meta name="twitter:card" content="summary_large_image">
<meta http-equiv="refresh" content="{refresh_sec}; url={dest_url}">
<style>
  :root {{ --bg:#faf8f3; --text:#2b2b2b; --muted:#6b6b6b; --accent:#b23a3a; --card:#ffffff; --border:#e8e3d8; }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; min-height:100vh; display:flex; align-items:center; justify-content:center; padding:24px 16px;
          font-family:"Hiragino Kaku Gothic ProN","Yu Gothic UI","Meiryo",system-ui,sans-serif; background:var(--bg); color:var(--text); line-height:1.7; }}
  .card {{ width:100%; max-width:520px; background:var(--card); border:1px solid var(--border); border-radius:16px; padding:28px 24px; text-align:center; }}
  .brand {{ font-size:12px; letter-spacing:.08em; color:var(--muted); margin-bottom:10px; }}
  h1 {{ font-size:20px; margin:0 0 10px; line-height:1.4; }}
  .who {{ font-weight:700; margin:0 0 4px; }}
  .what {{ color:var(--muted); font-size:14px; margin:0 0 18px; }}
  .btn {{ display:inline-block; background:var(--accent); color:#fff; text-decoration:none; font-weight:700; padding:12px 24px; border-radius:999px; font-size:15px; }}
  .btn:hover {{ opacity:.9; }}
  .note {{ font-size:12px; color:var(--muted); margin:14px 0 0; }}
</style>
</head>
<body>
<main class="card">
  <div class="brand">ことひらいふ</div>
  <h1>{dest_name} へ移動します</h1>
  <p class="who">{who}</p>
  <p class="what">{what}</p>
  <a class="btn" id="go" href="{dest_url}" rel="noopener">{button}</a>
  <p class="note">自動的に切り替わらない場合は、上のボタンを押してください。</p>
</main>
<script>
  // 計測ビーコンが先に飛ぶよう少し待ってから転送する。履歴に中継ページを残さない（replace）。
  setTimeout(function () {{ location.replace({dest_url_js}); }}, {delay_ms});
</script>
</body>
</html>
"""


def load_routes():
    with open(ROUTES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def page_path(dest, src):
    return "/go/%s/%s/" % (dest, src)


def build(cfg):
    origin = cfg["site_origin"].rstrip("/")
    delay = int(cfg.get("delay_ms", 1200))
    written = []
    for r in cfg["routes"]:
        dest, src = r["dest"], r["src"]
        if dest not in cfg["dests"]:
            raise SystemExit("routes.json: 未定義の dest '%s'" % dest)
        if src not in cfg["srcs"]:
            raise SystemExit("routes.json: 未定義の src '%s'" % src)
        d = cfg["dests"][dest]
        path = page_path(dest, src)
        html = TEMPLATE.format(
            src_label=escape(cfg["srcs"][src]),
            dest_name=escape(d["name"]),
            og_title=escape(d["name"] if dest == "site" else d["name"] + "｜ことひらいふ"),
            who=escape(d.get("who", "")),
            what=escape(d.get("what", "")),
            button=escape(d.get("button", d["name"] + " を開く")),
            dest_url=escape(d["url"], quote=True),
            dest_url_js=json.dumps(d["url"]),
            page_url=escape(origin + path, quote=True),
            og_image=escape(cfg.get("og_image", origin + "/assets/brand/og-image.jpg"), quote=True),
            delay_ms=delay,
            refresh_sec=max(2, (delay // 1000) + 2),
        )
        out = os.path.join(OUT_DIR, dest, src, "index.html")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write(html)
        written.append(path)
    # routes.json に無いが go/ に残っているページは警告だけ（削除はしない）
    known = set(written)
    if os.path.isdir(OUT_DIR):
        for dest in sorted(os.listdir(OUT_DIR)):
            dpath = os.path.join(OUT_DIR, dest)
            if not os.path.isdir(dpath):
                continue
            for src in sorted(os.listdir(dpath)):
                p = page_path(dest, src)
                if os.path.isdir(os.path.join(dpath, src)) and p not in known:
                    print("[build_routes] 注意: routes.json に無いページが残っています: %s" % p)
    return written


def list_table(cfg):
    origin = cfg["site_origin"].rstrip("/")
    print("| 置き場（出どころ） | 行き先 | 貼る URL | 置いた日 | メモ |")
    print("|---|---|---|---|---|")
    for r in cfg["routes"]:
        d = cfg["dests"][r["dest"]]
        print("| %s | %s | `%s%s` | %s | %s |" % (
            cfg["srcs"][r["src"]], d["name"], origin, page_path(r["dest"], r["src"]),
            r.get("placed") or "未", r.get("note", "")))


def main():
    cfg = load_routes()
    if "--list" in sys.argv[1:]:
        list_table(cfg)
        return
    written = build(cfg)
    print("[build_routes] 生成: %d ページ" % len(written))
    for p in written:
        print("  " + p)


if __name__ == "__main__":
    main()
