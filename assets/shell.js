/*
 * App shell shared by every page.
 *
 * A page only needs:
 *   <html data-theme="dark"> + the inline theme snippet in <head>
 *   <body data-root="../../.." data-section="01" data-page="concept">
 *     <main class="content"> ... details.box panes ... </main>
 *
 * This script adds the top bar (sidebar toggle, collapse/expand all, theme)
 * and the sidebar (chapter navigation + "on this page" table of contents),
 * and remembers sidebar / theme / pane state in localStorage.
 *
 * Shortcuts:  [  toggle sidebar    t  next theme (Ayu Dark / Mirage / Light)    e  expand all    c  collapse all
 *
 * It also colors Python code blocks (pre > code) with Ayu's syntax colors.
 * Add class="diagram" or class="plain" to a <pre> to skip coloring.
 */
(function () {
  const store = {
    get(k, d) { try { const v = localStorage.getItem("swe-prep:" + k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem("swe-prep:" + k, JSON.stringify(v)); } catch (e) { /* ignore */ } },
  };
  const h = (tag, attrs = {}, ...kids) => {
    const n = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (v == null) continue;
      if (k === "class") n.className = v;
      else if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
      else n.setAttribute(k, v);
    }
    for (const k of kids.flat(Infinity)) if (k != null) n.append(k.nodeType ? k : document.createTextNode(k));
    return n;
  };
  window.SWEStore = store;
  window.SWEh = h;
  document.addEventListener("DOMContentLoaded", boot);

  function boot() {
  const C = window.CURRICULUM || { sections: [] };
  const body = document.body;
  const ROOT = body.dataset.root || ".";
  const SECTION = body.dataset.section || null;
  const PAGE = body.dataset.page || "home";
  const sec = C.sections.find((s) => s.id === SECTION);
  const conceptHref = (s, file) => `${ROOT}/sections/${s.slug}/concepts/${file}`;
  const chapterHref = (s) => `${ROOT}/sections/${s.slug}/index.html`;
  const here = location.pathname.split("/").pop();

  // ---- Theme ----
  // Ayu Dark (default) -> Ayu Mirage -> Ayu Light. Colors live in style.css.
  const THEMES = ["dark", "mirage", "light"];
  const THEME_NAMES = { dark: "Ayu Dark", mirage: "Ayu Mirage", light: "Ayu Light" };
  const currentTheme = () => (THEMES.includes(document.documentElement.dataset.theme) ? document.documentElement.dataset.theme : "dark");
  const applyTheme = (t) => { document.documentElement.dataset.theme = t; store.set("theme", t); };
  const toggleTheme = () => { applyTheme(THEMES[(THEMES.indexOf(currentTheme()) + 1) % THEMES.length]); document.dispatchEvent(new Event("swe-theme")); };

  // ---- Code colors: tag Python tokens so style.css can paint them in Ayu's syntax colors ----
  const KEYWORDS = new Set("def class return if elif else for while in not and or is import from as with try except finally raise lambda yield pass break continue global nonlocal assert del async await".split(" "));
  const BUILTINS = new Set("len range print set dict list tuple sorted min max sum int str float bool enumerate zip abs isinstance super map filter any all reversed iter next open self object type hash id".split(" "));
  const TOKEN = /(#[^\n]*)|((?:[rRbBfFuU]{1,2})?(?:"""[\s\S]*?"""|'''[\s\S]*?'''|"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*'))|(\b\d[\d_]*(?:\.\d+)?(?:e[+-]?\d+)?\b)|([A-Za-z_][A-Za-z0-9_]*)|([-+*/%=<>!&|^~@]+)/g;
  const esc = (t) => t.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  function highlight(code) {
    const src = code.textContent;
    let out = "", last = 0, prevWord = "", m;
    TOKEN.lastIndex = 0;
    while ((m = TOKEN.exec(src))) {
      out += esc(src.slice(last, m.index));
      const [tok, com, str, num, word, op] = m;
      let cls = null;
      if (com) cls = "c";
      else if (str) cls = "s";
      else if (num) cls = "n";
      else if (op) cls = "o";
      else if (word) {
        if (word === "None" || word === "True" || word === "False") cls = "n";
        else if (KEYWORDS.has(word)) cls = "k";
        else if (prevWord === "def") cls = "f";
        else if (prevWord === "class") cls = "e";
        else if (BUILTINS.has(word)) cls = "e";
        else if (src[TOKEN.lastIndex] === "(") cls = "f";
        prevWord = word;
      }
      out += cls ? `<span class="${cls}">${esc(tok)}</span>` : esc(tok);
      last = TOKEN.lastIndex;
    }
    code.innerHTML = out + esc(src.slice(last));
  }
  const highlightAll = () => document.querySelectorAll("pre:not(.diagram):not(.plain) > code").forEach((c) => { if (!c.children.length) highlight(c); });

  // ---- Panes ----
  const boxes = () => [...document.querySelectorAll("details.box")];
  const paneKey = "panes:" + location.pathname;
  const paneState = store.get(paneKey, {});
  const setAll = (open) => { boxes().forEach((b) => (b.open = open)); };

  // ---- Sidebar ----
  const mobile = () => window.matchMedia("(max-width: 860px)").matches;
  const setSidebar = (hidden) => { body.classList.toggle("sidebar-hidden", hidden); if (!mobile()) store.set("sidebarHidden", hidden); };
  const toggleSidebar = () => setSidebar(!body.classList.contains("sidebar-hidden"));

  function buildTopbar() {
    const crumbs = h("nav", { class: "crumbs" });
    if (sec) {
      crumbs.append(" / ", h("a", { href: chapterHref(sec) }, `§${sec.id} ${sec.title}`));
      if (PAGE === "concept") crumbs.append(" / ", document.title);
    }
    const hasBoxes = boxes().length > 0;
    const themeBtn = h("button", { class: "btn icon", title: "Switch theme: Ayu Dark, Mirage, Light  (t)", "aria-label": "Switch theme" });
    const paint = () => { themeBtn.textContent = "◐ " + THEME_NAMES[currentTheme()]; };
    themeBtn.addEventListener("click", () => { toggleTheme(); paint(); });
    document.addEventListener("swe-theme", paint);
    paint();
    return h("header", { class: "topbar" },
      h("button", { class: "btn icon", title: "Toggle sidebar  [", "aria-label": "Toggle sidebar", onclick: toggleSidebar }, "☰"),
      h("a", { class: "brand", href: `${ROOT}/index.html` }, "swe", h("span", {}, "/"), "prep"),
      crumbs,
      h("div", { class: "spacer" }),
      hasBoxes ? h("button", { class: "btn hide-sm", title: "Collapse all panes  c", onclick: () => setAll(false) }, "Collapse all") : null,
      hasBoxes ? h("button", { class: "btn hide-sm", title: "Expand all panes  e", onclick: () => setAll(true) }, "Expand all") : null,
      themeBtn);
  }

  function buildSidebar() {
    const side = h("aside", { class: "sidebar", id: "sidebar" });
    if (sec) {
      side.append(h("h4", {}, `§${sec.id} · ${sec.title}`));
      side.append(h("a", { href: chapterHref(sec), class: PAGE === "chapter" ? "active" : null }, "Chapter overview"));
      for (const t of sec.topics) {
        const pages = sec.concepts.filter((c) => c.topic === t.id);
        if (pages.length) {
          for (const c of pages) {
            side.append(h("a", { href: conceptHref(sec, c.file), class: c.file === here && PAGE === "concept" ? "active" : null },
              h("span", { class: "tag" }, t.tag), c.title));
          }
        } else {
          side.append(h("a", { href: chapterHref(sec) + "#t-" + t.id, class: "pending", title: "Not written yet" },
            h("span", { class: "tag" }, t.tag), shortTitle(t.text)));
        }
      }
    }
    const heads = document.querySelectorAll("main.book h2[id]");
    if (heads.length) {
      const toc = h("div", { class: "toc" });
      heads.forEach((hd) => toc.append(h("a", { href: "#" + hd.id, "data-target": hd.id, onclick: () => { if (mobile()) setSidebar(true); } }, hd.textContent.trim())));
      side.append(h("h4", {}, "In this chapter"), toc);
    }
    const bx = heads.length ? [] : boxes();
    if (bx.length) {
      const toc = h("div", { class: "toc" });
      bx.forEach((b, i) => {
        if (!b.id) b.id = "pane-" + (i + 1);
        const label = b.querySelector(":scope > summary .label")?.textContent || b.querySelector(":scope > summary").textContent;
        toc.append(h("a", { href: "#" + b.id, "data-target": b.id, onclick: () => { b.open = true; if (mobile()) setSidebar(true); } }, label.trim()));
      });
      side.append(h("h4", {}, "On this page"), toc);
    }
    side.append(h("h4", {}, "All chapters"));
    for (const s of C.sections) {
      side.append(h("a", { href: chapterHref(s), class: s.id === SECTION && PAGE !== "chapter" ? null : null },
        h("span", { class: "tag" }, s.concepts.length ? s.concepts.length + " pg" : ""), `§${s.id} ${s.title}`));
    }
    return side;
  }

  function shortTitle(text) {
    const cut = text.split(/[:;(]/)[0].trim();
    return cut.length > 48 ? cut.slice(0, 46) + "…" : cut;
  }

  function scrollSpy() {
    const links = [...document.querySelectorAll(".toc a")];
    if (!links.length || !("IntersectionObserver" in window)) return;
    const obs = new IntersectionObserver((entries) => {
      for (const e of entries) if (e.isIntersecting) {
        links.forEach((a) => a.classList.toggle("active", a.dataset.target === e.target.id));
      }
    }, { rootMargin: "-20% 0px -70% 0px" });
    const heads = document.querySelectorAll("main.book h2[id]");
    (heads.length ? heads : boxes()).forEach((b) => obs.observe(b));
  }

  function init() {
    const main = document.querySelector("main.content");
    if (!main) return;
    // restore pane state, then remember changes
    boxes().forEach((b, i) => {
      const id = b.id || "pane-" + (i + 1);
      if (id in paneState) b.open = paneState[id];
      b.addEventListener("toggle", () => { paneState[id] = b.open; store.set(paneKey, paneState); });
    });
    const layout = h("div", { class: "layout" });
    main.replaceWith(layout);
    layout.append(buildSidebar(), main);
    body.prepend(buildTopbar());
    setSidebar(mobile() ? true : store.get("sidebarHidden", false));
    scrollSpy();
    highlightAll();
    document.addEventListener("keydown", (e) => {
      if (e.metaKey || e.ctrlKey || e.altKey || /input|textarea|select/i.test(e.target.tagName)) return;
      if (e.key === "[") toggleSidebar();
      else if (e.key === "t") toggleTheme();
      else if (e.key === "e") setAll(true);
      else if (e.key === "c") setAll(false);
    });
    if (location.hash) document.getElementById(location.hash.slice(1))?.setAttribute("open", "");
  }
  init();
  }
})();
