/* 🍜 うどん店タブの表示データ。
   基礎資料: 「琴平町DB - kotohira_udon_database.csv」（2026-07-13受領）。
   公式サイト・公式SNS・琴平町/香川県/観光協会等の公開情報を2026-07-13に照合した。
   営業時間・定休日・価格・駐車場は変動するため、来店前の再確認を前提とする。
   公式情報がない価格帯には「目安」と明記し、推測値を確定情報として扱わない。
   description は来訪者向けの紹介文、note は調査・更新担当者向けの内部メモ（画面には出さない）。
   schedule は営業中バッジの機械判定用（hours/closedのテキストが正で、schedule はそれを機械可読化したもの）。
   曜日は0=日〜6=土。closedDays=定休曜日／ranges=基本営業時間帯／byDay=曜日別の上書き／
   closedOnHoliday=祝日休みの店のみ付与／note=バッジ横に出す注意書き。祝日の特別営業時間（延長等）は未対応でnoteに記載。
   時間や休みが確認できず判定不能な店には schedule を付けない（＝バッジは非表示になるのが正しい挙動）。
   show:false は削除ではなく、営業形態の変更や現営業未確認のため画面から保留している項目。
   image は公式サイト等のog:imageを assets/places/ にローカル保存したもの（出所は imageSource）。
   Notion同様に画像はリポジトリを正とするlocal-first運用。og:imageが無い/ロゴのみ等の店舗は image を付けていない。 */
