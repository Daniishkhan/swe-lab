/*
 * Renders the dashboard (index.html: the next step, the track, deferred topics,
 * all chapters) and chapter pages (sections/<NN>/index.html) from window.CURRICULUM
 * and window.SWETrack. Per-topic status (todo / learning / confident) and
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

  // One status button per topic or milestone; same todo / learning / confident cycle everywhere
  function statusButton(key, onchange) {
    const st = status[key] || "todo";
    const btn = h("button", { class: "status", "data-s": st, type: "button", title: "Click to cycle: todo → learning → confident (done)" }, st);
    btn.addEventListener("click", () => {
      const next = STATES[(STATES.indexOf(btn.dataset.s) + 1) % 3];
      status[key] = next; store.set("status", status); btn.dataset.s = next; btn.textContent = next;
      if (onchange) onchange();
    });
    return btn;
  }
  const level = { E: "Easy", M: "Medium", H: "Hard" };
  const drillList = (t) => t.drills && t.drills.length ? h("details", { class: "drills" },
    h("summary", {}, `${t.drills.length} timed drills`),
    h("ol", {}, t.drills.map(([name, d]) => h("li", {}, h("span", { class: "lvl " + d, title: level[d] }, d), name)))) : null;

  function renderHome(root) {
    const T = window.SWETrack;
    const allPages = C.sections.flatMap((s) => s.concepts.map((c) => ({ s, c, path: pagePath(s, c) })));
    const allTopics = C.sections.flatMap((s) => s.topics);
    const exercises = C.sections.reduce((n, s) => n + s.exercises.length, 0);
    const confident = allTopics.filter((t) => status[t.id] === "confident").length;
    const pagesRead = allPages.filter((p) => (read[p.path] || 0) >= 90).length;
    const mainStages = T.stages.filter((st) => !st.pick);
    const trackCount = () => mainStages.reduce((a, st) => { const p = T.progress(st, status); return [a[0] + p.done, a[1] + p.total]; }, [0, 0]);

    // The next unfinished step on the track
    const top = h("div", { class: "home-top" });
    const nextCard = h("div", { class: "next-wrap" });
    const drawNext = () => {
      const x = T.next(status);
      if (!x) {
        nextCard.replaceChildren(h("a", { class: "continue", href: "#stage-" + T.stages.find((st) => st.pick).id },
          h("div", {}, h("div", { class: "k" }, "Main track done"), h("div", { class: "t" }, "When an onsite is booked, open the onsite stage and that company's pack"),
            h("div", { class: "s" }, "Until then, keep one timed problem a day going.")),
          h("div", { class: "go" }, h("span", { class: "cta" }, "Open", icon("arrow")))));
        return;
      }
      const pct = T.readPct(x, read);
      const hasPage = !x.isMilestone && x.pages.length > 0;
      nextCard.replaceChildren(h("a", { class: "continue", href: T.href(x, ROOT) },
        h("div", {}, h("div", { class: "k" }, `Next on your track · ${x.stage.label} · ${T.kindLabel(x)}`),
          h("div", { class: "t" }, T.title(x)),
          h("div", { class: "s" }, T.todo(x))),
        h("div", { class: "go" }, hasPage ? [bar(pct), h("span", {}, `${pct}%`)] : h("span", { class: "spacer" }),
          h("span", { class: "cta" }, hasPage && pct > 0 ? "Resume" : "Open", icon("arrow")))));
    };
    drawNext();
    top.append(nextCard);
    const stat = (v, total, label) => h("div", { class: "stat" }, h("div", { class: "v" }, String(v), total != null ? h("small", {}, ` / ${total}`) : null), h("div", { class: "l" }, label));
    const [td, tt] = trackCount();
    const trackStat = stat(td, tt, "track steps done");
    top.append(h("div", { class: "stats" },
      trackStat,
      stat(pagesRead, allPages.length, "pages read"),
      stat(exercises, null, "exercises with tests"),
      stat(confident, allTopics.length, "topics confident")));
    root.append(top);

    root.append(h("div", { class: "callout" },
      h("b", {}, "How to use it: "), "follow the track one step at a time. Read each page top to bottom, answer each quick check before reading on, then do the exercises and a few timed drills. ",
      "Mark a step ", h("i", {}, "confident"), " when you can explain it back without the page. ",
      "Press ", h("kbd", {}, "/"), " to jump anywhere, ", h("kbd", {}, "a"), " for theme and text size, ", h("kbd", {}, "?"), " for every shortcut."));

    // The track, stage by stage
    const refresh = () => {
      drawNext();
      const [d, t] = trackCount();
      trackStat.querySelector(".v").firstChild.textContent = String(d);
      stageHeads.forEach((f) => f());
    };
    const stageHeads = [];
    const focus = (T.next(status) || {}).stage;
    const openSet = new Set(store.get("openStages", []));
    const list = h("div", { class: "track" });
    let picked = false;
    for (const st of T.stages) {
      if (st.pick && !picked) {
        picked = true;
        list.append(h("div", { class: "track-sub" }, h("h3", {}, "When an onsite is booked"), h("span", { class: "aside-note" }, "Start the onsite stage and that company's pack the day it's booked, wherever you are on the track.")));
      }
      const prog = h("span", { class: "prog" });
      const pbar = bar(0);
      const paintHead = () => { const p = T.progress(st, status); prog.textContent = `${p.done} / ${p.total}`; pbar.firstChild.style.width = pct(p.done, p.total) + "%"; };
      stageHeads.push(paintHead);
      paintHead();
      const steps = h("ol", { class: "steps" });
      for (const x of st.steps) {
        const pages = x.pages.map((c) => h("a", { href: `${ROOT}/${T.pagePath(x, c)}` }, c.title));
        steps.append(h("li", { class: "step" + (x.optional ? " optional" : ""), id: "step-" + x.id },
          statusButton(x.key, refresh),
          h("div", { class: "body" },
            h("div", { class: "line" }, h("span", { class: "kind k-" + x.kind }, T.kindLabel(x)),
              h("a", { class: "name", href: T.href(x, ROOT) }, T.title(x)),
              x.optional ? h("span", { class: "opt" }, "optional") : null,
              badge(x.t.tag), h("span", { class: "id" }, x.id)),
            h("div", { class: "todo" }, T.todo(x, ROOT)),
            drillList(x.t))));
      }
      const m = st.milestone;
      const box = h("details", { class: "stage" + (st.pick ? " pick" : ""), id: "stage-" + st.id },
        h("summary", {},
          h("span", { class: "code" }, st.code),
          h("span", { class: "head" }, h("span", { class: "label" }, st.label), h("span", { class: "title" }, st.title), h("span", { class: "goal" }, st.goal)),
          h("span", { class: "side" }, prog, pbar)),
        steps,
        st.daily ? h("p", { class: "daily" }, h("b", {}, "Every day: "), st.daily) : null,
        m ? h("div", { class: "ms-box", id: "milestone-" + m.id }, statusButton(m.key, refresh),
          h("div", { class: "body" }, h("div", { class: "line" }, icon("flag"), h("b", {}, m.title)), h("div", { class: "todo" }, T.todo(m)))) : null);
      box.open = st === focus || openSet.has(st.id) || location.hash === "#stage-" + st.id;
      box.addEventListener("toggle", () => {
        const set = new Set(store.get("openStages", []));
        if (box.open) set.add(st.id); else set.delete(st.id);
        store.set("openStages", [...set]);
      });
      list.append(box);
    }
    root.append(h("div", { class: "section-head" }, h("h2", { id: "track" }, "Your track"),
      h("span", { class: "aside-note" }, "Seven weeks, plus onsite prep once an onsite is booked. Each step builds only on the steps before it.")), list);

    // Everything left off the track
    const groups = T.deferred();
    const n = groups.reduce((a, g) => a + g.topics.length, 0);
    root.append(h("details", { class: "stage deferred", id: "deferred" },
      h("summary", {}, h("span", { class: "code" }, "…"),
        h("span", { class: "head" }, h("span", { class: "label" }, "Deferred"), h("span", { class: "title" }, `${n} topics for after onsites are booked`),
          h("span", { class: "goal" }, "P2s and the deeper P1s. Pull one forward only if a company you are interviewing with is known to ask it."))),
      h("div", { class: "def-groups" }, groups.map((g) => h("div", { class: "def-group" },
        h("a", { class: "def-sec", href: href(g.s) }, `§${g.s.id} ${g.s.title}`),
        h("ul", {}, g.topics.map((t) => {
          const page = g.s.concepts.find((c) => c.topic === t.id);
          return h("li", {}, h("span", { class: "dot " + t.tag }), h("a", { href: page ? `${ROOT}/${pagePath(g.s, page)}` : href(g.s) + "#t-" + t.id }, page ? page.title : (t.short || t.text.split(/[:;(]/)[0])));
        })))))));

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
    root.append(h("div", { class: "section-head" }, h("h2", {}, "All chapters"), h("span", { class: "aside-note" }, `${C.sections.length} parts, as reference`)), grid,
      h("p", { class: "home-foot" }, "Data generated " + C.generated + ". Run ", h("code", {}, "make build"), " after adding pages."));
  }

  // Where a topic sits on the track: its stage, a mock it is the format of, or deferred
  function trackChip(t) {
    const T = window.SWETrack;
    const x = T.byTopic[t.id];
    const go = (label, to, cls) => h("a", { class: "wk" + (cls ? " " + cls : ""), href: to, title: "Where this sits on the track" }, label);
    if (x) return go(x.stage.label + (x.optional ? " · optional" : ""), `${ROOT}/index.html#stage-${x.stage.id}`);
    const ms = T.stages.filter((st) => st.milestone && st.milestone.format === t.id);
    if (ms.length) return go("Mock in " + ms.map((st) => st.label).join(", "), `${ROOT}/index.html#stage-${ms[0].id}`);
    return go("Deferred", `${ROOT}/index.html#deferred`, "off");
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
        h("div", { class: "head" }, h("span", { class: "id" }, t.id), badge(t.tag), h("span", {}, t.text), trackChip(t)),
        h("div", { class: "links" }, links.length ? links : h("span", { class: "empty" }, "not written yet")),
        t.drills ? h("div", { class: "links" }, drillList(t)) : null);
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
