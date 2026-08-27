/* サイトのナビ構造（第一階層グループ×第二階層ページ）とサイト情報3リンクを一元管理する。
   index.html（SPAのタブ・ハンバーガードロワー）と operator.html/contact.html/privacy.html
   （ドロワーのみ。PC用タブが無いので☰は常時表示）で共有する。
   CSSは各ページ側に用意する（index.htmlの<style>内 と site-info.css）。ここではデータと
   HTML生成・開閉の配線だけを持つ。 */
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
      {key:"home", label:"🏠 ホーム", shortLabel:"🏠 ホーム",
        items:[{key:"home", label:"🏠 ホーム"}]},
      {key:"now", label:"📰 町の今", shortLabel:"📰 町の今",
        items:[
          {key:"news", label:"📰 ニュース"},
          {key:"events", label:"📅 イベント"},
          {key:"campaigns", label:"🎁 キャンペーン"}
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
    /* index.html側はWIDGETS.footerLinksの実URLで上書きするため、ここではファイル名の直書きでよい。
       operator/contact/privacy.htmlは自分自身からの相対パスとしてこの値をそのまま使う */
    siteLinks: [
      {key:"operator", label:"運営者情報", url:"operator.html"},
      {key:"contact", label:"お問い合わせ", url:"contact.html"},
      {key:"privacy", label:"プライバシーポリシー", url:"privacy.html"}
    ]
  };

  /* ===== ドロワーのアコーディオンHTML生成（index.html・情報3ページ共通） =====
     大分類は「ホーム/町の今/訪れる・関わる/町を知る/サイト情報」の5つ。
     itemsが1件だけのグループ（ホーム）はトグル無しの単独リンクにする。
     leafの実リンクの作り方（ハッシュ遷移 or 実ページへの<a>）だけ呼び出し側のbuildLeafHtmlに委ねる。
     opts: {activeGroupKey, activeItemKey, activeSiteLinkKey, buildLeafHtml(it,active), resolveSiteLinkUrl(link)} */
  function accordionHTML(opts){
    opts = opts || {};
    const buildLeafHtml = opts.buildLeafHtml || function(it, active){
      return `<a class="drawer-link${active ? " active" : ""}" href="#${escNav(it.key)}">${escNav(it.label)}</a>`;
    };
    const resolveSiteLinkUrl = opts.resolveSiteLinkUrl || function(link){ return link.url; };
    const groups = (window.SITE_NAV.groups || []).concat([{
      key:"siteinfo", label:"サイト情報",
      items:(window.SITE_NAV.siteLinks || []).map(l => Object.assign({isSiteLink:true}, l))
    }]);
    return groups.map(g=>{
      const items = g.items || [];
      if(items.length === 1 && !items[0].isSiteLink){
        const it = items[0];
        return buildLeafHtml(it, opts.activeItemKey === it.key);
      }
      const subId = "drawerSub-" + g.key;
      const expanded = g.key === opts.activeGroupKey;
      const hasActive = items.some(it => it.isSiteLink
        ? opts.activeSiteLinkKey === it.key
        : opts.activeItemKey === it.key);
      const leafHtml = items.map(it => it.isSiteLink
        ? `<a class="drawer-link${opts.activeSiteLinkKey===it.key?' active':''}" href="${escNav(resolveSiteLinkUrl(it))}" target="_self" rel="noopener"${opts.activeSiteLinkKey===it.key?' aria-current="page"':''}>${escNav(it.label)}</a>`
        : buildLeafHtml(it, opts.activeItemKey === it.key)
      ).join("");
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

  /* ===== 情報3ページ（operator/contact/privacy.html）専用：ハンバーガー＋ドロワーを自前で組み立てる =====
     index.htmlは自前のドロワー実装（SPAのハッシュ遷移・#appFrameのinert化と統合済み）を使うため
     こちらは呼ばない。3ページ側は <script src="site-nav.js"></script> の後に
     SiteNav.mountInfoDrawer("operator"|"contact"|"privacy") を1回呼ぶだけでよい。 */
  function mountInfoDrawer(activeSiteLinkKey){
    const header = document.querySelector(".site-header-inner");
    if(!header) return;

    const hamburger = document.createElement("button");
    hamburger.type = "button";
    hamburger.className = "hamburger-btn";
    hamburger.id = "hamburgerBtn";
    hamburger.setAttribute("aria-haspopup", "true");
    hamburger.setAttribute("aria-expanded", "false");
    hamburger.setAttribute("aria-controls", "drawerPanel");
    hamburger.setAttribute("aria-label", "メニューを開く");
    hamburger.textContent = "☰";
    header.appendChild(hamburger);

    const overlay = document.createElement("div");
    overlay.className = "drawer-overlay";
    overlay.id = "drawerOverlay";
    overlay.setAttribute("aria-hidden", "true");
    overlay.innerHTML = `
      <div class="drawer-panel" id="drawerPanel" role="dialog" aria-modal="true" aria-label="メインメニュー">
        <div class="drawer-head">
          <span class="drawer-title">メニュー</span>
          <button class="drawer-close" id="drawerCloseBtn" aria-label="閉じる" type="button">×</button>
        </div>
        <nav class="drawer-nav" id="drawerNav" aria-label="サイトメニュー"></nav>
      </div>`;
    document.body.appendChild(overlay);

    const nav = document.getElementById("drawerNav");
    nav.innerHTML = accordionHTML({
      activeGroupKey: "siteinfo",
      activeSiteLinkKey: activeSiteLinkKey,
      buildLeafHtml: (it) => `<a class="drawer-link" href="index.html#${escNav(it.key)}" target="_self" rel="noopener">${escNav(it.label)}</a>`,
      resolveSiteLinkUrl: (link) => link.url
    });
    bindAccordionToggles(nav);

    let lastFocused = null;
    function isOpen(){ return overlay.classList.contains("show"); }
    function setBackgroundInert(inert){
      document.querySelectorAll("body > header, body > main, body > footer").forEach(el=>{
        if(inert){ el.setAttribute("inert", ""); el.setAttribute("aria-hidden", "true"); }
        else { el.removeAttribute("inert"); el.removeAttribute("aria-hidden"); }
      });
    }
    function open(){
      if(isOpen()) return;
      lastFocused = document.activeElement;
      overlay.classList.add("show");
      overlay.setAttribute("aria-hidden", "false");
      hamburger.setAttribute("aria-expanded", "true");
      setBackgroundInert(true);
      document.body.classList.add("drawer-open");
      document.getElementById("drawerCloseBtn").focus();
    }
    function close(){
      if(!isOpen()) return;
      overlay.classList.remove("show");
      overlay.setAttribute("aria-hidden", "true");
      hamburger.setAttribute("aria-expanded", "false");
      setBackgroundInert(false);
      document.body.classList.remove("drawer-open");
      if(lastFocused && lastFocused.isConnected && typeof lastFocused.focus === "function") lastFocused.focus();
      lastFocused = null;
    }
    hamburger.addEventListener("click", function(){ isOpen() ? close() : open(); });
    document.getElementById("drawerCloseBtn").addEventListener("click", close);
    overlay.addEventListener("click", function(e){ if(e.target === overlay) close(); });
    nav.addEventListener("click", function(e){ if(e.target.closest("a[href]")) close(); });
    document.addEventListener("keydown", function(e){
      if(!isOpen()) return;
      if(e.key === "Escape"){ e.preventDefault(); close(); return; }
      if(e.key !== "Tab") return;
      const focusable = Array.from(document.getElementById("drawerPanel").querySelectorAll(
        'a[href],button:not([disabled]),[tabindex]:not([tabindex="-1"])'
      ));
      if(!focusable.length){ e.preventDefault(); return; }
      const first = focusable[0], last = focusable[focusable.length - 1];
      if(e.shiftKey && (document.activeElement === first || !overlay.contains(document.activeElement))){
        e.preventDefault(); last.focus();
      } else if(!e.shiftKey && (document.activeElement === last || !overlay.contains(document.activeElement))){
        e.preventDefault(); first.focus();
      }
    });
  }

  window.SiteNav = {
    accordionHTML: accordionHTML,
    bindAccordionToggles: bindAccordionToggles,
    mountInfoDrawer: mountInfoDrawer
  };
})();
