"""イベントDBに「ふるさと住民アプリへの掲載」用の列を足す（一回限りの道具）。

既定は dry-run（何を足すかを表示するだけ）。--apply で実際に足す。
すでにある名前の列には触らない。既存の列の変更・削除はしない。

使い方（notion-event-formatter の .venv の python で）:
    python scripts/add_furusato_columns.py            # 何を足すかを表示
    python scripts/add_furusato_columns.py --apply    # 足す

設計: C:/Users/user/furusato-resident/検討/2026-11-21_貼り付け入力の道具_要件定義.md
"""
import argparse
import json
import sys

SKILL_DIR = "C:/Users/user/.claude/skills/kotohira-news-register"
sys.path.insert(0, SKILL_DIR)
import register_news as rn  # noqa: E402
from notion_client import Client  # noqa: E402

CATEGORIES = [
    "まちづくり", "教育・子育て", "農林水産業", "自然・環境", "防災・安全", "観光・レジャー", "地域経済",
    "歴史・文化", "芸術・クリエイティブ", "食・特産品", "健康・福祉", "広報・メディア", "スポーツ", "国際・多文化交流",
]

# 足す列。名前 → Notion のプロパティ定義
COLUMNS = {
    "ふるさと住民 掲載": {"select": {"options": [
        {"name": "載せる", "color": "yellow"},
        {"name": "掲載文あり", "color": "blue"},
        {"name": "申請済み", "color": "green"},
    ]}},
    "ふるさと住民 掲載文": {"rich_text": {}},
    "ふるさと住民 カテゴリ": {"multi_select": {"options": [{"name": c} for c in CATEGORIES]}},
    "ふるさと住民 タグ": {"multi_select": {"options": []}},
    "問い合わせ先 担当者名": {"rich_text": {}},
    "問い合わせ先 電話": {"phone_number": {}},
    "問い合わせ先 メール": {"email": {}},
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    with open(SKILL_DIR + "/config-events.json", encoding="utf-8") as f:
        cfg = json.load(f)
    client = Client(auth=rn.load_token(cfg))
    db_id = rn.resolve_database_id(cfg)
    # 登録スキルと同じ読み方（この環境の notion-client は databases 側に properties がある）
    existing = client.databases.retrieve(database_id=db_id)["properties"]
    print(f"イベントDB: 今ある列 {len(existing)} 個")

    to_add = {}
    for name, definition in COLUMNS.items():
        if name in existing:
            print(f"  すでにある（触らない）: {name} [{existing[name].get('type')}]")
        else:
            to_add[name] = definition
            print(f"  足す: {name} [{next(iter(definition))}]")

    if not to_add:
        print("足す列はありません。")
        return
    if not args.apply:
        print(f"dry-run: {len(to_add)} 列を足す予定。実際に足すには --apply")
        return

    client.databases.update(database_id=db_id, properties=to_add)
    after = client.databases.retrieve(database_id=db_id)["properties"]
    ok = [n for n in to_add if n in after]
    ng = [n for n in to_add if n not in after]
    print(f"足した: {len(ok)} 列 / 足せなかった: {len(ng)} 列 {ng if ng else ''}")
    print(f"イベントDB: 列 {len(existing)} → {len(after)} 個")
    lost = [n for n in existing if n not in after]
    print(f"消えた既存の列: {lost if lost else 'なし'}")


if __name__ == "__main__":
    main()
