"""イベントDB と、表「ふるさと住民 ニュース」の「ふるさと住民アプリへの掲載」用の列を読み書きする道具。

掲載文そのものは人か AI が考える。この道具は、探す・見る・決まりを確かめて書く、だけを行う。
書くのは次の列だけ。ほかの列には触らない。
  ふる住 掲載／掲載文／カテゴリ／タグ、問い合わせ先 担当者名／電話／メール

使い方（notion-event-formatter の .venv の python で）:
    python scripts/furusato_post.py find [--from 2026-11-22] [--q おでん]   # これからのイベントを探す
    python scripts/furusato_post.py show <page_id>                          # 1件の中身を見る
    python scripts/furusato_post.py set <page_id> --file 掲載.json           # 何を書くかを表示（空実行）
    python scripts/furusato_post.py set <page_id> --file 掲載.json --apply   # 書く

ニュースの表を相手にするときは、どの命令にも --news を付ける（手順はイベントと同じ）:
    python scripts/furusato_post.py find --news [--q おでん]
    python scripts/furusato_post.py show <page_id> --news
    python scripts/furusato_post.py set <page_id> --news --file 掲載.json [--apply]
  ニュースの 掲載.json に書けるのは body / categories / tags / status / title だけ（問い合わせ先の欄は無い）。
  表のIDは、環境変数 FURUSATO_NEWS_DB_ID か、下の IDS_PATH のファイルから読む（公開リポジトリに書かないため）。

掲載.json の形（どの項目も省ける。省いた列は触らない）:
    {"body": "掲載文", "categories": ["食・特産品"], "tags": ["初心者歓迎"],
     "contact_name": "担当者名", "contact_phone": "0877-00-0000", "contact_email": "a@example.com",
     "status": "掲載文あり"}

設計: C:/Users/user/furusato-resident/検討/2026-11-21_貼り付け入力の道具_要件定義.md
"""
import argparse
import datetime
import json
import os
import re
import sys

SKILL_DIR = "C:/Users/user/.claude/skills/kotohira-news-register"
sys.path.insert(0, SKILL_DIR)
import register_news as rn  # noqa: E402
from notion_client import Client  # noqa: E402

CATEGORIES = [
    "まちづくり", "教育・子育て", "農林水産業", "自然・環境", "防災・安全", "観光・レジャー", "地域経済",
    "歴史・文化", "芸術・クリエイティブ", "食・特産品", "健康・福祉", "広報・メディア", "スポーツ", "国際・多文化交流",
]
STATUSES = ["載せる", "掲載文あり", "申請済み"]
P_STATUS, P_BODY, P_CATS, P_TAGS = "ふる住 掲載", "ふる住 掲載文", "ふる住 カテゴリ", "ふる住 タグ"
P_NAME, P_TEL, P_MAIL = "問い合わせ先 担当者名", "問い合わせ先 電話", "問い合わせ先 メール"
# 管理画面の決まり（拡張機能 furusato-paste-input と同じ）
LEFT = re.compile(r"要確認|未定|調整中|確認中|TODO|〇〇|○○|（仮）")


# 主催者ごとの問い合わせ先の控え。連絡先が入るので、このリポジトリ（公開）には置かない
CONTACTS_PATH = "C:/Users/user/furusato-resident/data/event-contacts.json"
# Notion の表のIDの控え（{"furusato_news_db_id": "…"}）。これも公開リポジトリには置かない
IDS_PATH = "C:/Users/user/furusato-resident/data/notion-ids.json"
N_TITLE, N_KIND, N_END = "タイトル", "種類", "掲載終了"
EVENT_KEYS = {"body", "categories", "tags", "contact_name", "contact_phone", "contact_email", "status"}
NEWS_KEYS = {"body", "categories", "tags", "status", "title"}


