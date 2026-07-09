#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Notion API からニュース／イベント／キャンペーンの3DBを取得し、
ダッシュボード表示用の notion-data.js を生成するスクリプト。

- Notion API バージョン: 2025-09-03（data_sources API）
  konpie-bot（src/utils/kotohira_notion.py, notion_register.py,
  news_notion_writer.py）が使う notion-client 2.7.0 と同じ流儀
  （databases.retrieve → data_sources.query）に合わせている。
  同一DBを読むため、プロパティの解釈も konpie-bot 側の
  get_property_value 等に揃えた。
- 標準ライブラリのみで実装（pip依存なし）。
- サムネイル/参考画像は署名付きURL（Notion S3は約1時間、Discord CDNは
  約24時間で失効）が大半のため、取得直後にローカル（assets/thumbs/）へ
  保存し、notion-data.js には相対パスを書き込む。

使い方:
    python scripts/fetch_notion.py

環境変数:
    KOTOHIRA_DASHBOARD_NOTION_TOKEN … 優先されるトークン
    NOTION_TOKEN                    … 上記が無い場合のフォールバック
    NEWS_NOTION_DB_ID / KOTOHIRA_DATABASE_ID / CAMPAIGN_NOTION_DB_ID
                                     … 各DB IDの上書き（省略時は既定値を使用）

リポジトリ直下に .env ファイル（KEY=VALUE形式）を置けば、
そこからも読み込む（OS側の環境変数が優先）。
"""

from __future__ import annotations

import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

NOTION_VERSION = "2025-09-03"
API_BASE = "https://api.notion.com/v1"
JST = timezone(timedelta(hours=9))

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
OUTPUT_PATH = os.path.join(REPO_ROOT, "notion-data.js")
ENV_PATH = os.path.join(REPO_ROOT, ".env")


def load_env_file(path: str) -> None:
    """リポジトリ直下の .env を読み、未設定の環境変数のみ取り込む。

    書式は KEY=VALUE（# 始まりの行と空行は無視、値の前後の引用符は除去）。
    OS側で既に設定済みの環境変数が優先される。
    """
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip("'\"")
            if key:
                os.environ.setdefault(key, value)


load_env_file(ENV_PATH)

NEWS_DB_ID = os.environ.get(
    "NEWS_NOTION_DB_ID", "37c0b4e5ff5b80788422f5a83da8351c"
)
EVENT_DB_ID = os.environ.get(
    "KOTOHIRA_DATABASE_ID", "1530b4e5ff5b80fc9f16d42c112dcba9"
)
CAMPAIGN_DB_ID = os.environ.get(
    "CAMPAIGN_NOTION_DB_ID", "37c0b4e5ff5b8078b558e7cf2148744e"
)
# 体験・滞在DB（体験プログラム／おてつたび／ワーキングホリデー／求人／滞在）。
# 既定は空文字。Notion側でDBを作成しインテグレーションをコネクトしたうえで、
# 環境変数 EXPERIENCE_NOTION_DB_ID にDB IDを設定すると取得対象になる。
# 未設定の間は取得処理そのものをスキップし、既存3DBの動作に影響を与えない。
EXPERIENCE_DB_ID = os.environ.get("EXPERIENCE_NOTION_DB_ID", "")

NEWS_MAX = 60
EVENT_MAX = 200
EXPERIENCE_MAX = 200
RECENT_WINDOW_DAYS = 60

THUMBS_DIR = os.path.join(REPO_ROOT, "assets", "thumbs")
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".webp")
# 画像の“正”はこのローカルフォルダ。Notionは信用しない（表示バグ・URL失効あり）。
# assets/image-overrides.json のマッピングにマッチした項目は、Notionから一切
# 取得せず assets/manual/ のファイルを使う（local-first）。
MANUAL_DIR = os.path.join(REPO_ROOT, "assets", "manual")
OVERRIDES_PATH = os.path.join(REPO_ROOT, "assets", "image-overrides.json")
DOWNLOAD_TIMEOUT = 20
# 一部の新聞社サイト等は UA無しのリクエストを拒否するため、
# 一般的なブラウザ風の User-Agent を付与する。
DOWNLOAD_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
# これらのホストのURLは期限付き署名URL（保存に失敗したら再取得不能）。
SIGNED_URL_HOSTS = ("prod-files-secure.s3", "cdn.discordapp.com")

# HTMLタグ本体、末尾で閉じられていないタグ断片、連続空白の除去用。
HTML_TAG_RE = re.compile(r"<[^>]*>")
TRAILING_TAG_RE = re.compile(r"<[^>]*$")
WHITESPACE_RE = re.compile(r"\s+")


def get_token() -> str | None:
    """トークンを環境変数から取得。

    KOTOHIRA_DASHBOARD_NOTION_TOKEN を優先し、
    無ければ NOTION_TOKEN にフォールバックする。
    """
    return os.environ.get("KOTOHIRA_DASHBOARD_NOTION_TOKEN") or os.environ.get(
        "NOTION_TOKEN"
    )


def print_setup_guide() -> None:
    """トークン未設定時の日本語セットアップ案内。"""
    print(
        """
