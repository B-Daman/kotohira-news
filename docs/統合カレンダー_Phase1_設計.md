# 統合イベントカレンダー Phase 1 設計（multi-select レイヤー・金刀比羅宮レイヤー・一括付与）

- 作成: 2026-11-05（会話セッション）
- 前提: `docs/統合カレンダー要件定義.md` v1.0 ＋ 追補 v1.1（multi-select・値3つ明示・町外OK欄なし）。本人作業「NotionイベントDBに multi-select『カレンダー』を作る」は 2026-11-05 に完了（API で確認: 値＝基本のイベント／こんぴらカレンダー／金刀比羅宮）
- 状態: **設計（実装未着手）**

---

## 1. 現状の事実（2026-11-05 調査）

- イベントDB: 821件（2024-10-19〜2026-12-29）。「カレンダー」が空＝820件、`基本のイベント`＝1件（本人の試し）。「大規模イベント」✓＝2件。今日以降の件＝30
- サイトが読む `notion-data.js` は終了60日超を落とし上限200件なので106件。`calendar`/`featured` キーは未出力
- **未マージのブランチ `calendar-phase1`（0aab646・2026-09-10・wip）** に Phase 1 の表示実装がある（index.html +158/−15・fetch_notion.py +5）。main と衝突なし。中身は v1.0 の select（文字列1つ）前提
- `scripts/fetch_notion.py` に `get_multi_select`（空なら `[]`）・`get_checkbox` のヘルパーがある。`parse_event` はキャンペーンDBと共用（該当プロパティが無い DB では `[]`／False になるだけ）
- 登録ツール `~\.claude\skills\kotohira-news-register\register_news.py` ＋ `config-events.json`（イベントDB向け・dedup=title_date・defaults.カレンダー="金刀比羅宮"）。`--dry-run` あり。multi_select はカンマ区切り文字列で複数値。relation（開催場所）は送れない＝会場はコメント欄。終了日は「開催日時（終了）」を item に入れれば送れる見込み（dry-run で確認）
- トークン: ニュース登録の書き込みトークン（keyring `kotohira-notion-register`・`KOTOHIRA_NOTION_TOKEN`）は**イベントDBにも届く**（databases.retrieve OK・2026-11-05 確認）。`config-events.json` は `KOTOHIRA_EVENTS_NOTION_TOKEN` を探すため、そのままでは「トークンが見つかりません」で止まる
- **金刀比羅宮の61件のデータは消えている**（旧セッションの scratchpad のみに置かれていた）。公式サイトから取り直す（`docs/data/konpira-events-2026.json` に**リポジトリ内で**保存する）
- 既存のイベントDBに例大祭が4件ある（令和8年 金刀比羅宮例大祭／宵宮祭 10/9／例祭と御本宮発御 10/10／御旅所発御 10/11）。新規作成ではなく値を足す
- konpie-bot の登録経路 `konpie-bot\src\cogs\register_watcher.py` の `_map_event_like`（:73-93）が Discord からのイベント登録を作る。既定値はここで足す
- 開発ダッシュボード `docs/開発ダッシュボード.base.html` は v1.0・select 前提の記述（:327 現在地、:861-876 詳細設計§3、:1230-1272 検討中の案）。`python scripts/build_dashboard.py` で再生成。要件定義タブは `<!--@MD docs/統合カレンダー要件定義.md-->` で自動取り込み

## 2. データ

| 場所 | 変更 |
|---|---|
| Notion イベントDB | 変更なし（multi-select「カレンダー」作成済み・checkbox「大規模イベント」既存） |
| `fetch_notion.py` `parse_event` | `"calendar": get_multi_select(properties, "カレンダー")`（配列）、`"featured": get_checkbox(properties, "大規模イベント")` の2行 |
| `notion-data.js` events | `calendar: string[]`（空配列＝未分類）、`featured: bool` が全件に付く。campaigns にも付くが `[]`/false |

未分類（空配列）は**サイトでは基本のイベントとして扱う**（一括付与の前後で見た目が変わらない）。

## 3. index.html（ブランチ `calendar-phase1` をマージしてから v1.1 に書き直す）

### 3-1. 変えないもの（ブランチのまま使う）

色トークン `--cal-konpira`（紫）`--cal-towncal`（緑）、CSS `.cal-layer-chip` `.cal-source-dot` `.cal-src-*`、`toggleEventCalLayer`（イベントタブ本体の再描画・フォーカス戻し）、`eventsTabBodyHTML`、`switchEventCalView`／`navigateCalendar` の `visibleEvents()` 化、`onMainClick` の `data-cal-layer` 分岐

