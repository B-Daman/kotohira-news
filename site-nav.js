/* サイトのナビ構造（第一階層グループ×第二階層ページ）とサイト情報3リンクを一元管理する。
   2026-09-05: 運営者情報/お問い合わせ/プライバシーポリシーはindex.htmlのSPAビュー
   （#operator/#contact/#privacy）へ統合し、旧operator.html/contact.html/privacy.htmlは
   リダイレクト殻になった。このファイルはindex.htmlのみが使う（site-info.cssも同様に
   index.html非依存の3ページ専用だったため、3ページ側での参照は無くなっている）。
   CSSはindex.htmlの<style>内に用意する。ここではデータとHTML生成・開閉の配線だけを持つ。 */
(function(){
  "use strict";

  function escNav(s){
    return ("" + (s == null ? "" : s)).replace(/[&<>"']/g, c => ({
      "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;"
    }[c]));
  }

  /* ===== ナビ構造の正本 ===== */
  window.SITE_NAV = {
    groups: [
      {key:"home", label:"🏠 ホーム", shortLabel:"🏠 ホーム", flat:true,
        items:[{key:"home", label:"🏠 ホーム"}]},
      {key:"now", label:"📰 町の今", shortLabel:"📰 町の今",
        items:[
          {key:"news", label:"📰 ニュース"},
          {key:"events", label:"📅 イベント"},
          {key:"campaigns", label:"🎁 キャンペーン"}
        ]},
      /* 2026-09-05: 町民向けサイトという性格から、くらしを訪れる・関わるより先に置く（あっきーさん判断） */
      {key:"kurashi", label:"🏡 くらし", shortLabel:"🏡 くらし",
        items:[
          {key:"towncal", label:"🗓 こんぴらカレンダー"},
          {key:"shopcal", label:"🏪 お店の営業カレンダー"}
        ]},
      {key:"visit", label:"🧭 訪れる・関わる", shortLabel:"🧭 訪れる",
        items:[
          {key:"experiences", label:"🧭 体験・滞在"},
          {key:"udon", label:"🍜 うどん店"},
          /* sweets（かき氷・アイス）は2026-08-28にアーカイブ。#sweets直リンクでページは開けるが
             メニューには出さない。復活させる場合はここに {key:"sweets", label:"🍧 かき氷・アイス"} を戻す */
          {key:"parking", label:"🅿 駐車場"}
        ]},
      {key:"know", label:"🔗 町を知る", shortLabel:"🔗 町を知る",
        items:[
          {key:"orgs", label:"📋 団体"},
          {key:"links", label:"🔗 リンク"}
        ]}
    ],
    /* index.htmlのSPAビュー（#operator等）への通常のハッシュ遷移。groups同様、他のitemsと
       同じ扱いでよくなったため、urlフィールドは持たない（2026-09-05のSPA統合で廃止）。 */
    siteLinks: [
      {key:"operator", label:"👤 運営者情報"},
      {key:"contact", label:"✉️ お問い合わせ"},
      {key:"privacy", label:"🔒 プライバシーポリシー"}
    ]
  };

  /* ===== ドロワーのアコーディオンHTML生成 =====
     大分類は「ホーム/町の今/訪れる・関わる/くらし/町を知る/サイト情報」の6つ。
     items 1件のグループはデフォルトではトグル付きアコーディオンとして出す（例: くらし ▸ こんぴらカレンダー）。
     ホームだけは「グループを開いてから選ぶ」動線が冗長なため、flat:true を付けてトグル無しの
     単独リンクにする（1件グループ＝単独リンクを常時にすると、今後同様の単項目グループを足すたびに
     意図せずアコーディオンが消えてしまうため、対象をホームに限定する明示フラグにした）。
     2026-09-05: サイト情報3件（運営者情報等）もSPAの通常ルートになったため、他のitemsと同じ
     activeItemKey判定・buildLeafHtmlで統一した（以前あったisSiteLink/resolveSiteLinkUrlの
     別経路は廃止。呼び出し側のindex.htmlがactiveGroupKeyに"siteinfo"を渡せば、この3件を含む
     グループとして開閉・アクティブ表示される）。
     leafの実リンクの作り方（ハッシュ遷移等）だけ呼び出し側のbuildLeafHtmlに委ねる。
     opts: {activeGroupKey, activeItemKey, buildLeafHtml(it,active)} */
  function accordionHTML(opts){
    opts = opts || {};
    const buildLeafHtml = opts.buildLeafHtml || function(it, active){
      return `<a class="drawer-link${active ? " active" : ""}" href="#${escNav(it.key)}">${escNav(it.label)}</a>`;
    };
    const groups = (window.SITE_NAV.groups || []).concat([{
      key:"siteinfo", label:"ℹ️ サイト情報",
      items: window.SITE_NAV.siteLinks || []
    }]);
    return groups.map(g=>{
      const items = g.items || [];
      if(g.flat && items.length === 1){
        const it = items[0];
        return buildLeafHtml(it, opts.activeItemKey === it.key);
      }
      const subId = "drawerSub-" + g.key;
      const expanded = g.key === opts.activeGroupKey;
      const hasActive = items.some(it => opts.activeItemKey === it.key);
      const leafHtml = items.map(it => buildLeafHtml(it, opts.activeItemKey === it.key)).join("");
      return `<div class="drawer-group">
        <button type="button" class="drawer-group-toggle${hasActive?' active':''}" aria-expanded="${expanded?'true':'false'}" aria-controls="${subId}">
          <span class="drawer-group-label">${escNav(g.label)}</span>
          <span class="drawer-caret" aria-hidden="true">${expanded?'▾':'▸'}</span>
        </button>
        <div class="drawer-sub" id="${subId}"${expanded?'':' hidden'}>${leafHtml}</div>
      </div>`;
    }).join("");
  }

  /* グループの開閉トグル。呼び出し側のドロワーnav要素に一度だけ配線する（クリック委譲）。
     leafリンク（[data-route]やa[href]）のクリックはここでは扱わない（呼び出し側の役割）。 */
  function bindAccordionToggles(root){
    if(!root || root.dataset.accordionBound) return;
    root.dataset.accordionBound = "1";
    root.addEventListener("click", function(e){
      const btn = e.target.closest(".drawer-group-toggle");
      if(!btn) return;
      const expanded = btn.getAttribute("aria-expanded") === "true";
      const sub = document.getElementById(btn.getAttribute("aria-controls"));
      btn.setAttribute("aria-expanded", String(!expanded));
      const caret = btn.querySelector(".drawer-caret");
      if(caret) caret.textContent = expanded ? "▸" : "▾";
      if(sub) sub.hidden = expanded;
    });
  }

  window.SiteNav = {
    accordionHTML: accordionHTML,
    bindAccordionToggles: bindAccordionToggles
  };
})();