Notion連携のトークンが設定されていません。

【セットアップ手順】
1. https://www.notion.so/my-integrations で「新しいインテグレーション」を作成する
   - 種類: 内部インテグレーション
   - 権限: 「コンテンツを読み取る」のみを付与する（読み取り専用。更新・挿入・削除の権限は付けない）
2. 発行された Internal Integration Secret（"ntn_..." 等）を控える
3. Notion上で以下の3つのデータベースをそれぞれ開き、右上「...」メニュー→
   「コネクト」から、手順1で作成したインテグレーションを追加する
   - ニュースDB
   - イベントDB
   - キャンペーンDB
4. 環境変数 KOTOHIRA_DASHBOARD_NOTION_TOKEN にトークンを設定する
   例（PowerShell）: $env:KOTOHIRA_DASHBOARD_NOTION_TOKEN = "ntn_xxxxxxxx"
5. 再度 python scripts/fetch_notion.py を実行する
""".strip()
    )


def http_request(
    path: str,
    token: str,
    method: str = "GET",
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Notion APIへリクエストを送る（urllib標準ライブラリのみ）。"""
    url = f"{API_BASE}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Notion-Version", NOTION_VERSION)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.loads(res.read().decode("utf-8"))


def get_data_source_id(database_id: str, token: str) -> str:
    """database_id から data_source_id を取得する。

    2025-09系APIではdata_sources経由でクエリするため必要。
    """
    data = http_request(f"/databases/{database_id}", token)
    sources = data.get("data_sources", [])
    if not sources:
        raise RuntimeError("data sourceが見つかりません")
    return sources[0]["id"]


def query_data_source(
    data_source_id: str,
    token: str,
    sorts: list[dict[str, Any]],
    max_total: int,
) -> list[dict[str, Any]]:
    """data_sources/{id}/query をページネーションしながら呼び出す。

    最大 max_total 件まで取得する。
    """
    results: list[dict[str, Any]] = []
    cursor: str | None = None
    while len(results) < max_total:
        body: dict[str, Any] = {
            "page_size": min(100, max_total - len(results)),
            "sorts": sorts,
        }
        if cursor:
            body["start_cursor"] = cursor
        res = http_request(
            f"/data_sources/{data_source_id}/query",
            token,
            method="POST",
            body=body,
        )
        results.extend(res.get("results", []))
        if not res.get("has_more"):
            break
        cursor = res.get("next_cursor")
        if not cursor:
            break
    return results[:max_total]


# ---- プロパティ読み取りヘルパー ----
# （konpie-bot側の get_property_value 等と同じ解釈に合わせる）


def _prop(properties: dict[str, Any], key: str) -> dict[str, Any] | None:
    return properties.get(key) if isinstance(properties, dict) else None


def get_title(properties: dict[str, Any], key: str) -> str:
    p = _prop(properties, key)
    if not p or not p.get("title"):
        return ""
    return "".join(t.get("plain_text", "") for t in p["title"])


