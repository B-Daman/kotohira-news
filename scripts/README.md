# scripts/fetch_notion.py

Notionの「ニュースDB」「イベントDB」「キャンペーンDB」の3つを読み取り、
ダッシュボード表示用の `notion-data.js`（`window.NOTION_DATA`）を生成するスクリプトです。

pip依存なし（Python標準ライブラリのみ）で動作します。

Pillow が入っている環境では、サムネイル保存時に長辺1200pxへ縮小してWebPへ圧縮します。
入っていなければ圧縮せず原寸のまま保存するため、動作自体は変わりません。
GitHub Actions では uv 経由で Pillow を用意しています（`uv run --with Pillow`）。

## scripts/compress_thumbs.py

圧縮機能を入れる前に保存された既存画像（`assets/thumbs/` と `assets/manual/`）を、
まとめてWebPへ変換する一回性のスクリプトです。2026-08-25 に実行済みで、
参照中の画像は約90MBから11.8MBになりました。

元ファイルは削除せず、変換で不要になった一覧を `scripts/unused-images.txt` に出力します。
削除するかどうかは中身を確認したうえで判断してください。

```bash
python scripts/compress_thumbs.py --dry-run   # 結果の見込みだけ表示
python scripts/compress_thumbs.py             # 実行（何度実行しても結果は同じ）
```

## セットアップ手順

> **既存トークンの使い回し（推奨の近道）**: konpie-bot の読み取り専用トークン
> `KOTOHIRA_NOTION_TOKEN` をそのまま使えます。その場合、手順1は不要で、
> 手順2（ニュースDB・キャンペーンDBへのコネクト追加。イベントDBはコネクト済みのはず）と
> 手順3（トークン値を `KOTOHIRA_DASHBOARD_NOTION_TOKEN` に設定）のみ行ってください。
> 書き込み用の `NEWS_NOTION_TOKEN` は使わないこと（最小権限の原則）。
> なお konpie-bot 側でトークンをローテーションすると本スクリプトも401で止まる点に注意。

### 1. 読み取り専用インテグレーションの作成

1. https://www.notion.so/my-integrations を開き「新しいインテグレーション」を作成
2. 種類は「内部インテグレーション」、権限は **「コンテンツを読み取る」のみ** を付与する
   （更新・挿入・削除の権限は付けない。konpie-bot側の書き込み用トークンとは別物にする）
3. 発行された Internal Integration Secret（`ntn_...` など）を控える

### 2. 3つのDBへコネクト

Notion上で以下の3つのデータベースをそれぞれ開き、右上「...」メニュー →
「コネクト」から、手順1で作成したインテグレーションを追加する。

- ニュースDB
- イベントDB
- キャンペーンDB

コネクトを忘れているDBがあると、実行時にそのDBだけ HTTP 404 で失敗します
（他の2DBが成功していれば、そのDB分は既存の `notion-data.js` の内容を温存して継続します）。

> **会場DBにも別途コネクトが必要（2026-07-09判明）**: イベントDBの「開催場所」プロパティは
> 会場名を管理する別DB（会場DB）へのrelationになっている。会場DB自体にも本インテグレーションの
> コネクトを追加しないと、会場ページの取得が404になり（例外は握りつぶされる）、そのイベントの
> `place`（開催場所名）・`address`（住所）が空のまま出力されてしまう。実際に会場DBを共有した
> ことで `place` 72/85件・`address` 67/85件が入るようになった実績あり。詳細は後述
> 「イベントDBのプロパティ型の癖」を参照。

### 3. 環境変数の設定

| 環境変数 | 内容 | 必須/任意 |
|---|---|---|
| `KOTOHIRA_DASHBOARD_NOTION_TOKEN` | 手順1で発行したトークン（優先） | どちらか必須 |
| `NOTION_TOKEN` | 上記が無い場合のフォールバック | どちらか必須 |
| `NEWS_NOTION_DB_ID` | ニュースDBのID（省略時は既定値） | 任意 |
| `KOTOHIRA_DATABASE_ID` | イベントDBのID（省略時は既定値） | 任意 |
| `CAMPAIGN_NOTION_DB_ID` | キャンペーンDBのID（省略時は既定値） | 任意 |

