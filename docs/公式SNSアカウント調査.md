# 公式SNS・LINEアカウント調査 ― リンクタブの根拠記録

リンクタブ（links-data.js）に載せるSNS・LINEの調査記録。
手法: Deep Researchワークフロー（検索5系統 → 公式ソース精読 → 候補ごとに反証3票の検証。全Sonnet・17エージェント）＋公式サイト7件の直接確認。
公式性の基準: 公式サイト・自治体ドメイン・広報PDF・プラットフォーム認証・公式APIのいずれかで確認できること。検索でヒットしただけのアカウントは不採用。

調査日: 2026-07-09

---

## 確認できた公式アカウント（links-data.js に反映済み）

| 組織 | チャネル | URL | 根拠 |
|---|---|---|---|
| 琴平町役場 | LINE | line.me/R/ti/p/@029gpoup | 役場サイト告知ページにID明記（soshiki/2/6934.html）。LINE側名義「琴平町」・住所・代表電話が役場と一致。運用ポリシーPDFあり（企画防災課） |
| 琴平町役場 | Instagram | instagram.com/kotohiraokoshi | 役場サイトトップに掲載・公式明記 ※後日、地域おこし協力隊名義と判明し協力隊カードへ移動（第2回調査参照） |
| 琴平町役場 | YouTube | channel/UCZXQdj-oltsS5XpPaCe5Vgw | 役場サイトトップに掲載 ※第2回調査で @kotohirakoushiki と同一・役場本体名義と確定 |
| こんぴら観光まちづくり協会 | Instagram / Facebook | visitkotohira ／ kotohirakankou | 公式サイトトップに掲載 |
| 金刀比羅宮 | LINE VOOM / Instagram / X / Facebook | kotohiranomiya 各種 | 公式サイトトップに掲載 |
| 金刀比羅宮 | YouTube | @金刀比羅宮公式チャンネル | 公式サイト掲載動画の投稿者をYouTube公式oEmbed APIで特定 |
| 琴平町商工会 | Instagram | kotohira_shokokai | 公式サイトに掲載 |
| 琴平町社会福祉協議会 | Instagram | kotohirashakyo | 公式サイトに掲載 |
| 四国こんぴら歌舞伎大芝居 | Instagram | konpirakabuki | 公式サイトに掲載 |

### 本人（運営者）提供により追加（検証基準の対象外）
- ことひらまちじゅう図書館: Instagram kotohira_machitosho ／ X libkotohira
- 琴平町DAO: Discord招待 discord.gg/DBKp7WCyJ9
- 琴平デジタル町民: LINE @997qsntl（＋調査で確認したX @kotohiradigital。運営は琴平バス㈱）

---

## 「存在しない／使えない」ことを確認したもの（再調査不要の知見）

- **「このことひら／この琴平／コノコトヒラ」なるLINE・メディアは存在しない**。完全一致検索・類似名・LINE上の「琴平」を含むアカウント総当たりでも該当なし。LINE上の琴平系は「琴平町（役場）」「琴平デジタル町民」「コトバスエクスプレス」のみ
- 琴平町役場の**公式Xは無い**（サイト内のSNS案内にも記載なし）
- 観光まちづくり協会の**LINE・X・YouTubeは無い**（Instagram・Facebookのみ）
- 商工会の**本体名義Facebookは無い**（青年部・女性部名義のみ。組織本体と別名義のため不採用）
- 社協・歌舞伎はInstagramのみ。まちじゅう図書館はサイト上にSNS導線なし（フッターはシェアボタン。※後日、運営者提供でInstagram/X判明）
- 金刀比羅宮公式サイトの**YouTubeプレイリストリンクは壊れている**（list=PLd9kJzqbttpk、IDが途中で切断）。検索上位の「金刀比羅宮 公式『科野齋チャンネル』」は公式サイトからのリンクが無く公式性未確認のため不採用
- **MetaMe「琴平CW」（デジタル町民の旧メタバース側）は終了**（LP・詳細ページとも404）。「琴平デジタル町民」（LINE・琴平バス運営、2024年2月開始）とは別プロジェクト
- 琴平町観光案内所X・こんぴーくんX: 存在はするが公式性の裏付けが取れず不採用

---

## 運用メモ

- 追加時はこのファイルの基準（公式ソースでの確認）に従い、確認できたら本ファイルにも追記する
- 個人名義（町長・議員・協力隊員等）は原則載せない方針だが、町長は「町の今を知る主要な発信源」として本人性を確認の上で掲載する（2026-07-09の判断）。任期満了・交代時に見直す

---

## 第2回調査（広域・2026-07-09）

手法: 広域調査（帰属解明4本＋既存候補群の再検証。反証3票制、23件を審議）。

### 帰属の確定事項

