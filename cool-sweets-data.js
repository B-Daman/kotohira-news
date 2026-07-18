/* 🍧 かき氷・アイスタブの表示データ。
   こんぴら参りの途中で冷たい甘味を探す来訪者向け案内。
   専門店だけを集めた一覧ではなく、土産店・和洋菓子店・カフェ等の季節商品も掲載する。
   offerings / description は来訪者向け、note / sources は更新担当者向けの内部情報。
   商品・営業時間・価格は変動しやすいため、来店前に公式サイト・SNSで再確認する。
   image は公式サイト等のog:imageを assets/places/ にローカル保存したもの（出所は imageSource）。
   Notion同様に画像はリポジトリを正とするlocal-first運用。og:imageが無い/ロゴのみ等の店舗は image を付けていない。 */
window.COOL_SWEETS_DATA = {
  checked: "2026-07-15",
  zones: [
    { key: "kakigori", label: "かき氷", emoji: "🍧" },
    { key: "ice", label: "ソフトクリーム・アイス", emoji: "🍦" }
  ],
  items: [
    {
      id: "cool-hyokin",
      name: "ヒョーキン KAKI-GORI",
      zones: ["kakigori"],
      area: "JR琴平駅周辺",
      address: "香川県仲多度郡琴平町213",
      phone: "",
      hours: "10:00〜17:00",
      closed: "月曜日",
      priceRange: "公式サイト・Instagramで要確認",
      parking: "専用駐車場は要確認",
      availability: "5〜10月限定",
      offerings: "香川県産フルーツのかき氷（5〜10月限定）",
      description: "JR琴平駅近くの川沿いにある、かき氷とワッフルのおやつ処です。暑い時期は香川県産のいちごや桃、みかんなどを使った季節のかき氷を楽しめます。",
      note: "2024年開業。公式サイトで5〜10月限定のフルーツかき氷と営業日時を確認。",
      links: {
        official: "https://www.nine-storieshotel.jp/about_hyokin.php",
        instagram: "https://www.instagram.com/hyokin.kakigoori_/",
        map: "https://www.google.com/maps/search/?api=1&query=ヒョーキン+KAKI-GORI+琴平町",
        tourism: "https://www.kotohirakankou.jp/spot/eat/entry-425.html"
      },
      sources: [
        "https://www.nine-storieshotel.jp/about_hyokin.php",
        "https://www.kotohirakankou.jp/spot/eat/entry-425.html"
      ],
      checked: "2026-07-14",
      show: true
    },
    {
      id: "cool-usagiiro",
      name: "KOTOHIRAスィーツ うさぎいろ",
      zones: ["kakigori"],
      area: "表参道入口周辺",
      address: "香川県仲多度郡琴平町702-12",
      phone: "0877-73-5225",
      hours: "10:00〜17:30",
      closed: "月・火曜日（祝日は営業、翌日休み）",
      priceRange: "店頭・Instagramで要確認",
      parking: "無料駐車場あり",
      availability: "期間限定・Instagramで提供確認",
      offerings: "期間限定のかき氷・フルーツスムージー",
      description: "表参道入口近くの和洋菓子店です。旬の果物を使った大福や焼き菓子に加え、暑い時期には期間限定のかき氷やフルーツスムージーが登場します。",
      note: "かき氷は期間限定。提供中の種類と価格は公式Instagramで再確認する。",
      links: {
        instagram: "https://www.instagram.com/usagiiro_kagawa/",
        map: "https://www.google.com/maps/search/?api=1&query=KOTOHIRAスィーツ+うさぎいろ",
        tourism: "https://www.kotohirakankou.jp/spot/buy/entry-313.html"
      },
      sources: [
        "https://www.kotohirakankou.jp/spot/buy/entry-313.html",
        "https://www.instagram.com/usagiiro_kagawa/"
      ],
      checked: "2026-07-14",
      show: true
    },
    {
      id: "cool-shoyumame",
      name: "しょうゆ豆本舗参道店",
      zones: ["kakigori", "ice"],
      area: "表参道",
      address: "香川県仲多度郡琴平町811",
      phone: "0877-75-3264",
      hours: "要確認",
      closed: "なし",
      priceRange: "ソフト380円〜／苺氷り400円（公式掲載価格）",
      parking: "なし",
      availability: "公式ページに商品掲載",
      offerings: "苺氷り・ゆず氷／牛乳・抹茶・和三盆・かまたま等のソフト",
      description: "表参道で、果実を使った氷菓と琴平らしいソフトクリームを選べる土産店です。和三盆やかまたま、おいりトッピングなど、参拝の思い出になる味もそろいます。",
      note: "公式ページに営業時間の記載なし。価格変更の可能性があるため来店時に確認する。",
      image: "assets/places/cool-shoyumame.jpg",
      imageSource: "https://www.kotohira-nishikiya.com/しょうゆ豆本舗-参-道-店/",
      links: {
        official: "https://www.kotohira-nishikiya.com/しょうゆ豆本舗-参-道-店/",
        map: "https://www.google.com/maps/search/?api=1&query=しょうゆ豆本舗参道店+琴平町",
        tourism: "https://www.kotohirakankou.jp/spot/eat/entry-91.html"
      },
      sources: [
        "https://www.kotohira-nishikiya.com/しょうゆ豆本舗-参-道-店/",
        "https://www.kotohirakankou.jp/spot/eat/entry-91.html"
      ],
      checked: "2026-07-14",
      show: true
    },
    {
      id: "cool-kamitsubaki",
      name: "金刀比羅宮 カフェ＆レストラン神椿",
      zones: ["kakigori", "ice"],
      area: "金刀比羅宮 石段500段目",
      address: "香川県仲多度郡琴平町892-1",
      phone: "0877-73-0202",
      hours: "10:00〜17:00（フードLO 16:00／LO 16:30）",
      closed: "火曜日（祝日・年末年始を除く）",
      priceRange: "公式メニューで要確認",
      parking: "専用駐車場あり（専用車道を利用）",
      availability: "かき氷は7月から／ソフトは公式メニュー掲載",
      offerings: "かき氷（7月〜）／宇治抹茶ソフト・パフェ",
      description: "御本宮へ向かう石段500段目、境内の森にあるカフェです。参拝途中に涼みながら、夏のかき氷やソフトクリーム、パフェを味わえます。",
      note: "Googleマップの車道表示に注意。車利用は公式アクセス案内を参照する。",
      links: {
        official: "https://kamitsubaki.com/",
        map: "https://www.google.com/maps/search/?api=1&query=カフェ＆レストラン神椿",
        tourism: "https://www.kotohirakankou.jp/spot/eat/entry-384.html"
      },
      sources: [
        "https://kamitsubaki.com/menu/",
        "https://www.kotohirakankou.jp/spot/eat/entry-384.html",
        "https://www.konpira.or.jp/articles_2026/20260530_prevent-heatstroke/article.html"
      ],
      checked: "2026-07-14",
      show: true
    },
    {
      id: "cool-kotohira-terrace",
      name: "ことひらテラス",
      zones: ["ice"],
      area: "表参道入口周辺",
      address: "香川県仲多度郡琴平町716-5",
      phone: "0877-75-0001",
      hours: "10:00〜16:00",
      closed: "なし",
      priceRange: "公式サイト・店頭で要確認",
      parking: "乗用車100台（店舗正面）",
      availability: "公式ページに商品掲載",
      offerings: "和三盆・希少糖ミルク・しょうゆ／嫁入りおいりソフト",
      description: "表参道入口近くで、ご当地らしい味のソフトクリームを気軽に選べる店です。色とりどりのおいりを添えたソフトは、参拝前後のひと休みにも向いています。",
      note: "観光協会ページで営業時間・定休日・駐車場とソフトの種類を確認。",
      links: {
        official: "https://www.nakanoya.net/?service_category=kotohiraterrace",
        map: "https://www.google.com/maps/search/?api=1&query=ことひらテラス",
        tourism: "https://www.kotohirakankou.jp/spot/eat/entry-90.html"
      },
      sources: [
        "https://www.kotohirakankou.jp/spot/eat/entry-90.html",
        "https://www.nakanoya.net/?service_category=kotohiraterrace"
      ],
      checked: "2026-07-14",
      show: true
    },
    {
      id: "cool-kyuman-ishidanya",
      name: "灸まん本舗石段や",
      zones: ["kakigori"],
      area: "表参道",
      address: "香川県仲多度郡琴平町798",
      phone: "0877-75-3220",
      hours: "8:00〜17:00（土・日曜日は18:00まで）",
      closed: "なし",
      priceRange: "700円（2026年公式掲載）",
      parking: "なし",
      availability: "2026年5月18日から販売中",
      offerings: "さぬき姫スペシャル",
      description: "表参道の老舗土産店で、香川県産いちご『さぬきひめ』のジャムをたっぷりかけたかき氷を販売しています。店内で休憩できるため、参拝前後のひと休みにも利用できます。",
      note: "2026年5月18日の公式告知で販売開始を確認。価格は公式掲載時点。",
      links: {
        official: "https://kyuman.co.jp/weekly/",
        map: "https://www.google.com/maps/search/?api=1&query=灸まん本舗石段や+琴平町",
        tourism: "https://www.kotohirakankou.jp/spot/buy/entry-92.html"
      },
      sources: [
        "https://kyuman.co.jp/weekly/",
        "https://www.kotohirakankou.jp/spot/buy/entry-92.html"
      ],
      checked: "2026-07-15",
      show: true
    },
    {
      id: "cool-konpira-purin",
      name: "こんぴらプリン",
      zones: ["ice"],
      area: "表参道入口周辺",
      address: "香川県仲多度郡琴平町716-5",
      phone: "0877-85-5560",
      hours: "平日9:30〜17:30／土日祝9:30〜18:00（売り切れ次第終了）",
      closed: "なし",
      priceRange: "ソフト350円／パフェ450円（公式掲載価格）",
      parking: "なし",
      availability: "公式メニューに掲載",
      offerings: "プリンソフト・抹茶ソフト・プリンパフェ",
      description: "表参道入口近くのプリン専門店です。軽い口当たりのプリン風味ソフトや抹茶ソフト、プリンとソフトクリームを一緒に味わえるパフェを持ち歩きで楽しめます。",
      note: "公式サイトの現行メニュー・店舗情報を確認。Instagramは営業変更の確認先として掲載。",
      links: {
        official: "https://konpirapurin.com/",
        instagram: "https://www.instagram.com/konpirapurin/",
        map: "https://www.google.com/maps/search/?api=1&query=こんぴらプリン+琴平町"
      },
      sources: [
        "https://konpirapurin.com/",
        "https://www.instagram.com/konpirapurin/"
      ],
      checked: "2026-07-15",
      show: true
    },
    {
      id: "cool-sugi-bee",
      name: "杉養蜂園 金刀比羅店",
      zones: ["ice"],
      area: "表参道",
      address: "香川県仲多度郡琴平町802",
      phone: "0877-75-0538",
      hours: "9:00〜17:15（季節により変動）",
      closed: "要確認",
      priceRange: "店頭で要確認",
      parking: "要確認",
      availability: "店舗案内・直近の訪問情報で販売確認",
      offerings: "はちみつソフト・巣房蜜ソフトクリーム",
      description: "表参道にあるはちみつ専門店です。はちみつの風味を楽しめるソフトクリームや、巣蜜をのせたぜいたくなソフトを参拝途中の食べ歩きに選べます。",
      note: "公式店舗ページ、観光協会、直近の店舗情報で営業を確認。営業時間は季節変動あり。",
      links: {
        official: "https://sugi-bee.com/store/kagawa-konpira/",
        map: "https://www.google.com/maps/search/?api=1&query=杉養蜂園+金刀比羅店",
        tourism: "https://www.kotohirakankou.jp/spot/buy/"
      },
      sources: [
        "https://sugi-bee.com/store/kagawa-konpira/",
        "https://www.kotohirakankou.jp/spot/buy/"
      ],
      checked: "2026-07-15",
      show: true
    },
    {
      id: "cool-nakanoya-kotohira",
      name: "ナカノヤ琴平",
      zones: ["ice"],
      area: "表参道入口周辺",
      address: "香川県仲多度郡琴平町796",
      phone: "0877-75-0001",
      hours: "9:30〜16:00（売り切れ次第終了）",
      closed: "要確認",
      priceRange: "店頭で要確認",
      parking: "近隣駐車場を利用",
      availability: "公式案内・直近の訪問情報で販売確認",
      offerings: "嫁入りおいりソフト・和三盆ソフト",
      description: "中野うどん学校に併設された表参道入口近くの店です。和三盆ソフトに色とりどりのおいりを添えた『嫁入りおいりソフト』は、琴平らしい食べ歩きの一品です。",
      note: "公式アクセス案内で現行営業時間を確認。ソフトは直近の訪問情報も照合。画像は併設元の中野うどん学校（同住所796）の外観写真を共用（店頭のソフトクリーム売場が写っているため。アクセスページのog:imageは通り全景で他店看板が目立ち不採用）。",
      image: "assets/places/udon-nakano-school.jpg",
      imageSource: "https://www.nakanoya.net/nakanoudon/",
      links: {
        official: "https://www.nakanoya.net/access/",
        map: "https://www.google.com/maps/search/?api=1&query=ナカノヤ琴平"
      },
      sources: [
        "https://www.nakanoya.net/access/",
        "https://yayoicafe.jp/blog-entry-1238.html"
      ],
      checked: "2026-07-15",
      show: true
    },
    {
      id: "cool-tanakaya",
      name: "たなかや FRESH JUICE & KAKIGORI",
      zones: ["kakigori", "ice"],
      area: "表参道入口周辺",
      address: "香川県仲多度郡琴平町720-12",
      phone: "0877-88-8222",
      hours: "10:00〜18:00（変更の可能性あり）",
      closed: "要確認",
      priceRange: "店頭で要確認",
      parking: "要確認",
      availability: "かき氷・ソフトの販売案内あり／当日は店頭確認",
      offerings: "かき氷・おいりソフト・塩ソフト・フレッシュジュース",
      description: "表参道入口にある食べ歩き向けの店です。かき氷、ソフトクリーム、フレッシュジュースなどから、その日の暑さや気分に合う冷たいものを選べます。",
      note: "琴平町の2025年取扱店資料で店舗を確認。商品と営業時間は店舗情報・直近訪問情報を照合したが当日確認を推奨。",
      links: {
        map: "https://www.google.com/maps/search/?api=1&query=たなかや+FRESH+JUICE+KAKIGORI+琴平町"
      },
      sources: [
        "https://www.mapple.net/spot/37011164/",
        "https://www.town.kotohira.kagawa.jp/uploaded/attachment/5623.pdf"
      ],
      checked: "2026-07-15",
      show: true
    },
    {
      id: "cool-goriyakuya",
      name: "ご利益や",
      zones: ["kakigori"],
      area: "表参道 石段192段目",
      address: "香川県仲多度郡琴平町一之坂1051-2",
      phone: "0877-89-4511",
      hours: "10:00〜17:00",
      closed: "不定休（Instagramで確認）",
      priceRange: "店頭・Instagramで要確認",
      parking: "なし",
      availability: "Instagramで営業日・季節商品を確認",
      offerings: "高瀬茶の二宮金時・桃など季節のかき氷",
      description: "表参道の石段192段目にある甘味処です。地産地消にこだわった高瀬茶のかき氷や季節の果物を使うかき氷を、店内で休みながら味わえます。",
      note: "公式Instagramへの導線、観光協会の現行掲載、香川県の地産地消資料を照合。休業日はInstagramで確認する。系列サイト（artcafe-shimizuonsen.com）のog:imageは清水温泉の建物写真で本店舗と別の場所のため画像は不採用（プレースホルダ運用）。",
      links: {
        official: "https://artcafe-shimizuonsen.com/",
        instagram: "https://www.instagram.com/goriyakuya/",
        map: "https://www.google.com/maps/search/?api=1&query=ご利益や+琴平町",
        tourism: "https://www.kotohirakankou.jp/spot/buy/entry-170.html"
      },
      sources: [
        "https://www.instagram.com/goriyakuya/",
        "https://www.kotohirakankou.jp/spot/buy/entry-170.html",
        "https://mitoyo-city.note.jp/n/n997d79a9e314"
      ],
      checked: "2026-07-15",
      show: true
    },
    {
      id: "cool-goda-fukutaro",
      name: "合田福太郎商店",
      zones: ["ice"],
      area: "表参道",
      address: "香川県仲多度郡琴平町808-1",
      phone: "0877-75-3320",
      hours: "要確認",
      closed: "不定休",
      priceRange: "店頭で要確認",
      parking: "要確認",
      availability: "観光案内掲載／当日の在庫は店頭確認",
      offerings: "甘さ控えめの豆腐アイス",
      description: "表参道の土産店で、すっきりした甘さの豆腐アイスを扱っています。専門店ではないからこそ見落としやすい、参拝途中のひんやり甘味です。",
      note: "観光協会の現行店舗情報と琴平エリアガイドの商品掲載を照合。営業時間と在庫は要確認。",
      links: {
        map: "https://www.google.com/maps/search/?api=1&query=合田福太郎商店+琴平町",
        tourism: "https://www.kotohirakankou.jp/spot/buy/entry-421.html"
      },
      sources: [
        "https://www.kotohirakankou.jp/spot/buy/entry-421.html",
        "https://shikoku-guide.com/datas/sightseeing/pdf/020240916112039_IkIU.pdf"
      ],
      checked: "2026-07-15",
      show: true
    },
    {
      id: "cool-terakoya-honpo",
      name: "寺子屋本舗 琴平店",
      zones: ["ice"],
      area: "表参道",
      address: "香川県仲多度郡琴平町959-4",
      phone: "0877-75-2370",
      hours: "9:30〜17:30（変更の可能性あり）",
      closed: "要確認",
      priceRange: "店頭で要確認",
      parking: "なし",
      availability: "2025〜2026年の観光案内で対象商品を確認",
      offerings: "しょうゆソフトなど",
      description: "表参道の手焼きせんべい店で、琴平らしいしょうゆ風味のソフトクリームを扱っています。せんべいを選ぶ合間にも立ち寄れる食べ歩きスポットです。",
      note: "JR四国の2025〜2026年観光案内でソフトクリーム提供店として確認。営業時間は来店前の確認を推奨。",
      links: {
        official: "https://www.terakoyahonpo.jp/",
        map: "https://www.google.com/maps/search/?api=1&query=寺子屋本舗+琴平店"
      },
      sources: [
        "https://www.jr-shikoku.co.jp/pr/sunriseseto_konpira.pdf",
        "https://www.terakoyahonpo.jp/"
      ],
      checked: "2026-07-15",
      show: true
    }
  ]
};
