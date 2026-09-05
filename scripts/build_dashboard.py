# -*- coding: utf-8 -*-
"""
開発ダッシュボードのビルド（pip依存なし）

  docs/開発ダッシュボード.base.html   … 手編集する正本（前半の編集済みタブ＋注入マーカー）
  docs/開発ダッシュボード.html        … 生成物（直接編集しない。次回ビルドで上書きされる）

base 内のマーカーを、原本ファイルをHTML化した内容で置き換えて生成物を書き出す。
kotobus/shift-scheduler の「sekkei.base.html ＋ build.js」方式を Python で再現したもの。

使い方:
  python scripts/build_dashboard.py

base 側で使えるマーカー（パスはリポジトリ直下からの相対）:
  <!--@MD docs/ロードマップ.md-->             Markdown を HTML 化して節（.section-title ＋ .doc）として注入
  <!--@CODE .github/workflows/update-dam-data.yml-->   テキストファイルをコードブロックとして注入
  <!--@BUILT-->                                ビルド日時（YYYY-MM-DD HH:MM）
  <!--@MTIME docs/要件定義書.md-->              ファイルの更新日（YYYY-MM-DD。無ければ —）

Markdown 変換は原本mdで使われている範囲（見出し・段落・箇条書き（入れ子・チェックボックス）・
番号付き・表・コードフェンス・引用・区切り線・太字・斜体・インラインコード・リンク・画像・
生HTML行）に限定した最小実装。相対リンク・画像は原本mdの場所を基準に file:// の絶対URLへ変換する。
"""
import datetime
import hashlib
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs" / "開発ダッシュボード.base.html"
OUT = ROOT / "docs" / "開発ダッシュボード.html"

MARK_MD = re.compile(r"<!--@MD\s+(.+?)\s*-->")
MARK_CODE = re.compile(r"<!--@CODE\s+(.+?)\s*-->")
MARK_BUILT = "<!--@BUILT-->"
MARK_MTIME = re.compile(r"<!--@MTIME\s+(.+?)\s*-->")

LIST_RE = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
INLINE_CODE_RE = re.compile(r"`([^`]+)`")


# ---------- パス・URL ----------
def file_url(path: Path) -> str:
    return "file:///" + str(path.resolve()).replace("\\", "/")


def resolve_url(url: str, base_dir: Path) -> str:
    if re.match(r"^(https?:|mailto:|file:|#|tel:)", url, re.I):
        return url
    target = (base_dir / url.split("#")[0]).resolve()
    frag = ("#" + url.split("#", 1)[1]) if "#" in url else ""
    return file_url(target) + frag


# ---------- インライン ----------
def inline(text: str, base_dir: Path) -> str:
    codes = []

    def keep(m):
        codes.append(html.escape(m.group(1)))
        return "\x00%d\x00" % (len(codes) - 1)

    text = INLINE_CODE_RE.sub(keep, text)
    text = html.escape(text, quote=False)
    text = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)",
                  lambda m: '<img src="%s" alt="%s">' % (resolve_url(m.group(2), base_dir), m.group(1)), text)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)",
                  lambda m: '<a href="%s">%s</a>' % (resolve_url(m.group(2), base_dir), m.group(1)), text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", text)
    text = re.sub(r"~~(.+?)~~", r"<s>\1</s>", text)
    text = re.sub("\x00(\\d+)\x00", lambda m: "<code>%s</code>" % codes[int(m.group(1))], text)
    return text


# ---------- ブロック ----------
def split_row(line: str):
    line = line.strip()
    line = line.replace("\\|", "\x01")
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip().replace("\x01", "|") for c in line.split("|")]


def render_table(header, rows, base_dir):
    th = "".join("<th>%s</th>" % inline(c, base_dir) for c in header)
    body = []
    for r in rows:
        r = (r + [""] * len(header))[:len(header)]
        body.append("<tr>%s</tr>" % "".join("<td>%s</td>" % inline(c, base_dir) for c in r))
    return ('<div class="table-wrap"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>'
            % (th, "".join(body)))


def parse_list(lines, i, base_dir):
    """i番目から始まる箇条書きを解析し、(html, 次の行番号) を返す。入れ子はインデントで判定。"""
    n = len(lines)
    items = []          # [ordered, [text or nested-html, ...]]
    base_indent = None
    ordered = False
    while i < n:
        line = lines[i]
        if not line.strip():
            j = i + 1
            while j < n and not lines[j].strip():
                j += 1
            if j < n and (LIST_RE.match(lines[j]) or lines[j].startswith(" " * ((base_indent or 0) + 2))):
                i = j
                continue
            break
        m = LIST_RE.match(line)
        if m:
            ind = len(m.group(1).replace("\t", "    "))
            if base_indent is None:
                base_indent = ind
                ordered = m.group(2)[0].isdigit()
            if ind < base_indent:
                break
            if ind > base_indent and items:
                sub, i = parse_list(lines, i, base_dir)
                items[-1][1].append(("html", sub))
                continue
            items.append([m.group(2)[0].isdigit(), [("text", m.group(3))]])
            i += 1
            continue
        if line.startswith(" ") and items:
            items[-1][1].append(("text", line.strip()))
            i += 1
            continue
        break
    lis = []
    for _, parts in items:
        txt = " ".join(p for k, p in parts if k == "text")
        subs = "".join(p for k, p in parts if k == "html")
        cls = ""
        cm = re.match(r"^\[( |x|X)\]\s+(.*)$", txt)
        if cm:
            cls = ' class="task %s"' % ("done" if cm.group(1).lower() == "x" else "todo")
            txt = cm.group(2)
        lis.append("<li%s>%s%s</li>" % (cls, inline(txt, base_dir), subs))
    tag = "ol" if ordered else "ul"
    return "<%s>%s</%s>" % (tag, "".join(lis), tag), i