- **役場YouTube**: `channel/UCZXQdj-oltsS5XpPaCe5Vgw` と `@kotohirakoushiki` は同一チャンネル（YouTube公式oEmbed API＋役場サイト掲載動画との一致で確認）。名義は役場本体「琴平町公式チャンネル」
- **協力隊Facebook**: numeric ID `659888847433823` と `facebook.com/kotohira.chiikiokoshi` は同一ページ（投稿ID一致で確認）
- **`@琴平町地域おこし協力隊`（YouTube）**: 実在（HTTP200）だが外部参照・被リンクがゼロで公式性は未確認。運営者本人の判断により掲載を継続中

### 町長 片岡英樹のアカウント

| チャネル | URL | 採否 | 根拠 |
|---|---|---|---|
| Amebaブログ | ameblo.jp/kataoka-hideki | 採用（確度高） | 「オフィシャルブログ」明記。Amebaプロフィール職業欄に「公務員琴平町長」 |
| X | x.com/kidogeisha | 採用（準公式） | Amebaプロフィールからの相互リンクあり |
| Instagram | instagram.com/kataokahideki | 不採用 | 単独ソースのみで被リンクなし、なりすまし複製の可能性排除できず |
| Facebook | 「琴平町長 片岡英樹」 | 不採用 | 類似名の別URLが並存し、複製の可能性排除できず |

町公式サイトの町長プロフィールページ（site/tyoutyou/3807.html）にSNSリンクの掲載は無い。

### 温泉むすめ「こんぴら桃萌」

キャラクター「こんぴら桃萌」（onsen-musume.jp/character/konpira_momo）。2023-07-09にこんぴら観光大使委嘱、常設パネル3拠点（中野うどん学校／こんぴら温泉 湯元八千代／こんぴら観光まちづくり協会）を設置、2026-05-27に生誕祭（ことひらテラス、こんぴら観光まちづくり協会主催）開催。X `@konpiramomo`（x.com/konpiramomo）を掲載採用するが、運営主体（地元か温泉むすめプロジェクト本部か）は未特定のため要注記。

### 検証を通過したが掲載対象外としたもの

| 対象 | チャネル | 対象外理由 |
|---|---|---|
| 琴平小学校・榎井小学校 | website | 個別施設のためリンク集対象外 |
| 香川県立琴平高等学校 | Instagram | 個別施設のためリンク集対象外 |
| 仲多度南部消防組合消防本部 | website | 個別施設（広域組合）のため対象外 |
| KOTO VEGAS内テナント（TeaRoom／kotonote） | Instagram | 個別営利店舗のため対象外 |
| KOTOHIRA YAMA EXPO・公式X | website／x.com/kotohiraart | 2025-12-25閉幕済み、休止中のため対象外 |

### 反証で落ちたもの（抜粋、3票内訳）

| 候補 | チャネル | URL | 票 |
|---|---|---|---|
| こんぴーくん（追加X垢） | X | x.com/konpykonpy | NG/NG/NG |
| 琴平町観光案内所 | X | x.com/cIfHRP5bla54791 | NG/NG/NG |
| 四国金毘羅ねぷた祭り | Facebook | facebook.com/kompira.neputa | NG/NG/NG |
| わん詣こんぴら狗プロジェクト | Instagram | instagram.com/wp_kotohira | NG/NG/NG |
| 象郷小学校 | website | e-zogo.edumap.jp | NG/NG/NG |
| 琴平中学校 | website | kotohira-j-web.jimdofree.com | NG/NG/NG |
| KOTOVEGAS統合アカウント | Instagram | instagram.com/kotovegas | NG/NG/NG |
| YAMA EXPO公式Instagram | Instagram | instagram.com/kotohiraart | NG/NG/OK |

### 主なネガティブ所見

- 小中学校4校（琴平小・榎井小・象郷小・琴平中）はいずれも独自サイトを持つが、学校名義の公式SNSは無い（児童生徒保護の観点とみられる）
- 町立こども園・保育所・幼稚園は独自サイト・SNSを持たず、役場サイト内ページのみで案内
- 公民館（琴平・中央・榎井）は独自サイト・SNSを持たず、役場サイト内ページのみで案内
- 文化会館（歴史民俗資料館・琴平公民館併設）は独自サイト・SNSを持たない
- 町議会は独自サイト・SNS（YouTube中継等）を持たない
- 教育委員会は独自サイト・SNSを持たない
- こんぴら温泉郷・温泉旅館協同組合は組合としての独自サイト・SNSを持たない（各旅館は個別に保有）
- 商店街振興組合（法人格を持つ団体）としての独自SNSは見当たらない
- 消防団（住民組織）自体の独自SNSは無い。類似名Facebook「仲多度南部消防組合消防本部」は公式サイトからの被リンクがなく非採用
- 琴平ロータリークラブ（kotohira-rc.com）はドメインが名前解決不可、国際ロータリー第2670地区の現行クラブ一覧にも該当なし。解散・統合の可能性が高く非採用
