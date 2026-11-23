#!/usr/bin/env node
/*
 * Load chapter pages in a headless browser and report what a reader would hit.
 *
 *   node tools/check_page.js sections/02-algorithms/concepts/sorting.html [more.html] [--shots DIR]
 *
 * For each page, at desktop (1280x900) and phone (390x844) width:
 *   - console errors and uncaught exceptions
 *   - requests to anything but file:// (pages must work offline)
 *   - sideways scroll, and the widest elements causing it
 *   - every V.player stepped to its last frame, then re-checked
 * Book pages also get a markup lint: each .check has a check-* id, one
 * data-correct option and both feedback blocks; each .figure has a .cap;
 * every h2 has an id; no duplicate ids. At desktop width, code blocks too wide
 * for their box are reported too, including those in asides and feedback,
 * because the hidden end of a line is easy to miss.
 * --shots DIR saves full-page screenshots: desktop in all four themes, phone in dark.
 *
 * Needs Playwright (pre-installed in Claude's cloud sessions; locally: npm i -g playwright).
 * Exits 1 if anything was found.
 */
const path = require("path");
const fs = require("fs");
let chromium;
try { ({ chromium } = require("playwright")); } catch (e) {
  console.error("Playwright not found. Install it with: npm i -g playwright && npx playwright install chromium");
  process.exit(2);
}

const args = process.argv.slice(2);
const shotsAt = args.indexOf("--shots");
const shots = shotsAt >= 0 ? args.splice(shotsAt, 2)[1] : null;
if (!args.length) { console.error("usage: node tools/check_page.js PAGE.html [...] [--shots DIR]"); process.exit(2); }
if (shots) fs.mkdirSync(shots, { recursive: true });

const SIZES = [{ name: "desktop", width: 1280, height: 900 }, { name: "phone", width: 390, height: 844 }];
const THEMES = ["dark", "mirage", "gruvbox", "light"];

const overflow = () => {
  const over = document.documentElement.scrollWidth - innerWidth;
  if (over <= 0) return null;
  const wide = [...document.querySelectorAll("main *")]
    .filter((el) => el.getBoundingClientRect().right > innerWidth + 1)
    .filter((el) => !el.closest(".table-wrap, pre"))
    .slice(0, 5)
    .map((el) => el.tagName.toLowerCase() + (el.id ? "#" + el.id : "") + (el.className && typeof el.className === "string" ? "." + el.className.trim().split(/\s+/).join(".") : ""));
  return `scrolls sideways by ${over}px` + (wide.length ? `; widest: ${wide.join(", ")}` : "");
};

const stepPlayers = () => {
  let n = 0;
  for (const c of document.querySelectorAll(".viz-controls")) {
    const next = c.querySelector('button[title="Next"]');
    for (let k = 0; next && k < 1000; k++) {
      const m = (c.querySelector("span")?.textContent || "").match(/(\d+) \/ (\d+)/);
      if (!m || m[1] === m[2]) break;
      next.click();
    }
    n++;
  }
  return n;
};

const lint = () => {
  const out = [];
  if (!document.querySelector("main.book")) return out;
  const ids = {};
  document.querySelectorAll("[id]").forEach((el) => { ids[el.id] = (ids[el.id] || 0) + 1; });
  Object.entries(ids).filter(([, n]) => n > 1).forEach(([id]) => out.push(`duplicate id "${id}"`));
  document.querySelectorAll("main h2:not([id])").forEach((h) => out.push(`h2 without id: "${h.textContent.trim()}"`));
  document.querySelectorAll(".check").forEach((c, i) => {
    const name = c.id || `check #${i + 1}`;
    if (!c.id.startsWith("check-")) out.push(`${name}: id should start with "check-"`);
    const right = c.querySelectorAll(".opts [data-correct]").length;
    if (right !== 1) out.push(`${name}: ${right} options marked data-correct (want 1)`);
    if (!c.querySelector(".fb.right") || !c.querySelector(".fb.wrong")) out.push(`${name}: needs both .fb.right and .fb.wrong`);
  });
  document.querySelectorAll(".figure").forEach((f, i) => { if (!f.querySelector(".cap")) out.push(`figure #${i + 1} has no .cap`); });
  return out;
};

// Code blocks whose lines are cut off at this width. Opens asides and shows quick-check feedback first.
const clipped = () => {
  const shut = [...document.querySelectorAll("main details:not([open])")];
  shut.forEach((d) => (d.open = true));
  const css = document.createElement("style");
  css.textContent = "main .check .fb { display: block !important; }";
  document.head.append(css);
  const out = [...document.querySelectorAll("main pre")]
    .filter((p) => p.scrollWidth > p.clientWidth + 1)
    .map((p) => {
      const longest = p.textContent.split("\n").reduce((a, b) => (b.length > a.length ? b : a), "").trim();
      return `code block cut off by ${p.scrollWidth - p.clientWidth}px: "${longest.slice(0, 50)}${longest.length > 50 ? "…" : ""}"`;
    });
  css.remove();
  shut.forEach((d) => (d.open = false));
  return out;
};

(async () => {
  const browser = await chromium.launch();
  let bad = 0;
  for (const page of args) {
    const file = path.resolve(page);
    const problems = new Set();
    for (const size of SIZES) {
      const ctx = await browser.newContext({ viewport: { width: size.width, height: size.height } });
      const tab = await ctx.newPage();
      tab.on("console", (m) => { if (m.type() === "error") problems.add(`console error: ${m.text()}`); });
      tab.on("pageerror", (e) => problems.add(`uncaught: ${e.message}`));
      tab.on("request", (r) => { if (!r.url().startsWith("file:") && !r.url().startsWith("data:")) problems.add(`external request: ${r.url()}`); });
      await tab.goto("file://" + file, { waitUntil: "load" });
      const o1 = await tab.evaluate(overflow);
      if (o1) problems.add(`${size.name}: ${o1}`);
      if (size.name === "desktop") (await tab.evaluate(lint)).forEach((p) => problems.add(p));
      if (size.name === "desktop") (await tab.evaluate(clipped)).forEach((p) => problems.add(p));
      const players = await tab.evaluate(stepPlayers);
      const o2 = await tab.evaluate(overflow);
      if (o2 && o2 !== o1) problems.add(`${size.name}, players at last frame: ${o2}`);
      if (shots) {
        const base = path.join(shots, path.basename(file, ".html"));
        for (const theme of size.name === "desktop" ? THEMES : ["dark"]) {
          for (let k = 0; k < THEMES.length && (await tab.evaluate(() => document.documentElement.dataset.theme)) !== theme; k++) {
            await tab.keyboard.press("t");
          }
          await tab.screenshot({ path: `${base}-${size.name}-${theme}.png`, fullPage: true });
        }
      }
      if (size.name === "desktop") console.log(`${page}: ${players} player(s) stepped through`);
      await ctx.close();
    }
    if (problems.size) { bad++; problems.forEach((p) => console.log(`  ✗ ${p}`)); } else console.log("  ✓ clean");
  }
  await browser.close();
  if (shots) console.log(`screenshots in ${shots}`);
  process.exit(bad ? 1 : 0);
})();
