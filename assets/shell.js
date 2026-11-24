/*
 * App shell shared by every page.
 *
 * A page only needs:
 *   <html data-theme="dark"> + the inline theme snippet in <head>
 *   <script src=".../shell.js"> in <head> (it applies saved preferences before first paint)
 *   <body data-root="../../.." data-section="01" data-page="home|chapter|concept">
 *     <main class="content"> ... </main>
 *
 * This script adds:
 *   - the top bar: sidebar toggle, breadcrumbs, search, theme, Appearance (Aa), contents toggle
 *   - the left sidebar: the track (weekly stages from curriculum.json) or every chapter, as trees
 *   - previous / next links on chapter pages that follow the track (window.SWETrack)
 *   - the right rail on book pages: "On this page" contents with scroll spy and reading progress
 *   - the Appearance panel: theme, reading font, text size, line width, code font
 *   - a jump-to palette (/ or Cmd-K) and a shortcuts sheet (?)
 * Preferences, sidebar / rail visibility and reading progress live in localStorage.
 *
 * Shortcuts:  [ sidebar   ] contents   t next theme   a appearance   + / - text size
 *             / or Cmd-K jump to   e / c open / close all asides   ? shortcuts   Esc close
 *
 * It also colors Python code blocks (pre > code) with the theme's syntax colors.
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

  // ---- The track: the learning order in curriculum.json ("track"), shared by the
  // sidebar, the home page, chapter pages and each page's previous / next links ----
  function makeTrack(C) {
    if (!C || !C.track) return null;
    const topic = {};
    C.sections.forEach((s) => s.topics.forEach((t) => (topic[t.id] = { t, s })));
    const KIND = { "07": "design", "14": "story", "15": "mock" };
    const stages = C.track.stages.map((st, si) => {
      const o = Object.assign({}, st, { si });
      o.steps = st.steps.map((x) => {
        const { t, s } = topic[x.topic];
        const pages = s.concepts.filter((c) => c.topic === x.topic);
        const isWritten = pages.some((c) => c.status !== "outline");
        const isOutline = pages.length > 0 && !isWritten;
        return Object.assign({}, x, {
          id: x.topic, key: x.topic, t, s, stage: o, optional: !!x.optional, kind: KIND[s.id] || "learn",
          pages, isWritten, isOutline,
          exercises: s.exercises.filter((e) => e.topics.includes(x.topic)),
        });
      });
      o.milestone = st.milestone ? Object.assign({}, st.milestone, { key: st.milestone.id, stage: o, isMilestone: true, kind: "milestone" }) : null;
      o.code = /^Week (\d+)/.test(st.label) ? "W" + st.label.match(/^Week (\d+)/)[1]
        : /^Phase (\d+)/.test(st.label) ? st.label.match(/^Phase (\d+)/)[1]
        : st.label[0];
      return o;
    });
    const items = (st) => st.steps.concat(st.milestone ? [st.milestone] : []);
    const all = stages.flatMap((st) => st.steps);
    const byTopic = Object.fromEntries(all.map((x) => [x.id, x]));
    const main = stages.filter((st) => !st.pick && !st.parallel).flatMap(items);
    const status = () => store.get("status", {});
    const read = () => store.get("read", {});
    const pagePath = (x, c) => `sections/${x.s.slug}/concepts/${c.file}`;
    const short = (t) => t.short || t.text.split(/[:;(]/)[0].trim();
    const T = {
      stages, all, byTopic, items, short, pagePath,
      isDone: (x, st = status()) => st[x.key] === "confident",
      readPct: (x, r = read()) => (x.pages && x.pages.length ? Math.min(...x.pages.map((c) => r[pagePath(x, c)] || 0)) : 0),
      title: (x) => (x.isMilestone ? x.title : x.isWritten ? x.pages[0].title : short(x.t)),
      kindLabel: (x) => ({ learn: x.isWritten ? "Read" : x.isOutline ? "Outline" : "Learn", design: "Design", story: "Story", mock: x.isWritten ? "Read" : "Mock", milestone: "Milestone" })[x.kind],
      href: (x, root) => x.isMilestone ? `${root}/index.html#stage-${x.stage.id}`
        : x.pages.length ? `${root}/${pagePath(x, x.pages[0])}` : `${root}/sections/${x.s.slug}/index.html#t-${x.id}`,
      // What to do for this step, as DOM nodes
      todo(x, root) {
        const ask = (q) => ["Ask Claude: ", h("q", {}, q), "."];
        // "Load balancing" becomes "load balancing"; "TCP vs UDP" stays as it is
        const lower = (s) => (/^[A-Z][a-z]/.test(s) ? s[0].toLowerCase() + s.slice(1) : s);
        if (x.isMilestone) return [x.bar + " ", ...ask(x.ask)];
        if (x.do) return [x.do];
        if (x.kind === "design") return ["45 minutes, timed, out loud. Start a worksheet with ", h("code", {}, `python3 tools/new.py case "${short(x.t)}"`), "."];
        if (x.kind === "story") return ["Write one STAR story that answers it: ", h("code", {}, 'python3 tools/new.py story "Your title"'), "."];
        if (x.kind === "mock") return ask("mock interview, " + lower(short(x.t)));
        if (!x.isWritten) return ["Outline ready — ", ...ask("teach me " + lower(short(x.t))), " Plan on 45 minutes, and end by explaining it back."];
        const n = x.exercises.length;
        const ex = n === 1 ? "the exercise" : `the ${n} exercises`;
        return ["Read it and answer each quick check", n ? [", then do ", root ? h("a", { href: `${root}/sections/${x.s.slug}/index.html#exercises` }, ex) : ex] : null, "."];
      },
      progress(st, s = status()) {
        const req = items(st).filter((x) => !x.optional);
        return { done: req.filter((x) => T.isDone(x, s)).length, total: req.length };
      },
      // The next unfinished required step, in order: the main stages, then any pick stage already started
      next(s = status()) {
        return main.find((x) => !x.optional && !T.isDone(x, s)) || null;
      },
      // The ordered list a step belongs to: all main stages, or its own parallel/pick stage
      flow: (x) => (x.stage.pick || x.stage.parallel ? items(x.stage) : main),
      // The track step whose chapter page is relPath
      forPage: (relPath) => all.find((x) => x.pages.some((c) => pagePath(x, c) === relPath)) || null,
      // Topics left off the track: deferred until onsites are booked
      deferred: () => C.sections.map((s) => ({ s, topics: s.topics.filter((t) => !byTopic[t.id] && !stages.some((st) => st.milestone && st.milestone.format === t.id)) })).filter((g) => g.topics.length),
    };
    return T;
  }
  window.SWETrack = makeTrack(window.CURRICULUM);

  // ---- Preferences: applied right away (this script runs in <head>) so there's no flash ----
  const THEMES = [["dark", "Ayu Dark"], ["mirage", "Ayu Mirage"], ["gruvbox", "Gruvbox Dark Hard"], ["light", "Ayu Light"]];
  const THEME_IDS = THEMES.map((t) => t[0]);
  const SIZES = [15, 16, 17, 18, 19.5, 21];
  const DEFAULTS = { font: "sans", size: 2, width: "normal", code: "jetbrains" };
  const prefs = Object.assign({}, DEFAULTS, store.get("prefs", {}));
  const html = document.documentElement;
  let theme = THEME_IDS.includes(store.get("theme", "dark")) ? store.get("theme", "dark") : "dark";
  function applyPrefs() {
    prefs.size = Math.max(0, Math.min(SIZES.length - 1, prefs.size | 0));
    html.dataset.theme = theme;
    html.dataset.font = prefs.font;
    html.dataset.code = prefs.code;
    html.dataset.width = prefs.width;
    html.style.setProperty("--fs", SIZES[prefs.size] + "px");
  }
  applyPrefs();
  const savePrefs = () => { applyPrefs(); store.set("prefs", prefs); document.dispatchEvent(new Event("swe-prefs")); };
  const setTheme = (t) => { theme = t; store.set("theme", t); applyPrefs(); document.dispatchEvent(new Event("swe-theme")); };
  const cycleTheme = () => setTheme(THEME_IDS[(THEME_IDS.indexOf(theme) + 1) % THEME_IDS.length]);

  // ---- Icons (inline SVG, stroke = currentColor) ----
  const ICONS = {
    panelL: '<rect x="3" y="4" width="18" height="16" rx="2.5"/><path d="M9.5 4v16"/>',
    panelR: '<rect x="3" y="4" width="18" height="16" rx="2.5"/><path d="M14.5 4v16"/>',
    search: '<circle cx="11" cy="11" r="6.5"/><path d="m20 20-4.2-4.2"/>',
    chev: '<path d="m9 6 6 6-6 6"/>',
    home: '<path d="M3.5 10.5 12 3.5l8.5 7"/><path d="M5.5 9v11.5h13V9"/>',
    book: '<path d="M3 5h6a3 3 0 0 1 3 3v12a2.5 2.5 0 0 0-2.5-2.5H3z"/><path d="M21 5h-6a3 3 0 0 0-3 3v12a2.5 2.5 0 0 1 2.5-2.5H21z"/>',
    flask: '<path d="M9 3h6"/><path d="M10 3v6.5L4.6 18.4A1.7 1.7 0 0 0 6.1 21h11.8a1.7 1.7 0 0 0 1.5-2.6L14 9.5V3"/><path d="M7.5 15h9"/>',
    grid: '<rect x="3.5" y="3.5" width="7" height="7" rx="1.5"/><rect x="13.5" y="3.5" width="7" height="7" rx="1.5"/><rect x="3.5" y="13.5" width="7" height="7" rx="1.5"/><rect x="13.5" y="13.5" width="7" height="7" rx="1.5"/>',
    hash: '<path d="M5 9h15M4 15h15M10 3.5 8 20.5M16 3.5l-2 17"/>',
    dot: '<circle cx="12" cy="12" r="3.5"/>',
    up: '<path d="M12 19V5M5.5 11.5 12 5l6.5 6.5"/>',
    arrow: '<path d="M5 12h14M13 5.5l6.5 6.5-6.5 6.5"/>',
    keys: '<rect x="2.5" y="6" width="19" height="12" rx="2.5"/><path d="M6.5 10h.01M10 10h.01M14 10h.01M17.5 10h.01M7.5 14h9"/>',
    theme: '<circle cx="12" cy="12" r="8.5"/><path d="M12 3.5a8.5 8.5 0 0 0 0 17z" fill="currentColor"/>',
    x: '<path d="M18 6 6 18M6 6l12 12"/>',
    check: '<path d="M20 6.5 9 17.5l-5-5"/>',
    expand: '<path d="m7 15 5 5 5-5M7 9l5-5 5 5"/>',
    flag: '<path d="M5.5 21V4"/><path d="M5.5 4.5h11l-2.2 4 2.2 4h-11"/>',
    route: '<circle cx="6" cy="18.5" r="2.2"/><circle cx="18" cy="5.5" r="2.2"/><path d="M8.2 18.5H16a3.2 3.2 0 0 0 0-6.4H8a3.2 3.2 0 0 1 0-6.4h7.8"/>',
    play: '<circle cx="12" cy="13" r="7.5"/><path d="M12 9.5v3.5l2.5 1.5M9.5 3h5"/>',
  };
  const icon = (name) => { const w = document.createElement("span"); w.className = "svg-wrap"; w.innerHTML = `<svg class="i" viewBox="0 0 24 24" aria-hidden="true">${ICONS[name]}</svg>`; return w; };

  window.SWEicon = icon;
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
  const mobile = () => window.matchMedia("(max-width: 860px)").matches;
  const readMap = store.get("read", {});
  const relPath = sec && PAGE === "concept" ? `sections/${sec.slug}/concepts/${here}` : null;

  // ---- Code colors: tag Python tokens so style.css can paint them in the theme's syntax colors ----
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

  // ---- Collapsibles (asides on book pages, boxes on older pages) ----
  const collapsibles = () => [...document.querySelectorAll("details.box, details.aside")];
  const paneKey = "panes:" + location.pathname;
  const paneState = store.get(paneKey, {});
  const setAll = (open) => collapsibles().forEach((b) => (b.open = open));

  // ---- Sidebar & rail visibility ----
  const toggles = { side: [], rail: [] };
  const paintToggles = () => {
    toggles.side.forEach((b) => b.setAttribute("aria-pressed", String(!body.classList.contains("sidebar-hidden"))));
    toggles.rail.forEach((b) => b.setAttribute("aria-pressed", String(!body.classList.contains("rail-hidden"))));
  };
  const setSidebar = (hidden) => { body.classList.toggle("sidebar-hidden", hidden); if (!mobile()) store.set("sidebarHidden", hidden); paintToggles(); };
  const toggleSidebar = () => setSidebar(!body.classList.contains("sidebar-hidden"));
  const setRail = (hidden) => { body.classList.toggle("rail-hidden", hidden); store.set("railHidden", hidden); paintToggles(); };
  const toggleRail = () => setRail(!body.classList.contains("rail-hidden"));

  // ---- Headings of this book page ----
  const heads = [...document.querySelectorAll("main.book h2[id]")];
  const headParts = (hd) => ({
    num: hd.querySelector(".sec-num")?.textContent.trim() || "",
    text: [...hd.childNodes].filter((n) => !(n.classList && n.classList.contains("sec-num"))).map((n) => n.textContent).join("").trim(),
  });
  function tocList(extraClass) {
    const toc = h("div", { class: "toc" + (extraClass ? " " + extraClass : "") });
    heads.forEach((hd) => {
      const { num, text } = headParts(hd);
      toc.append(h("a", { href: "#" + hd.id, "data-target": hd.id, onclick: () => { if (mobile()) setSidebar(true); } },
        num ? h("span", { class: "n" }, num) : null, h("span", {}, text)));
    });
    return toc;
  }

  function iconButton(name, title, onclick, extra = {}) {
    const b = h("button", Object.assign({ class: "ghost", title, "aria-label": title.replace(/\s+\S+$/, ""), type: "button", onclick }, extra), icon(name));
    return b;
  }

  // ---- Top bar ----
  function buildTopbar(hasRail) {
    const crumbs = h("nav", { class: "crumbs", "aria-label": "Breadcrumb" });
    if (sec) {
      crumbs.append(h("span", { class: "sep" }, "/"));
      crumbs.append(PAGE === "concept" ? h("a", { href: chapterHref(sec) }, `§${sec.id} ${sec.title}`) : h("span", { class: "cur" }, `§${sec.id} ${sec.title}`));
      if (PAGE === "concept") crumbs.append(h("span", { class: "sep" }, "/"), h("span", { class: "cur" }, document.title));
    } else if (PAGE === "practice") {
      crumbs.append(h("span", { class: "sep" }, "/"), h("span", { class: "cur" }, "Practice hub"));
    } else if (PAGE === "cheatsheet") {
      crumbs.append(h("span", { class: "sep" }, "/"), h("span", { class: "cur" }, "Python cheatsheet"));
    }
    const sideBtn = iconButton("panelL", "Toggle sidebar  [", toggleSidebar);
    toggles.side.push(sideBtn);
    const search = h("button", { class: "search-trigger", type: "button", title: "Jump to a chapter or section  /", "aria-label": "Search", onclick: openPalette },
      icon("search"), h("span", { class: "label" }, "Jump to…"), h("kbd", {}, navigator.platform.includes("Mac") ? "⌘K" : "Ctrl K"));
    const themeBtn = iconButton("theme", "Next theme  t", cycleTheme);
    const aaBtn = h("button", { class: "ghost", type: "button", title: "Appearance: theme, font, size  a", "aria-label": "Appearance", "aria-expanded": "false", onclick: (e) => { e.stopPropagation(); togglePop(); } },
      h("span", { class: "aa" }, "Aa"));
    aaBtn.id = "aa-btn";
    let railBtn = null;
    if (hasRail) {
      railBtn = iconButton("panelR", "Toggle contents  ]", toggleRail);
      railBtn.classList.add("rail-toggle");
      toggles.rail.push(railBtn);
    }
    return h("header", { class: "topbar" },
      sideBtn,
      h("a", { class: "brand", href: `${ROOT}/index.html` }, h("span", { class: "mark", "aria-hidden": "true" }, "s/"), h("span", {}, "swe", h("span", { class: "slash" }, "/"), "prep")),
      crumbs,
      h("div", { class: "spacer" }),
      search, themeBtn, aaBtn,
      railBtn ? h("span", { class: "divider rail-toggle" }) : null, railBtn);
  }

  // ---- Sidebar: every chapter as a tree; the current one open ----
  function shortTitle(t) {
    const cut = (t.short || t.text.split(/[:;(]/)[0]).trim();
    return cut.length > 48 ? cut.slice(0, 46) + "…" : cut;
  }
  // A collapsible group in the sidebar: a row (chevron + link) and its children
  function navGroup(isOpen, isCur, extraClass, label, storeKey, id, link, kids) {
    const wrap = h("div", { class: "sec" + (isOpen ? " open" : "") + (isCur ? " current" : "") + (extraClass ? " " + extraClass : "") });
    const chev = h("button", { class: "chev", type: "button", "aria-label": `Show what is in ${label}`, "aria-expanded": String(isOpen) }, icon("chev"));
    chev.addEventListener("click", () => {
      const open = !wrap.classList.contains("open");
      wrap.classList.toggle("open", open);
      chev.setAttribute("aria-expanded", String(open));
      const set = new Set(store.get(storeKey, []));
      if (open) set.add(id); else set.delete(id);
      store.set(storeKey, [...set]);
    });
    wrap.append(h("div", { class: "sec-row" }, chev, link), kids);
    return wrap;
  }

  function buildTrackNav() {
    const T = window.SWETrack;
    const box = h("div", { class: "view", "data-view": "track" });
    const openSet = new Set(store.get("openStages", []));
    const status = store.get("status", {});
    const cur = relPath ? T.forPage(relPath) : null;
    const nextUp = T.next(status);
    const focus = cur ? cur.stage : nextUp ? nextUp.stage : null;
    let paralleled = false, picked = false;
    for (const st of T.stages) {
      if (st.parallel && !paralleled) { paralleled = true; box.append(h("div", { class: "nav-label" }, "Parallel track")); }
      if (st.pick && !picked) { picked = true; box.append(h("div", { class: "nav-label" }, "When an onsite is booked")); }
      const { done, total } = T.progress(st, status);
      const link = h("a", { href: `${ROOT}/index.html#stage-${st.id}`, title: `${st.label}: ${st.title}` },
        h("span", { class: "no" }, st.code), h("span", { class: "title" }, st.title),
        h("span", { class: "count", title: `${done} of ${total} done` }, `${done}/${total}`));
      const kids = h("div", { class: "sec-kids" });
      for (const x of T.items(st)) {
        const active = x === cur;
        const done = T.isDone(x, status);
        const tip = x.isMilestone ? x.bar : `${T.kindLabel(x)}${x.optional ? " (optional)" : ""} · ${x.t.tag} · ${x.t.text}`;
        kids.append(h("a", { class: "kid" + (x.isMilestone ? " ms" : x.isWritten ? "" : " pending") + (active ? " active" : "") + (x === nextUp ? " next-up" : ""),
          href: T.href(x, ROOT), title: tip, "aria-current": active ? "page" : null },
          x.isMilestone ? icon("flag") : h("span", { class: "dot " + x.t.tag }),
          h("span", {}, T.title(x)), x.optional ? h("span", { class: "opt" }, "opt") : null,
          done && !active ? h("span", { class: "read-mark", title: "Done" }, "✓") : null));
        if (active && heads.length) kids.append(tocList("toc-inline"));
      }
      box.append(navGroup(st === focus || openSet.has(st.id), st === focus, null, st.title, "openStages", st.id, link, kids));
    }
    const def = T.deferred().reduce((n, g) => n + g.topics.length, 0);
    box.append(h("a", { class: "nav-link deferred-link", href: `${ROOT}/index.html#deferred`, title: "P2s and later topics, for after onsites are booked" }, icon("dot"), `Deferred: ${def} topics`));
    return box;
  }

  function buildSidebar() {
    const nav = h("nav", { class: "nav", "aria-label": "Track and chapters" });
    nav.append(
      h("a", { class: "nav-link" + (PAGE === "home" ? " active" : ""), href: `${ROOT}/index.html` }, icon("home"), "Home"),
      h("a", { class: "nav-link" + (PAGE === "practice" ? " active" : ""), href: `${ROOT}/practice.html` }, icon("play"), "Practice hub"),
      h("a", { class: "nav-link" + (PAGE === "cheatsheet" ? " active" : ""), href: `${ROOT}/python-cheatsheet.html` }, icon("hash"), "Python cheatsheet"));
    const chapters = buildChapterNav();
    if (window.SWETrack) {
      const track = buildTrackNav();
      // A deferred page isn't on the track, so show it in the chapter tree (without saving that choice)
      let view = (relPath && !window.SWETrack.forPage(relPath)) || store.get("navView", "track") === "chapters" ? "chapters" : "track";
      const tabs = h("div", { class: "nav-tabs", role: "tablist", "aria-label": "Sidebar view" });
      const paint = () => {
        tabs.querySelectorAll("button").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.v === view)));
        track.hidden = view !== "track";
        chapters.hidden = view !== "chapters";
      };
      const tab = (v, label, ic) => h("button", { type: "button", role: "tab", "data-v": v, onclick: () => { view = v; store.set("navView", v); paint(); } }, icon(ic), label);
      tabs.append(tab("track", "Track", "route"), tab("chapters", "Chapters", "book"));
      nav.append(tabs, track, chapters);
      paint();
    } else nav.append(chapters);
    const foot = h("div", { class: "side-foot" },
      h("span", { title: "Asked almost everywhere" }, h("span", { class: "dot P0" }), "P0"),
      h("span", { title: "Often asked" }, h("span", { class: "dot P1" }), "P1"),
      h("span", { title: "Nice to have" }, h("span", { class: "dot P2" }), "P2"),
      h("button", { type: "button", onclick: openKeys, title: "Keyboard shortcuts  ?" }, "Shortcuts ", h("kbd", {}, "?")));
    return h("aside", { class: "sidebar", id: "sidebar" }, nav, foot);
  }

  function buildChapterNav() {
    const nav = h("div", { class: "view", "data-view": "chapters" });
    const openSet = new Set(store.get("openSecs", []));
    const T = window.SWETrack;
    for (const s of C.sections) {
      const isCur = s.id === SECTION;
      const writtenCount = s.concepts.filter((c) => c.status !== "outline").length;
      const link = h("a", { href: chapterHref(s), class: isCur && PAGE === "chapter" ? "active" : null, title: `§${s.id} ${s.title}` },
        h("span", { class: "no" }, s.id), h("span", { class: "title" }, s.title),
        writtenCount ? h("span", { class: "count", title: `${writtenCount} chapters written` }, writtenCount) : null);
      const kids = h("div", { class: "sec-kids" });
      for (const t of s.topics) {
        const pages = s.concepts.filter((c) => c.topic === t.id);
        const off = T && !T.byTopic[t.id] ? " off-track" : "";
        const offTip = off ? " · deferred (not on the track)" : "";
        if (pages.length) {
          for (const c of pages) {
            const active = isCur && PAGE === "concept" && c.file === here;
            const isOutline = c.status === "outline";
            const done = !isOutline && (readMap[`sections/${s.slug}/concepts/${c.file}`] || 0) >= 90;
            kids.append(h("a", { class: "kid" + off + (isOutline ? " pending" : "") + (active ? " active" : ""), href: conceptHref(s, c.file), title: `${t.tag} · ${isOutline ? "outline · " : ""}${t.text}${offTip}`, "aria-current": active ? "page" : null },
              h("span", { class: "dot " + t.tag }), h("span", {}, c.title), isOutline ? h("span", { class: "opt" }, "out") : null, done && !active ? h("span", { class: "read-mark", title: "Read" }, "✓") : null));
            if (active && heads.length) kids.append(tocList("toc-inline"));
          }
        } else {
          kids.append(h("a", { class: "kid pending" + off, href: chapterHref(s) + "#t-" + t.id, title: `${t.tag} · teach/worksheet${offTip}` },
            h("span", { class: "dot " + t.tag }), shortTitle(t)));
        }
      }
      nav.append(navGroup(isCur || openSet.has(s.id), isCur, writtenCount ? null : "empty-sec", s.title, "openSecs", s.id, link, kids));
    }
    return nav;
  }

  // ---- Right rail: contents + progress ----
  let meter = null, meterLabel = null;
  function buildRail() {
    meter = h("span");
    meterLabel = h("span", {}, "0% read");
    return h("aside", { class: "rail", "aria-label": "On this page" },
      h("div", { class: "rail-label" }, "On this page"),
      tocList(),
      h("div", { class: "rail-foot" },
        h("div", { class: "meter" }, meter), meterLabel,
        h("a", { href: "#", onclick: (e) => { e.preventDefault(); scrollTo({ top: 0, behavior: "smooth" }); } }, icon("up"), "Back to top"),
        document.querySelector("details.aside") ? h("a", { href: "#", onclick: (e) => { e.preventDefault(); const anyClosed = collapsibles().some((d) => !d.open); setAll(anyClosed); } }, icon("expand"), "Open / close all asides") : null));
  }

  function trackReading() {
    if (!relPath) return;
    store.set("last", { path: relPath, title: document.title, sec: sec.id });
    let saved = readMap[relPath] || 0, pending = null;
    const update = () => {
      const max = document.documentElement.scrollHeight - innerHeight;
      const pct = max > 0 ? Math.min(100, Math.round((100 * scrollY) / max)) : 100;
      if (meter) { meter.style.width = pct + "%"; meterLabel.textContent = pct + "% read"; }
      if (pct > saved) {
        saved = pct;
        clearTimeout(pending);
        pending = setTimeout(() => { const m = store.get("read", {}); m[relPath] = Math.max(m[relPath] || 0, saved); store.set("read", m); }, 400);
      }
    };
    addEventListener("scroll", update, { passive: true });
    update();
  }

  function scrollSpy() {
    if (!heads.length) return;
    let cur = null;
    const update = () => {
      const line = innerHeight * 0.25;
      let id = heads[0].id;
      for (const hd of heads) { if (hd.getBoundingClientRect().top <= line) id = hd.id; else break; }
      if (id === cur) return;
      cur = id;
      document.querySelectorAll(".toc a").forEach((a) => a.classList.toggle("active", a.dataset.target === id));
    };
    addEventListener("scroll", update, { passive: true });
    update();
  }

  // ---- Previous / next follow the track, not the chapter's section ----
  function trackPager() {
    const T = window.SWETrack;
    const navEl = document.querySelector("main nav.chapter-nav");
    if (!T || !navEl || !relPath) return;
    const x = T.forPage(relPath);
    if (!x) {
      navEl.before(h("div", { class: "track-between" }, h("b", {}, "Off the track. "),
        "This chapter is deferred until onsites are booked, so the links below follow its section. ",
        h("a", { href: `${ROOT}/index.html#deferred` }, "Back to the track")));
      return;
    }
    const flow = T.flow(x);
    const i = flow.indexOf(x);
    const isPage = (y) => !y.isMilestone && !y.optional && y.pages.length > 0; // optional pages are listed in between
    let p = i - 1; while (p >= 0 && !isPage(flow[p])) p--;
    let n = i + 1; while (n < flow.length && !isPage(flow[n])) n++;
    const prev = p >= 0 ? flow[p] : null, next = n < flow.length ? flow[n] : null;
    const between = flow.slice(i + 1, n);
    const where = (y) => (y.stage !== x.stage ? y.stage.label + " · " : "");
    const named = (y) => T.title(y) + (y.optional ? " (optional)" : "");
    navEl.replaceChildren(
      prev ? h("a", { href: T.href(prev, ROOT) }, h("small", {}, "← " + where(prev) + "Previous on the track"), named(prev))
        : h("a", { href: `${ROOT}/index.html` }, h("small", {}, "← Back to"), "Your track"),
      next ? h("a", { class: "next", href: T.href(next, ROOT) }, h("small", {}, where(next) + "Next on the track →"), named(next))
        : h("a", { class: "next", href: `${ROOT}/index.html#stage-${x.stage.id}` }, h("small", {}, "Next →"), "Back to your track"));
    if (between.length) {
      const shown = between.slice(0, 6);
      navEl.before(h("div", { class: "track-between" }, h("b", {}, "Before the next chapter: "),
        shown.map((y, k) => [k ? " · " : "", h("a", { href: T.href(y, ROOT) }, `${T.kindLabel(y)}: ${named(y)}`)]),
        between.length > shown.length ? ` and ${between.length - shown.length} more.` : ".",
        " ", h("a", { href: `${ROOT}/index.html#stage-${x.stage.id}` }, "See the track")));
    }
  }

  // ---- Appearance panel ----
  let pop = null;
  function buildPop() {
    const themeGroup = h("div", { class: "themes", role: "radiogroup", "aria-label": "Theme" });
    THEMES.forEach(([id, name]) => themeGroup.append(h("button", { class: "theme-opt", type: "button", role: "radio", "data-theme": id, "data-v": id, onclick: () => { setTheme(id); paintPop(); } },
      h("span", { class: "preview" }, h("i"), h("i"), h("i")), h("span", { class: "name" }, name))));
    const seg = (key, opts, label) => {
      const s = h("div", { class: "seg", role: "radiogroup", "aria-label": label });
      opts.forEach(([v, text, sample]) => s.append(h("button", { type: "button", role: "radio", "data-k": key, "data-v": v, onclick: () => { prefs[key] = v; savePrefs(); paintPop(); } },
        sample ? h("span", { class: "sample", style: sample }, "Ag") : null, text)));
      return s;
    };
    const ticks = h("div", { class: "ticks" });
    SIZES.forEach((px, i) => ticks.append(h("span", { title: px + "px", onclick: () => { prefs.size = i; savePrefs(); paintPop(); } })));
    const sizeVal = h("span", { class: "val" });
    const step = (d) => { prefs.size = Math.max(0, Math.min(SIZES.length - 1, prefs.size + d)); savePrefs(); paintPop(); };
    const importInput = h("input", { type: "file", accept: ".json", style: "display:none" });
    importInput.addEventListener("change", () => {
      const f = importInput.files && importInput.files[0];
      if (!f) return;
      const r = new FileReader();
      r.onload = () => {
        try {
          const obj = JSON.parse(String(r.result || "{}"));
          if (!obj || typeof obj !== "object") return;
          Object.entries(obj).forEach(([k, v]) => { if (k.startsWith("swe-prep:")) localStorage.setItem(k, typeof v === "string" ? v : JSON.stringify(v)); });
          location.reload();
        } catch (_) { alert("Could not read backup JSON."); }
      };
      r.readAsText(f);
    });
    const exportProgress = () => {
      const out = {};
      for (let i = 0; i < localStorage.length; i++) {
        const k = localStorage.key(i);
        if (k && k.startsWith("swe-prep:")) {
          try { out[k] = JSON.parse(localStorage.getItem(k)); } catch (_) { out[k] = localStorage.getItem(k); }
        }
      }
      const blob = new Blob([JSON.stringify(out, null, 2)], { type: "application/json" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `swe-lab-progress-${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      setTimeout(() => URL.revokeObjectURL(a.href), 1000);
    };
    pop = h("div", { class: "pop", id: "appearance", role: "dialog", "aria-label": "Appearance", onclick: (e) => e.stopPropagation() },
      h("h3", {}, "Appearance", h("button", { class: "ghost", type: "button", "aria-label": "Close", onclick: () => togglePop(false), style: "width:28px;height:28px" }, icon("x"))),
      h("div", { class: "group" }, h("div", { class: "glabel" }, h("span", {}, "Theme"), h("kbd", {}, "t")), themeGroup),
      h("div", { class: "group" }, h("div", { class: "glabel" }, "Reading font"),
        seg("font", [["sans", "Inter", "font-family:Inter"], ["serif", "Literata", "font-family:Literata"], ["system", "System", "font-family:-apple-system,BlinkMacSystemFont,sans-serif"]], "Reading font")),
      h("div", { class: "group" }, h("div", { class: "glabel" }, h("span", {}, "Text size"), h("span", {}, h("kbd", {}, "−"), " ", h("kbd", {}, "+"))),
        h("div", { class: "stepper" },
          h("button", { class: "btn icon", type: "button", "aria-label": "Smaller text", onclick: () => step(-1), style: "font-size:0.75rem;width:34px;justify-content:center" }, "A"),
          ticks,
          h("button", { class: "btn icon", type: "button", "aria-label": "Larger text", onclick: () => step(1), style: "font-size:1.05rem;width:34px;justify-content:center" }, "A"),
          sizeVal)),
      h("div", { class: "group" }, h("div", { class: "glabel" }, "Line width"), seg("width", [["narrow", "Narrow"], ["normal", "Normal"], ["wide", "Wide"]], "Line width")),
      h("div", { class: "group" }, h("div", { class: "glabel" }, "Code font"), seg("code", [["jetbrains", "JetBrains Mono"], ["system", "SF Mono"]], "Code font")),
      h("div", { class: "group" }, h("div", { class: "glabel" }, "Progress backup"),
        h("div", { style: "display:grid;grid-template-columns:1fr 1fr;gap:8px" },
          h("button", { class: "btn", type: "button", style: "justify-content:center", onclick: exportProgress }, "Export JSON"),
          h("button", { class: "btn", type: "button", style: "justify-content:center", onclick: () => importInput.click() }, "Import JSON")),
        importInput),
      h("div", { class: "group" }, h("button", { class: "btn reset", type: "button", onclick: () => { Object.assign(prefs, DEFAULTS); savePrefs(); setTheme("dark"); paintPop(); } }, "Reset appearance")));
    pop._paint = () => {
      pop.querySelectorAll(".theme-opt").forEach((b) => b.setAttribute("aria-checked", String(b.dataset.v === theme)));
      pop.querySelectorAll(".seg button").forEach((b) => b.setAttribute("aria-checked", String(prefs[b.dataset.k] === b.dataset.v)));
      [...ticks.children].forEach((t, i) => t.classList.toggle("on", i <= prefs.size));
      sizeVal.textContent = SIZES[prefs.size] + "px";
    };
    document.body.append(pop);
    return pop;
  }
  const paintPop = () => pop && pop._paint();
  function togglePop(force) {
    if (!pop) buildPop();
    const open = force === undefined ? !pop.classList.contains("open") : force;
    if (open) closeModals();
    paintPop();
    pop.classList.toggle("open", open);
    document.getElementById("aa-btn")?.setAttribute("aria-expanded", String(open));
  }
  document.addEventListener("click", () => { if (pop?.classList.contains("open")) togglePop(false); });
  document.addEventListener("swe-theme", paintPop);

  // ---- Jump-to palette ----
  let palette = null;
  function paletteItems() {
    const items = [];
    const pageHeads = heads.length ? heads : [...document.querySelectorAll("main.content h2[id]")];
    pageHeads.forEach((hd) => { const { num, text } = headParts(hd); items.push({ grp: "On this page", icon: "hash", title: (num ? num + ". " : "") + text, href: "#" + hd.id, where: "" }); });
    items.push(
      { grp: "Workspace", icon: "home", title: "Home · Track dashboard", href: `${ROOT}/index.html`, where: "" },
      { grp: "Workspace", icon: "play", title: "Practice hub · Bare editor, Mock log & STAR matrix", href: `${ROOT}/practice.html`, where: "" },
      { grp: "Workspace", icon: "hash", title: "Python cheatsheet · Quick lookup from basics to advanced", href: `${ROOT}/python-cheatsheet.html`, where: "" });
    for (const s of C.sections) {
      const written = s.concepts.filter((c) => c.status !== "outline");
      const outlines = s.concepts.filter((c) => c.status === "outline");
      items.push({ grp: "Subjects", icon: "grid", title: `§${s.id} ${s.title}`, href: chapterHref(s), where: written.length ? `${written.length} written` : outlines.length ? `${outlines.length} outlines` : "" });
      for (const c of written) items.push({ grp: "Chapters", icon: "book", title: c.title, href: conceptHref(s, c.file), where: `§${s.id} ${s.title}` });
      for (const c of outlines) items.push({ grp: "Outlines", icon: "dot", title: c.title, href: conceptHref(s, c.file), where: `§${s.id} outline` });
      for (const t of s.topics) if (!s.concepts.some((c) => c.topic === t.id)) items.push({ grp: "Topics", icon: "dot", title: shortTitle(t), href: chapterHref(s) + "#t-" + t.id, where: `§${s.id} · ${t.tag}`, extra: t.text });
    }
    return items;
  }
  function buildPalette() {
    const all = paletteItems();
    const input = h("input", { type: "text", placeholder: "Jump to a chapter, page or section…", "aria-label": "Search", autocomplete: "off", spellcheck: "false" });
    const results = h("div", { class: "results", role: "listbox" });
    let shown = [], sel = 0;
    const draw = () => {
      const q = input.value.trim().toLowerCase().split(/\s+/).filter(Boolean);
      shown = all.filter((it) => {
        if (!q.length) return it.grp !== "Topics" && it.grp !== "Outlines" && (heads.length ? it.grp !== "Chapters" || it.where.startsWith("§" + SECTION) : true);
        const hay = (it.title + " " + it.where + " " + (it.extra || "")).toLowerCase();
        return q.every((w) => hay.includes(w));
      }).slice(0, 80);
      sel = Math.min(sel, Math.max(0, shown.length - 1));
      results.replaceChildren();
      if (!shown.length) { results.append(h("div", { class: "none" }, "Nothing matches. Try fewer words.")); return; }
      let grp = null;
      shown.forEach((it, i) => {
        if (it.grp !== grp) { grp = it.grp; results.append(h("div", { class: "grp" }, grp)); }
        const a = h("a", { class: "res" + (i === sel ? " sel" : ""), href: it.href, role: "option", onmousemove: () => { if (sel !== i) { sel = i; paintSel(); } }, onclick: () => closeModals() },
          icon(it.icon), h("span", {}, it.title), it.where ? h("span", { class: "where" }, it.where) : null);
        results.append(a);
      });
    };
    const paintSel = () => {
      const rows = results.querySelectorAll(".res");
      rows.forEach((r, i) => r.classList.toggle("sel", i === sel));
      rows[sel]?.scrollIntoView({ block: "nearest" });
    };
    input.addEventListener("input", () => { sel = 0; draw(); });
    input.addEventListener("keydown", (e) => {
      if (e.key === "ArrowDown") { e.preventDefault(); sel = Math.min(shown.length - 1, sel + 1); paintSel(); }
      else if (e.key === "ArrowUp") { e.preventDefault(); sel = Math.max(0, sel - 1); paintSel(); }
      else if (e.key === "Enter" && shown[sel]) { e.preventDefault(); closeModals(); location.href = shown[sel].href; }
    });
    palette = h("div", { class: "modal palette", onclick: (e) => { if (e.target === palette) closeModals(); } },
      h("div", { class: "panel-box", role: "dialog", "aria-label": "Jump to" },
        h("div", { class: "q-row" }, icon("search"), input),
        results,
        h("div", { class: "hint" }, h("span", {}, h("kbd", {}, "↑"), " ", h("kbd", {}, "↓"), " move"), h("span", {}, h("kbd", {}, "↵"), " open"), h("span", {}, h("kbd", {}, "esc"), " close"))));
    palette._open = () => { input.value = ""; sel = 0; draw(); palette.classList.add("open"); input.focus(); };
    document.body.append(palette);
  }
  function openPalette() { togglePop(false); closeModals(); if (!palette) buildPalette(); palette._open(); }

  // ---- Shortcuts sheet ----
  let keysModal = null;
  function openKeys() {
    togglePop(false); closeModals();
    if (!keysModal) {
      const row = (keys, what) => [h("dt", {}, keys.map((k, i) => [i ? " " : "", h("kbd", {}, k)])), h("dd", {}, what)];
      keysModal = h("div", { class: "modal", onclick: (e) => { if (e.target === keysModal) closeModals(); } },
        h("div", { class: "panel-box keys", role: "dialog", "aria-label": "Keyboard shortcuts" },
          h("h3", {}, "Keyboard shortcuts"),
          h("dl", {},
            row(["/"], "Jump to a chapter, page or section (also ⌘K)"),
            row(["["], "Show or hide the chapters sidebar"),
            row(["]"], "Show or hide the contents rail (wide screens)"),
            row(["t"], "Next theme: Ayu Dark, Ayu Mirage, Gruvbox Dark Hard, Ayu Light"),
            row(["a"], "Appearance: theme, font, text size, line width"),
            row(["+", "−"], "Larger or smaller text"),
            row(["e", "c"], "Open or close every aside on the page"),
            row(["esc"], "Close whatever is open"),
            row(["?"], "This sheet"))));
      document.body.append(keysModal);
    }
    keysModal.classList.add("open");
  }
  function closeModals() { document.querySelectorAll(".modal.open").forEach((m) => m.classList.remove("open")); }

  // ---- Assemble ----
  function init() {
    const main = document.querySelector("main.content");
    if (!main) return;
    collapsibles().forEach((b, i) => {
      if (!b.classList.contains("box")) return;
      const id = b.id || "pane-" + (i + 1);
      if (id in paneState) b.open = paneState[id];
      b.addEventListener("toggle", () => { paneState[id] = b.open; store.set(paneKey, paneState); });
    });
    const hasRail = heads.length > 0;
    const layout = h("div", { class: "layout" });
    const page = h("div", { class: "page" + (hasRail ? " has-rail" : "") });
    main.replaceWith(layout);
    page.append(main);
    if (hasRail) page.append(buildRail());
    layout.append(buildSidebar(), page);
    body.prepend(buildTopbar(hasRail));
    body.append(h("div", { class: "scrim", onclick: () => setSidebar(true) }));
    setSidebar(mobile() ? true : store.get("sidebarHidden", false));
    if (hasRail) setRail(store.get("railHidden", false));
    const nav = document.querySelector(".sidebar .nav");
    const active = nav.querySelector(".view:not([hidden]) .kid.active, .view:not([hidden]) .sec-row a.active");
    if (active) nav.scrollTop = Math.max(0, active.offsetTop - nav.clientHeight / 3);
    trackPager();
    scrollSpy();
    trackReading();
    highlightAll();
    // On GitHub Pages, .py/.md/.json repo files aren't copied into _site/ — open them on GitHub instead of 404ing
    if (location.hostname.endsWith(".github.io")) {
      const owner = location.hostname.slice(0, -".github.io".length);
      const siteRoot = new URL(ROOT + "/", location.href).pathname;
      const repo = siteRoot.split("/").filter(Boolean)[0] || `${owner}.github.io`;
      document.querySelectorAll("a[href]").forEach((a) => {
        const raw = a.getAttribute("href");
        if (!raw || /^(?:https?:|mailto:|#)/i.test(raw)) return;
        if (!/\.(?:py|md|json|txt|sh|ya?ml|toml)(?:#.*)?$/i.test(raw)) return;
        const resolved = new URL(raw, location.href);
        if (resolved.origin !== location.origin || !resolved.pathname.startsWith(siteRoot)) return;
        const rel = resolved.pathname.slice(siteRoot.length);
        a.href = `https://github.com/${owner}/${repo}/blob/main/${rel}${resolved.hash}`;
        a.target = "_blank";
        a.rel = "noopener";
        if (!a.title) a.title = "View in GitHub repo (edit locally & run pytest)";
      });
    }
    document.addEventListener("keydown", (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { e.preventDefault(); openPalette(); return; }
      if (e.key === "Escape") { closeModals(); togglePop(false); if (mobile()) setSidebar(true); return; }
      if (e.metaKey || e.ctrlKey || e.altKey || /input|textarea|select/i.test(e.target.tagName)) return;
      const k = e.key;
      if (k === "[") toggleSidebar();
      else if (k === "]" && hasRail) toggleRail();
      else if (k === "t") cycleTheme();
      else if (k === "a") togglePop();
      else if (k === "/") { e.preventDefault(); openPalette(); }
      else if (k === "?") openKeys();
      else if (k === "+" || k === "=") { prefs.size++; savePrefs(); paintPop(); }
      else if (k === "-" || k === "_") { prefs.size--; savePrefs(); paintPop(); }
      else if (k === "e") setAll(true);
      else if (k === "c") setAll(false);
    });
    if (location.hash) document.getElementById(location.hash.slice(1))?.setAttribute("open", "");
  }
  init();
  }
})();
