/*
 * Renders the dashboard (index.html: next step, 4-lane readiness overview,
 * filterable track with inline exercises & one-click prompt copy, deferred
 * topics, all chapters) and chapter pages (sections/<NN>/index.html) from
 * window.CURRICULUM and window.SWETrack.
 */
(function () {
  const C = window.CURRICULUM;
  const h = window.SWEh;
  const icon = window.SWEicon;
  const store = window.SWEStore;
  const STATES = ["todo", "learning", "confident"];
  const status = store.get("status", {});
  const read = store.get("read", {});
  const drillDone = store.get("drills", {});
  const dayDone = store.get("days", {});
  const ROOT = document.body.dataset.root || ".";
  const badge = (tag) => h("span", { class: "badge " + tag }, tag);
  const href = (s) => `${ROOT}/sections/${s.slug}/index.html`;
  const pagePath = (s, c) => `sections/${s.slug}/concepts/${c.file}`;
  const pct = (a, b) => (b ? Math.round((100 * a) / b) : 0);
  const bar = (p) => h("div", { class: "bar" }, h("span", { style: `width:${p}%` }));

  function copyButton(label, text) {
    const btn = h("button", { class: "copy-btn", type: "button", title: text }, label);
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const finish = () => {
        const orig = btn.textContent;
        btn.textContent = "Copied";
        btn.classList.add("copied");
        setTimeout(() => { btn.textContent = orig; btn.classList.remove("copied"); }, 1400);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(finish, fallback);
      } else fallback();
      function fallback() {
        const ta = document.createElement("textarea");
        ta.value = text; ta.style.position = "fixed"; ta.style.opacity = "0";
        document.body.append(ta); ta.select();
        try { document.execCommand("copy"); } catch (_) {}
        ta.remove(); finish();
      }
    });
    return btn;
  }

  function extractPrompt(x) {
    if (x.isMilestone) return x.ask || null;
    if (x.do) {
      const m = /Ask Claude:\s*[“"]([^”"]+)[”"]/.exec(x.do);
      if (m) return m[1];
    }
    if (!x.pages.length && x.kind === "learn") {
      const title = (x.t.short || x.t.text.split(/[:;(]/)[0]).trim();
      const lower = /^[A-Z][a-z]/.test(title) ? title[0].toLowerCase() + title.slice(1) : title;
      return `teach me ${lower}`;
    }
    return null;
  }

  const testLabel = (ex) => {
    if (!ex.result) return h("span", { class: "test-none" }, "not run");
    const { passed, total } = ex.result;
    return h("span", { class: passed === total ? "test-pass" : "test-fail" }, `${passed}/${total}`);
  };
  const readLabel = (p) => (p >= 90 ? h("span", { class: "test-pass" }, "✓ read") : p > 0 ? h("span", { class: "test-none" }, `${p}% read`) : null);

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
  function drillList(t) {
    if (!t.drills || !t.drills.length) return null;
    const sum = h("summary", {});
    const paintSum = () => {
      const done = t.drills.filter(([n]) => drillDone[n]).length;
      sum.textContent = done ? `${done} / ${t.drills.length} timed drills done` : `${t.drills.length} timed drills`;
    };
    paintSum();
    const ol = h("ol", {}, t.drills.map(([name, d]) => {
      const cb = h("input", { type: "checkbox" });
      cb.checked = !!drillDone[name];
      const lbl = h("label", { class: "check-row" + (cb.checked ? " checked" : "") },
        cb, h("span", { class: "lvl " + d, title: level[d] }, d), h("span", {}, name));
      cb.addEventListener("change", () => {
        drillDone[name] = cb.checked;
        if (!cb.checked) delete drillDone[name];
        store.set("drills", drillDone);
        lbl.classList.toggle("checked", cb.checked);
        paintSum();
      });
      return h("li", {}, lbl);
    }));
    return h("details", { class: "drills" }, sum, ol);
  }

  function stepMeta(x) {
    const bits = [];
    if (x.exercises && x.exercises.length) {
      x.exercises.forEach((ex) => {
        bits.push(h("a", {
          class: "ex-chip",
          href: `${ROOT}/sections/${x.s.slug}/index.html#exercises`,
          title: ex.title,
        }, icon("flask"), h("code", {}, ex.module), ex.result ? testLabel(ex) : null));
      });
      const expr = x.exercises.length === 1
        ? x.exercises[0].module
        : x.exercises.map((e) => e.module).join(" or ");
      bits.push(copyButton("Copy pytest", `python3 -m pytest -k "${expr}"`));
    }
    const prompt = extractPrompt(x);
    if (prompt) bits.push(copyButton("Copy prompt", prompt));
    return bits.length ? h("div", { class: "step-meta" }, bits) : null;
  }

  function dayPlan(st, T) {
    const drill = {};
    C.sections.forEach((s) => s.topics.forEach((t) => (t.drills || []).forEach(([n, d]) => (drill[n] = d))));
    const link = (id) => {
      if (st.milestone && st.milestone.id === id) return h("a", { href: `#milestone-${id}` }, st.milestone.title);
      const x = T.byTopic[id];
      return x ? h("a", { href: T.href(x, ROOT) }, T.title(x)) : id;
    };
    const mins = (t) => { const m = /(?:(\d+)h)?\s*(?:(\d+)m)?/.exec(t); return (+m[1] || 0) * 60 + (+m[2] || 0); };
    const total = (d) => d.plan.reduce((a, p) => a + mins(p.t), 0) + 30 * (d.drills || []).length;
    const fmt = (m) => `${Math.floor(m / 60)}h${m % 60 ? " " + (m % 60) + "m" : ""}`;
    return h("details", { class: "days", id: "days-" + st.id },
      h("summary", {}, "Day by day", h("span", { class: "aside-note" }, " · " + st.days.length + " days, ~4 to 5 hours each")),
      st.dayNote ? h("p", { class: "day-note" }, st.dayNote) : null,
      h("ol", { class: "day-list" }, st.days.map((d, di) => {
        const keys = d.plan.map((_, pi) => `${st.id}:${di}:${pi}`);
        if (d.drills && d.drills.length) keys.push(`${st.id}:${di}:drills`);
        const hrsEl = h("span", { class: "hrs" });
        const paintDay = () => {
          const done = keys.filter((k) => dayDone[k]).length;
          hrsEl.textContent = done === keys.length ? `${done}/${keys.length} done ✓` : done ? `${done}/${keys.length} · ~${fmt(total(d))}` : `about ${fmt(total(d))}`;
          hrsEl.classList.toggle("test-pass", done === keys.length);
        };
        paintDay();
        const makeRow = (k, timeStr, content) => {
          const cb = h("input", { type: "checkbox" });
          cb.checked = !!dayDone[k];
          const li = h("li", { class: cb.checked ? "day-done" : "" },
            cb, h("span", { class: "t" }, timeStr), h("span", {}, content));
          cb.addEventListener("change", () => {
            if (cb.checked) dayDone[k] = true; else delete dayDone[k];
            store.set("days", dayDone);
            li.classList.toggle("day-done", cb.checked);
            paintDay();
          });
          return li;
        };
        const rows = d.plan.map((p, pi) => makeRow(`${st.id}:${di}:${pi}`, p.t, [link(p.topic), ": ", p.do]));
        if (d.drills && d.drills.length) {
          rows.push(makeRow(`${st.id}:${di}:drills`, fmt(30 * d.drills.length), [
            d.drills.length === 1 ? "One timed drill: " : `${d.drills.length} timed drills: `,
            d.drills.map((n, i) => [i ? " and " : "", h("span", { class: "lvl " + (drill[n] || "M"), title: level[drill[n]] || "" }, drill[n] || "M"), " " + n]),
          ]));
        }
        return h("li", { class: "day" }, h("div", { class: "day-head" }, h("b", {}, d.label), hrsEl), h("ul", {}, rows));
      })));
  }

  function laneOf(st) {
    if (st.id === "p0") return "p0";
    if (["w1", "w2", "w3", "w4"].includes(st.id)) return "coding";
    if (st.parallel) return "behavioral";
    if (st.pick) return "packs";
    return "systems";
  }

  function renderHome(root) {
    const T = window.SWETrack;
    const allPages = C.sections.flatMap((s) => s.concepts.filter((c) => c.status !== "outline").map((c) => ({ s, c, path: pagePath(s, c) })));
    const allTopics = C.sections.flatMap((s) => s.topics);
    const exercises = C.sections.reduce((n, s) => n + s.exercises.length, 0);
    const confident = allTopics.filter((t) => status[t.id] === "confident").length;
    const pagesRead = allPages.filter((p) => (read[p.path] || 0) >= 90).length;
    const mainStages = T.stages.filter((st) => !st.pick && !st.parallel);
    const weekCount = mainStages.filter((st) => /^Week \d+/.test(st.label)).length;
    const countFor = (ids) => T.stages.filter((st) => ids.includes(st.id))
      .reduce((a, st) => { const p = T.progress(st, status); return [a[0] + p.done, a[1] + p.total]; }, [0, 0]);
    const trackCount = () => mainStages.reduce((a, st) => { const p = T.progress(st, status); return [a[0] + p.done, a[1] + p.total]; }, [0, 0]);

    // Next step + headline stats
    const top = h("div", { class: "home-top" });
    const nextCard = h("div", { class: "next-wrap" });
    const drawNext = () => {
      const x = T.next(status);
      if (!x) {
        nextCard.replaceChildren(h("a", { class: "continue", href: "#stage-" + T.stages.find((st) => st.pick).id },
          h("div", {}, h("div", { class: "k" }, "Main track done"), h("div", { class: "t" }, "Open the onsite stage and your target company's pack"),
            h("div", { class: "s" }, "Keep one bare-editor coding problem a day going until the onsite.")),
          h("div", { class: "go" }, h("span", { class: "cta" }, "Open", icon("arrow")))));
        return;
      }
      const p = T.readPct(x, read);
      const hasPage = !x.isMilestone && x.isWritten;
      nextCard.replaceChildren(h("a", { class: "continue", href: T.href(x, ROOT) },
        h("div", {}, h("div", { class: "k" }, `Next up · ${x.stage.label}`),
          h("div", { class: "t" }, T.title(x)),
          h("div", { class: "s" }, T.todo(x))),
        h("div", { class: "go" }, hasPage ? [bar(p), h("span", {}, `${p}%`)] : h("span", { class: "spacer" }),
          h("span", { class: "cta" }, hasPage && p > 0 ? "Resume" : "Open", icon("arrow")))));
    };
    drawNext();
    top.append(nextCard);
    const stat = (v, total, label) => h("div", { class: "stat" }, h("div", { class: "v" }, String(v), total != null ? h("small", {}, ` / ${total}`) : null), h("div", { class: "l" }, label));
    const [td, tt] = trackCount();
    const trackStat = stat(td, tt, "track steps done");
    const confStat = stat(confident, allTopics.length, "topics confident");
    top.append(h("div", { class: "stats" },
      trackStat,
      stat(pagesRead, allPages.length, "chapters read"),
      stat(exercises, null, "exercises with tests"),
      confStat));
    root.append(top);

    // 4-lane readiness overview cards
    const LANE_CARDS = [
      { key: "p0", eyebrow: "Phase 0 · 5 days", title: "Python warm-up & setup", sub: "Foundations, idioms, stdlib, bare-editor playbook & project map", ids: ["p0"], cls: "lane-p0" },
      { key: "coding", eyebrow: "Weeks 1–4 · Screen Ready", title: "Coding & concurrency", sub: "Google bare-editor DSA, 4-level builds & threads/asyncio", ids: ["w1", "w2", "w3", "w4"], cls: "lane-coding" },
      { key: "systems", eyebrow: "Weeks 5–10 · Onsite Mastery", title: "System design & AI infra", sub: "L5 distributed systems, storage, LLM serving & scale follow-ups", ids: ["w5", "w6", "w7", "w8", "w9", "w10"], cls: "lane-systems" },
      { key: "behavioral", eyebrow: "Parallel · 1h / Sunday", title: "Behavioral & leadership", sub: "STAR bank, Google G&L hypotheticals & Anthropic Values", ids: ["behavioral"], cls: "lane-beh" },
    ];
    const lanePainters = [];
    let activeLane = store.get("laneFilter", "all");
    const laneGrid = h("div", { class: "lanes" });
    const laneBtns = {};
    LANE_CARDS.forEach((lc) => {
      const countEl = h("span", { class: "lane-count" });
      const barEl = bar(0);
      const paint = () => {
        const [d, t] = countFor(lc.ids);
        countEl.textContent = `${d} / ${t}`;
        barEl.firstChild.style.width = pct(d, t) + "%";
      };
      lanePainters.push(paint);
      paint();
      const card = h("button", { type: "button", class: "lane-card " + lc.cls, "data-lane": lc.key },
        h("div", { class: "lane-top" }, h("span", { class: "lane-eye" }, lc.eyebrow), countEl),
        h("div", { class: "lane-title" }, lc.title),
        h("div", { class: "lane-sub" }, lc.sub),
        barEl);
      card.addEventListener("click", () => {
        setLane(activeLane === lc.key ? "all" : lc.key);
        document.getElementById("track")?.scrollIntoView({ behavior: "smooth", block: "start" });
      });
      laneBtns[lc.key] = card;
      laneGrid.append(card);
    });
    root.append(laneGrid);

    root.append(h("div", { class: "callout" },
      h("b", {}, "Daily workflow: "), "follow the track in order—Phase 0 first, then pure technical weeks, plus ~1 hour every Sunday on the Parallel Behavioral track. ",
      "Use ", h("b", {}, "Copy pytest"), " and ", h("b", {}, "Copy prompt"), " right inside any step. ",
      "Press ", h("kbd", {}, "/"), " to jump anywhere, ", h("kbd", {}, "a"), " for appearance, ", h("kbd", {}, "?"), " for shortcuts."));

    // Track filter bar
    const LANE_TABS = [
      ["all", "All"],
      ["p0", "Phase 0"],
      ["coding", "Coding W1–4"],
      ["systems", "Systems & AI W5–10"],
      ["behavioral", "Behavioral"],
      ["packs", "Packs"],
    ];
    const laneFilters = h("div", { class: "filters lane-filters", role: "group", "aria-label": "Filter track by lane" });
    const list = h("div", { class: "track" });
    const stageNodes = [];
    const dividerNodes = [];

    const refresh = () => {
      drawNext();
      const [d, t] = trackCount();
      trackStat.querySelector(".v").firstChild.textContent = String(d);
      confStat.querySelector(".v").firstChild.textContent = String(allTopics.filter((x) => status[x.id] === "confident").length);
      stageHeads.forEach((f) => f());
      lanePainters.forEach((f) => f());
    };

    const stageHeads = [];
    const focus = (T.next(status) || {}).stage;
    const openSet = new Set(store.get("openStages", []));
    let paralleled = false, picked = false;

    for (const st of T.stages) {
      if (st.parallel && !paralleled) {
        paralleled = true;
        const div = h("div", { class: "track-sub", "data-lane-div": "behavioral" },
          h("h3", {}, "Parallel track (1 hour/week)"),
          h("span", { class: "aside-note" }, "Run alongside technical weeks on Sundays so stories and non-technical mocks build steadily without breaking technical flow."));
        dividerNodes.push(div);
        list.append(div);
      }
      if (st.pick && !picked) {
        picked = true;
        const div = h("div", { class: "track-sub", "data-lane-div": "packs" },
          h("h3", {}, "When an onsite is booked"),
          h("span", { class: "aside-note" }, "Start the onsite stage and your target company's pack the day it's booked, wherever you are on the track."));
        dividerNodes.push(div);
        list.append(div);
      }
      const prog = h("span", { class: "prog" });
      const pbar = bar(0);
      const paintHead = () => { const p = T.progress(st, status); prog.textContent = `${p.done} / ${p.total}`; pbar.firstChild.style.width = pct(p.done, p.total) + "%"; };
      stageHeads.push(paintHead);
      paintHead();

      const steps = h("ol", { class: "steps" });
      st.steps.forEach((x, idx) => {
        const tagPill = x.isWritten ? h("span", { class: "kind k-learn" }, "Chapter")
          : x.isOutline ? h("span", { class: "kind k-outline" }, "Outline")
          : x.kind === "design" ? h("span", { class: "kind k-design" }, "Case")
          : x.kind === "mock" ? h("span", { class: "kind k-mock" }, "Mock")
          : null;
        steps.append(h("li", { class: "step" + (x.optional ? " optional" : ""), id: "step-" + x.id },
          statusButton(x.key, refresh),
          h("div", { class: "body" },
            h("div", { class: "line" },
              h("span", { class: "step-num" }, `${idx + 1}.`),
              h("a", { class: "name", href: T.href(x, ROOT) }, T.title(x)),
              tagPill,
              x.optional ? h("span", { class: "opt" }, "optional") : null),
            h("div", { class: "todo" }, T.todo(x, ROOT)),
            stepMeta(x),
            drillList(x.t))));
      });

      const m = st.milestone;
      const lane = laneOf(st);
      const box = h("details", { class: "stage" + (st.pick ? " pick" : "") + (st.parallel ? " parallel" : ""), id: "stage-" + st.id, "data-lane": lane },
        h("summary", {},
          h("span", { class: "code" }, st.code),
          h("span", { class: "head" }, h("span", { class: "label" }, st.label), h("span", { class: "title" }, st.title), h("span", { class: "goal" }, st.goal)),
          h("span", { class: "side" }, prog, pbar)),
        steps,
        st.daily ? h("p", { class: "daily" }, h("b", {}, "Every day: "), st.daily) : null,
        st.days ? dayPlan(st, T) : null,
        m ? h("div", { class: "ms-box", id: "milestone-" + m.id }, statusButton(m.key, refresh),
          h("div", { class: "body" },
            h("div", { class: "line" }, icon("flag"), h("b", {}, m.title), m.ask ? copyButton("Copy mock prompt", m.ask) : null),
            h("div", { class: "todo" }, T.todo(m)))) : null);
      box.open = st === focus || openSet.has(st.id) || location.hash === "#stage-" + st.id;
      box.addEventListener("toggle", () => {
        const set = new Set(store.get("openStages", []));
        if (box.open) set.add(st.id); else set.delete(st.id);
        store.set("openStages", [...set]);
      });
      stageNodes.push(box);
      list.append(box);
    }

    function setLane(lane) {
      activeLane = lane;
      store.set("laneFilter", lane);
      laneFilters.replaceChildren(...LANE_TABS.map(([k, lbl]) => h("button", {
        class: "btn", type: "button", "aria-pressed": String(activeLane === k),
        onclick: () => setLane(k),
      }, lbl)));
      Object.entries(laneBtns).forEach(([k, el]) => el.classList.toggle("active", activeLane === k));
      let shownBoxes = [];
      stageNodes.forEach((el) => {
        const show = activeLane === "all" || el.dataset.lane === activeLane;
        el.hidden = !show;
        if (show) shownBoxes.push(el);
      });
      dividerNodes.forEach((d) => {
        d.hidden = activeLane !== "all" && d.dataset.laneDiv !== activeLane;
      });
      if (activeLane !== "all" && shownBoxes.length && !shownBoxes.some((b) => b.open)) {
        shownBoxes[0].open = true;
      }
    }
    setLane(activeLane);

    root.append(
      h("div", { class: "section-head" },
        h("div", {}, h("h2", { id: "track" }, "Your track"),
          h("div", { class: "aside-note", style: "margin-top:4px" }, `Phase 0 warm-up + ${weekCount} pure technical weeks (~5h/day), parallel behavioral track, and onsite packs.`)),
        laneFilters),
      list);

    // Deferred topics
    const groups = T.deferred();
    const n = groups.reduce((a, g) => a + g.topics.length, 0);
    root.append(h("details", { class: "stage deferred", id: "deferred" },
      h("summary", {}, h("span", { class: "code" }, "…"),
        h("span", { class: "head" }, h("span", { class: "label" }, "Deferred"), h("span", { class: "title" }, `${n} topics for after onsites are booked`),
          h("span", { class: "goal" }, "P2s and deeper P1s. Pull one forward only if a target company is known to ask it."))),
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
      const written = s.concepts.filter((c) => c.status !== "outline").length;
      const outlines = s.concepts.filter((c) => c.status === "outline").length;
      const pillText = written ? `${written} ${written === 1 ? "chapter" : "chapters"}`
        : outlines ? `${outlines} ${outlines === 1 ? "outline" : "outlines"}`
        : s.exercises.length ? `${s.exercises.length} exercises` : "Teach / worksheets";
      grid.append(h("a", { class: "card" + (written || outlines || s.exercises.length ? "" : " dim"), href: href(s) },
        h("div", { class: "top" }, h("span", { class: "num" }, "§" + s.id), h("span", { class: "pill" + (written ? "" : " soon") }, pillText)),
        h("h3", {}, s.title),
        h("div", { class: "meta" }, Object.entries(counts).map(([t, cnt]) => h("span", { class: "pri", title: `${cnt} ${t} topics` }, h("span", { class: "dot " + t }), `${cnt} ${t}`)),
          (written || outlines) && s.exercises.length ? h("span", {}, `${s.exercises.length} exercises`) : null),
        h("div", { class: "foot" }, h("div", { class: "row" }, h("span", {}, "Confident"), h("span", {}, `${done} / ${s.topics.length}`)), bar(pct(done, s.topics.length)))));
    }
    root.append(h("div", { class: "section-head" }, h("h2", {}, "Reference chapters"), h("span", { class: "aside-note" }, `${C.sections.length} subject areas`)), grid,
      h("p", { class: "home-foot" }, "Data generated " + C.generated + ". Run ", h("code", {}, "make build"), " after adding pages or exercises."));
  }

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
    const writtenCh = s.concepts.filter((c) => c.status !== "outline").length;
    const outlineCh = s.concepts.filter((c) => c.status === "outline").length;
    root.append(h("header", { class: "ch-head" },
      h("div", { class: "eyebrow" }, "Subject " + s.id),
      h("h1", {}, s.title),
      h("div", { class: "stats-line" },
        h("span", {}, h("b", {}, String(writtenCh)), writtenCh === 1 ? " chapter written" : " chapters written"),
        outlineCh ? h("span", {}, h("b", {}, String(outlineCh)), outlineCh === 1 ? " outline" : " outlines") : null,
        h("span", {}, h("b", {}, String(s.exercises.length)), " exercises"),
        h("span", {}, doneEl, ` / ${s.topics.length} topics confident`)),
      barEl));
    s.notes.forEach((n) => root.append(h("div", { class: "callout" }, n)));
    if (!writtenCh) root.append(h("div", { class: "callout" },
      h("b", {}, "How to study this section: "), "work through topics via interactive ", h("code", {}, "teach"), " sessions, exercises, and worksheets—outline pages are ready to expand into full chapters whenever you want."));

    const tags = [...new Set(s.topics.map((t) => t.tag))];
    let filter = store.get("filter:" + id, "all");
    const list = h("ul", { class: "topics" });
    const filters = h("div", { class: "filters", role: "group", "aria-label": "Filter by priority" });
    const recount = () => {
      const n = s.topics.filter((t) => status[t.id] === "confident").length;
      doneEl.textContent = String(n);
      barEl.firstChild.style.width = pct(n, s.topics.length) + "%";
    };
    const row = (t, idx) => {
      const st = status[t.id] || "todo";
      const btn = h("button", { class: "status", "data-s": st, type: "button", title: "Click to cycle: todo → learning → confident" }, st);
      btn.addEventListener("click", () => {
        const next = STATES[(STATES.indexOf(btn.dataset.s) + 1) % 3];
        status[t.id] = next; store.set("status", status); btn.dataset.s = next; btn.textContent = next; recount();
      });
      const pages = s.concepts.filter((c) => c.topic === t.id);
      const exs = s.exercises.filter((e) => e.topics.includes(t.id));
      const links = [
        ...pages.map((c) => h("span", {}, icon(c.status === "outline" ? "dot" : "book"), h("a", { href: "concepts/" + c.file }, c.title), c.status === "outline" ? h("span", { class: "kind k-outline" }, "Outline") : readLabel(read[pagePath(s, c)] || 0))),
        ...exs.map((e) => h("span", {}, icon("flask"), h("code", {}, e.file), testLabel(e))),
      ];
      if (!pages.some((c) => c.status !== "outline")) {
        const short = (t.short || t.text.split(/[:;(]/)[0]).trim();
        const lower = /^[A-Z][a-z]/.test(short) ? short[0].toLowerCase() + short.slice(1) : short;
        links.push(copyButton("Copy teach prompt", `teach me ${lower}`));
      }
      return h("li", { class: "topic", id: "t-" + t.id }, btn,
        h("div", { class: "head" }, h("span", { class: "id" }, `${idx + 1}.`), badge(t.tag), h("span", {}, t.short ? [h("b", {}, t.short), " — ", h("span", { class: "muted" }, t.text)] : t.text), trackChip(t)),
        h("div", { class: "links" }, links),
        t.drills ? h("div", { class: "links" }, drillList(t)) : null);
    };
    const draw = () => {
      filters.replaceChildren(...["all", ...tags].map((t) => h("button", { class: "btn", type: "button", "aria-pressed": String(filter === t),
        onclick: () => { filter = t; store.set("filter:" + id, t); draw(); } }, t === "all" ? "All" : t)));
      list.replaceChildren(...s.topics.filter((t) => filter === "all" || t.tag === filter).map((t, i) => row(t, i)));
    };
    draw();
    root.append(h("div", { class: "section-head" }, h("h2", { id: "topics" }, "Topics"), filters), list);

    if (s.exercises.length) {
      root.append(h("div", { class: "section-head" }, h("h2", { id: "exercises" }, "Exercises"), h("span", { class: "aside-note" }, `${s.exercises.length} stubs with tests`)),
        h("p", { class: "muted" }, "Stubs raise NotImplementedError until you implement them. From the repo root:"),
        h("pre", { class: "plain" }, h("code", {}, `python3 -m pytest sections/${s.slug}/exercises   # whole section\nmake one K=py_idioms                            # one exercise\nmake progress                                   # run all + update badges`)),
        h("div", { class: "table-wrap" }, h("table", {}, h("thead", {}, h("tr", {}, h("th", {}, "Module"), h("th", {}, "Exercise"), h("th", {}, "Status"), h("th", {}, "Run"))),
          h("tbody", {}, s.exercises.map((e) => h("tr", {},
            h("td", {}, h("a", { href: `exercises/${e.file}` }, h("code", {}, e.file))),
            h("td", {}, e.title),
            h("td", {}, testLabel(e)),
            h("td", {}, copyButton("Copy pytest", `python3 -m pytest -k ${e.module}`))))))));
    }
  }

  const root = document.getElementById("app");
  const sec = document.body.dataset.section;
  if (sec) renderChapter(root, sec); else renderHome(root);
  document.addEventListener("DOMContentLoaded", () => { if (location.hash) document.getElementById(location.hash.slice(1))?.scrollIntoView(); });
})();
