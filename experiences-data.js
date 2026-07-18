/* ことひらいふ「🧭 体験・滞在」タブ用のデータ。
   手編集運用（links-data.js と同じくコード直書き）。将来 Notion 側の
   体験・滞在DB（EXPERIENCE_NOTION_DB_ID）を設定して scripts/fetch_notion.py
   を実行すると notion-data.js に experiences が生成され、そちらが優先される
   （index.html の取り込みで ND_RAW.experiences が非空ならそれを使う）。
   その時までの暫定コンテンツをここに置く。
   各itemは scripts/fetch_notion.py の parse_experience() が生成する形に合わせる:
   {id, title, category, org, summary, start, end, place, reward, target, url, linkLabel, status, image, imageFit, imageSource, show}。
   linkLabel は外部リンクの文言を変えたい場合だけ指定する（省略時は「詳細・応募ページを開く」）。
   imageFit は正方形ロゴ等を切らずに載せたい場合だけ "contain" を指定する。
   status は 募集中／案内／準備中／終了 のいずれか。
   ・募集中／案内 … 種別ごとにグループ表示される（案内は終了日のない入口ページ向け）
   ・終了 … 「募集終了」の折りたたみに入る（誤導防止のため過去実績もここで残す）
   ・準備中 … coming soon。現状のレンダリングでは非表示（開催決定時に status を変える）
   show:false のitemは index.html の experiencesTabHTML() で除外される（レンダリング対象外）。
   image は links-data.js と同じ local-first ルール: 画像の“正”はこのリポジトリの
   assets/experiences/ に保存したローカルファイル（Notion/外部URLを直接参照しない、
   スクリーンショットも不可）。出所は (a) 本人・団体からの提供画像、または
   (b) 対象サイトの og:image をスクリプトで取得・保存したものに限る（2026-07-10、
   本タスクで v1 の "" から更新。docs/体験滞在-Deep-Research-2026-07-10.md 由来の
   項目は未着手のため引き続き "" で種別ごとの絵文字プレースホルダに任せる）。
   個人の氏名・個人携帯番号は載せない。事業者・行政の公開連絡先（固定電話・法人メール等）は可。
   事実の出所は docs/体験滞在-Deep-Research-2026-07-10.md（第5章・第6章・第7章）。2026-07-10 時点。

   ── v2 方針（2026-07-10 再構成）─────────────────────────────────────────
   ユーザー方針により「個別案件を並べず導線で完結、載せるのは体験×滞在セットのみ」。
   カテゴリは EXPERIENCE_CATS =「体験プログラム／お手伝い滞在／移住・行政」の3種に集約。
   ・体験プログラム … 体験予約サイトとTOKKEN（特別な権利）の入口を掲載
   ・お手伝い滞在 … 体験と滞在がセットの募集のみ（HAKOBUNEフリアコ／おてつたび香川一覧／
     SMOUT琴平一覧の3件＋過去おてつたび実績6件の折りたたみ）
   ・移住・行政 … 町公式の入口1件（地域おこし協力隊）
   上記以外（個別体験施設・単独求人・単独の宿・移住支援金など）は末尾の「アーカイブ」に
   show:false で退避（削除せず。再掲の可能性があるため）。 */
