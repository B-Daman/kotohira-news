# scripts/fetch_notion.py

Notionの「ニュースDB」「イベントDB」「キャンペーンDB」の3つを読み取り、
ダッシュボード表示用の `notion-data.js`（`window.NOTION_DATA`）を生成するスクリプトです。

pip依存なし（Python標準ライブラリのみ）で動作します。

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

## 週次運用での位置づけ

`notion-data.js` はダッシュボード（`index.html`）が読み込む静的データファイルです。
Notion側の更新を反映するには、週次などのタイミングで本スクリプトを再実行し、
生成された `notion-data.js` をコミット・デプロイしてください。
（`data.js` はSNS由来の別データで、本スクリプトの対象外です）

## 画像のローカル保存について

サムネイル/参考画像のURLは大半が期限付き署名URL（Notion S3は約1時間、
Discord CDNは約24時間で失効）のため、取得直後に `assets/thumbs/` へ
ダウンロードし、`notion-data.js` には相対パスを書き込みます。
ファイル名はNotionのページID（ハイフン除去）ベースで、既に同名ファイルが
あれば再ダウンロードしません。**本スクリプトはファイル削除を行わないため、
Notion側で画像を差し替えた場合など、`assets/thumbs/` に古い孤児ファイルが
残ることがあります。** 気になる場合は手動で整理してください。