### 3-2. 書き直すもの（select → multi-select）

```js
const EVENT_CAL_BASE = "基本のイベント";
const EVENT_CAL_LAYER_ORDER = [EVENT_CAL_BASE, "金刀比羅宮", "こんぴらカレンダー"];
const EVENT_CAL_LAYER_META = {
  [EVENT_CAL_BASE]: {emoji:"📅", label:"基本のイベント", cls:"cal-src-town"},
  "金刀比羅宮":     {emoji:"⛩", label:"金刀比羅宮",     cls:"cal-src-konpira"},
  "こんぴらカレンダー": {emoji:"🗓", label:"こんぴらカレンダー", cls:"cal-src-towncal"}
};
let eventCalLayers = {[EVENT_CAL_BASE]: true, "金刀比羅宮": true, "こんぴらカレンダー": false};

function calsOf(it){            // 未分類（空配列・キー無し）は基本のイベント扱い
  const a = Array.isArray(it.calendar) ? it.calendar.filter(Boolean) : [];
  return a.length ? a : [EVENT_CAL_BASE];
}
function isEventLayerOn(key){ return key in eventCalLayers ? eventCalLayers[key] : true; }  // 未知の値は既定ON
function isEventVisible(it){ return calsOf(it).some(isEventLayerOn); }
function visibleEvents(){ return ND.events.filter(isEventVisible); }
function homeEvents(){          // ホームの直近: 基本のイベント ＋ 金刀比羅宮のうち大規模✓
  return ND.events.filter(it => { const c = calsOf(it); return c.includes(EVENT_CAL_BASE) || (c.includes("金刀比羅宮") && it.featured); });
}
function calPrimary(it){        // 色の優先: 金刀比羅宮 > こんぴらカレンダー > 基本（無指定）
  const c = calsOf(it);
  if(c.includes("金刀比羅宮")) return "金刀比羅宮";
  if(c.includes("こんぴらカレンダー")) return "こんぴらカレンダー";
  if(c.includes(EVENT_CAL_BASE)) return EVENT_CAL_BASE;
  return c[0];
}
function calSourceClass(it){ const p = calPrimary(it); return p === EVENT_CAL_BASE ? "" : " " + ((EVENT_CAL_LAYER_META[p]||{}).cls || "cal-src-other"); }
function calSourceDotsHTML(it){ // 値の数だけ色ドット（基本も含む・最大3）
  return calsOf(it).slice(0,3).map(k => `<span class="cal-source-dot ${(EVENT_CAL_LAYER_META[k]||{}).cls || 'cal-src-other'}" aria-hidden="true"></span>`).join("");
}
```

- 呼び出し側: ブランチの `calSourceClass(it.calendar)` → `calSourceClass(it)`、`calSourceDotHTML(it.calendar)` → `calSourceDotsHTML(it)`（月グリッド・週グリッド・バー）
- **チップは3つ固定**で常に出す（ブランチの「非空値が無ければ出さない」を外す）。データに未知の値があれば末尾にデータ駆動で足す。チップの並びと見た目は `.cal-layer-chip`
- 詳細モーダルのソースバッジは**値の数だけ**並べる。基本のイベントだけの件はバッジを出さない（今までどおり）。基本＋こんぴらカレンダーの件は「🗓 こんぴらカレンダー」だけ出す（基本は暗黙）
- 全レイヤーOFFのときの文言はブランチのまま
- 初期状態・ページ内のみ保持（localStorage なし）は要件どおり

### 3-3. 触らない箇所

ホームの外側の空判定（`ND.events.length`）はブランチのとおり `ND.events` のまま。ディープリンクの迂回路は無い（調査済み）

## 4. 既存イベントへの一括付与（`scripts/backfill_calendar.py` 新規）

- 対象: 「カレンダー」が空の全件（今日時点 820件。過去のイベントも含める＝未分類を残さない）
- 読み: `fetch_notion.py` の関数で data_sources API（2025-09-03）から全件を取り、空の件の id を集める
- 書き: 書き込みトークンで `PATCH /v1/pages/{id}` に `{"properties": {"カレンダー": {"multi_select": [{"name": "基本のイベント"}]}}}`。他のプロパティは送らない
- `--dry-run`（件数と先頭10件の題名・日付を表示。書かない）→ 本人の「実行して」→ `--apply`（毎秒3件以内・失敗は id と理由をログに残して続行・最後に件数を報告）
- 一度きりの道具。実行後に `fetch_notion.py` を回して `notion-data.js` の calendar が入ったことを確認する
- 守ること: トークンの値を出力しない。`.env` を読まない（keyring 経由）。削除・他プロパティの変更をしない