window.EXPERIENCES_DATA = {
  updated: "2026-07-13",
  items: [
    /* ===== 🎨 体験プログラム・特別な権利（各サービスの入口へ導線を集約） ===== */
    {
      id: "exp-kotohira-travel",
      title: "琴平の体験・ツアー予約サイト（琴平バス）",
      category: "体験プログラム",
      org: "琴平バス株式会社",
      summary: "個別の体験プログラムはこのサイトで予約・確認できます。うどん作り・ご利益飴づくり・着物レンタル・こんぴら歌舞伎ガイド・e-bikeなど約14件を掲載する町内体験プラットフォーム（2026年3月始動）。予約センター 050-3537-5678。",
      start: "",
      end: "",
      place: "琴平町内各所",
      reward: "",
      target: "",
      url: "https://www.kotohira-travel.com/tour/",
      status: "案内",
      image: "",
      show: true
    },
    /* image: kotohira-travel.com の og:image（/assets/img/base/ogp.jpg）は
       2026-07-10 時点で404（壊れている）。取得できず空のまま、種別絵文字に任せる。 */

    {
      id: "exp-tokken-kotohira",
      title: "TOKKEN｜琴平町の特別な権利",
      category: "体験プログラム",
      org: "あるやうむ",
      summary: "琴平町のTOKKEN（特別な権利）を一覧・詳細から確認できます。",
      start: "",
      end: "",
      place: "琴平町",
      reward: "",
      target: "",
      url: "https://tokken.alyawmu.com/towns/2168535d-e203-4ef0-9f97-57d2f68be5f3",
      linkLabel: "TOKKENを見る",
      status: "案内",
      image: "assets/experiences/tokken-og.png",
      imageFit: "contain",
      imageSource: "https://alyawmu-ec-next-746157168937.asia-northeast1.run.app/opengraph-image.png?67c120bbe5813825",
      show: true
    },

    /* ===== 🤝 お手伝い滞在（体験と滞在がセットの募集のみ） ===== */
    {
      id: "exp-hakobune-free-accommodation",
      title: "HAKOBUNE フリーアコモデーション（ヘルパー募集）",
      category: "お手伝い滞在",
      org: "HAKOBUNE（運営: 栞や / Shioriya Co., Ltd.）",
      summary: "表参道入口の複合施設HAKOBUNE（1Fカフェ・2Fイベント・3Fシェアアトリエ・4FホステルCabin）でのヘルパー募集。カフェ・ホステル運営やSNS・DIYなどを1日4〜5時間・完全週休二日。定員到達の場合あり・要問い合わせ（ページ更新2026年3月）。",
      start: "",
      end: "",
      place: "琴平町725-1",
      reward: "宿泊費・光熱費無料（勤務相殺）。食費等は自己負担、追加勤務は時給1,100円〜",
      target: "最短2週間〜（応相談）・定員3名。外国籍はワーキングホリデービザ必須。応募はフォーム→書類選考→オンライン面接",
      url: "https://hakobune-building.com/hakobune-free-accommodation/",
      status: "募集中",
      image: "assets/experiences/hakobune-helpers.jpg",
      show: true
    },
    {
      id: "exp-otetsutabi-hub",
      title: "おてつたび（琴平町の受け入れ実績9事業者）",
      category: "お手伝い滞在",
      org: "おてつたび",
      summary: "琴平町では9事業者がおてつたびの受け入れ実績あり。現在は募集ゼロのため、再開通知は各事業者のフォローで受け取れる。",
      start: "",
      end: "",
      place: "琴平町内",
      reward: "",
      target: "",
      url: "https://otetsutabi.com/businesses/kagawa",
      status: "案内",
      image: "assets/experiences/otetsutabi.jpg",
      show: true
    },
    {
      id: "exp-smout-kotohira",
      title: "SMOUT 琴平町の募集一覧",
      category: "お手伝い滞在",
      org: "株式会社カヤック（面白法人カヤック）",
      summary: "琴平町の『関わり』募集（プロジェクト・お手伝い・仕事）が随時掲載される一覧。SMOUTは移住・関係人口づくりのスカウト型マッチングサービス。",
      start: "",
      end: "",
      place: "琴平町",
      reward: "",
      target: "",
      url: "https://smout.jp/plans?city_id=1607",
      status: "案内",
      image: "assets/experiences/smout.png",
      show: true
    },

    /* ----- お手伝い滞在：過去おてつたび実績（status:終了 → 折りたたみに入る） ----- */
    {
      id: "exp-otetsutabi-kotori-2406",
      title: "コトリ コワーキング＆ホステル｜広報・宿泊運営のお手伝い",
      category: "お手伝い滞在",
      org: "コトリ コワーキング＆ホステル（琴平バス）",
      summary: "施設清掃・SNS広報・宿泊運営・イベント企画のお手伝い。未経験OK。",
      start: "2024-06-17",
      end: "2024-06-30",
      place: "琴平町720-15",
      reward: "50時間勤務で計50,000円。宿泊=ドミトリー、朝食は自炊",
      target: "街づくり・移住・発信・交流に関心のある方",
      url: "https://otetsutabi.com/plans/6866",
      status: "終了",
      image: "",
      show: true
    },
    {
      id: "exp-otetsutabi-kotori-2408",
      title: "コトリ コワーキング＆ホステル｜広報活動・宿泊運営のお手伝い",
      category: "お手伝い滞在",
      org: "コトリ コワーキング＆ホステル（琴平バス）",
      summary: "アイディア出し・清掃・接客・SNS発信が中心。学生歓迎。",
      start: "2024-08-05",
      end: "2024-08-23",
      place: "琴平町720-15",
      reward: "50時間勤務で計50,000円。宿泊=ドミトリー、全食自炊",
      target: "学生歓迎",
      url: "https://otetsutabi.com/plans/7691",
      status: "終了",
      image: "",
      show: true
    },
    {
      id: "exp-otetsutabi-tsuruya",
      title: "こんぴら温泉 つるや旅館｜配膳・接客／客室清掃のお手伝い",
      category: "お手伝い滞在",
      org: "こんぴら温泉 つるや旅館",
      summary: "創業180年の老舗旅館で食事配膳・接客や客室清掃のお手伝い。2024年頃、過去4案件を実施。",
      start: "",
      end: "",
      place: "琴平町620",
      reward: "宿泊=個室（女将宅の空き部屋）",
      target: "話好きな方歓迎",
      url: "https://otetsutabi.com/business_sites/1546",
      status: "終了",
      image: "",
      show: true
    },
    {
      id: "exp-otetsutabi-yachiyo",
      title: "こんぴら温泉 湯元八千代｜清掃・配膳・フロントのお手伝い",
      category: "お手伝い滞在",
      org: "こんぴら温泉 湯元八千代",
      summary: "客室清掃・ベッドメイキング・配膳やフロント業務のシフト制。2024年に過去4回実施（うち1件の募集締切は2024年10月31日）。",
      start: "",
      end: "",
      place: "琴平町611",
      reward: "宿泊=個室（男女別）",
      target: "",
      url: "https://otetsutabi.com/business_sites/1585",
      status: "終了",
      image: "",
      show: true
    },
    /* start/endがコトリ2024年6月回と同一日付だが、レポート第2章(3)(4)で個別に裏取り済み（複数施設同時受け入れ企画のため一致）。コピーミスではない。 */
    {
      id: "exp-otetsutabi-nakanoya",
      title: "中野うどん学校 琴平校｜うどん作り業務アシスタント",
      category: "お手伝い滞在",
      org: "中野うどん学校 琴平校",
      summary: "観光客向けうどん教室のアシスタント。準備・接客・片付けなど。未経験OK。",
      start: "2024-06-17",
      end: "2024-06-30",
      place: "琴平町796",
      reward: "36時間労働で36,000円。宿泊=個室寮、昼はまかない付",
      target: "未経験OK",
      url: "https://otetsutabi.com/plans/6786",
      status: "終了",
      image: "",
      show: true
    },
    {
      id: "exp-otetsutabi-donzo",
      title: "DONZO Brewing（呑象ブリューイング）｜ホール業務のお手伝い",
      category: "お手伝い滞在",
      org: "DONZO Brewing（呑象ブリューイング）",
      summary: "地域活性化に取り組むマイクロブルワリーのホール業務。接客・ドリンク作成・簡単調理など。",
      start: "2024-06-17",
      end: "2024-06-30",
      place: "琴平町182-2",
      reward: "40時間勤務で計40,000円。宿泊=事務所内の個室",
      target: "年齢不問・学生歓迎・未経験OK",
      url: "https://otetsutabi.com/plans/6785",
      status: "終了",
      image: "",
      show: true
    },

    /* ===== 🏛 移住・行政（町公式の入口1件） ===== */
    {
      id: "exp-chiiki-okoshi",
      title: "琴平町 地域おこし協力隊",
      category: "移住・行政",
      org: "琴平町",
      summary: "現在の募集有無は町公式ページで確認（問合せ: 観光商工課 0877-75-6710）。",
      start: "",
      end: "",
      place: "琴平町",
      reward: "",
      target: "",
      url: "https://www.town.kotohira.kagawa.jp/life/4/22/49/",
      status: "案内",
      image: "assets/experiences/kyoryokutai.jpg",
      show: true
    },

    /* ===== アーカイブ（非表示。show:false で除外される） =============================
       方針: 導線完結・体験×滞在セットのみ掲載（v2, 2026-07-10）。
       個別体験施設・単独求人・単独の宿・移住支援金などは下記に退避。
       データは捨てない（再掲の可能性があるため show:false で残す）。
       ※category は退避前の旧種別のまま（非表示なのでグループ表示には影響しない）。 */

    /* --- 旧「体験プログラム」：予約サイト（exp-kotohira-travel）に集約したため非表示 --- */
    {
      id: "exp-kinryo-museum",
      title: "金陵の郷（酒蔵見学）",
      category: "体験プログラム",
      org: "西野金陵株式会社",
      summary: "江戸時代の白壁酒蔵を再現した見学施設。酒造道具の展示や試飲を楽しめる。入場無料・年中無休（2025年6月改装）。",
      start: "",
      end: "",
      place: "琴平町623",
      reward: "入場無料",
      target: "",
      url: "https://www.nishino-kinryo.co.jp/museum/",
      status: "案内",
      image: "",
      show: false
    },
    {
      id: "exp-nakanoya-udon",
      title: "中野うどん学校 琴平校（うどん打ち体験）",
      category: "体験プログラム",
      org: "株式会社中野屋",
      summary: "粉を練り、足踏み、麺棒でのばして切る一連のさぬきうどん作りを職人が指導。作ったうどんはその場で試食・持ち帰り可。",
      start: "",
      end: "",
      place: "琴平町796",
      reward: "1名1,760円（税込）〜。完全予約制（0877-75-0001）",
      target: "手ぶらOK・年齢問わず・子連れ可",
      url: "https://www.nakanoya.net/",
      status: "案内",
      image: "",
      show: false
    },
    {
      id: "exp-nishikiya-wasanbon",
      title: "にしきや（和三盆手作り体験）",
      category: "体験プログラム",
      org: "にしきや",
      summary: "200年以上の歴史を持つ菓子木型を使った和三盆の干菓子作り体験。出来立てをお抹茶と味わえる。年中無休。詳細は要確認。",
      start: "",
      end: "",
      place: "琴平町696",
      reward: "",
      target: "",
      url: "",
      status: "案内",
      image: "",
      show: false
    },

    /* --- 旧「求人」：単独求人（体験×滞在セットではない）ため非表示 --- */
    {
      id: "exp-kotosankaku-chori",
      title: "ことひら温泉 琴参閣｜調理補助（アルバイト・パート）",
      category: "求人",
      org: "株式会社琴参閣",
      summary: "宿泊客向け会席料理の調理補助（小鉢の盛り付け・器の準備など）。未経験歓迎。応募前に最新状況の確認を推奨。",
      start: "",
      end: "",
      place: "琴平町685-11",
      reward: "時給1,200〜1,500円。社会保険完備・交通費支給",
      target: "未経験歓迎。試用期間3か月、正社員登用制度あり",
      url: "https://www.kotosankaku.jp/",
      status: "募集中",
      image: "",
      show: false
    },
    {
      id: "exp-resortbaito-kotohira",
      title: "琴平温泉の住み込みリゾートバイト求人一覧",
      category: "求人",
      org: "リゾートバイト.com",
      summary: "琴平温泉エリアの住み込みリゾートバイト求人の一覧ページ。ダイブ・ワクトリにも同種の一覧がある。",
      start: "",
      end: "",
      place: "琴平町",
      reward: "",
      target: "",
      url: "https://www.resortbaito.com/shikoku/kagawa/kotoshira/",
      status: "案内",
      image: "",
      show: false
    },
    {
      id: "exp-kotobus-recruit",
      title: "琴平バス 採用情報",
      category: "求人",
      org: "琴平バス株式会社",
      summary: "琴平バス（コトリ運営会社）の採用情報。中途採用の案内ページ。",
      start: "",
      end: "",
      place: "琴平町",
      reward: "",
      target: "",
      url: "https://www.kotobus.com/recruit/",
      status: "案内",
      image: "",
      show: false
    },

    /* --- 旧「滞在・宿泊」：単独の宿・ツアー（体験×滞在セットではない）ため非表示 --- */
    {
      id: "exp-kotori-hostel",
      title: "コトリ コワーキング＆ホステル",
      category: "滞在・宿泊",
      org: "琴平バス株式会社",
      summary: "四国初のコリビング拠点。中長期滞在・デジタルノマド向け（Booking.com Traveler Review Award 2026受賞）。",
      start: "",
      end: "",
      place: "琴平町720-15",
      reward: "",
      target: "",
      url: "https://www.kotori-japan.com/",
      status: "案内",
      image: "",
      show: false
    },
    {
      id: "exp-cabin-hostel",
      title: "ホステルCabin（HAKOBUNE 4F）",
      category: "滞在・宿泊",
      org: "HAKOBUNE / 栞や",
      summary: "「つくる人のための宿」。制作・合宿にも対応するクリエイティブリトリートホステル。",
      start: "",
      end: "",
      place: "琴平町725-1",
      reward: "",
      target: "",
      url: "https://cabin-kotohira.com/",
      status: "案内",
      image: "",
      show: false
    },
    {
      id: "exp-kotovilla",
      title: "KOTOVilla（一棟貸しヴィラ）",
      category: "滞在・宿泊",
      org: "KOTOVilla",
      summary: "2025年12月開業の一棟貸しヴィラ。最大10名・駅徒歩3分。家族利用からワーケーションまで対応。",
      start: "",
      end: "",
      place: "琴平町榎井791-20",
      reward: "2名45,000円（税込）〜",
      target: "",
      url: "https://www.marugame2.jp/stores/113406",
      status: "案内",
      image: "",
      show: false
    },
    {
      id: "exp-minpaku-hoyu",
      title: "民泊朋友（まごころハウス 朋友）",
      category: "滞在・宿泊",
      org: "民泊朋友",
      summary: "高天井のリビングとアートスペースが特徴の一棟貸し民泊。最大9名・ペット同伴可。",
      start: "",
      end: "",
      place: "琴平町下櫛梨1092-2",
      reward: "1人あたり7,000円前後〜（人数による）",
      target: "",
      url: "https://www.minpaku-hoyu.com/",
      status: "案内",
      image: "",
      show: false
    },
    {
      id: "exp-konpira-machiya",
      title: "こんぴら町家（古民家一棟貸し・3棟）",
      category: "滞在・宿泊",
      org: "こんぴら町家",
      summary: "一日一組限定の古民家一棟貸し「うす・まる・はな」。駅徒歩1分、半露天風呂付き。",
      start: "",
      end: "",
      place: "琴平町榎井",
      reward: "",
      target: "",
      url: "https://konpira-machiya.com/en/",
      status: "案内",
      image: "",
      show: false
    },
    {
      id: "exp-guesthouse-kotohira",
      title: "ゲストハウス琴平",
      category: "滞在・宿泊",
      org: "ゲストハウス琴平",
      summary: "築約60年の古民家を改装した全3室の小規模ゲストハウス（素泊まり型）。琴電琴平駅徒歩1分。",
      start: "",
      end: "",
      place: "琴平町564-3",
      reward: "",
      target: "",
      url: "https://travel.rakuten.co.jp/HOTEL/168986/168986.html",
      status: "案内",
      image: "",
      show: false
    },
    {
      id: "exp-local-learning-tour",
      title: "ローカルラーニングツアー琴平（琴平バス）",
      category: "滞在・宿泊",
      org: "琴平バス コトバスセールス&ツアーズ",
      summary: "地域を学び、気付き、発見へと導く3日間の宿泊型体験ツアー。coming soon・開催日未発表。",
      start: "",
      end: "",
      place: "琴平町（集合: Kotori）",
      reward: "",
      target: "",
      url: "https://www.kotobus-tour.jp/local_learning/index.html",
      status: "準備中",
      image: "",
      show: false
    },

    /* --- 旧「移住・行政」：移住支援金（入口は地域おこし協力隊に集約）ため非表示 --- */
    {
      id: "exp-ijyuu-tokyo",
      title: "東京圏移住支援事業",
      category: "移住・行政",
      org: "琴平町",
      summary: "東京圏から琴平町への移住者向けの支援金。単身60万円・2人以上世帯100万円・子育て加算あり。",
      start: "",
      end: "",
      place: "琴平町",
      reward: "支援金: 単身60万円／2人以上世帯100万円＋子育て加算",
      target: "",
      url: "https://www.town.kotohira.kagawa.jp/site/ijyuu/3791.html",
      status: "案内",
      image: "",
      show: false
    }
  ]
};