def news_db_id():
    value = os.environ.get("FURUSATO_NEWS_DB_ID")
    if not value:
        try:
            with open(IDS_PATH, encoding="utf-8") as f:
                value = json.load(f).get("furusato_news_db_id")
        except FileNotFoundError:
            value = None
    if not value:
        sys.exit(f"ニュースの表のIDがありません。環境変数 FURUSATO_NEWS_DB_ID か {IDS_PATH} に入れてください")
    return value


def load_contacts():
    try:
        with open(CONTACTS_PATH, encoding="utf-8") as f:
            return json.load(f).get("団体", {})
    except FileNotFoundError:
        return {}


def find_contact(org):
    """主催者の名前（または別名）で控えを引く。"""
    contacts = load_contacts()
    if org in contacts:
        return contacts[org]
    return next((c for c in contacts.values() if org in c.get("別名", [])), None)


def client_and_db():
    with open(SKILL_DIR + "/config-events.json", encoding="utf-8") as f:
        cfg = json.load(f)
    return Client(auth=rn.load_token(cfg)), rn.resolve_database_id(cfg)


def text_of(prop):
    """プロパティ1つを、人が読める文字にする。"""
    if not prop:
        return ""
    t = prop.get("type")
    v = prop.get(t)
    if v is None:
        return ""
    if t in ("title", "rich_text"):
        return "".join(x.get("plain_text") or x.get("text", {}).get("content", "") for x in v)
    if t in ("select", "status"):
        return v.get("name", "")
    if t == "multi_select":
        return "、".join(x.get("name", "") for x in v)
    if t == "date":
        return v.get("start") or ""
    if t in ("url", "email", "phone_number"):
        return v or ""
    if t == "number":
        return str(v)
    if t == "checkbox":
        return "✓" if v else ""
    if t == "relation":
        return f"（リレーション {len(v)}件）"
    if t == "rollup":
        return " / ".join(text_of(x) for x in v.get("array", [])) if v.get("type") == "array" else ""
    if t == "formula":
        return str(v.get(v.get("type")) or "")
    return ""


def cmd_find_news(args):
    client, _ = client_and_db()
    kw = {"filter": {"property": N_TITLE, "title": {"contains": args.q}}} if args.q else {}
    res = client.databases.query(database_id=news_db_id(), page_size=args.limit,
                                 sorts=[{"timestamp": "created_time", "direction": "descending"}], **kw)
    for p in res["results"]:
        pr = p["properties"]
        print(f"{p['created_time'][:10]} | {text_of(pr.get(N_KIND)) or '-':8} | {text_of(pr.get(P_STATUS)) or '-':6} | "
              f"終了 {text_of(pr.get(N_END)) or '-':10} | {text_of(pr.get(N_TITLE))} | {p['id']}")
    print(f"{len(res['results'])} 件（ふるさと住民 ニュース・新しい順）")


def cmd_find(args):
    if args.news:
        return cmd_find_news(args)
    client, db = client_and_db()
    start = args.date_from or datetime.date.today().isoformat()
    flt = {"and": [
        {"property": "開催日時（開始）", "date": {"on_or_after": start}},
        {"property": "カレンダー", "multi_select": {"contains": "基本のイベント"}},
    ]}
    if args.q:
        flt["and"].append({"property": "イベント名", "title": {"contains": args.q}})
    res = client.databases.query(database_id=db, filter=flt, page_size=args.limit,
                                 sorts=[{"property": "開催日時（開始）", "direction": "ascending"}])
    for p in res["results"]:
        pr = p["properties"]
        print(f"{text_of(pr['開催日時（開始）'])[:16]} | {text_of(pr.get(P_STATUS)) or '-':6} | {text_of(pr['イベント名'])} | {p['id']}")
    print(f"{len(res['results'])} 件（{start} 以降・基本のイベント）")


