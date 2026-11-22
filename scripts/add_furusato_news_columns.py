"""Notion の表「ふるさと住民 ニュース」に、列を作る（一回限りの道具）。

表そのもの（空のデータベース）は、本人が Notion で作って、書き込み用のインテグレーションを接続しておく。
この道具は、その表に列を足し、題名の列を「タイトル」にし、貼り付け用の関数の列を作る。
既定は dry-run。--apply で実際に足す。すでにある名前の列には触らない。

使い方（notion-event-formatter の .venv の python で）:
    python scripts/add_furusato_news_columns.py --db <表のURLかID>            # 何を足すかを表示
    python scripts/add_furusato_news_columns.py --db <表のURLかID> --apply    # 足す

設計: C:/Users/user/furusato-resident/検討/2026-11-21_貼り付け入力の道具_要件定義.md の「ニュース」
"""
import argparse
import json
import re
import sys

SKILL_DIR = "C:/Users/user/.claude/skills/kotohira-news-register"
sys.path.insert(0, SKILL_DIR)
import register_news as rn  # noqa: E402
from notion_client import Client  # noqa: E402

from add_furusato_columns import CATEGORIES  # noqa: E402

TITLE = "タイトル"
KINDS = ["今週のイベント", "今週末のイベント", "開催の報告", "紹介されました", "募集の知らせ"]
FORMULA_NAME = "ふる住 掲載データ"

# 列の名前は、イベントDBの掲載用の列と同じにしてある（手順をそろえるため）
COLUMNS = {
    "種類": {"select": {"options": [{"name": k} for k in KINDS]}},
    "メモ": {"rich_text": {}},
    "外部リンク": {"url": {}},
    "ふる住 掲載": {"select": {"options": [
        {"name": "載せる", "color": "yellow"},
        {"name": "掲載文あり", "color": "blue"},
        {"name": "申請済み", "color": "green"},
    ]}},
    "ふる住 掲載文": {"rich_text": {}},
    "ふる住 カテゴリ": {"multi_select": {"options": [{"name": c} for c in CATEGORIES]}},
    "ふる住 タグ": {"multi_select": {"options": []}},
    "掲載終了": {"date": {}},
    "画像": {"files": {}},
}

# 貼り付け用の文（行の形）。拡張機能 furusato-paste-input が読む。掲載開始は入れない（貼った日の 0:00 が入る）
FORMULA = (
    '("kind: furusato-news\\n"'
    f' + "title: " + prop("{TITLE}") + "\\n"'
    ' + "publish_end: " + if(empty(prop("掲載終了")), "", formatDate(prop("掲載終了"), "YYYY-MM-DD") + " 23:59") + "\\n"'
    ' + "link: " + prop("外部リンク") + "\\n"'
    ' + "categories: " + join(prop("ふる住 カテゴリ"), "、") + "\\n"'
    ' + "tags: " + join(prop("ふる住 タグ"), "、") + "\\n"'
    ' + "body:\\n" + prop("ふる住 掲載文"))'
)


def db_id_of(value: str) -> str:
    m = re.search(r"([0-9a-f]{32})", value.replace("-", ""))
    if not m:
        sys.exit("表の URL か ID が読めません")
    return m.group(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    with open(SKILL_DIR + "/config-events.json", encoding="utf-8") as f:
        cfg = json.load(f)
    client = Client(auth=rn.load_token(cfg))
    db_id = db_id_of(args.db)
    db = client.databases.retrieve(database_id=db_id)
    existing = db["properties"]
    name = "".join(t.get("plain_text", "") for t in db.get("title", []))
    print(f"表: {name}（列 {len(existing)} 個）")

    title_now = next(n for n, p in existing.items() if p["type"] == "title")
    changes = {}
    if title_now != TITLE:
        changes[title_now] = {"name": TITLE}
        print(f"  題名の列の名前を変える: {title_now} → {TITLE}")
    for col, definition in COLUMNS.items():
        if col in existing:
            print(f"  すでにある（触らない）: {col} [{existing[col]['type']}]")
        else:
            changes[col] = definition
            print(f"  足す: {col} [{next(iter(definition))}]")
    need_formula = FORMULA_NAME not in existing
    print(f"  {'足す' if need_formula else 'すでにある（触らない）'}: {FORMULA_NAME} [formula]")

    if not args.apply:
        print("dry-run: 書いていません。実際に足すには --apply")
        return
    if changes:
        client.databases.update(database_id=db_id, properties=changes)
    if need_formula:  # 関数は、参照する列ができてから作る
        client.databases.update(database_id=db_id, properties={FORMULA_NAME: {"formula": {"expression": FORMULA}}})
    after = client.databases.retrieve(database_id=db_id)["properties"]
    want = [TITLE, *COLUMNS, FORMULA_NAME]
    missing = [n for n in want if n not in after]
    print(f"列 {len(existing)} → {len(after)} 個。足りない列: {missing if missing else 'なし'}")
    print(f"表のID: {db_id}")


if __name__ == "__main__":
    main()
