/*
 * Book chapter behavior (pages with <main class="content book">).
 *
 *  - Reading progress bar under the top bar.
 *  - Quick checks (.check): click an option. Right answers show the .fb.right
 *    note; wrong answers show .fb.wrong, a simpler re-explanation, and let you
 *    try again. Your FIRST answer to each check is remembered.
 *  - #review at the end of the chapter: your score, plus links back to the
 *    sections where you missed a check, so you re-read only what didn't stick.
 *
 * Markup for a check:
 *   <div class="check" id="check-growth">
 *     <p class="q">Question?</p>
 *     <div class="opts"><button data-correct>Right</button><button>Wrong</button></div>
 *     <div class="fb right">Why it's right.</div>
 *     <div class="fb wrong">Another way to think about it.</div>
 *   </div>
 */
(function () {
  const store = window.SWEStore;
  const key = "book:" + location.pathname.split("/").slice(-3).join("/");
  const results = store.get(key, {});

  function sectionOf(el) {
    let n = el;
    while (n && n.previousElementSibling !== undefined) {
      let p = n.previousElementSibling;
      while (p) { if (p.tagName === "H2") return p; p = p.previousElementSibling; }
      n = n.parentElement;
      if (!n || n.tagName === "MAIN") break;
    }
    return null;
  }

  function wire(check) {
    const label = document.createElement("div");
    label.className = "check-label"; label.textContent = "Quick check";
    check.prepend(label);
    const right = check.querySelector(".fb.right"), wrong = check.querySelector(".fb.wrong");
    check.querySelectorAll(".opts button").forEach((b) => b.addEventListener("click", () => {
      const ok = b.hasAttribute("data-correct");
      if (!(check.id in results)) { results[check.id] = ok; store.set(key, results); renderReview(); }
      b.classList.add(ok ? "picked-right" : "picked-wrong");
      if (ok) { right?.classList.add("show"); wrong?.classList.remove("show"); check.classList.add("done-right"); }
      else { wrong?.classList.add("show"); }
    }));
  }

  function renderReview() {
    const host = document.getElementById("review");
    if (!host) return;
    const checks = [...document.querySelectorAll(".check")];
    const answered = checks.filter((c) => c.id in results);
    const missed = answered.filter((c) => !results[c.id]);
    const h = window.SWEh;
    host.replaceChildren();
    host.append(h("h4", {}, "Your quick checks"));
    if (!answered.length) { host.append(h("p", { class: "muted" }, "You haven't answered any quick checks yet. They're scattered through the chapter; your first answer to each one is counted here.")); return; }
    host.append(h("p", {}, `First-try score: ${answered.length - missed.length} / ${answered.length} answered (${checks.length} in the chapter).`));
    if (missed.length) {
      const secs = [...new Set(missed.map((c) => sectionOf(c)).filter(Boolean))];
      host.append(h("p", {}, "Worth re-reading before the exercises:"),
        h("ul", {}, secs.map((s) => h("li", {}, h("a", { href: "#" + s.id }, s.textContent)))));
    } else if (answered.length === checks.length) {
      host.append(h("p", {}, "Every check right on the first try. Go straight to the stretch exercises."));
    }
    host.append(h("button", { class: "btn", onclick: () => { for (const k in results) delete results[k]; store.set(key, results); location.reload(); } }, "Reset my answers"));
  }

  function progressBar() {
    const bar = document.createElement("div");
    bar.className = "reading-bar";
    document.body.append(bar);
    const update = () => {
      const max = document.documentElement.scrollHeight - innerHeight;
      bar.style.width = (max > 0 ? (100 * scrollY) / max : 0) + "%";
    };
    addEventListener("scroll", update, { passive: true }); update();
  }

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".check").forEach(wire);
    // Restore earlier answers as a light hint (doesn't reveal which option was right).
    renderReview();
    progressBar();
  });
})();