def md_to_html(md: str, base_dir: Path) -> str:
    lines = md.replace("\r\n", "\n").split("\n")
    out, para = [], []
    i, n = 0, len(lines)

    def flush():
        if para:
            out.append("<p>%s</p>" % inline(" ".join(para), base_dir))
            para.clear()

    while i < n:
        line = lines[i]
        s = line.strip()
        if s.startswith("```"):
            flush()
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            out.append("<pre><code>%s</code></pre>" % html.escape("\n".join(buf)))
            continue
        m = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", s)
        if m:
            flush()
            lvl = len(m.group(1))
            out.append("<h%d>%s</h%d>" % (lvl, inline(m.group(2), base_dir), lvl))
            i += 1
            continue
        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", s):
            flush()
            out.append("<hr>")
            i += 1
            continue
        if "|" in s and i + 1 < n and TABLE_SEP_RE.match(lines[i + 1]):
            flush()
            header = split_row(s)
            i += 2
            rows = []
            while i < n and "|" in lines[i] and lines[i].strip():
                rows.append(split_row(lines[i]))
                i += 1
            out.append(render_table(header, rows, base_dir))
            continue
        if s.startswith(">"):
            flush()
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip()[1:].strip())
                i += 1
            out.append("<blockquote>%s</blockquote>" % md_to_html("\n".join(buf), base_dir))
            continue
        if LIST_RE.match(line):
            flush()
            block, i = parse_list(lines, i, base_dir)
            out.append(block)
            continue
        if re.match(r"^<[a-zA-Z/!]", s):
            flush()
            out.append(line)
            i += 1
            continue
        if not s:
            flush()
            i += 1
            continue
        para.append(s)
        i += 1
    flush()
    return "\n".join(out)


# ---------- 注入 ----------
def slug(path: Path) -> str:
    """節のid用。日本語ファイル名はASCIIが残らず全て同じidになるため、パスのハッシュで一意にする。"""
    base = re.sub(r"[^0-9A-Za-z]+", "-", path.stem).strip("-").lower()
    digest = hashlib.md5(str(path.as_posix()).encode("utf-8")).hexdigest()[:8]
    return (base + "-" if base else "d-") + digest


def mtime_str(path: Path) -> str:
    return datetime.datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d")


def render_md(rel: str) -> str:
    path = ROOT / rel
    md = path.read_text(encoding="utf-8")
    title = path.stem
    m = re.search(r"^#\s+(.+?)\s*$", md, re.M)
    if m:
        title = m.group(1).strip()
        md = md[:m.start()] + md[m.end():]
    body = md_to_html(md, path.parent)
    return (
        '<div class="section-title" id="doc-%s">%s<span class="sub">%s・更新 %s</span></div>\n'
        '<div class="doc-src">原本: <a href="%s">%s</a>（本タブは原本の写し。編集は原本側で）</div>\n'
        '<div class="doc">\n%s\n</div>'
        % (slug(path), html.escape(title), html.escape(rel), mtime_str(path), file_url(path), html.escape(rel), body)
    )


def render_code(rel: str) -> str:
    path = ROOT / rel
    return (
        '<div class="section-title" id="doc-%s">%s<span class="sub">更新 %s</span></div>\n'
        '<div class="doc-src">原本: <a href="%s">%s</a></div>\n'
        '<pre class="src"><code>%s</code></pre>'
        % (slug(path), html.escape(path.name), mtime_str(path), file_url(path), html.escape(rel),
           html.escape(path.read_text(encoding="utf-8")))
    )


def build() -> int:
    if not BASE.exists():
        print("base が見つかりません:", BASE, file=sys.stderr)
        return 1
    src = BASE.read_text(encoding="utf-8")
    missing = []

    def sub_md(m):
        rel = m.group(1).strip()
        if not (ROOT / rel).exists():
            missing.append(rel)
            return '<div class="note warn">原本が見つかりません: %s</div>' % html.escape(rel)
        return render_md(rel)

    def sub_code(m):
        rel = m.group(1).strip()
        if not (ROOT / rel).exists():
            missing.append(rel)
            return '<div class="note warn">原本が見つかりません: %s</div>' % html.escape(rel)
        return render_code(rel)

    def sub_mtime(m):
        rel = m.group(1).strip()
        return mtime_str(ROOT / rel) if (ROOT / rel).exists() else "\u2014"

    out = MARK_MD.sub(sub_md, src)
    out = MARK_CODE.sub(sub_code, out)
    out = MARK_MTIME.sub(sub_mtime, out)
    out = out.replace(MARK_BUILT, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    banner = ("<!-- 自動生成: docs/開発ダッシュボード.base.html ＋ 原本md注入（python scripts/build_dashboard.py）。"
              "このファイルは直接編集せず、base を編集して再ビルドする -->\n")
    out = out.replace("<!DOCTYPE html>\n", "<!DOCTYPE html>\n" + banner, 1)
    OUT.write_text(out, encoding="utf-8", newline="\n")
    print("wrote", OUT, "(%d bytes)" % OUT.stat().st_size)
    if missing:
        print("警告: 原本が見つからないマーカー:", ", ".join(missing), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(build())