### 4-1. トークンの参照名

`config-events.json` の `token_env` を `KOTOHIRA_NOTION_TOKEN` に揃える（同じ書き込みトークンでイベントDBに届くことを確認済み）。v1.0 が心配した「読み取り専用トークンとの衝突」は、kotohira-news の `.env` を読み込む処理の中でだけ起きる話で、登録スキルは keyring から読むので起きない。`backfill_calendar.py` も同じ `load_token(config-events.json)` を使う

## 5. 登録経路の既定値

| 経路 | 変更 |
|---|---|
| `config-events.json`（通常のイベント登録） | `defaults.カレンダー` を `"基本のイベント"` に |
| `config-events-konpira.json`（新規・金刀比羅宮の一括登録専用） | `defaults.カレンダー` を `"金刀比羅宮"`。大規模行事は item 側で `"基本のイベント,金刀比羅宮"`、`大規模イベント: true` |
| konpie-bot `register_watcher.py` `_map_event_like` | `kind == "event"` のとき `"カレンダー": "基本のイベント"` を足す（campaign には足さない） |
| Phase 2（こんぴらカレンダー CSV） | `"こんぴらカレンダー"` を付け、承認画面のチェックで `基本のイベント` を足す（別設計） |

## 6. 金刀比羅宮の年中行事の登録

1. **再取得**: 公式サイト（konpira.or.jp）の令和8年年間行事から `docs/data/konpira-events-2026.json` を作る（調査担当が 2026-11-05 に実行中。リポジトリに置き、消えないようにする）。規則は v1.0 のとおり: 裏取りできた行事のみ／月次祭は登録しない／祝舎系は2026年分のみ／移動祝日連動は実日付で
2. **突合**: 既存の例大祭4件は新規作成せず「カレンダー」に `金刀比羅宮` を足す（`基本のイベント` は既に一括付与で付いている）。その他は `register_news.py --config config-events-konpira.json --dry-run` で重複（title_date・類似0.85）を見る
3. **承認**: dry-run の一覧（件数・重複・保留）を本人が見て「登録して」→ 本登録。登録件数と結果を報告
4. 会場は「開催場所」relation に送れないのでコメント欄に書く（既存どおり）
5. 年次運用: 毎年1月に公式の新年度一覧と突き合わせ（移動祝日連動の件は必ず確認）

## 7. 開発ダッシュボード

`docs/開発ダッシュボード.base.html` の次を v1.1・実装状況に合わせて書き換え、`python scripts/build_dashboard.py` で再生成する: 現在地（:327）／詳細設計§3（:861-876・行番号は実装後に取り直す）／検討中の案（:1230-1272）／決定ログに 2026-11-05 の裁定（multi-select・値3つ・町外OK欄なし・Phase 3 ICS）／要件定義タブの説明文（:375 を v1.1 に）

## 8. 手順と分担

1. ブランチ `calendar-phase1` を main にマージ（衝突なし確認済み）→ 3-2 の書き直し → `fetch_notion.py` 2行（sonnet）
2. ローカルで `fetch_notion.py` を回し `notion-data.js` に `calendar`/`featured` が入ることを確認（まだ全件 `[]`＝見た目は変わらない）。`node --check`、headless Chrome でスタブデータ（配列値を注入）のレイヤー切替・色・ホームの規則・モーダルのバッジを確認（sonnet。本人にスクショを頼まない）
3. コミット・push（毎時の Actions が `notion-data.js` を再生成する）
4. `backfill_calendar.py` の dry-run → **本人の承認** → apply → 再取得で確認（Fable）
5. `config-events.json` の既定値と token_env、konpie-bot の既定値（sonnet）。konpie-bot は Railway 稼働中なので、変更は commit・push して再デプロイの確認まで
6. 金刀比羅宮: データ取得（進行中）→ dry-run → **本人の承認** → 登録（Fable）
7. ダッシュボード更新・再生成・コミット
8. Fable が全体を確認

## 9. 本人の判断が要る点

1. 一括付与（4章）の apply。dry-run の件数を見てから
2. 金刀比羅宮の登録（6章）。dry-run の一覧を見てから
3. 既存の例大祭4件に `金刀比羅宮` を足すこと（6-2）。既定: 足す

## 10. 守ること

- Notion への書き込みは dry-run → 本人の承認 → 実行の順。トークンは出力しない。`.env` は読まない
- 削除をしない。既存のプロパティ値を上書きしない（空の件に値を足すだけ）
- サイトの見た目は、一括付与の前後で変わらない（未分類＝基本のイベント扱い）
- 新しい周期・常駐は増やさない（Actions の毎時更新に乗る）