def cmd_show(args):
    client, _ = client_and_db()
    pr = client.pages.retrieve(page_id=args.page_id)["properties"]
    if args.news:
        for name in [N_TITLE, N_KIND, "メモ", "外部リンク", N_END, P_STATUS, P_CATS, P_TAGS, P_BODY]:
            print(f"【{name}】{text_of(pr.get(name))}")
        print(f"【画像】{len(pr.get('画像', {}).get('files', []))} 枚")
        return
    for name in ["イベント名", "開催日時（開始）", "開催日時（終了）", "市町村", "住所", "主催/運営", "参加費（日本円）", "内容",
                 "コメント", "ソース", "関連リンク", P_STATUS, P_CATS, P_TAGS, P_NAME, P_TEL, P_MAIL, P_BODY]:
        print(f"【{name}】{text_of(pr.get(name))}")
    places = pr.get("開催場所", {}).get("relation", [])
    for r in places:
        try:
            pp = client.pages.retrieve(page_id=r["id"])["properties"]
            title = next((text_of(v) for v in pp.values() if v.get("type") == "title"), "")
            print(f"【開催場所】{title}")
        except Exception:  # 場所DBに届かないときは名前を出さない
            print("【開催場所】（読めませんでした）")


def check(data, news=False):
    """書く前に、管理画面の決まりを確かめる。返すもの＝(エラー, 注意)"""
    err, warn = [], []
    unknown = set(data) - (NEWS_KEYS if news else EVENT_KEYS)
    if unknown:
        err.append(f"知らない項目: {sorted(unknown)}")
    body = data.get("body")
    if body is not None:
        if not isinstance(body, str):
            err.append("body は文字で")
        else:
            if len(body) > 800:
                err.append(f"掲載文が {len(body)} 字（800字まで。末尾にアンケートの段が付くため）")
            if LEFT.search(body):
                warn.append(f"掲載文に「{LEFT.search(body).group()}」が残っている")
            if not news and "http" not in body:
                warn.append("掲載文にアンケートの URL がない（琴平町の決まり）")
    cats = data.get("categories")
    if cats is not None:
        bad = [c for c in cats if c not in CATEGORIES]
        if bad:
            err.append(f"画面にないカテゴリ: {bad}")
        if len(cats) > 5:
            err.append("カテゴリは5件まで")
    tags = data.get("tags")
    if tags is not None:
        bad = [t for t in tags if len(t) > 10]
        if bad:
            err.append(f"10字を超えるタグ: {bad}")
        if len(tags) > 5:
            err.append("タグは5つまで")
        if any("," in t or "、" in t for t in tags):
            err.append("タグに「,」「、」は使えない（掲載データの区切りと重なる）")
    tel = data.get("contact_phone")
    if tel and not re.fullmatch(r"[0-9-]{1,13}", tel):
        err.append("電話は半角の数字とハイフンで13字まで")
    mail = data.get("contact_email")
    if mail and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", mail):
        err.append("メールの形ではない")
    title = data.get("title")
    if title is not None and not (isinstance(title, str) and 0 < len(title) <= 100):
        err.append("title は1〜100字で")
    name = data.get("contact_name")
    if name and len(name) > 100:
        err.append("担当者名は100字まで")
    if data.get("status") and data["status"] not in STATUSES:
        err.append(f"status は {STATUSES} のどれか")
    return err, warn