設定方法は2つ（どちらでも可）:

**A. `.env` ファイル（推奨・毎回の設定が不要）**

リポジトリ直下の `.env.example` を `.env` という名前でコピーし、トークンを記入する。
`.env` は .gitignore 済みでコミットされません。

**B. PowerShellの環境変数（そのセッション限り）**

```powershell
$env:KOTOHIRA_DASHBOARD_NOTION_TOKEN = "ntn_xxxxxxxx"
```

## 実行方法

```bash
python scripts/fetch_notion.py
```

リポジトリ直下に `notion-data.js` を UTF-8 で生成/更新します。

## 運用での位置づけ

`notion-data.js` はダッシュボード（`index.html`）が読み込む静的データファイルです。

**2026-07-19以降は GitHub Actions（`.github/workflows/update-notion-data.yml`）が毎日
00:00 JST に本スクリプトを自動実行し、差分があればコミット・push（=GitHub Pages反映）します。**
トークンはリポジトリSecret `KOTOHIRA_DASHBOARD_NOTION_TOKEN` から渡されます。
ローカルでの手動実行（.env利用）は、即時反映やデバッグ時の手段として引き続き使えます。
（`data.js` はSNS由来の別データで、本スクリプトの対象外です）

## イベントDBのプロパティ型の癖（get_any_text）

イベントDBはプロパティごとにNotion上の型がまちまちで、rich_text専用の取得関数だと
値があるのに空文字になってしまう項目があった。これに対応するため、プロパティの型を
問わず平文を取り出す `get_any_text()` を追加している（rich_text/title/select/
multi_select/formula/rollupに対応）。主な対象:

| プロパティ名 | Notion上の型 | 備考 |
|---|---|---|
| 参加費（日本円） | 数値（number） | 旧実装（テキスト専用取得）では値が入らず空になっていた。表示側（`index.html`の`formatEventFee()`）で0=「無料」、それ以外は「N,NNN円」に整形する |
| 主催/運営 | マルチセレクト（multi_select） | 旧実装では空になっていた。複数選択時は " / " で連結して1つの文字列にする |
| 住所 | ロールアップ（rollup） | 「開催場所」relationの参照先（会場ページ）から自動で入る。開催場所が未設定、または参照先の会場DBが未共有だと空になる |
| 開催場所 | リレーション（relation） | テキストではないため、そのままでは会場ページのIDしか取れない。会場名への解決は下記参照 |

### 開催場所（relation）の会場名解決

`fetch_events()` は各イベントの「開催場所」relationからページID一覧を集め（`_place_ids`）、
`resolve_place_names()` が各IDに対応する会場ページのタイトルを取得して `place` に書き込む
（複数会場が紐づく場合は " / " で連結）。同じ会場を多くのイベントが参照するため、ページIDで
キャッシュしてAPIコール数を会場の種類数ぶんに抑えている。`_place_ids` は解決後に取り除かれ、
最終的な `notion-data.js` には含まれない。

会場ページがインテグレーションに共有されていない（コネクトされていない）場合、ページ取得は
HTTP 404になるが、`fetch_page_title()` は例外を握りつぶして空文字を返す仕様になっている
（イベント表示自体は止めないため）。そのため、コネクト漏れがあってもエラーは出ず、該当イベントの
`place`・`address` が静かに空になる点に注意（上記「会場DBにも別途コネクトが必要」参照）。

## 画像のローカル保存について

サムネイル/参考画像のURLは大半が期限付き署名URL（Notion S3は約1時間、
Discord CDNは約24時間で失効）のため、取得直後に `assets/thumbs/` へ
ダウンロードし、`notion-data.js` には相対パスを書き込みます。
ファイル名はNotionのページID（ハイフン除去）ベースで、既に同名ファイルが
あれば再ダウンロードしません。**本スクリプトはファイル削除を行わないため、
Notion側で画像を差し替えた場合など、`assets/thumbs/` に古い孤児ファイルが
残ることがあります。** 気になる場合は手動で整理してください。
