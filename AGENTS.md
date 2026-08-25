# kotohira-news

表示名「ことひらいふ」。琴平町のニュース・イベント・キャンペーン・グルメ等を集約する静的サイト。将来のGitHub Pages公開を想定している（現時点では予定段階、README記載）。

## Scope And Sources of Truth

- 表示部の正本は `index.html`。`index-legacy.html` / `index-redesign.html` / `index-redesign2.html` / `index-before-portal-sidebar-20260714.html` は旧版・比較用であり、通常の作業対象ではない。
- データは複数系統あり、それぞれ生成経路が異なる。**手編集せず生成元を経由する**:
  - `registry.json`（団体×媒体の正本）→ `/kotohira-news` スキル経由で `data.js` を再生成
  - Notion 3DB（イベント/キャンペーン/ニュース）→ `scripts/fetch_notion.py` 経由で `notion-data.js` を再生成（GitHub Actions `.github/workflows/update-notion-data.yml` が毎日15:00 UTC＝JST 0:00に自動実行し、コミット・pushまで行う）
  - `udon-data.js` / `parking-data.js` / `links-data.js` / `experiences-data.js` / `cool-sweets-data.js` / `site-widgets-data.js` は手編集運用（現状把握、生成スクリプトは未確認）
- 画像は長辺1200pxのWebPに揃える。`fetch_notion.py` が取得時に圧縮し、`find_local_thumb` は
  同名ファイルがあれば `.webp` を優先する。手動で `assets/` に画像を足す場合も、
  数MBの原寸ファイルをそのまま置かない（閲覧者の通信量に直結する）
- `.env` / `.env.example` が直下に存在する。**中身は読み取らず、値を回答に表示しない。** GitHub Actions側ではNotionトークンをGitHub Secretsで参照する設計（ワークフローyaml上で確認済み）。

## Safe Static Verification

- `python scripts/fetch_notion.py` — Notionからデータ取得し `notion-data.js` を再生成（pip依存なし、README記載）。ただし外部API呼び出しを伴うため実行前に確認する。
- `index.html` をブラウザで開いての目視確認。

## Live Operations

- GitHub Actions によるNotionデータの自動取得・自動コミット・自動pushは無人で動いている。手動での `git push` は既存の自動更新と衝突しないよう `git status` / `git log` を確認してから行う。
- GitHub Pages公開後は、公開リポジトリに個人情報・未公開の数値をコミットしないよう特に注意する（現時点では公開は予定段階）。

## Project Shape

- `index.html` — 表示部の正本
- `registry.json` — 団体×媒体データの正本
- `data.js` / `notion-data.js` / `udon-data.js` / `parking-data.js` / `links-data.js` / `experiences-data.js` / `cool-sweets-data.js` / `site-widgets-data.js` — 表示用データ（生成物または手編集、上記参照）
- `scripts/fetch_notion.py` — Notionデータ取得スクリプト
- `scripts/image_utils.py` — 画像をWebPへ縮小・圧縮する共通処理（Pillowが無ければ無圧縮で続行）
- `scripts/compress_thumbs.py` — 既存画像を一括でWebP化する一回性スクリプト（2026-08-25実行済み）
- `assets/` — サムネイル・リンク・体験・手動画像
- `docs/` — 要件定義書・設計書・ロードマップ
- `.github/workflows/update-notion-data.yml` — 日次自動更新ワークフロー
- `operator.html` / `privacy.html` — 運営者情報・プライバシーページ

## Development Notes

- `.env` の値は絶対に読み取らない・出力しない。
- 旧版HTML（`index-legacy.html` 等）を誤って本番導線に混ぜない。
- 生成物系のJSファイルを直接編集すると、次回の自動更新やスキル実行で上書きされる。

## Definition of Done

- データ変更は正しい生成元（registry.json → スキル、Notion → fetch_notion.py）を経由している。
- `.env` の中身を読んだり出力したりしていない。
- 公開想定のファイルに個人情報・未公開の数値が含まれていない。
- GitHub Actionsの自動更新との競合が無いことを確認した。
