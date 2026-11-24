/*
 * Interactive offline Practice Hub (practice.html):
 *   1. Bare-editor scratchpad (line numbers, 4-space Tab, zero autocomplete) + multi-mode phase timer
 *   2. Timed Mock & Drill Log (1-4 senior scores, averages, Markdown export)
 *   3. STAR Story Bank Matrix (9 senior dimensions + live gap detector + Markdown export)
 */
(function () {
  const h = window.SWEh;
  const store = window.SWEStore;
  const root = document.getElementById("practice-app");
  if (!root) return;

  function copyText(text, btn) {
    const done = () => {
      const orig = btn.textContent;
      btn.textContent = "Copied";
      btn.classList.add("copied");
      setTimeout(() => { btn.textContent = orig; btn.classList.remove("copied"); }, 1400);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, fallback);
    } else fallback();
    function fallback() {
      const ta = document.createElement("textarea");
      ta.value = text; ta.style.position = "fixed"; ta.style.opacity = "0";
      document.body.append(ta); ta.select();
      try { document.execCommand("copy"); } catch (_) {}
      ta.remove(); done();
    }
  }

  let activeTab = store.get("practiceTab", "editor");
  const tabsBar = h("div", { class: "hub-tabs", role: "tablist", "aria-label": "Practice hub views" });
  const panes = {};

  // =========================================================================
  // Tab 1: Bare-Editor Scratchpad + Multi-Mode Phase Timer
  // =========================================================================
  const MODES = {
    drill25: { label: "25m Drill", total: 25 * 60, fmt: "Google Coding", phases: [[3, "Clarify constraints & examples"], [9, "Brute force → Optimal + sign-off"], [19, "Clean code (no execution)"], [24, "Literal trace table & edges"], [25, "Log this run"]] },
    google45: { label: "45m Google Coding", total: 45 * 60, fmt: "Google Coding", phases: [[5, "Clarify bounds & 3 examples"], [15, "Brute force → Optimal + sign-off"], [32, "Clean code (no run)"], [40, "Literal trace table & edges"], [45, "Wrap & escalating follow-ups"]] },
    design45: { label: "45m System Design", total: 45 * 60, fmt: "System Design", phases: [[5, "Requirements & scope cuts"], [10, "Back-of-envelope math"], [18, "API & data model"], [26, "High-level architecture"], [38, "Black-box deep dive"], [45, "Failures, SLOs & rollout"]] },
    conc60: { label: "60m Concurrency", total: 60 * 60, fmt: "Concurrency", phases: [[6, "Clarify thread-safety & limits"], [16, "Locking / async architecture"], [42, "Implementation + no lock during I/O"], [52, "Race-catching tests"], [60, "Deadlock & starvation proof"]] },
    levels90: { label: "90m 4-Level Build", total: 90 * 60, fmt: "Practical 4-Level", phases: [[15, "Level 1 + modular skeleton + tests"], [35, "Level 2 without rewriting L1"], [65, "Level 3 (TTL / scan / quota)"], [90, "Level 4 (transactions / rollback)"]] },
  };
  let curMode = "google45", left = MODES[curMode].total, timer = null;
  const phaseEl = h("div", { class: "small muted", style: "text-transform:uppercase;letter-spacing:.08em;font-weight:700" });
  const clockEl = h("div", { class: "timer-clock" });
  const startBtn = h("button", { class: "btn primary", type: "button" }, "Start");
  const resetBtn = h("button", { class: "btn", type: "button" }, "Reset");
  const modeBtns = {};

  function paintTimer() {
    const m = Math.floor(left / 60), s = left % 60;
    clockEl.textContent = `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
    clockEl.classList.toggle("warn", left <= 300);
    const elapsed = (MODES[curMode].total - left) / 60;
    const p = MODES[curMode].phases.find(([end]) => elapsed < end) || MODES[curMode].phases[MODES[curMode].phases.length - 1];
    phaseEl.textContent = left === 0 ? "Time's up — log your self-score honestly" : (timer ? "Now · " : "Ready · ") + p[1];
  }
  function stopTimer() { if (timer) { clearInterval(timer); timer = null; startBtn.textContent = "Start"; } }
  startBtn.addEventListener("click", () => {
    if (timer) { stopTimer(); paintTimer(); return; }
    if (left === 0) left = MODES[curMode].total;
    startBtn.textContent = "Pause";
    timer = setInterval(() => { left = Math.max(0, left - 1); paintTimer(); if (left === 0) stopTimer(); }, 1000);
    paintTimer();
  });
  resetBtn.addEventListener("click", () => { stopTimer(); left = MODES[curMode].total; paintTimer(); });
  const presetWrap = h("div", { style: "display:flex;flex-wrap:wrap;gap:6px" }, Object.entries(MODES).map(([k, cfg]) => {
    const b = h("button", { class: "btn", type: "button", "aria-pressed": String(k === curMode) }, cfg.label);
    b.addEventListener("click", () => {
      stopTimer(); curMode = k; left = cfg.total;
      Object.entries(modeBtns).forEach(([mk, el]) => el.setAttribute("aria-pressed", String(mk === k)));
      paintTimer();
    });
    modeBtns[k] = b;
    return b;
  }));
  paintTimer();

  const gutter = h("div", { class: "bare-gutter", "aria-hidden": "true" }, "1");
  const editor = h("textarea", {
    class: "bare-editor",
    spellcheck: "false",
    autocomplete: "off",
    autocorrect: "off",
    autocapitalize: "off",
    placeholder: "# Google bare-editor scratchpad (no autocomplete, no syntax linting)\n# 1. Clarify constraints & example\n# 2. Brute force + complexity -> Optimal + complexity\n# 3. Code cleanly\n# 4. Dry-run variable table on normal + empty + boundary\n",
  });
  editor.value = store.get("scratch", "");
  const statsEl = h("span", {});
  const syncGutter = () => {
    const lines = Math.max(18, editor.value.split("\n").length);
    gutter.textContent = Array.from({ length: lines }, (_, i) => i + 1).join("\n");
    gutter.scrollTop = editor.scrollTop;
    const actualLines = editor.value ? editor.value.split("\n").length : 0;
    statsEl.textContent = `${actualLines} lines · ${editor.value.length} chars (auto-saved locally)`;
  };
  editor.addEventListener("input", () => { store.set("scratch", editor.value); syncGutter(); });
  editor.addEventListener("scroll", () => { gutter.scrollTop = editor.scrollTop; });
  editor.addEventListener("keydown", (e) => {
    if (e.key !== "Tab") return;
    e.preventDefault();
    const s = editor.selectionStart, end = editor.selectionEnd, v = editor.value;
    if (!e.shiftKey) {
      editor.value = v.slice(0, s) + "    " + v.slice(end);
      editor.selectionStart = editor.selectionEnd = s + 4;
    } else if (s === end && v.slice(Math.max(0, s - 4), s) === "    ") {
      editor.value = v.slice(0, s - 4) + v.slice(end);
      editor.selectionStart = editor.selectionEnd = s - 4;
    }
    store.set("scratch", editor.value); syncGutter();
  });
  syncGutter();

  const CHECKS = [
    "Clarified input bounds, types, duplicates, empty case, and confirmed a concrete example",
    "Stated brute force + exact time/space complexity before optimizing",
    "Got buy-in on optimal approach and complexity before writing code",
    "Dry-ran line-by-line with a variable table on normal, empty, and boundary cases",
    "Prepared a crisp answer for 100x scale, streaming/bounded RAM, or concurrency follow-up",
  ];
  const checkState = store.get("bareChecks", {});
  const checklist = h("details", { class: "aside", open: true },
    h("summary", {}, "Pre-finish dry-run checklist"),
    h("div", { style: "display:grid;gap:6px;padding:4px 0 12px" }, CHECKS.map((txt, i) => {
      const cb = h("input", { type: "checkbox" });
      cb.checked = !!checkState[i];
      const lbl = h("label", { class: "check-row" + (cb.checked ? " checked" : "") }, cb, h("span", {}, txt));
      cb.addEventListener("change", () => {
        if (cb.checked) checkState[i] = true; else delete checkState[i];
        store.set("bareChecks", checkState);
        lbl.classList.toggle("checked", cb.checked);
      });
      return lbl;
    })));

  const copyCodeBtn = h("button", { class: "btn", type: "button" }, "Copy code");
  copyCodeBtn.addEventListener("click", () => copyText(editor.value, copyCodeBtn));
  const clearBtn = h("button", { class: "btn", type: "button" }, "Clear pad & checks");
  clearBtn.addEventListener("click", () => {
    if (editor.value && !confirm("Clear the scratchpad and reset the dry-run checklist?")) return;
    editor.value = ""; store.set("scratch", ""); syncGutter();
    Object.keys(checkState).forEach((k) => delete checkState[k]);
    store.set("bareChecks", checkState);
    checklist.querySelectorAll("input[type=checkbox]").forEach((c) => { c.checked = false; c.parentElement.classList.remove("checked"); });
  });
  const logRunBtn = h("button", { class: "btn primary", type: "button" }, "Log this run →");
  logRunBtn.addEventListener("click", () => {
    const minsUsed = Math.max(1, Math.round((MODES[curMode].total - left) / 60));
    logFmt.value = MODES[curMode].fmt;
    logTime.value = `${minsUsed}m`;
    setTab("log");
    logPrompt.focus();
  });

  const editorRefs = h("p", { class: "small muted", style: "margin:10px 0 0" },
    "Phase 0 references: ",
    h("a", { href: "python-cheatsheet.html" }, "Python cheatsheet"),
    " · ",
    h("a", { href: "sections/15-interview-formats/concepts/algorithmic-round.html#s8" }, "Bare-editor playbook"),
    " · ",
    h("a", { href: "sections/10-code-quality-design-testing/concepts/python-control-flow.html#summary" }, "Control flow"),
    " · ",
    h("a", { href: "sections/10-code-quality-design-testing/concepts/python-data-structures.html#summary" }, "Built-in structures"),
    " · ",
    h("a", { href: "sections/10-code-quality-design-testing/concepts/python-memory-model.html#summary" }, "Memory model"),
    " · ",
    h("a", { href: "sections/10-code-quality-design-testing/concepts/python-idioms.html#summary" }, "Streams & idioms"),
    " · ",
    h("a", { href: "sections/10-code-quality-design-testing/concepts/python-building-blocks.html#summary" }, "Decorators & @dataclass"),
    " · ",
    h("a", { href: "sections/10-code-quality-design-testing/concepts/python-toolkit.html#s7" }, "Stdlib toolkit"));

  panes.editor = h("section", {},
    h("div", { class: "timer-bar" },
      h("div", {}, phaseEl, clockEl),
      h("div", { style: "display:flex;flex-wrap:wrap;gap:8px;align-items:center" }, startBtn, resetBtn),
      presetWrap),
    h("div", { class: "bare-wrap" }, gutter, editor),
    h("div", { class: "bare-foot" }, statsEl, h("div", { style: "display:flex;gap:8px;flex-wrap:wrap" }, copyCodeBtn, clearBtn, logRunBtn)),
    checklist,
    editorRefs);

  // =========================================================================
  // Tab 2: Mock & Drill Log
  // =========================================================================
  let logs = store.get("mockLogs", []);
  const FORMATS = ["Google Coding", "Practical 4-Level", "Concurrency", "System Design", "AI-Infra Design", "Behavioral / G&L", "Past-Project Deep Dive", "Hiring Manager", "Full Loop"];
  const logDate = h("input", { type: "date", value: new Date().toISOString().slice(0, 10) });
  const logFmt = h("select", {}, FORMATS.map((f) => h("option", { value: f }, f)));
  const logPrompt = h("input", { type: "text", placeholder: "e.g. Concurrent web crawler w/ per-host cap" });
  const logTime = h("input", { type: "text", value: "45m", placeholder: "45m" });
  const logSelf = h("select", {}, ["1", "2", "3", "4"].map((v) => h("option", { value: v, selected: v === "3" ? "" : null }, v)));
  const logMock = h("select", {}, ["", "1", "2", "3", "4"].map((v) => h("option", { value: v }, v || "—")));
  const logWell = h("input", { type: "text", placeholder: "Clean scoping, caught edge case in dry-run" });
  const logFix = h("input", { type: "text", placeholder: "Spent too long before coding; drill Dijkstra" });
  const logTableHost = h("div", {});
  const logStats = h("div", { class: "cov-strip" });

  function renderLogs() {
    logStats.replaceChildren();
    const scored = logs.filter((r) => Number(r.self));
    const avgSelf = scored.length ? (scored.reduce((a, r) => a + Number(r.self), 0) / scored.length).toFixed(1) : "—";
    const mScored = logs.filter((r) => Number(r.mock));
    const avgMock = mScored.length ? (mScored.reduce((a, r) => a + Number(r.mock), 0) / mScored.length).toFixed(1) : "—";
    logStats.append(
      h("span", { class: "cov-pill ok" }, `${logs.length} runs logged`),
      h("span", { class: "cov-pill" }, `Avg self: ${avgSelf} / 4`),
      h("span", { class: "cov-pill" }, `Avg mock: ${avgMock} / 4`));

    if (!logs.length) {
      logTableHost.replaceChildren(h("div", { class: "callout" }, "No mocks or timed drills logged yet. Complete a run and log it above—your scores track readiness across all formats."));
      return;
    }
    logTableHost.replaceChildren(h("div", { class: "table-wrap" }, h("table", {},
      h("thead", {}, h("tr", {}, ["Date", "Format", "Prompt", "Time", "Self / Mock", "What went well", "What to fix", ""].map((t) => h("th", {}, t)))),
      h("tbody", {}, logs.map((r, idx) => h("tr", {},
        h("td", {}, r.date),
        h("td", {}, h("span", { class: "badge" }, r.fmt)),
        h("td", {}, h("b", {}, r.prompt)),
        h("td", {}, r.time),
        h("td", {}, `${r.self} / ${r.mock || "—"}`),
        h("td", {}, r.well),
        h("td", {}, r.fix),
        h("td", {}, h("button", { class: "copy-btn", type: "button", onclick: () => { logs.splice(idx, 1); store.set("mockLogs", logs); renderLogs(); } }, "Delete"))))))));
  }

  const addLogBtn = h("button", { class: "btn primary", type: "button" }, "Add entry");
  addLogBtn.addEventListener("click", () => {
    if (!logPrompt.value.trim()) { logPrompt.focus(); return; }
    logs.unshift({
      date: logDate.value || new Date().toISOString().slice(0, 10),
      fmt: logFmt.value,
      prompt: logPrompt.value.trim(),
      time: logTime.value.trim() || "45m",
      self: logSelf.value,
      mock: logMock.value,
      well: logWell.value.trim(),
      fix: logFix.value.trim(),
    });
    store.set("mockLogs", logs);
    logPrompt.value = ""; logWell.value = ""; logFix.value = "";
    renderLogs();
  });

  const exportLogBtn = h("button", { class: "btn", type: "button" }, "Copy Markdown for mock-log.md");
  exportLogBtn.addEventListener("click", () => {
    const header = "| Date | Format | Prompt | Time | Score: self / mock (1-4) | What went well | What to fix |\n|---|---|---|---|---|---|---|";
    const rows = logs.map((r) => `| ${r.date} | ${r.fmt} | ${r.prompt} | ${r.time} | ${r.self} / ${r.mock || "-"} | ${r.well} | ${r.fix} |`);
    copyText([header, ...rows].join("\n"), exportLogBtn);
  });

  panes.log = h("section", {},
    h("div", { class: "hub-form" },
      h("label", {}, "Date", logDate),
      h("label", {}, "Format", logFmt),
      h("label", {}, "Time", logTime),
      h("label", {}, "Self score (1–4)", logSelf),
      h("label", {}, "Mock score (1–4)", logMock),
      h("label", { class: "span-all" }, "Prompt / problem", logPrompt),
      h("label", {}, "What went well", logWell),
      h("label", {}, "Weakest moment / next drill", logFix),
      h("div", { class: "span-all", style: "display:flex;gap:8px;flex-wrap:wrap" }, addLogBtn, exportLogBtn)),
    logStats,
    logTableHost);
  renderLogs();

  // =========================================================================
  // Tab 3: STAR Story Bank Matrix (Parallel Behavioral Track)
  // =========================================================================
  const DIMS = ["Ownership", "Conflict", "Failure", "Influence", "Mentoring", "Prioritization", "Deep dive", "Ambiguity", "Humility / Safety"];
  let stories = store.get("starStories", []);
  const stTitle = h("input", { type: "text", placeholder: "e.g. Zero-downtime payments shard migration" });
  const stHook = h("input", { type: "text", placeholder: "10-sec hook + headline metric (e.g. cut p99 65%)" });
  const stNotes = h("textarea", { rows: 3, placeholder: "S / T / A (say 'I') / R (numbers) / Reflection (what you'd change)" });
  const dimBoxes = {};
  const dimWrap = h("div", { class: "star-tags" }, DIMS.map((d) => {
    const cb = h("input", { type: "checkbox" });
    dimBoxes[d] = cb;
    return h("label", {}, cb, d);
  }));
  const covHost = h("div", { class: "cov-strip" });
  const storyHost = h("div", {});

  function renderStories() {
    covHost.replaceChildren(...DIMS.map((d) => {
      const cnt = stories.filter((s) => (s.dims || []).includes(d)).length;
      return h("span", { class: "cov-pill " + (cnt ? "ok" : "miss") }, `${d}: ${cnt}`);
    }));
    if (!stories.length) {
      storyHost.replaceChildren(h("div", { class: "callout" }, "Goal: 8 to 10 STAR stories covering every pill above (amber = gap to fill on Sunday's Parallel Behavioral hour)."));
      return;
    }
    storyHost.replaceChildren(h("div", { class: "table-wrap" }, h("table", {},
      h("thead", {}, h("tr", {}, ["Story", ...DIMS, ""].map((t) => h("th", {}, t)))),
      h("tbody", {}, stories.map((st, idx) => h("tr", {},
        h("td", {}, h("b", {}, st.title), st.hook ? h("div", { class: "small muted" }, st.hook) : null, st.notes ? h("details", { class: "drills" }, h("summary", {}, "STAR notes"), h("p", { class: "small", style: "white-space:pre-wrap;margin-top:6px" }, st.notes)) : null),
        ...DIMS.map((d) => h("td", { style: "text-align:center" }, (st.dims || []).includes(d) ? h("span", { class: "test-pass" }, "✓") : h("span", { class: "muted" }, "·"))),
        h("td", {}, h("button", { class: "copy-btn", type: "button", onclick: () => { stories.splice(idx, 1); store.set("starStories", stories); renderStories(); } }, "Delete"))))))));
  }

  const addStoryBtn = h("button", { class: "btn primary", type: "button" }, "Save STAR story");
  addStoryBtn.addEventListener("click", () => {
    if (!stTitle.value.trim()) { stTitle.focus(); return; }
    const dims = DIMS.filter((d) => dimBoxes[d].checked);
    stories.push({ title: stTitle.value.trim(), hook: stHook.value.trim(), notes: stNotes.value.trim(), dims });
    store.set("starStories", stories);
    stTitle.value = ""; stHook.value = ""; stNotes.value = "";
    DIMS.forEach((d) => (dimBoxes[d].checked = false));
    renderStories();
  });

  const exportStoryBtn = h("button", { class: "btn", type: "button" }, "Copy Markdown for story-bank.md");
  exportStoryBtn.addEventListener("click", () => {
    const header = "| Story | " + DIMS.join(" | ") + " |\n|" + Array(DIMS.length + 1).fill("---").join("|") + "|";
    const rows = stories.map((s) => `| ${s.title} | ` + DIMS.map((d) => ((s.dims || []).includes(d) ? "✓" : "")).join(" | ") + " |");
    copyText([header, ...rows].join("\n"), exportStoryBtn);
  });

  const storyRefs = h("p", { class: "small muted", style: "margin:10px 0 0" },
    "Phase 0 reference: ",
    h("a", { href: "sections/14-behavioral-leadership/concepts/project-deep-dive.html" }, "Flagship project deep dive & 60-sec intro (14.01)"));

  panes.stories = h("section", {},
    h("div", { class: "hub-form" },
      h("label", {}, "Story title", stTitle),
      h("label", {}, "One-line hook + metric", stHook),
      h("label", { class: "span-all" }, "STAR notes (Situation · Task · Action ('I') · Result · Reflection)", stNotes),
      h("div", { class: "span-all" }, h("div", { class: "small muted" }, "Maps to Google G&L / Anthropic dimensions:"), dimWrap),
      h("div", { class: "span-all", style: "display:flex;gap:8px;flex-wrap:wrap" }, addStoryBtn, exportStoryBtn)),
    covHost,
    storyHost,
    storyRefs);
  renderStories();

  // =========================================================================
  // Tab Switching
  // =========================================================================
  const TABS = [
    ["editor", "Bare-editor & timer"],
    ["log", "Mock & drill log"],
    ["stories", "STAR story matrix"],
  ];
  function setTab(k) {
    activeTab = k;
    store.set("practiceTab", k);
    tabsBar.replaceChildren(...TABS.map(([id, lbl]) => h("button", {
      type: "button", role: "tab", "aria-selected": String(activeTab === id),
      onclick: () => setTab(id),
    }, lbl)));
    Object.entries(panes).forEach(([id, el]) => { el.hidden = id !== activeTab; });
  }
  root.append(tabsBar, panes.editor, panes.log, panes.stories);
  setTab(activeTab);
})();