def cmd_set(args):
    with open(args.file, encoding="utf-8") as f:
        data = json.load(f)
    err, warn = check(data, args.news)
    for w in warn:
        print("注意:", w)
    if err:
        for e in err:
            print("エラー:", e)
        sys.exit(1)

    props = {}
    if "title" in data:
        props[N_TITLE] = {"title": [{"type": "text", "text": {"content": data["title"]}}]}
    if "body" in data:
        # rich_text は1かたまり2,000字まで。掲載文は1,000字までなので1つで足りる
        props[P_BODY] = {"rich_text": [{"type": "text", "text": {"content": data["body"]}}] if data["body"] else []}
    if "categories" in data:
        props[P_CATS] = {"multi_select": [{"name": c} for c in data["categories"]]}
    if "tags" in data:
        props[P_TAGS] = {"multi_select": [{"name": t} for t in data["tags"]]}
    if "contact_name" in data:
        props[P_NAME] = {"rich_text": [{"type": "text", "text": {"content": data["contact_name"]}}] if data["contact_name"] else []}
    if "contact_phone" in data:
        props[P_TEL] = {"phone_number": data["contact_phone"] or None}
    if "contact_email" in data:
        props[P_MAIL] = {"email": data["contact_email"] or None}
    status = data.get("status") or ("掲載文あり" if data.get("body") else None)
    if status:
        props[P_STATUS] = {"select": {"name": status}}
    client, _ = client_and_db()
    before = client.pages.retrieve(page_id=args.page_id)["properties"]
    if args.news:
        if N_KIND not in before:
            sys.exit("ニュースの表の行ではありません（--news を外すか、page_id を確かめてください）")
        print("ニュース:", text_of(before[N_TITLE]), "/", text_of(before.get(N_KIND)) or "種類なし")
    else:
        print("イベント:", text_of(before["イベント名"]), "/", text_of(before["開催日時（開始）"])[:16])

    # 問い合わせ先が掲載.json に無く、Notion にもまだ無いときは、主催者ごとの控えから入れる
    has_contact = any(k in data for k in ("contact_name", "contact_phone", "contact_email"))
    filled = any(text_of(before.get(n)) for n in (P_NAME, P_TEL, P_MAIL))
    if not args.news and not has_contact and not filled:
        orgs = [o.get("name", "") for o in before.get("主催/運営", {}).get("multi_select", [])]
        hit = next(((o, c) for o in orgs for c in [find_contact(o)] if c), None)
        if hit:
            org, c = hit
            sub = {k: c[k] for k in ("contact_name", "contact_phone", "contact_email") if c.get(k)}
            e2, _ = check(sub)
            if e2:
                print(f"注意: 控えの「{org}」に決まりに合わない値があるので使いません: {e2}")
            else:
                print(f"問い合わせ先を控えから入れます: {org}（確認日 {c.get('確認日', '不明')}）")
                if sub.get("contact_name"):
                    props[P_NAME] = {"rich_text": [{"type": "text", "text": {"content": sub["contact_name"]}}]}
                if sub.get("contact_phone"):
                    props[P_TEL] = {"phone_number": sub["contact_phone"]}
                if sub.get("contact_email"):
                    props[P_MAIL] = {"email": sub["contact_email"]}
        elif orgs:
            print(f"問い合わせ先の控えなし: {'、'.join(orgs)}（主催者に聞いて {CONTACTS_PATH} に書く）")
    if not props:
        print("書く項目がありません。")
        return
    for name in props:
        old = text_of(before.get(name))
        new = text_of({**props[name], "type": next(iter(props[name]))})
        mark = "（変更なし）" if old == new else ""
        print(f"--- {name} {mark}")
        if old != new:
            print(f"  今: {old[:80]!r}{'…' if len(old) > 80 else ''}")
            print(f"  → : {new[:80]!r}{'…' if len(new) > 80 else ''}（{len(new)}字）")
    if not args.apply:
        print("dry-run: 書いていません。書くには --apply")
        return
    client.pages.update(page_id=args.page_id, properties=props)
    after = client.pages.retrieve(page_id=args.page_id)["properties"]
    ng = [n for n in props if text_of(after.get(n)) != text_of({**props[n], "type": next(iter(props[n]))})]
    print("書きました。" if not ng else f"書けなかった列: {ng}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("find")
    f.add_argument("--from", dest="date_from")
    f.add_argument("--q")
    f.add_argument("--limit", type=int, default=30)
    f.add_argument("--news", action="store_true", help="表「ふるさと住民 ニュース」を相手にする")
    f.set_defaults(fn=cmd_find)
    s = sub.add_parser("show")
    s.add_argument("page_id")
    s.add_argument("--news", action="store_true")
    s.set_defaults(fn=cmd_show)
    w = sub.add_parser("set")
    w.add_argument("page_id")
    w.add_argument("--file", required=True)
    w.add_argument("--apply", action="store_true")
    w.add_argument("--news", action="store_true")
    w.set_defaults(fn=cmd_set)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
