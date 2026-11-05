# 統合イベントカレンダー Phase 3 設計（レイヤー別 ICS 配信 → Google カレンダー購読）

- 作成: 2026-11-05（会話セッション）
- 前提: 追補 v1.1 の Phase 3（本人要望「3つのカレンダーを別々に管理したまま、自分のスケジュールに反映したい」）。Phase 1 実装済み
- 状態: **設計（実装は同日に着手）**

---

## 1. 方針

サイトが ICS（iCalendar）ファイルを配信し、本人が Google カレンダーで「URL で追加」する。書き込み権限を一切持たないので事故が起きない。レイヤー別に分けるので Google 側でも ON/OFF できる。

## 2. 配信するファイル（サイト直下）

| ファイル | 中身 |
|---|---|
| `events-all.ics` | 全件 |
| `events-base.ics` | `基本のイベント` を持つ件（未分類＝空も含む） |
| `events-konpira.ics` | `金刀比羅宮` を持つ件 |
| `events-towncal.ics` | `こんぴらカレンダー` を持つ件 |

- 元データ: `notion-data.js` の events（終了から60日以内と今後・上限200件）。過去の全件は入れない（購読カレンダーは今後の予定が要る）
- 生成: `scripts/build_ics.py`（新規）。毎時の `update-notion-data.yml` で `fetch_notion.py` の直後に実行し、変更があれば既存のコミット段で一緒にコミット（`git add *.ics`）
- 1件の書き方: `UID`＝Notion ページ id＋`@kotohilife.com`、`DTSTART`／`DTEND`（時刻ありは `TZID=Asia/Tokyo`、終日は DATE で終了＋1日）、`SUMMARY`＝イベント名、`LOCATION`＝開催場所（無ければ市町村）、`DESCRIPTION`＝コメント＋参加費＋主催＋サイトのイベントURL、`URL`＝公式リンク、`CATEGORIES`＝カレンダー値、`DTSTAMP`＝取得日時。`X-WR-CALNAME` にレイヤー名（例「ことひらいふ 金刀比羅宮」）、`X-WR-TIMEZONE=Asia/Tokyo`。行は 75 バイト折り返し・CRLF（RFC 5545）
- 複数日の件は DTSTART の日から DTEND（終了日＋1）まで

## 3. サイト側の案内

- イベントタブのカレンダーの下（チップの近く）に「📲 自分のカレンダーに入れる」の小さな節: 4つの ICS の URL と、Google カレンダーの手順（「他のカレンダー」＋ →「URL で追加」→ URL を貼る。反映は Google 側の周期で半日〜1日）を3行で
- Phase 2 の「こんぴらカレンダー」は町民向けなので、案内の既定は all・base・konpira の3つを前に、towncal は「町民向け」の注記つきで後ろに

## 4. 本人の使い方（1回だけ）

Google カレンダーで4本（または必要な分）を URL で追加する。以後は自動で更新される。

## 5. 守ること

- ICS に個人情報を入れない（イベントDBの公開項目だけ。konpie-bot が持つ内部メモは使わない）
- 60日より前の件は入れない（ファイルが肥大しない）
- 既存の毎時 workflow に乗せる。新しい周期は作らない

## 6. 検証

- `python scripts/build_ics.py` を手で回し、4ファイルが RFC 5545 の体裁（BEGIN/END・CRLF・折り返し）であること。Google カレンダーの取り込みは本人が1本試す（URL 追加後、予定が見えるか）
- `update-notion-data.yml` を手動起動し、`*.ics` がコミットされ `https://kotohilife.com/events-all.ics` が取れること
