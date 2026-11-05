/* 🗓 こんぴらカレンダー（広報ことひら誌面のカレンダー面を画像として掲載）。
   手編集運用（Notion連携ではなくコード直書き）。

   月次運用手順:
   (1) 新しい号のカレンダー面画像を長辺1200px以内のWebPで assets/towncal/YYYY-MM.webp に置く
   (2) このファイルの month / image / sourceName を書き換える
   それだけで表示が切り替わる。(1)(2)は scripts/fetch_towncal.py で自動化できる
   （町ホームページのPDF/画像URLとページ番号を渡すと両方まとめてやってくれる。使い方は
   スクリプト先頭のコメント参照）。
   (3) 誌面の行事を転記した assets/towncal/events-YYYY-MM.csv を同時に置く（2026-11-05〜。
   列= date,dow,title,time,place,booking,category,note,source。category は色分けからの推定。
   統合カレンダー Phase 2（Notion 登録）の入力）。 */
window.TOWNCAL = {
  month: "2026-11",                          // 掲載中の号（YYYY-MM）
  image: "assets/towncal/2026-11.webp",
  sourceName: "広報ことひら 2026年11月号",
  sourceUrl: "https://www.town.kotohira.kagawa.jp/site/kouhou/list18.html",
  sourceLinkLabel: "琴平町ホームページ（広報ことひら）"
};
