# assets/manual/ — 手動画像（画像の“正”）

サイトに表示する画像は、**このフォルダに置いたファイルが最優先**です。
Notion は画像に使いません（表示バグ・URL失効があり信用しないため）。

## 使い方
1. `C:\Users\user\Downloads\琴平町イベント画像` などから、使いたい画像を
   このフォルダ（`assets/manual/`）にコピーする（ファイル名は自由。分かりやすい名前推奨）。
2. リポジトリ直下の `assets/image-overrides.json` に「どの項目にどの画像を出すか」を書く。
   - キー … その項目の **出典URL**（`http…`）、または **タイトルの一部**（空白区切りで複数語＝すべて含む項目にマッチ）
   - 値 … このフォルダ内のファイル名
3. `python scripts/fetch_notion.py` を実行 → マッチした項目はこの画像を使い、
   **Notionからは一切取得しません**（ログに「ローカル画像を◯件適用（Notion非経由）」と出ます）。
4. 画像ファイルと `image-overrides.json` を git にコミットすれば、公開サイトでも確実に出ます。

## 例（image-overrides.json）
```json
{
  "https://www.instagram.com/p/XXXX/": "kimono14.jpg",
  "夏のお茶会 藤田屋": "chakai_fujitaya.png"
}
```

- マッピングに無い項目は、従来どおり Notion の画像を試します（段階的に移行できます）。
- 指定したファイルがこのフォルダに無いと、fetch 実行時に警告が出ます（空表示に気づけるように）。
