/*
 * Renders the dashboard (index.html) and chapter pages (sections/<NN>/index.html)
 * from window.CURRICULUM. Per-topic status (todo / learning / confident) is
 * stored in this browser's localStorage.
 */
(function () {
  const C = window.CURRICULUM;
  const h = window.SWEh || ((t) => document.createElement(t));
  const store = window.SWEStore;
  const STATES = ["todo", "learning", "confident"];
  const status = store.get("status", {});
  const ROOT = document.body.dataset.root || ".";
  const badge = (tag) => h("span", { class: "badge " + tag }, tag);
  const href = (s) => `${ROOT}/sections/${s.slug}/index.html`;

  const testLabel = (ex) => {
    if (!ex.result) return h("span", { class: "test-none" }, "tests not run");
    const { passed, total } = ex.result;
    return h("span", { class: passed === total ? "test-pass" : "test-fail" }, `${passed}/${total} passing`);
  };

  function renderHome(root) {
    const byId = Object.fromEntries(C.sections.map((s) => [s.id, s]));
    root.append(h("h2", {}, "Order of attack"), h("div", { class: "phases" },
      C.phases.map((p) => h("div", { class: "phase" },
        h("div", { class: "n" }, "PHASE " + p.n), h("div", { class: "t" }, p.title), h("div", { class: "g" }, p.goal),
        h("div", { class: "links" }, p.sections.map((id, i) => [i ? " · " : "", h("a", { href: href(byId[id]) }, "§" + id)]))))));

    const grid = h("div", { class: "grid" });
    for (const s of C.sections) {
      const done = s.topics.filter((t) => status[t.id] === "confident").length;
      const counts = {};
      s.topics.forEach((t) => (counts[t.tag] = (counts[t.tag] || 0) + 1));
      grid.append(h("a", { class: "card" + (s.concepts.length ? " focus" : ""), href: href(s) },
        h("div", { class: "num" }, "§" + s.id + (s.concepts.length ? "  ·  in progress" : "")),
        h("h3", {}, s.title),
        h("div", { class: "meta" }, Object.entries(counts).map(([t, n]) => [badge(t), n + " "])),
        h("div", { class: "meta" }, `${s.concepts.length} concept pages · ${s.exercises.length} exercises · ${done}/${s.topics.length} confident`),
        h("div", { class: "bar" }, h("span", { style: `width:${s.topics.length ? (100 * done) / s.topics.length : 0}%` }))));
    }
    root.append(h("h2", {}, "Chapters"), grid,
      h("p", { class: "muted small", style: "margin-top:30px" }, "Data generated " + C.generated + ". Run ", h("code", {}, "make build"), " after adding pages."));
  }

  function renderChapter(root, id) {
    const s = C.sections.find((x) => x.id === id);
    document.title = `§${s.id} ${s.title}`;
    root.append(h("p", { class: "muted small" }, "Chapter " + s.id), h("h1", {}, s.title));
    s.notes.forEach((n) => root.append(h("div", { class: "callout" }, n)));
    if (!s.concepts.length) root.append(h("div", { class: "callout warn" },
      "No concept pages yet. Scaffold one with ", h("code", {}, `python tools/new.py concept ${s.topics[0].id} <slug> "Title"`)));

    const tags = [...new Set(s.topics.map((t) => t.tag))];
    let filter = store.get("filter:" + id, "all");
    const list = h("ul", { class: "topics" });
    const filters = h("div", { class: "filters" });
    const row = (t) => {
      const st = status[t.id] || "todo";
      const btn = h("button", { class: "status", "data-s": st, title: "Click to cycle: todo → learning → confident" }, st);
      btn.addEventListener("click", () => {
        const next = STATES[(STATES.indexOf(btn.dataset.s) + 1) % 3];
        status[t.id] = next; store.set("status", status); btn.dataset.s = next; btn.textContent = next;
      });
      const links = [
        ...s.concepts.filter((c) => c.topic === t.id).map((c) => h("a", { href: "concepts/" + c.file }, "📖 " + c.title)),
        ...s.exercises.filter((e) => e.topics.includes(t.id)).map((e) => h("span", {}, "🧪 ", h("code", {}, e.file), " ", testLabel(e))),
      ];
      return h("li", { class: "topic", id: "t-" + t.id }, btn, h("span", { class: "id" }, t.id),
        h("div", {}, badge(t.tag), " ", t.text),
        h("div", { class: "links" }, links.length ? links : h("span", { class: "empty" }, "not written yet")));
    };
    const draw = () => {
      filters.replaceChildren(...["all", ...tags].map((t) => h("button", { class: "btn", "aria-pressed": String(filter === t),
        onclick: () => { filter = t; store.set("filter:" + id, t); draw(); } }, t)));
      list.replaceChildren(...s.topics.filter((t) => filter === "all" || t.tag === filter).map(row));
    };
    draw();
    root.append(box("topics", "Map", "Topics", [filters, list]));

    if (s.exercises.length) {
      root.append(box("exercises", "Do", "Exercises", [
        h("p", { class: "muted" }, "Stubs raise NotImplementedError until you implement them. From the repo root:"),
        h("pre", {}, h("code", {}, `pytest sections/${s.slug}/exercises        # whole chapter\npytest -k lru_cache                          # one exercise\nmake progress                                # run all + update this page`)),
        h("div", { class: "table-wrap" }, h("table", {}, h("thead", {}, h("tr", {}, h("th", {}, "File"), h("th", {}, "Exercise"), h("th", {}, "Topic"), h("th", {}, "Status"))),
          h("tbody", {}, s.exercises.map((e) => h("tr", {}, h("td", {}, h("code", {}, e.file)), h("td", {}, e.title), h("td", {}, e.topics.join(", ")), h("td", {}, testLabel(e)))))))]));
    }
  }

  function box(id, kicker, label, kids) {
    return h("details", { class: "box", open: "", id }, h("summary", {}, h("span", { class: "kicker" }, kicker), h("span", { class: "label" }, label)),
      h("div", { class: "box-body" }, kids));
  }

  const root = document.getElementById("app");
  const sec = document.body.dataset.section;
  if (sec) renderChapter(root, sec); else renderHome(root);
})();