window.UDON_DATA = {
  checked: "2026-07-13",
  sourceFile: "琴平町DB - kotohira_udon_database.csv",
  sourceCount: 19,
  kinds: ["うどん店", "うどん作り体験", "製麺所・工場", "食事処・土産"],
  items: [
    {
      id: "udon-konpira-factory",
      name: "こんぴらうどん 本社工場併設店",
      kind: "製麺所・工場",
      area: "琴平町・JR琴平駅／表参道入口周辺",
      address: "香川県仲多度郡琴平町680",
      phone: "0877-73-3128",
      schedule: {
        closedDays: [2, 3],
        ranges: [["07:30", "15:00"]],
        note: "売り切れ次第終了・臨時変更あり"
      },
      hours: "7:30～15:00（売り切れ次第終了）",
      closed: "火・水曜日（臨時変更あり）",
      priceRange: "～999円（目安）",
      parking: "あり（台数は要確認）",
      seats: "要確認",
      features: ["製麺工場併設", "朝営業", "営業再開後の時間・休みは要確認"],
      description: "JR琴平駅と表参道入口に近い、製麺工場併設ならではの空気を味わえるうどん店です。",
      note: "2026年2月末までの休業告知後、同年5～6月の営業実績を確認。現行価格と駐車台数は公式確定値がないため、来店前の確認を推奨します。",
      status: "営業中と判断",
      confidence: "medium",
      links: {
        official: "https://www.konpira.co.jp/",
        facebook: "https://www.facebook.com/Konpiraudonsandouten",
        map: "https://maps.app.goo.gl/JSWisXX9wRRfogBHA",
        reference: "https://www.honba-sanukiudon.jp/shoplist/detail.php?i=9"
      },
      sources: [
        "https://www.konpira.co.jp/%E5%B7%A5%E5%A0%B4%E5%BA%97%E4%BC%91%E6%A5%AD%E6%97%A5/",
        "https://www.honba-sanukiudon.jp/shoplist/detail.php?i=9"
      ],
      checked: "2026-07-13",
      show: true
    },
    {
      id: "udon-nakano-school",
      name: "中野うどん学校 琴平校",
      kind: "うどん作り体験",
      area: "琴平町・表参道",
      address: "香川県仲多度郡琴平町796",
      phone: "0877-75-0001",
      schedule: {
        closedDays: [],
        ranges: [["09:00", "15:00"]],
        note: "うどん作り体験の受付時間"
      },
      hours: "体験9:00～15:00（A館8:30～17:30／B館9:00～17:00）",
      closed: "年中無休",
      priceRange: "体験1,760円／追加料理330～1,210円",
      parking: "専用駐車場あり（満車時は有料駐車場案内の場合あり）",
      seats: "要確認",
      features: ["うどん作り体験", "食事", "お土産", "2名以上から体験可"],
      description: "表参道でうどん作りと食事、お土産選びまで一度に楽しめる体験スポットです。",
      note: "15名以上の体験は1名1,650円。開校予定と空き状況は公式サイトでご確認ください。",
      status: "営業中",
      confidence: "high",
      image: "assets/places/udon-nakano-school.jpg",
      imageSource: "https://www.nakanoya.net/nakanoudon/",
      links: {
        official: "https://www.nakanoya.net/nakanoudon/",
        instagram: "https://www.instagram.com/udonschool_kotohira/",
        facebook: "https://www.facebook.com/udonschool.kotohira",
        map: "https://maps.app.goo.gl/WNYTowrw2Ddtos5YA",
        tourism: "https://www.my-kagawa.jp/udon/feature/sanukiudon/factory"
      },
      sources: [
        "https://www.nakanoya.net/nakanoudon/",
        "https://www.nakanoya.net/access/",
        "https://www.my-kagawa.jp/udon/feature/sanukiudon/factory"
      ],
      checked: "2026-07-13",
      show: true
    },
    {
      id: "udon-komatsuya",
      name: "小松屋（土産店）",
      kind: "食事処・土産",
      area: "琴平町・表参道",
      address: "香川県仲多度郡琴平町953-1",
      phone: "0877-75-2054",
      hours: "実店舗の商品販売時間は公式確認",
      closed: "公式確認",
      priceRange: "飲食受付終了",
      parking: "専用無料駐車場なし",
      seats: "",
      features: ["土産用讃岐うどん", "実店舗・通信販売"],
      note: "公式サイトが2023年に団体昼食・うどん飲食の受付終了を案内。土産店としては営業継続していますが、うどん店一覧では非表示にしています。",
      status: "飲食受付終了",
      confidence: "high",
      links: {
        official: "http://www.2054.co.jp/",
        map: "https://maps.app.goo.gl/a4BqggAQbfgpjP3q6",
        reference: "http://www.2054.co.jp/komatuyacom.htm"
      },
      sources: ["http://www.2054.co.jp/", "http://www.2054.co.jp/komatuyacom.htm"],
      checked: "2026-07-13",
      show: false
    },
    {
      id: "udon-toraya",
      name: "虎屋うどん",
      kind: "うどん店",
      area: "琴平町・表参道",
      address: "香川県仲多度郡琴平町957-1",
      phone: "0877-89-6746",
      schedule: {
        closedDays: [],
        ranges: [["09:00", "16:00"]],
        note: "不定休（最新情報はInstagram）"
      },
      hours: "9:00～16:00",
      closed: "不定休（最新情報はInstagram）",
      priceRange: "～999円（目安）",
      parking: "なし",
      seats: "要確認",
      features: ["そば・うどん", "歴史的建物", "宿泊施設併設"],
      description: "歴史ある建物でうどんやそばを味わい、琴平らしい趣に触れられる表参道の一軒です。",
      note: "観光協会は年中無休と掲載していますが、現行情報の競合があるため不定休として案内します。",
      status: "営業中",
      confidence: "medium",
      links: {
        instagram: "https://www.instagram.com/torayaudon2023/",
        map: "https://maps.app.goo.gl/siBFjMC9xgAfYxAt5",
        tourism: "https://www.kotohirakankou.jp/spot/eat/entry-98.html"
      },
      sources: ["https://www.kotohirakankou.jp/spot/eat/entry-98.html", "https://www.instagram.com/torayaudon2023/"],
      checked: "2026-07-13",
      show: true
    },
    {
      id: "udon-tsurudaya",
      name: "つるだや",
      kind: "うどん店",
      area: "琴平町・表参道",
      address: "香川県仲多度郡琴平町951",
      phone: "0877-73-3848",
      schedule: {
        closedDays: [],
        ranges: [["08:00", "17:00"]],
        note: "臨時休業あり"
      },
      hours: "8:00～17:00",
      closed: "年中無休（臨時休業あり）",
      priceRange: "500円～（目安）",
      parking: "あり（台数・利用条件は要確認）",
      seats: "要確認",
      features: ["石段近く", "うどん店", "土産物店", "食事・土産利用者は駐車無料"],
      description: "こんぴらさんの石段近くで、うどんと土産選びを一緒に楽しめる表参道の店です。",
      note: "駐車台数は情報源で異なります。最新の利用条件・料金は公式アクセス案内をご確認ください。",
      status: "営業中",
      confidence: "high",
      links: {
        official: "https://turudaya.jp/",
        map: "https://maps.app.goo.gl/2comAhpbH6SRw332A",
        tourism: "https://www.kotohirakankou.jp/spot/eat/entry-100.html"
      },
      sources: ["https://turudaya.jp/concept/", "https://turudaya.jp/access", "https://turudaya.jp/food/classic-menu"],
      checked: "2026-07-13",
      show: true
    },
    {
      id: "udon-inoue",
      name: "うどんや井上",
      kind: "うどん店",
      area: "琴平町・榎井",
      address: "香川県仲多度郡琴平町177-2",
      phone: "0877-75-3907",
      hours: "10:00～14:00（要確認）",
      closed: "月曜日（火曜営業は要確認）",
      priceRange: "～999円（目安）",
      parking: "2台",
      seats: "11席",
      features: ["路地裏", "小規模店", "昔ながらのうどん"],
      description: "榎井の路地裏にたたずみ、昔ながらの雰囲気と素朴なうどんを楽しめる小さな店です。",
      note: "公式サイト・公式SNSがなく、営業時間には情報差があります。電話での事前確認を推奨します。",
      status: "営業中と判断",
      confidence: "medium",
      links: {
        map: "https://maps.app.goo.gl/Ny4UjqFAHifDsWq5A",
        tourism: "https://www.kotohirakankou.jp/spot/eat/entry-95.html",
        reference: "https://tabelog.com/kagawa/A3703/A370302/37000255/"
      },
      sources: ["https://www.kotohirakankou.jp/spot/eat/entry-95.html", "https://tabelog.com/kagawa/A3703/A370302/37000255/"],
      checked: "2026-07-13",
      show: true
    },
    {
      id: "udon-menfune",
      name: "讃岐うどん めん舟",
      kind: "うどん店",
      area: "琴平町・苗田",
      address: "香川県仲多度郡琴平町苗田957-5",
      phone: "0877-85-9776",
      schedule: {
        closedDays: [1],
        ranges: [["10:00", "14:00"]],
        byDay: { "0": [["10:00", "15:00"]], "6": [["10:00", "15:00"]] },
        note: "麺切れ次第終了・祝日は〜15:00の場合あり"
      },
      hours: "10:00～14:00（土日祝～15:00、麺切れ終了）",
      closed: "月曜日",
      priceRange: "要確認",
      parking: "20台",
      seats: "54席",
      features: ["手打ち", "牛すじうどん", "青とうしょうゆ"],
      description: "手打ち麺に牛すじうどんや青とうしょうゆなど、ひと味違う名物がそろう苗田の店です。",
      note: "公的ページに現行価格の掲載がないため、価格は店舗でご確認ください。",
      status: "営業中",
      confidence: "high",
      image: "assets/places/udon-menfune.jpg",
      imageSource: "https://www.my-kagawa.jp/udon/4255",
      links: {
        map: "https://maps.app.goo.gl/NHoq1LEtMcGRx39E8",
        tourism: "https://www.my-kagawa.jp/udon/4255"
      },
      sources: ["https://www.my-kagawa.jp/udon/4255"],
      checked: "2026-07-13",
      show: true
    },
    {
      id: "udon-musashi",
      name: "手打ちうどん むさし",
      kind: "うどん店",
      area: "琴平町・五條",
      address: "香川県仲多度郡琴平町五條637-2",
      phone: "0877-75-0520",
      schedule: {
        closedDays: [1, 2],
        ranges: [["10:00", "15:00"], ["17:00", "20:00"]],
        note: "祝日は営業し翌平日休・不定休あり"
      },
      hours: "10:00～15:00（L.O.14:20）／17:00～20:00（L.O.19:20）",
      closed: "月・火曜日（祝日は営業し翌平日休、ほか不定休あり）",
      priceRange: "うどん450～880円（大＋140円）",
      parking: "あり（店頭＋隣接施設、台数要確認）",
      seats: "要確認",
      features: ["手打ち", "カレーうどん", "一般店"],
      description: "五條で手打ち麺とカレーうどんを味わえる、表参道のにぎわいから少し離れた一般店です。",
      note: "営業日変更があるため、来店前に公式サイトをご確認ください。",
      status: "営業中",
      confidence: "high",
      links: {
        official: "https://www.udon-musashi.com/",
        map: "https://maps.app.goo.gl/3mXe6RmrbNCWD4EMA",
        tourism: "https://www.my-kagawa.jp/ko/udon/udon04"
      },
      sources: ["https://www.udon-musashi.com/"],
      checked: "2026-07-13",
      show: true
    },
    {
      id: "udon-tentekomai",
      name: "てんてこ舞",
      kind: "うどん店",
      area: "琴平町・表参道",
      address: "香川県仲多度郡琴平町717",
      phone: "0877-75-0001",
      schedule: {
        closedDays: [],
        ranges: [["10:00", "15:30"]],
        byDay: { "0": [["09:30", "16:00"]], "6": [["09:30", "16:00"]] },
        note: "臨時休業あり・祝日は土日祝時間の場合あり"
      },
      hours: "平日10:00～15:30／土日祝9:30～16:00",
      closed: "年中無休（臨時休業あり）",
      priceRange: "400～750円",
      parking: "100台",
      seats: "要確認",
      features: ["セルフ式", "団体利用可", "歴史的建物"],
      description: "歴史ある建物の趣を感じながら、セルフ式で気軽に讃岐うどんを楽しめる表参道の店です。",
      note: "公式メニュー掲載価格を基にしています。臨時休業・売り切れは公式情報をご確認ください。",
      status: "営業中",
      confidence: "high",
      links: {
        official: "https://www.nakanoya.net/?service_category=tentekomai",
        instagram: "https://www.instagram.com/udonschool_kotohira/",
        facebook: "https://www.facebook.com/udonschool.kotohira",
        map: "https://maps.app.goo.gl/NMxry1eDGSqyyBJZ8",
        tourism: "https://www.kotohirakankou.jp/gourmet/udon/entry-99.html"
      },
      sources: ["https://www.nakanoya.net/?service_category=tentekomai", "https://www.nakanoya.net/menu/?smenu=tentekomai%2F"],
      checked: "2026-07-13",
      show: true
    },
    {
      id: "udon-konpira-sando",
      name: "こんぴらうどん参道店",
      kind: "うどん店",
      area: "琴平町・表参道",
      address: "香川県仲多度郡琴平町810-3",
      phone: "0877-73-5785",
      hours: "8:00～17:00（営業日の目安）",
      closed: "不定期営業（最新情報は公式サイト）",
      priceRange: "要確認",
      parking: "20台（飲食利用者無料）",
      seats: "要確認",
      features: ["表参道", "老舗", "手打ちうどん"],
      description: "表参道に店を構える老舗で、琴平散策の途中に昔ながらの手打ちうどんを味わえます。",
      note: "公式サイトが現在は不定期営業と案内しています。営業日を必ず公式新着情報でご確認ください。",
      status: "不定期営業",
      confidence: "high",
      links: {
        official: "https://www.konpira.co.jp/",
        facebook: "https://www.facebook.com/Konpiraudonsandouten",
        map: "https://maps.app.goo.gl/FbrB7MYwP33mP79C8",
        tourism: "https://www.kotohirakankou.jp/gourmet/udon/entry-114.html"
      },
      sources: ["https://www.konpira.co.jp/", "https://www.pref.kagawa.lg.jp/documents/58612/r7toshiakeudon.pdf"],
      checked: "2026-07-13",
      show: true
    },
    {
      id: "udon-tanukiya",
      name: "宗家 金毘羅饂飩 狸屋",
      kind: "うどん店",
      area: "琴平町・表参道",
      address: "香川県仲多度郡琴平町700-8",
      phone: "0877-73-2409",
      schedule: {
        closedDays: [],
        ranges: [["10:00", "17:00"]],
        byDay: { "0": [["09:30", "17:00"]], "6": [["09:30", "17:00"]] },
        note: "不定休・売り切れ次第終了"
      },
      hours: "平日10:00～17:00／土日祝9:30～17:00（売り切れ終了）",
      closed: "不定休",
      priceRange: "580～1,180円",
      parking: "約10台",
      seats: "100席",
      features: ["自家製麺", "本格手打ち", "伝統店"],
      description: "表参道で自家製麺と本格手打ちの味を受け継ぎ、琴平のうどん文化を伝える伝統店です。",
      note: "営業時間・価格は公式掲載を優先しています。",
      status: "営業中",
      confidence: "high",
      links: {
        official: "https://www.tanukiyaudon.com/?mode=f1",
        map: "https://maps.app.goo.gl/CfrddL4pDFu7XWff6",
        tourism: "https://www.kotohirakankou.jp/gourmet/udon/entry-140.html"
      },
      sources: ["https://www.tanukiyaudon.com/?mode=f1", "https://www.tanukiyaudon.com/?mode=f3"],
      checked: "2026-07-13",
      show: true
    },
    {
      id: "udon-iwanoya",
      name: "いわのや",
      kind: "うどん店",
      area: "琴平町・JR琴平駅周辺",
      address: "香川県仲多度郡琴平町291-10",
      phone: "0877-75-5282",
      schedule: {
        closedDays: [0],
        ranges: [["10:30", "15:00"]],
        note: "売り切れ次第終了"
      },
      hours: "10:30～15:00（売り切れ次第終了）",
      closed: "日曜日",
      priceRange: "要確認",
      parking: "22台",
      seats: "要確認",
      features: ["セルフ式", "JR琴平駅近く", "自家製薬味・青とう"],
      description: "JR琴平駅近くで、自家製の薬味や青とうを添えたセルフ式うどんを楽しめる店です。",
      note: "現行価格の公的掲載がないため、店舗でご確認ください。",
      status: "営業中",
      confidence: "high",
      links: {
        instagram: "https://www.instagram.com/iwanoyaudon/",
        map: "https://maps.app.goo.gl/rTUsgRqiRRp8VhaA8",
        tourism: "https://www.kotohirakankou.jp/gourmet/udon/entry-186.html"
      },
      sources: ["https://www.pref.kagawa.lg.jp/documents/58612/r7toshiakeudon.pdf", "https://www.kotohirakankou.jp/gourmet/udon/entry-186.html"],
      checked: "2026-07-13",
      show: true
    },
    {
      id: "udon-country",
      name: "カントリー",
      kind: "うどん店",
      area: "琴平町・下櫛梨",
      address: "香川県仲多度郡琴平町下櫛梨1020-5",
      phone: "0877-75-4468",
      hours: "10:45～19:00（要確認）",
      closed: "木曜日",
      priceRange: "～999円（目安）",
      parking: "あり（台数不明）",
      seats: "38席",
      features: ["セルフ式", "地元向けうどん店"],
      description: "下櫛梨にある地元向けのセルフ式うどん店で、観光地の店とは違う日常の味に出会えます。",
      note: "公式サイト・公式SNSがなく、営業時間に情報差があります。撮影禁止との案内もあるため現地ルールに従ってください。",
      status: "営業中と判断",
      confidence: "medium",
      links: {
        map: "https://maps.app.goo.gl/LpcHd5icpKdYHPBc7",
        reference: "https://tabelog.com/kagawa/A3703/A370302/37001558/"
      },
      sources: ["https://tabelog.com/kagawa/A3703/A370302/37001558/", "https://map.yahoo.co.jp/v3/place/40c0gE12FTw/review"],
      checked: "2026-07-13",
      show: true
    },
    {
      id: "udon-tsumugi",
      name: "琴平うどん食堂 紡麦～TSUMUGI～",
      kind: "うどん店",
      area: "琴平町・表参道入口周辺",
      address: "香川県仲多度郡琴平町722-1",
      phone: "070-4317-5544",
      schedule: {
        closedDays: [],
        ranges: [["11:00", "14:00"], ["16:30", "22:00"]],
        note: "不定休（最新情報はInstagram）"
      },
      hours: "11:00～14:00（L.O.13:30）／16:30～22:00頃",
      closed: "不定休（最新情報はInstagram）",
      priceRange: "昼～999円／夜1,000～1,999円（目安）",
      parking: "なし（近隣コインパーキング）",
      seats: "30席",
      features: ["創作うどん", "夜は居酒屋メニュー", "不定休"],
      description: "表参道入口で、創作うどんと居酒屋メニューの両方を楽しめる親しみやすい食堂です。",
      note: "休業日の情報が媒体間で異なるため、Instagramの最新投稿をご確認ください。",
      status: "営業中と判断",
      confidence: "medium",
      links: {
        instagram: "https://www.instagram.com/tsumugi_after/",
        facebook: "https://www.facebook.com/people/%E7%90%B4%E5%B9%B3%E3%81%86%E3%81%A9%E3%82%93%E9%A3%9F%E5%A0%82-%E7%B4%A1%E9%BA%A6/100076166670297/",
        map: "https://maps.app.goo.gl/mgwbBFeeYzsJena16",
        tourism: "https://www.kotohirakankou.jp/spot/eat/entry-200.html"
      },
      sources: ["https://www.kotohirakankou.jp/spot/eat/entry-200.html", "https://www.instagram.com/tsumugi_after/"],
      checked: "2026-07-13",
      show: true
    },
    {
      id: "udon-shukugetsu",
      name: "宿月",
      kind: "食事処・土産",
      area: "琴平町",
      address: "香川県仲多度郡琴平町1068",
      phone: "0877-85-8404",
      hours: "完全予約制（昼11:00／13:00開始、夜17:00～22:00）",
      closed: "月曜日＋臨時休業",
      priceRange: "昼3,300～4,400円／夜5,500～16,500円",
      parking: "店舗南約50mに4台",
      seats: "18席",
      features: ["日本料理", "饂飩会席", "前々日17時までの完全予約制", "2名以上"],
      description: "琴平で日本料理と饂飩会席をじっくり味わい、土地の食文化に触れられる一軒です。",
      note: "更新メモ: 現行公式では完全予約制・月曜日休。",
      status: "営業中",
      confidence: "high",
      links: {
        official: "https://shukugetsu.com/",
        instagram: "https://www.instagram.com/shukugetsu/",
        facebook: "https://www.facebook.com/shukugetsu/",
        map: "https://maps.app.goo.gl/zRT1zTxqN2jnJuyd6",
        tourism: "https://www.kotohirakankou.jp/spot/eat/entry-389.html"
      },
      sources: ["https://shukugetsu.com/guide.html", "https://shukugetsu.com/menu.html", "https://shukugetsu.com/access.html"],
      checked: "2026-07-13",
      show: true
    },
    {
      id: "udon-nishikido",
      name: "西木戸",
      kind: "食事処・土産",
      area: "琴平町・JR琴平駅／表参道入口周辺",
      address: "香川県仲多度郡琴平町696 にしきや1F",
      phone: "0877-75-3264",
      hours: "11:00～麺がなくなり次第終了",
      closed: "年中無休",
      priceRange: "～999円（目安）",
      parking: "大型バス20台（普通車台数は要確認）",
      seats: "32席",
      features: ["うどん御膳", "土産と食事", "団体利用"],
      description: "JR琴平駅と表参道入口に近く、うどん御膳と土産選びを一緒に楽しめる食事処です。",
      note: "更新メモ: 公式所在地は琴平町696。普通車の駐車台数は公式記載なし。",
      status: "営業中",
      confidence: "high",
      image: "assets/places/udon-nishikido.jpg",
      imageSource: "https://www.kotohira-nishikiya.com/",
      links: {
        official: "https://www.kotohira-nishikiya.com/",
        map: "https://www.google.com/maps/search/?api=1&query=%E8%A5%BF%E6%9C%A8%E6%88%B8+%E9%A6%99%E5%B7%9D%E7%9C%8C%E4%BB%B2%E5%A4%9A%E5%BA%A6%E9%83%A1%E7%90%B4%E5%B9%B3%E7%94%BA696",
        reference: "https://www.kotohira-nishikiya.com/%E3%81%8A%E9%A3%9F%E4%BA%8B/"
      },
      sources: ["https://www.kotohira-nishikiya.com/", "https://www.kotohira-nishikiya.com/%E3%81%8A%E9%A3%9F%E4%BA%8B/"],
      checked: "2026-07-13",
      show: true
    },
    {
      id: "udon-osyoya",
      name: "大庄屋製麺（旧・琴平の10分うどん）",
      kind: "製麺所・工場",
      area: "琴平町（旧情報）",
      address: "旧所在地: 香川県仲多度郡琴平町1223-9",
      phone: "0877-75-5980",
      hours: "琴平での現営業は確認できず",
      closed: "要確認",
      priceRange: "旧価格200円（現行対象外）",
      parking: "旧情報20台",
      seats: "",
      features: ["製麺所", "うどん作り体験", "10分うどんは高松へ移転"],
      note: "現行の10分うどんは高松市番町へ移転。琴平施設の飲食営業を確認できないため非表示にしています。",
      status: "琴平での営業未確認",
      confidence: "high",
      links: {
        official: "https://osyoya.com/",
        instagram: "https://www.instagram.com/osyoya/",
        x: "https://x.com/10pun_udon",
        reference: "https://osyoya.com/10punudon/"
      },
      sources: ["https://osyoya.com/", "https://osyoya.com/10punudon/", "https://osyoya.com/company/"],
      checked: "2026-07-13",
      show: false
    },
    {
      id: "udon-yoshidaya",
      name: "吉田家",
      kind: "うどん店",
      area: "琴平町・表参道",
      address: "香川県仲多度郡琴平町928-2",
      phone: "0877-75-2797",
      hours: "9:00～16:00",
      closed: "要確認",
      priceRange: "～1,999円（目安）",
      parking: "なし",
      seats: "80席",
      features: ["こんぴらさん92段目", "うどん店"],
      description: "こんぴらさんの石段92段目にあり、参拝の途中でうどんを味わえる表参道の一軒です。",
      note: "営業時間・定休日・価格は公式の詳細掲載がないため、来店前の確認を推奨します。",
      status: "営業中",
      confidence: "medium",
      links: {
        map: "https://maps.app.goo.gl/DoWtseqe4y8ah1u69",
        tourism: "https://www.kotohirakankou.jp/spot/eat/entry-208.html",
        reference: "https://tabelog.com/kagawa/A3703/A370302/37001458/"
      },
      sources: ["https://www.kotohirakankou.jp/spot/eat/entry-208.html", "https://tabelog.com/kagawa/A3703/A370302/37001458/"],
      checked: "2026-07-13",
      show: true
    },
    {
      id: "udon-fujinoya",
      name: "藤の家食堂",
      kind: "食事処・土産",
      area: "琴平町・榎井",
      address: "香川県仲多度郡琴平町榎井34-4",
      phone: "要確認",
      schedule: {
        closedDays: [0],
        closedOnHoliday: true,
        ranges: [["10:30", "18:00"]]
      },
      hours: "10:30～18:00",
      closed: "日曜日・祝日",
      priceRange: "～999円（目安）",
      parking: "道路向かい南側5台＋店舗裏約20台",
      seats: "要確認",
      features: ["食堂", "中華そば・巻き寿司", "うどん・鍋焼きうどんあり"],
      description: "榎井で中華そばや巻き寿司、うどん、鍋焼きうどんまで幅広く味わえる町の食堂です。",
      note: "うどん専門店ではありませんが、うどん提供の記録と2026年5月の営業実績を確認したため食事処として掲載します。",
      status: "営業中",
      confidence: "medium",
      links: {
        map: "https://www.google.com/maps/search/?api=1&query=%E8%97%A4%E3%81%AE%E5%AE%B6%E9%A3%9F%E5%A0%82+%E9%A6%99%E5%B7%9D%E7%9C%8C%E4%BB%B2%E5%A4%9A%E5%BA%A6%E9%83%A1%E7%90%B4%E5%B9%B3%E7%94%BA%E6%A6%8E%E4%BA%9534-4",
        reference: "https://map.yahoo.co.jp/v3/place/v12YQNhzFkk"
      },
      sources: ["https://www.pref.kagawa.lg.jp/documents/3882/taberu_nomu.pdf", "https://tabelog.com/kagawa/A3703/A370302/37000269/"],
      checked: "2026-07-13",
      show: true
    }
  ]
};