def get_rich_text(properties: dict[str, Any], key: str) -> str:
    p = _prop(properties, key)
    if not p or not p.get("rich_text"):
        return ""
    return "".join(t.get("plain_text", "") for t in p["rich_text"])


def get_url(properties: dict[str, Any], key: str) -> str:
    p = _prop(properties, key)
    if not p:
        return ""
    return p.get("url") or ""


def get_select(properties: dict[str, Any], key: str) -> str:
    p = _prop(properties, key)
    if not p or not p.get("select"):
        return ""
    return p["select"].get("name", "")


def get_checkbox(properties: dict[str, Any], key: str) -> bool:
    p = _prop(properties, key)
    if not p:
        return False
    return bool(p.get("checkbox", False))


def get_relation_ids(properties: dict[str, Any], key: str) -> list[str]:
    """relationプロパティのリンク先ページIDのリストを返す（未リンクは空）。"""
    p = _prop(properties, key)
    if not p or p.get("type") != "relation":
        return []
    return [r.get("id", "") for r in p.get("relation", []) if r.get("id")]


def get_date_start(properties: dict[str, Any], key: str) -> str:
    """日付を返す。

    時刻があればJSTの 'YYYY-MM-DDTHH:MM'、無ければ 'YYYY-MM-DD'。
    """
    p = _prop(properties, key)
    if not p or not p.get("date"):
        return ""
    start = p["date"].get("start") or ""
    if not start:
        return ""
    has_time = "T" in start
    try:
        dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
    except ValueError:
        return start
    if has_time:
        if dt.tzinfo is not None:
            dt = dt.astimezone(JST)
        return dt.strftime("%Y-%m-%dT%H:%M")
    return dt.strftime("%Y-%m-%d")


def get_files_url(properties: dict[str, Any], key: str) -> str:
    """files配列の先頭ファイルのURL（external/fileのどちらにも対応）。"""
    p = _prop(properties, key)
    if not p or not p.get("files"):
        return ""
    f = p["files"][0]
    file_type = f.get("type")
    if file_type == "external":
        return f.get("external", {}).get("url", "")
    if file_type == "file":
        return f.get("file", {}).get("url", "")
    return f.get("external", {}).get("url") or f.get("file", {}).get("url") or ""


def _format_number(n: Any) -> str:
    """数値を表示用文字列にする（整数はそのまま、桁区切りは付けない）。"""
    if isinstance(n, float) and n.is_integer():
        return str(int(n))
    return str(n)


def _value_to_text(v: dict[str, Any]) -> str:
    """1つのプロパティ値オブジェクトから表示用の平文を取り出す。

    rich_text / title / number / select / multi_select / formula / date /
    rollup（配列・数値・日付）に対応する。ロールアップ中身の型ゆらぎ
    （テキスト・数値・リレーション先タイトル等）も吸収する。
    """
    if not isinstance(v, dict):
        return ""
    t = v.get("type")
    if t == "rich_text":
        return "".join(x.get("plain_text", "") for x in v.get("rich_text", []))
    if t == "title":
        return "".join(x.get("plain_text", "") for x in v.get("title", []))
    if t == "number":
        n = v.get("number")
        return "" if n is None else _format_number(n)
    if t == "select":
        return (v.get("select") or {}).get("name", "")
    if t == "multi_select":
        return " / ".join(o.get("name", "") for o in v.get("multi_select", []))
    if t == "formula":
        f = v.get("formula") or {}
        ft = f.get("type")
        if ft == "string":
            return f.get("string") or ""
        if ft == "number":
            n = f.get("number")
            return "" if n is None else _format_number(n)
        if ft == "date":
            return (f.get("date") or {}).get("start") or ""
        return ""
    if t == "date":
        return (v.get("date") or {}).get("start") or ""
    if t == "rollup":
        r = v.get("rollup") or {}
        rt = r.get("type")
        if rt == "array":
            parts = [_value_to_text(el) for el in r.get("array", [])]
            return " / ".join(p for p in parts if p)
        if rt == "number":
            n = r.get("number")
            return "" if n is None else _format_number(n)
        if rt == "date":
            return (r.get("date") or {}).get("start") or ""
        return ""
    return ""


