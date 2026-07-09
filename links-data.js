/* ことひらいふ「🔗 リンク」タブ用の公式リンク集。
   手編集OK（Notion連携ではなくコード直書き運用）。
   選定ルール: その分野の「一次窓口」だけを載せる。個別スポット・個別施設は
   観光協会・役場などのハブサイトに任せ、発信している団体は団体タブに、
   コワーキング・宿など「行ける拠点」は体験・滞在タブに任せる。
   例外: こんぴら歌舞伎は町最大の文化イベントのため公式サイトを直接掲載する。
   note には「ここに行けば何がわかるか」の道案内を書く。
   sns は公式に確認できたアカウントだけを載せる（偽物対策）。根拠は
   docs/公式SNSアカウント調査.md に記録する。2026-07-09 確認。
   各リンクは {name, url, note, image, sns:{line,instagram,x,youtube,facebook,discord}} 形式。
   url・sns・image は任意（独自サイトが無い取り組みは url:"" でバッジのみ）。
   image は assets/links/ のローカル画像（local-first）。出所は ①自作・撮影・先方提供
   ②サイトのog:image（シェア用に提供された画像のみ）に限る。スクリーンショットは
   権利上使わない。キャラクター画像は権利者・関係者からの提供があるものだけ使う
   （こんぴーくんは提供画像。温泉むすめは未提供のため使わない）。 */
window.LINKS_DATA = {
  updated: "2026-07-09",
  categories: [
    {
      name: "🏛 公式窓口",
      links: [
        {
          name: "琴平町役場（公式サイト）",
          url: "https://www.town.kotohira.kagawa.jp/",
          note: "くらし・行政手続き・防災など、町の公式情報はこちら",
          image: "assets/links/yakuba.png",
          sns: {
            line: "https://line.me/R/ti/p/@029gpoup",
            youtube: "https://www.youtube.com/@kotohirakoushiki"
          }
        },
        {
          name: "こんぴら観光まちづくり協会（琴平まるごとNavi）",
          url: "https://www.kotohirakankou.jp/",
          note: "観光・宿泊・食事・アクセスの情報はこちら",
          image: "assets/links/kankou-navi.png",
          sns: {
            instagram: "https://www.instagram.com/visitkotohira/",
            facebook: "https://www.facebook.com/kotohirakankou/"
          }
        },
        {
          name: "金刀比羅宮（こんぴらさん）",
          url: "https://www.konpira.or.jp/",
          note: "こんぴらさんの参拝・行事の情報はこちら",
          sns: {
            line: "https://linevoom.line.me/user/_dWbpVMB5Im4FTV7C5bSCC_Ohdn2yh0aORSlLo6U",
            instagram: "https://www.instagram.com/kotohiranomiya",
            x: "https://twitter.com/kotohiranomiya",
            youtube: "https://www.youtube.com/@%E9%87%91%E5%88%80%E6%AF%94%E7%BE%85%E5%AE%AE%E5%85%AC%E5%BC%8F%E3%83%81%E3%83%A3%E3%83%B3%E3%83%8D%E3%83%AB",
            facebook: "https://www.facebook.com/kotohiranomiya"
          }
        },
        {
          name: "琴平町商工会",
          url: "https://www.shokokai-kagawa.or.jp/kotohira/",
          note: "町内事業者の支援・経営相談はこちら",
          image: "assets/links/shokokai.png",
          sns: {
            instagram: "https://www.instagram.com/kotohira_shokokai/"
          }
        },
        {
          name: "琴平町社会福祉協議会",
          url: "https://www.k-wel.or.jp/",
          note: "福祉・ボランティアの相談窓口はこちら",
          image: "assets/links/shakyo-og.png",
          sns: {
            instagram: "https://www.instagram.com/kotohirashakyo/"
          }
        }
      ]
    },
    {
      name: "🎭 文化・まちの取り組み",
      links: [
        {
          name: "四国こんぴら歌舞伎大芝居",
          url: "https://www.konpirakabuki.jp/",
          note: "毎年春に金丸座で開催される歌舞伎公演の公式情報はこちら",
          sns: {
            instagram: "https://www.instagram.com/konpirakabuki/"
          }
        },
        {
          name: "ことひらまちじゅう図書館",
          url: "https://kotohira-machitosho.com/",
          note: "町のあちこちが図書館になる読書プロジェクト",
          image: "assets/links/machitosho-og.jpg",
          sns: {
            instagram: "https://www.instagram.com/kotohira_machitosho/",
            x: "https://x.com/libkotohira"
          }
        },
        {
          name: "温泉むすめ「こんぴら桃萌」",
          url: "https://onsen-musume.jp/character/konpira_momo",
          note: "こんぴら温泉のキャラクター。こんぴら観光大使としてパネル・グッズ・イベントも",
          sns: {
            x: "https://x.com/konpiramomo"
          }
        }
      ]
    },
    {
      name: "📣 まちの発信・コミュニティ",
      links: [
        {
          name: "琴平町長 片岡英樹",
          url: "https://ameblo.jp/kataoka-hideki/",
          note: "町長本人のブログとX。町政の動きを本人の言葉で発信しています",
          sns: {
            x: "https://x.com/kidogeisha"
          }
        },
        {
          name: "琴平町地域おこし協力隊",
          url: "https://www.town.kotohira.kagawa.jp/life/4/22/49/",
          note: "町の日常やイベント・活動の様子をSNSで発信しています",
          image: "assets/links/kyoryokutai.png",
          sns: {
            instagram: "https://www.instagram.com/kotohiraokoshi/",
            x: "https://x.com/kotohiraokoshi",
            youtube: "https://www.youtube.com/@%E7%90%B4%E5%B9%B3%E7%94%BA%E5%9C%B0%E5%9F%9F%E3%81%8A%E3%81%93%E3%81%97%E5%8D%94%E5%8A%9B%E9%9A%8A",
            facebook: "https://www.facebook.com/kotohira.chiikiokoshi/"
          }
        },
        {
          name: "こんぴーくん",
          url: "",
          note: "琴平町のご当地キャラクター",
          image: "assets/links/konpykun.png",
          sns: {
            instagram: "https://www.instagram.com/konpykonpy/"
          }
        },
        {
          name: "琴平町DAO",
          url: "",
          note: "地域おこし協力隊発のまちづくりコミュニティ。Discordから参加できます",
          image: "assets/links/kotohira-dao.png",
          sns: {
            discord: "https://discord.gg/DBKp7WCyJ9"
          }
        },
        {
          name: "琴平デジタル町民",
          url: "",
          note: "琴平バスが運営する“デジタル町民”の取り組み。LINEから参加できます",
          image: "assets/links/digital-chomin.png",
          sns: {
            line: "https://line.me/R/ti/p/@997qsntl",
            instagram: "https://www.instagram.com/kotohiradigitaltownresidents/",
            x: "https://x.com/kotohiradigital"
          }
        }
      ]
    }
  ]
};
