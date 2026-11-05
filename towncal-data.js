/* 🗓 こんぴらカレンダー（広報ことひら誌面のカレンダー面を画像として掲載）。
   issues[] は号の一覧（新しい順）。ページは今日の年月と同じ号を表示し、無ければ最新号を表示する。
   翌月号が入っていれば「来月号を見る」で切り替えられる。

   月次運用（2026-11-05〜 自動化）:
   (1) 画像: 毎時の GitHub Actions（update-notion-data.yml）が、毎月20日以降の09:00 JST に
       翌月号が無ければ scripts/fetch_towncal.py --auto を実行する。町ホームページの広報一覧から
       新しい号を見つけ、カレンダー面を assets/towncal/YYYY-MM.webp に保存して、この issues[] の
       先頭に追加する。ページ判定が一意でなければ取り込まずに失敗する（メールで気づく）。
       急ぐときは Actions の手動実行（workflow_dispatch）。
   (2) 手動で直すとき: python scripts/fetch_towncal.py <PDFまたは画像のURL> <YYYY-MM> [--page N]
       （従来の使い方。issues[] の同じ月を差し替える／無ければ追加する）。
   (3) 誌面の行事を転記した assets/towncal/events-YYYY-MM.csv は、日曜の週次ラン
       （akki-staff の sns-drafter run_weekly.bat → scripts/towncal_csv.py）が claude -p で作る。
       列= date,dow,title,time,place,booking,category,note,source,check。category は色分けからの推定。
       check=1 は読み取りに自信がない行。統合カレンダー Phase 2（Notion 登録）の入力。
       2026-10・11 号は人（Claude）が手で転記したため check 列は無い。 */
window.TOWNCAL = {
  issues: [
    { month: "2026-11", image: "assets/towncal/2026-11.webp", sourceName: "広報ことひら 2026年11月号" },
    { month: "2026-10", image: "assets/towncal/2026-10.webp", sourceName: "広報ことひら 2026年10月号" },
    { month: "2026-09", image: "assets/towncal/2026-09.webp", sourceName: "広報ことひら 2026年9月号" }
  ],
  sourceUrl: "https://www.town.kotohira.kagawa.jp/site/kouhou/list18.html",
  sourceLinkLabel: "琴平町ホームページ（広報ことひら）"
};