def get_any_text(properties: dict[str, Any], key: str) -> str:
    """プロパティ型に依存せず平文を取り出す（rich_text/number/rollup等に対応）。

    「参加費（日本円）」のように型がテキストか数値か不定な項目や、
    「住所」のようなロールアップ項目に用いる。get_rich_text では
    リッチテキスト以外の型が空になってしまうため、その代替。
    """
    p = _prop(properties, key)
    if not p:
        return ""
    return _value_to_text(p)


def strip_html(text: str) -> str:
    """HTMLタグ・壊れたタグ断片・実体参照を除去した平文を返す。

    Google News RSS由来の要約に、Notionのrich_text文字数上限で
    タグの途中が切れた断片（例: 末尾が `<a href="https:...`）が
    混入することがあるため、完全なタグを除去した後、閉じられて
    いない末尾のタグ開始断片も除去する。&amp; 等のHTMLエンティティは
    アンエスケープし、連続する空白は1つに畳む。
    """
    if not text:
        return text
    stripped = HTML_TAG_RE.sub("", text)
    stripped = TRAILING_TAG_RE.sub("", stripped)
    stripped = html.unescape(stripped)
    return WHITESPACE_RE.sub(" ", stripped).strip()


def is_signed_url(url: str) -> bool:
    """署名付き（期限切れになる）URLかどうかをホスト名で判定する。"""
    host = urllib.parse.urlparse(url).netloc.lower()
    return any(signed_host in host for signed_host in SIGNED_URL_HOSTS)


def guess_extension(url: str, content_type: str | None) -> str:
    """URLパスの拡張子、無ければContent-Typeから拡張子を推定する。

    どちらからも判定できなければ .jpg を返す。
    """
    path = urllib.parse.urlparse(url).path.lower()
    for ext in IMAGE_EXTENSIONS:
        if path.endswith(ext):
            return ext
    content_type_map = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
    }
    if content_type:
        main_type = content_type.split(";")[0].strip().lower()
        if main_type in content_type_map:
            return content_type_map[main_type]
    return ".jpg"


def find_local_thumb(file_id: str) -> str:
    """file_id（ページIDのハイフン除去）で既に保存済みのファイルを探す。

    見つかれば相対パス、無ければ空文字を返す。
    """
    for ext in IMAGE_EXTENSIONS:
        if os.path.exists(os.path.join(THUMBS_DIR, f"{file_id}{ext}")):
            return f"assets/thumbs/{file_id}{ext}"
    return ""


def download_image(url: str, page_id: str) -> tuple[str, bool]:
    """画像をダウンロードしてローカルへ保存し、相対パスと成否を返す。

    既に同名ファイル（拡張子違いも含む）があれば再ダウンロードせず
    そのパスを返す。失敗時、署名URL（Notion S3/Discord CDN）は空文字、
    それ以外の恒久URLは元URLをそのまま返す（どちらも成否は False）。
    """
    file_id = page_id.replace("-", "")
    if not file_id:
        return ("" if is_signed_url(url) else url), False

    existing = find_local_thumb(file_id)
    if existing:
        return existing, True

    req = urllib.request.Request(url)
    req.add_header("User-Agent", DOWNLOAD_USER_AGENT)
    try:
        with urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT) as res:
            content_type = res.headers.get("Content-Type")
            data = res.read()
    except Exception:
        return ("" if is_signed_url(url) else url), False

    ext = guess_extension(url, content_type)
    os.makedirs(THUMBS_DIR, exist_ok=True)
    file_path = os.path.join(THUMBS_DIR, f"{file_id}{ext}")
    with open(file_path, "wb") as f:
        f.write(data)
    return f"assets/thumbs/{file_id}{ext}", True


