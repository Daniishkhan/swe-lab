/*
 * Renders the dashboard (index.html) and chapter pages (sections/<NN>/index.html)
 * from window.CURRICULUM. Per-topic status (todo / learning / confident) and
 * reading progress are stored in this browser's localStorage.
 */
(function () {
  const C = window.CURRICULUM;
  const h = window.SWEh;
  const icon = window.SWEicon;
  const store = window.SWEStore;
  const STATES = ["todo", "learning", "confident"];
  const status = store.get("status", {});
  const read = store.get("read", {});
  const ROOT = document.body.dataset.root || ".";
  const badge = (tag) => h("span", { class: "badge " + tag }, tag);
  const href = (s) => `${ROOT}/sections/${s.slug}/index.html`;
  const pagePath = (s, c) => `sections/${s.slug}/concepts/${c.file}`;
  const pct = (a, b) => (b ? Math.round((100 * a) / b) : 0);
  const bar = (p) => h("div", { class: "bar" }, h("span", { style: `width:${p}%` }));

  const testLabel = (ex) => {
    if (!ex.result) return h("span", { class: "test-none" }, "tests not run");
    const { passed, total } = ex.result;
    return h("span", { class: passed === total ? "test-pass" : "test-fail" }, `${passed}/${total} passing`);
  };
  const readLabel = (p) => (p >= 90 ? h("span", { class: "test-pass" }, "✓ read") : p > 0 ? h("span", { class: "test-none" }, `${p}% read`) : null);

  function renderHome(root) {
    const byId = Object.fromEntries(C.sections.map((s) => [s.id, s]));
    const allPages = C.sections.flatMap((s) => s.concepts.map((c) => ({ s, c, path: pagePath(s, c) }))).sort((a, b) => a.c.topic.localeCompare(b.c.topic));
    const allTopics = C.sections.flatMap((s) => s.topics);
    const exercises = C.sections.reduce((n, s) => n + s.exercises.length, 0);
    const confident = allTopics.filter((t) => status[t.id] === "confident").length;
    const pagesRead = allPages.filter((p) => (read[p.path] || 0) >= 90).length;

    // Continue where you left off (or start at the first written page)
    const last = store.get("last", null);
    let target = last && allPages.find((p) => p.path === last.path);
    const fresh = !target;
    if (fresh) target = allPages.find((p) => (read[p.path] || 0) < 90) || allPages[0];
    const top = h("div", { class: "home-top" });
    if (target) {
      const p = read[target.path] || 0;
      top.append(h("a", { class: "continue", href: `${ROOT}/${target.path}` },
        h("div", {}, h("div", { class: "k" }, fresh ? "Start here" : "Continue reading"),
          h("div", { class: "t" }, target.c.title),
          h("div", { class: "s" }, `§${target.s.id} ${target.s.title}`)),
        h("div", { class: "go" }, bar(p), h("span", {}, `${p}%`), h("span", { class: "cta" }, fresh ? "Open" : "Resume", icon("arrow")))));
    }
    const stat = (v, total, label) => h("div", { class: "stat" }, h("div", { class: "v" }, String(v), total != null ? h("small", {}, ` / ${total}`) : null), h("div", { class: "l" }, label));
    top.append(h("div", { class: "stats" },
      stat(allPages.length, null, "pages written"),
      stat(pagesRead, allPages.length, "pages read"),
      stat(exercises, null, "exercises with tests"),
      stat(confident, allTopics.length, "topics confident")));
    root.append(top);

    root.append(h("div", { class: "callout" },
      h("b", {}, "How to use it: "), "read each page top to bottom like a book, answer each quick check before reading on, then do the exercises. ",
      "Press ", h("kbd", {}, "/"), " to jump anywhere, ", h("kbd", {}, "a"), " for theme and text size, ", h("kbd", {}, "?"), " for every shortcut."));

    root.append(h("div", { class: "section-head" }, h("h2", {}, "Order of attack"), h("span", { class: "aside-note" }, "Seven phases, roughly in this order")),
      h("ol", { class: "plan" }, C.phases.map((p) => h("li", {},
        h("span", { class: "n" }, String(p.n)), h("div", { class: "t" }, p.title), h("div", { class: "g" }, p.goal),
        h("div", { class: "chips" }, p.sections.map((id) => h("a", { class: "chip", href: href(byId[id]), title: byId[id].title }, "§" + id + " " + byId[id].title.split(/[,:]| and /)[0])))))));

    const grid = h("div", { class: "grid" });
    for (const s of C.sections) {
      const done = s.topics.filter((t) => status[t.id] === "confident").length;
      const counts = {};
      s.topics.forEach((t) => (counts[t.tag] = (counts[t.tag] || 0) + 1));
      const written = s.concepts.length;
      grid.append(h("a", { class: "card" + (written ? "" : " dim"), href: href(s) },
        h("div", { class: "top" }, h("span", { class: "num" }, "§" + s.id), h("span", { class: "pill" + (written ? "" : " soon") }, written ? `${written} ${written === 1 ? "page" : "pages"}` : "Not started")),
        h("h3", {}, s.title),
        h("div", { class: "meta" }, Object.entries(counts).map(([t, n]) => h("span", { class: "pri", title: `${n} ${t} topics` }, h("span", { class: "dot " + t }), `${n} ${t}`)),
          s.exercises.length ? h("span", {}, `${s.exercises.length} exercises`) : null),
        h("div", { class: "foot" }, h("div", { class: "row" }, h("span", {}, "Confident"), h("span", {}, `${done} / ${s.topics.length}`)), bar(pct(done, s.topics.length)))));
    }
    root.append(h("div", { class: "section-head" }, h("h2", {}, "Chapters"), h("span", { class: "aside-note" }, `${C.sections.length} parts`)), grid,
      h("p", { class: "home-foot" }, "Data generated " + C.generated + ". Run ", h("code", {}, "make build"), " after adding pages."));
  }

  function renderChapter(root, id) {
    const s = C.sections.find((x) => x.id === id);
    document.title = `§${s.id} ${s.title}`;
    const done = s.topics.filter((t) => status[t.id] === "confident").length;
    const doneEl = h("b", {}, String(done));
    const barEl = bar(pct(done, s.topics.length));
    root.append(h("header", { class: "ch-head" },
      h("div", { class: "eyebrow" }, "Chapter " + s.id),
      h("h1", {}, s.title),
      h("div", { class: "stats-line" },
        h("span", {}, h("b", {}, String(s.concepts.length)), " pages written"),
        h("span", {}, h("b", {}, String(s.exercises.length)), " exercises"),
        h("span", {}, doneEl, ` / ${s.topics.length} topics confident`)),
      barEl));
    s.notes.forEach((n) => root.append(h("div", { class: "callout" }, n)));
    if (!s.concepts.length) root.append(h("div", { class: "callout warn" },
      "No pages written yet. Scaffold one with ", h("code", {}, `python3 tools/new.py concept ${s.topics[0].id} <slug> "Title"`)));

    const tags = [...new Set(s.topics.map((t) => t.tag))];
    let filter = store.get("filter:" + id, "all");
    const list = h("ul", { class: "topics" });
    const filters = h("div", { class: "filters", role: "group", "aria-label": "Filter by priority" });
    const recount = () => {
      const n = s.topics.filter((t) => status[t.id] === "confident").length;
      doneEl.textContent = String(n);
      barEl.firstChild.style.width = pct(n, s.topics.length) + "%";
    };
    const row = (t) => {
      const st = status[t.id] || "todo";
      const btn = h("button", { class: "status", "data-s": st, type: "button", title: "Click to cycle: todo → learning → confident" }, st);
      btn.addEventListener("click", () => {
        const next = STATES[(STATES.indexOf(btn.dataset.s) + 1) % 3];
        status[t.id] = next; store.set("status", status); btn.dataset.s = next; btn.textContent = next; recount();
      });
      const links = [
        ...s.concepts.filter((c) => c.topic === t.id).map((c) => h("span", {}, icon("book"), h("a", { href: "concepts/" + c.file }, c.title), readLabel(read[pagePath(s, c)] || 0))),
        ...s.exercises.filter((e) => e.topics.includes(t.id)).map((e) => h("span", {}, icon("flask"), h("code", {}, e.file), testLabel(e))),
      ];
      return h("li", { class: "topic", id: "t-" + t.id }, btn,
        h("div", { class: "head" }, h("span", { class: "id" }, t.id), badge(t.tag), h("span", {}, t.text)),
        h("div", { class: "links" }, links.length ? links : h("span", { class: "empty" }, "not written yet")));
    };
    const draw = () => {
      filters.replaceChildren(...["all", ...tags].map((t) => h("button", { class: "btn", type: "button", "aria-pressed": String(filter === t),
        onclick: () => { filter = t; store.set("filter:" + id, t); draw(); } }, t === "all" ? "All" : t)));
      list.replaceChildren(...s.topics.filter((t) => filter === "all" || t.tag === filter).map(row));
    };
    draw();
    root.append(h("div", { class: "section-head" }, h("h2", { id: "topics" }, "Topics"), filters), list);

    if (s.exercises.length) {
      root.append(h("div", { class: "section-head" }, h("h2", { id: "exercises" }, "Exercises"), h("span", { class: "aside-note" }, `${s.exercises.length} stubs with tests`)),
        h("p", { class: "muted" }, "Stubs raise NotImplementedError until you implement them. From the repo root:"),
        h("pre", { class: "plain" }, h("code", {}, `pytest sections/${s.slug}/exercises        # whole chapter\npytest -k lru_cache                          # one exercise\nmake progress                                # run all + update this page`)),
        h("div", { class: "table-wrap" }, h("table", {}, h("thead", {}, h("tr", {}, h("th", {}, "File"), h("th", {}, "Exercise"), h("th", {}, "Topic"), h("th", {}, "Status"))),
          h("tbody", {}, s.exercises.map((e) => h("tr", {}, h("td", {}, h("code", {}, e.file)), h("td", {}, e.title), h("td", {}, e.topics.join(", ")), h("td", {}, testLabel(e))))))));
    }
  }

  const root = document.getElementById("app");
  const sec = document.body.dataset.section;
  if (sec) renderChapter(root, sec); else renderHome(root);
  // The topic rows are built after shell.js; honour a #t-NN.MM link now that they exist.
  document.addEventListener("DOMContentLoaded", () => { if (location.hash) document.getElementById(location.hash.slice(1))?.scrollIntoView(); });
})();
