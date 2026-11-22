"""イベントDBと表「ふるさと住民 ニュース」に、感想アンケートの URL の列を足す（一回限りの道具）。

モニター実証の間は、記事の説明文の末尾に感想アンケートの段を付ける決まり（2026-11-22）。
URL は団体専用の「アンケートURL生成」ページで本人が発行する（番号は記事タイトルと結び付くので、自動では作らない）。
発行した URL を列「ふる住 アンケートURL」に貼ると、関数「ふる住 掲載データ」の本文の末尾に、決まった段が付く。
空のままなら、これまでと同じ文が出る。

既定は dry-run（いまの関数を表示するだけ）。--apply で列を足し、関数を書き換える。

使い方（notion-event-formatter の .venv の python で）:
    python scripts/add_furusato_survey_column.py
    python scripts/add_furusato_survey_column.py --apply
"""
import argparse
import json
import sys

SKILL_DIR = "C:/Users/user/.claude/skills/kotohira-news-register"
sys.path.insert(0, SKILL_DIR)
import register_news as rn  # noqa: E402
from notion_client import Client  # noqa: E402

# 表のIDは、公開リポジトリに書かない。手元の控えから読む
IDS_FILE = "C:/Users/user/furusato-resident/data/notion-ids.json"
SURVEY = "ふる住 アンケートURL"
FORMULA_NAME = "ふる住 掲載データ"
BODY = 'prop("ふる住 掲載文")'
# 段の文言は、本人が申請で使った形（2026-11-22）
BODY_WITH_SURVEY = (
    f'({BODY} + if(empty(prop("{SURVEY}")), "", '
    '"\\n\\n【記事の感想について】\\n記事の感想は、以下のアンケートにご記入頂けますと幸いです。\\n"'
    f' + prop("{SURVEY}")))'
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    with open(SKILL_DIR + "/config-events.json", encoding="utf-8") as f:
        cfg = json.load(f)
    client = Client(auth=rn.load_token(cfg))
    with open(IDS_FILE, encoding="utf-8") as f:
        news_db_id = json.load(f)["furusato_news_db_id"]
    for label, db_id in (("イベントDB", rn.resolve_database_id(cfg)), ("ニュースの表", news_db_id)):
        props = client.databases.retrieve(database_id=db_id)["properties"]
        expr = props[FORMULA_NAME]["formula"]["expression"]
        print(f"== {label}（列 {len(props)} 個）")
        print("  いまの関数:", expr)
        if SURVEY in expr or "アンケート" in expr:
            print("  関数はもう書き換え済み（触らない）")
            continue
        if expr.count(BODY) != 1:
            print("  関数の中に本文の列が1つだけ見つからないので、止めます")
            continue
        new_expr = expr.replace(BODY, BODY_WITH_SURVEY)
        print("  新しい関数:", new_expr)
        if not args.apply:
            continue
        if SURVEY not in props:
            client.databases.update(database_id=db_id, properties={SURVEY: {"url": {}}})
        client.databases.update(database_id=db_id, properties={FORMULA_NAME: {"formula": {"expression": new_expr}}})
        after = client.databases.retrieve(database_id=db_id)["properties"]
        print(f"  列 {len(props)} → {len(after)} 個。{SURVEY}: {'あり' if SURVEY in after else 'なし'}")
        print("  書き換え後:", after[FORMULA_NAME]["formula"]["expression"])
    if not args.apply:
        print("dry-run: 書いていません。実際に行うには --apply")


if __name__ == "__main__":
    main()