def load_image_overrides() -> dict[str, str]:
    """assets/image-overrides.json（キー→ファイル名）を読む。無ければ空dict。

    キーは出典URL または タイトル。'_' で始まるキーは説明用として無視する。
    """
    if not os.path.exists(OVERRIDES_PATH):
        return {}
    try:
        with open(OVERRIDES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {}
        return {k: v for k, v in data.items() if not str(k).startswith("_") and v}
    except Exception as e:
        print(f"[警告] image-overrides.json の読み込みに失敗（無視します）: {e}")
        return {}


def _override_matches(key: str, item: dict[str, Any]) -> bool:
    """オーバーライドのキーが item にマッチするか。

    http... で始まるキーはURL照合（部分一致・双方向）、それ以外はタイトルの
    トークンAND一致（空白区切りの語がすべてタイトルに含まれれば一致）。
    """
    key = str(key).strip()
    if not key:
        return False
    url = item.get("url") or ""
    title = item.get("title") or ""
    if key.startswith("http"):
        return bool(url) and (key in url or url in key)
    tokens = key.split()
    return bool(tokens) and all(tok in title for tok in tokens)


def apply_image_overrides(
    items: list[dict[str, Any]], field: str, overrides: dict[str, str]
) -> int:
    """image-overrides.json を最優先で適用する（Notion非依存のローカル画像）。

    マッチした item は field を assets/manual/<file> に差し替える。以後
    save_images はローカルパスを見てNotion取得をスキップする。指定ファイルが
    無い場合は警告して据え置く（誤って空表示になった時に気づけるように）。
    先に一致したキーを採用。返り値は適用件数。
    """
    if not overrides:
        return 0
    applied = 0
    for item in items:
        for key, filename in overrides.items():
            if not _override_matches(key, item):
                continue
            path = os.path.join(MANUAL_DIR, filename)
            if os.path.exists(path):
                item[field] = f"assets/manual/{filename}"
                applied += 1
            else:
                print(
                    f"[警告] image-overrides: '{key}' の画像が見つかりません: "
                    f"assets/manual/{filename}"
                )
            break
    return applied


def save_images(items: list[dict[str, Any]], field: str) -> tuple[int, int]:
    """items内のfield（thumbnail/image）を対象にローカル保存する。

    値がある項目のみを対象とし、(対象件数, 成功件数) を返す。
    item[field] は保存後のパス（または空文字/元URL）に書き換える。
    既に assets/ で始まるローカルパス（手動オーバーライド等）はNotionから
    取得せずそのまま使う。
    """
    total = 0
    success = 0
    for item in items:
        url = item.get(field, "")
        if not url or url.startswith("assets/"):
            continue
        total += 1
        page_id = str(item.get("id", ""))
        local_path, ok = download_image(url, page_id)
        item[field] = local_path
        if ok:
            success += 1
    return total, success


def parse_news(page: dict[str, Any]) -> dict[str, Any]:
    properties = page.get("properties", {})
    return {
        "id": page.get("id", ""),
        "title": get_title(properties, "見出し"),
        "url": get_url(properties, "出典URL"),
        "summary": strip_html(get_rich_text(properties, "要約")),
        "org": get_select(properties, "出典団体"),
        "media": get_select(properties, "出典媒体"),
        "date": get_date_start(properties, "公開日"),
        "thumbnail": get_files_url(properties, "サムネイル"),
        "duplicate": get_checkbox(properties, "重複の可能性"),
        "pickup": get_checkbox(properties, "定例で紹介"),
        "show": get_checkbox(properties, "表示対象"),
    }


def status_from_dates(start: str, end: str) -> str:
    """開始/終了日からステータス（実施前/実施中/終了）を算出する。

    NotionのステータスプロパティはkonpieBotが登録時に一度書くだけで
    日付が過ぎても更新されない（空のことも多い）ため、保存値は使わず
    取得のたびに計算する。ベースは konpie-bot の
    register_watcher.py: _status_from_dates。ただし終了日が無い場合は
    「開始日当日で終了」とみなす（原典は登録時の一度きりの計算なので
    過去の単発イベントが実施中のままになる問題がなかった）。
    """
    today = datetime.now(JST).date()
    s = e = None
    try:
        s = datetime.fromisoformat(start[:10]).date() if start else None
    except ValueError:
        s = None
    try:
        e = datetime.fromisoformat(end[:10]).date() if end else None
    except ValueError:
        e = None
    if s is None and e is None:
        return "実施前"
    if s and today < s:
        return "実施前"
    eff_end = e or s
    if eff_end and today > eff_end:
        return "終了"
    return "実施中"


def parse_event(page: dict[str, Any]) -> dict[str, Any]:
    properties = page.get("properties", {})
    start = get_date_start(properties, "開催日時（開始）")
    end = get_date_start(properties, "開催日時（終了）")
    return {
        "id": page.get("id", ""),
        "title": get_title(properties, "イベント名"),
        "url": get_url(properties, "ソース"),
        "start": start,
        "end": end,
        "status": status_from_dates(start, end),
        "city": get_select(properties, "市町村"),
        # 「開催場所」は会場DBへの relation、「住所」はその relation 経由の rollup。
        # 会場名は fetch_events が relation 先ページのタイトルを解決して place に
        # 埋める（_place_ids は解決時に取り除かれ、出力JSONには含まれない）。
        # 「住所」rollup は会場を紐づければ自動で入る（get_any_text が対応済み）。
        "place": "",
        "_place_ids": get_relation_ids(properties, "開催場所"),
        "address": get_any_text(properties, "住所"),
        "image": get_files_url(properties, "参考画像"),
        "comment": strip_html(get_rich_text(properties, "コメント")),
        "fee": get_any_text(properties, "参加費（日本円）"),
        "organizer": get_any_text(properties, "主催/運営"),
    }


def filter_events(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """ステータスによる絞り込み。

    実施前/実施中は全件、終了は開始日が実行日の60日前以降のみ残す。
    """
    today = datetime.now(JST).date()
    cutoff = today - timedelta(days=RECENT_WINDOW_DAYS)
    filtered: list[dict[str, Any]] = []
    for item in items:
        if item.get("status") == "終了":
            start = item.get("start", "")
            if not start:
                continue
            try:
                start_date = datetime.fromisoformat(start[:10]).date()
            except ValueError:
                continue
            if start_date < cutoff:
                continue
        filtered.append(item)
    return filtered


def fetch_news(token: str) -> list[dict[str, Any]]:
    """ニュースDBを取得し、「表示対象」チェック済みの項目のみ返す。

    notion-data.js はPhase2で公開予定のファイルのため、非表示指定の
    記事はそもそも書き出さない（公開事故防止）。並びは公開日降順を
    維持する。
    注意: 現状 NEWS_MAX（先頭 max_total 件）を取得してから絞り込む
    ため、DB全体の件数が NEWS_MAX を超え、かつ表示対象チェック済みが
    NEWS_MAX 件目より後ろに偏っていると漏れる可能性がある。現時点は
    総件数がNEWS_MAX未満のため実害は無いが、将来DBが増えて超えたら
    Notion側フィルタ（data_sources.query の filter で「表示対象」を
    直接絞る）への切り替えを検討すること。
    """
    dsid = get_data_source_id(NEWS_DB_ID, token)
    sorts = [{"property": "公開日", "direction": "descending"}]
    pages = query_data_source(dsid, token, sorts, NEWS_MAX)
    items = [parse_news(p) for p in pages]
    return [item for item in items if item.get("show")]


def fetch_page_title(page_id: str, token: str) -> str:
    """ページのタイトル（type=title のプロパティ）を取得する。失敗時は空文字。

    会場ページがインテグレーションに共有されていない場合は404になるため、
    例外はすべて握りつぶして空文字を返す（イベント表示自体は止めない）。
    """
    try:
        page = http_request(f"/pages/{page_id}", token)
    except Exception:
        return ""
    for val in (page.get("properties") or {}).values():
        if isinstance(val, dict) and val.get("type") == "title":
            return "".join(t.get("plain_text", "") for t in val.get("title", []))
    return ""


def resolve_place_names(items: list[dict[str, Any]], token: str) -> None:
    """「開催場所」relation のリンク先ページ名を place に解決する。

    同じ会場を多数のイベントが参照するため、ページIDでキャッシュして
    APIコールを会場数ぶんに抑える。_place_ids はここで取り除く。
    """
    cache: dict[str, str] = {}
    for item in items:
        ids = item.pop("_place_ids", [])
        names: list[str] = []
        for pid in ids:
            if pid not in cache:
                cache[pid] = fetch_page_title(pid, token)
            if cache[pid]:
                names.append(cache[pid])
        if names:
            item["place"] = " / ".join(names)


def fetch_events(database_id: str, token: str) -> list[dict[str, Any]]:
    dsid = get_data_source_id(database_id, token)
    sorts = [{"property": "開催日時（開始）", "direction": "descending"}]
    pages = query_data_source(dsid, token, sorts, EVENT_MAX)
    items = [parse_event(p) for p in pages]
    items = filter_events(items)
    # 絞り込み後に会場名を解決する（対象件数を減らしてAPIコールを節約）
    resolve_place_names(items, token)
    return items


def parse_experience(page: dict[str, Any]) -> dict[str, Any]:
    """体験・滞在DBの1ページを表示用dictへ変換する。

    ステータスは手動運用（募集中／通年／準備中／終了）。イベントと違い
    通年・随時募集や求人があり日付から一意に決まらないため、日付計算では
    なくNotionのセレクト値をそのまま使う。空なら「募集中」とみなす。
    """
    properties = page.get("properties", {})
    return {
        "id": page.get("id", ""),
        "title": get_title(properties, "タイトル"),
        "category": get_select(properties, "種別"),
        "org": get_rich_text(properties, "団体・主催"),
        "summary": strip_html(get_rich_text(properties, "概要")),
        "start": get_date_start(properties, "募集開始日"),
        "end": get_date_start(properties, "募集終了日"),
        "place": get_rich_text(properties, "場所"),
        "reward": get_rich_text(properties, "費用・報酬"),
        "target": get_rich_text(properties, "対象・条件"),
        "url": get_url(properties, "応募・詳細URL"),
        "status": get_select(properties, "ステータス") or "募集中",
        "image": get_files_url(properties, "画像"),
        "show": get_checkbox(properties, "表示対象"),
    }


def fetch_experiences(database_id: str, token: str) -> list[dict[str, Any]]:
    """体験・滞在DBを取得し、「表示対象」チェック済みの項目のみ返す。

    並びは募集開始日の降順。日付未設定（通年・随時）の項目も取りこぼさ
    ないよう、ソートはNotion側に任せつつ全件（EXPERIENCE_MAX上限）取る。
    """
    dsid = get_data_source_id(database_id, token)
    sorts = [{"property": "募集開始日", "direction": "descending"}]
    pages = query_data_source(dsid, token, sorts, EXPERIENCE_MAX)
    items = [parse_experience(p) for p in pages]
    return [item for item in items if item.get("show")]


def load_existing_data() -> dict[str, Any]:
    """既存の notion-data.js があれば window.NOTION_DATA の中身を返す。

    ファイルが無い、またはパースに失敗した場合は空辞書を返す。
    """
    if not os.path.exists(OUTPUT_PATH):
        return {}
    try:
        with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        start = content.index("{")
        json_str = content[start:].rstrip()
        if json_str.endswith(";"):
            json_str = json_str[:-1]
        return json.loads(json_str)
    except Exception:
        return {}


def describe_http_error(key: str, error: urllib.error.HTTPError) -> None:
    if error.code == 404:
        print(
            f"[警告] {key}DBの取得に失敗しました（HTTP 404）: "
            f"このDBにインテグレーションがコネクトされていない可能性があります。"
            f"Notion側でDBを開き「...」メニュー→「コネクト」から追加してください。"
        )
    else:
        print(f"[警告] {key}DBの取得に失敗しました（HTTP {error.code}）")


def main() -> None:
    token = get_token()
    if not token:
        print_setup_guide()
        sys.exit(1)

    existing = load_existing_data()
    overrides = load_image_overrides()
    if overrides:
        print(f"画像オーバーライド: {len(overrides)}件のマッピングを読み込みました")
    result: dict[str, list[dict[str, Any]]] = {}
    errors: dict[str, str] = {}
    image_total = 0
    image_success = 0
    override_total = 0

    tasks: list[tuple[str, str, Callable[[], list[dict[str, Any]]]]] = [
        ("news", "thumbnail", lambda: fetch_news(token)),
        ("events", "image", lambda: fetch_events(EVENT_DB_ID, token)),
        ("campaigns", "image", lambda: fetch_events(CAMPAIGN_DB_ID, token)),
    ]
    # 体験・滞在DBは EXPERIENCE_NOTION_DB_ID が設定されている場合のみ取得する。
    if EXPERIENCE_DB_ID:
        tasks.append(
            ("experiences", "image", lambda: fetch_experiences(EXPERIENCE_DB_ID, token))
        )

    for key, image_field, fn in tasks:
        print(f"{key}を取得中...")
        try:
            items = fn()
            # ローカル画像オーバーライドを最優先で適用（Notionを画像に使わない）
            applied = apply_image_overrides(items, image_field, overrides)
            override_total += applied
            if applied:
                print(f"{key}: ローカル画像を{applied}件適用（Notion非経由）")
            t, s = save_images(items, image_field)
            image_total += t
            image_success += s
            result[key] = items
            print(f"{key}: {len(items)}件取得しました")
        except urllib.error.HTTPError as e:
            describe_http_error(key, e)
            errors[key] = f"HTTP {e.code}"
        except Exception as e:
            print(f"[警告] {key}DBの取得に失敗しました（{type(e).__name__}）")
            errors[key] = type(e).__name__

    # 失敗したDBは、既存 notion-data.js に該当キーがあれば温存する
    result_keys = ["news", "events", "campaigns"]
    if EXPERIENCE_DB_ID:
        result_keys.append("experiences")
    for key in result_keys:
        if key not in result:
            if key in existing:
                result[key] = existing[key]
                print(
                    f"{key}: 取得失敗のため既存データを温存します"
                    f"（{len(existing[key])}件）"
                )
            else:
                result[key] = []

    if errors and not any(result.values()):
        print(
            "すべてのDB取得に失敗し、温存できる既存データもありません。"
            "notion-data.js は更新しません。"
        )
        sys.exit(1)

    data = {
        "fetched": datetime.now(JST).strftime("%Y-%m-%d %H:%M"),
        "news": result.get("news", []),
        "events": result.get("events", []),
        "campaigns": result.get("campaigns", []),
    }
    # 体験・滞在は、DB設定済みか既存データがある場合のみ書き出す（未設定時は
    # キー自体を省略し、既存の体験データがあれば温存する）。
    if EXPERIENCE_DB_ID or "experiences" in existing:
        data["experiences"] = result.get(
            "experiences", existing.get("experiences", [])
        )

    if override_total:
        print(f"画像: ローカル手動画像を{override_total}件適用（Notion非経由）")
    if image_total:
        image_failed = image_total - image_success
        print(
            f"画像: {image_total}件中 {image_success}件保存, "
            f"{image_failed}件失敗（Notion由来）"
        )

    js = "/* 自動生成: scripts/fetch_notion.py が再生成します。手編集しないでください */\n"
    js += "window.NOTION_DATA = " + json.dumps(data, ensure_ascii=False, indent=2)
    js += ";\n"

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(js)

    print(f"notion-data.js を書き出しました: {OUTPUT_PATH}")
    if errors:
        print(f"[注意] 取得に失敗したDB: {', '.join(errors.keys())}")


if __name__ == "__main__":
    main()
