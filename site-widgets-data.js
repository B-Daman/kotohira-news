/* ことひらいふ 共通ウィジェット・広告用の公開設定。
   index.html から window.SITE_WIDGETS_DATA を読み込み、PCのサイドバー、
   スマートフォンの本文内ウィジェット、フッターで共通利用する。

   ── 運用ルール ─────────────────────────────────────────────────────
   ・このファイルはブラウザから誰でも閲覧できる。公開してよい情報だけを記載する。
   ・担当者の個人情報、契約金額、請求・入金状況、社内メモ等は入れない。
   ・日付は YYYY-MM-DD、日時はタイムゾーン付きISO 8601を使用する。
   ・LINEオープンチャットは、正式な参加URL・QR画像・運営主体・ルールURLを
     確認して全項目を設定するまで enabled:true にしない。
   ・enabled は文字列ではなく true / false の真偽値で記載する。
   ・広告は enabled:true かつ startDate〜endDate の期間内だけ表示する。
     startDate / endDate が空文字なら、それぞれ開始日／終了日の制限なしとして扱う。
   ・広告の id、advertiserName、placements は必須。title または image＋alt も必須。
   ・広告の画像は原則として assets/ 以下に保存したローカル画像を指定する。

   ads の各項目:
   {id, enabled, advertiserName, title, image, alt, url,
    startDate, endDate, placements, order}
   placements は "sidebar"（PCサイドバー）または
   "mobile-inline"（スマートフォン本文内）を配列で指定する。 */
window.SITE_WIDGETS_DATA = {
  updated: "2026-07-14",

  /* 気象庁の香川県短期予報をブラウザで自動取得する。
     dataUrl は気象庁サイト内部で利用される公開JSONのため、画面側では構造検証・
     タイムアウト・24時間キャッシュ・公式ページへのフォールバックを行う。 */
  weather: {
    enabled: true,
    locationLabel: "琴平町",
    forecastAreaLabel: "香川県",
    temperaturePointLabel: "高松",
    sourceName: "気象庁",
    sourceUrl: "https://www.jma.go.jp/bosai/forecast/",
    dataUrl: "https://www.jma.go.jp/bosai/forecast/data/forecast/370000.json",
    forecastUrl: "https://www.jma.go.jp/bosai/forecast/#area_type=offices&area_code=370000",
    warningUrl: "https://www.jma.go.jp/bosai/warning/#area_type=class20s&area_code=3740300",
    cacheHours: 24
  },

  /* 参加URL・QR画像・運営主体を確認済みのため公開。ルールURLは整い次第 rulesUrl に追加する
     （空の項目は画面側で「あれば表示」扱いのため未設定でも表示は成立する）。 */
  lineOpenChat: {
    enabled: true,
    name: "ことひらいふ",
    description: "琴平町の“今”を語り合うLINEオープンチャットです。イベント情報や町の話題をゆるく共有しています。",
    joinUrl: "https://line.me/ti/g2/LcgsGouflXLtNbOlOtrBcxeeNQJ1nADVrqhj-w?utm_source=invitation&utm_medium=link_copy&utm_campaign=default",
    qrImage: "assets/line-openchat-qr.jpg",
    rulesUrl: "",
    disclaimer: "参加・退会は自由です。個人情報の書き込みはお控えください。"
  },

  /* 正式情報の確定前は、noindex の暫定ページへ案内する。 */
  footerLinks: {
    privacyPolicyUrl: "privacy.html",
    operatorUrl: "operator.html"
  },

  /* 広告データは契約・掲載許可が確定したものだけ追加する。 */
  ads: []
};
