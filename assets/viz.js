/*
 * Tiny visualization toolkit for concept pages. No dependencies.
 *
 *   V.el(tag, attrs, ...children)      build an HTML element
 *   V.s(tag, attrs, ...children)       build an SVG element
 *   V.cells(values, opts)              a row of array cells (indexes, pointers, highlights)
 *   V.player(box, { frames, draw })    step-through player with prev / play / next / speed
 *   V.binaryTree(svg, root, opts)      lay out and draw a binary tree {val, left, right}
 *   V.graph(svg, nodes, edges, opts)   draw a node-link graph with fixed coordinates
 *
 * A "frame" is any object your draw(frame) function understands. If a frame has a
 * `msg` string, the player shows it as the caption (HTML allowed).
 */
(function () {
  const SVGNS = "http://www.w3.org/2000/svg";
  const assign = (n, attrs) => {
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v == null || v === false) continue;
      if (k === "class") n.setAttribute("class", v);
      else if (k === "text") n.textContent = v;
      else if (k === "html") n.innerHTML = v;
      else if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
      else n.setAttribute(k, v);
    }
    return n;
  };
  const add = (n, kids) => { for (const k of kids.flat(Infinity)) if (k != null && k !== false) n.append(k.nodeType ? k : document.createTextNode(String(k))); return n; };
  const el = (tag, attrs, ...kids) => add(assign(document.createElement(tag), attrs), kids);
  const s = (tag, attrs, ...kids) => add(assign(document.createElementNS(SVGNS, tag), attrs), kids);

  /** Row of cells. opts: cls(i, v) -> class, ptrs: {index: "label"}, idx: show indexes (default true). */
  function cells(values, opts = {}) {
    const { cls = () => "", ptrs = {}, idx = true, label = (v) => v } = opts;
    const hasPtr = Object.keys(ptrs).length > 0;
    return el("div", { class: "cells" + (hasPtr ? " with-ptrs" : "") },
      values.map((v, i) => el("div", { class: "cell " + (cls(i, v) || "") + (v === null || v === undefined ? " empty" : "") },
        ptrs[i] != null ? el("span", { class: "ptr" }, ptrs[i]) : null,
        v === null || v === undefined ? "·" : label(v, i),
        idx ? el("span", { class: "idx" }, i) : null)));
  }

  /**
   * Player. Renders into `box` (an element): a stage, a caption and controls.
   * frames: array, draw(frame, stage, index). Returns { load(frames), go(i) }.
   */
  function player(box, { frames = [], draw, speed = 700, extraControls = [] } = {}) {
    const stage = el("div", { class: "viz-stage" });
    const caption = el("div", { class: "viz-caption", "aria-live": "polite" });
    const counter = el("span", { class: "muted small" });
    let i = 0, timer = null, ms = speed;
    const go = (k) => {
      if (!frames.length) { stage.replaceChildren(); counter.textContent = ""; caption.textContent = ""; return; }
      i = Math.max(0, Math.min(frames.length - 1, k));
      stage.replaceChildren();
      draw(frames[i], stage, i);
      caption.innerHTML = frames[i].msg || "";
      counter.textContent = `${i + 1} / ${frames.length}`;
    };
    const stop = () => { clearInterval(timer); timer = null; playBtn.textContent = "▶ Play"; };
    const playBtn = el("button", { class: "btn primary", onclick: () => {
      if (timer) return stop();
      if (i >= frames.length - 1) go(0);
      playBtn.textContent = "❚❚ Pause";
      timer = setInterval(() => (i >= frames.length - 1 ? stop() : go(i + 1)), ms);
    } }, "▶ Play");
    const speedInput = el("input", { type: "range", min: 100, max: 1500, step: 100, value: 1600 - ms, title: "Speed",
      oninput: (e) => { ms = 1600 - Number(e.target.value); if (timer) { stop(); playBtn.click(); } } });
    const controls = el("div", { class: "viz-controls" },
      el("button", { class: "btn", title: "First", onclick: () => { stop(); go(0); } }, "⏮"),
      el("button", { class: "btn", title: "Previous", onclick: () => { stop(); go(i - 1); } }, "◀"),
      playBtn,
      el("button", { class: "btn", title: "Next", onclick: () => { stop(); go(i + 1); } }, "▶|"),
      counter, el("span", { class: "muted small" }, "speed"), speedInput, ...extraControls);
    box.append(stage, caption, controls);
    const api = { load(f) { stop(); frames = f; go(0); }, go, get index() { return i; } };
    go(0);
    return api;
  }

  /** Lay out a binary tree with in-order x positions. Returns list of {node, x, y, parent}. */
  function layoutTree(root) {
    const out = [];
    let x = 0;
    (function walk(n, depth, parent) {
      if (!n) return;
      walk(n.left, depth + 1, n);
      out.push({ node: n, x: x++, y: depth, parent });
      walk(n.right, depth + 1, n);
    })(root, 0, null);
    return out;
  }

  /** Draw a binary tree into an <svg class="viz">. opts.cls(node) -> class string. */
  function binaryTree(svg, root, opts = {}) {
    const { cls = () => "", dx = 46, dy = 58, r = 17, label = (n) => n.val } = opts;
    const items = layoutTree(root);
    svg.replaceChildren();
    if (!items.length) { svg.setAttribute("viewBox", "0 0 200 60"); svg.append(s("text", { x: 100, y: 30, class: "label", "text-anchor": "middle", text: "(empty)" })); return; }
    const pos = new Map(items.map((it) => [it.node, { x: 30 + it.x * dx, y: 30 + it.y * dy }]));
    const w = 60 + (items.length - 1) * dx, hgt = 60 + Math.max(...items.map((i) => i.y)) * dy;
    svg.setAttribute("viewBox", `0 0 ${Math.max(w, 200)} ${hgt}`);
    svg.style.maxWidth = Math.max(w, 200) * 1.15 + "px";
    for (const it of items) if (it.parent) {
      const a = pos.get(it.parent), b = pos.get(it.node);
      svg.append(s("line", { class: "edge " + (opts.edgeCls ? opts.edgeCls(it.parent, it.node) : ""), x1: a.x, y1: a.y, x2: b.x, y2: b.y }));
    }
    for (const it of items) {
      const p = pos.get(it.node);
      svg.append(s("g", { class: "node " + cls(it.node) }, s("circle", { cx: p.x, cy: p.y, r }), s("text", { x: p.x, y: p.y, text: label(it.node) })));
    }
  }

  /**
   * Draw a graph. nodes: [{id, x, y}], edges: [[a, b, w?]].
   * opts: directed, nodeCls(id), edgeCls(a, b), width, height.
   */
  function graph(svg, nodes, edges, opts = {}) {
    const { directed = false, nodeCls = () => "", edgeCls = () => "", width = 360, height = 220, r = 17 } = opts;
    svg.replaceChildren();
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    svg.style.maxWidth = width * 1.3 + "px";
    const id = "arrow" + Math.random().toString(36).slice(2, 7);
    svg.append(s("defs", {}, s("marker", { id, viewBox: "0 0 10 10", refX: 9, refY: 5, markerWidth: 7, markerHeight: 7, orient: "auto-start-reverse" },
      s("path", { d: "M0,0 L10,5 L0,10 z", fill: "currentColor" }))));
    const at = Object.fromEntries(nodes.map((n) => [n.id, n]));
    for (const [a, b, w] of edges) {
      const A = at[a], B = at[b];
      const dx = B.x - A.x, dy = B.y - A.y, len = Math.hypot(dx, dy) || 1;
      const x1 = A.x + (dx / len) * r, y1 = A.y + (dy / len) * r, x2 = B.x - (dx / len) * (r + (directed ? 3 : 0)), y2 = B.y - (dy / len) * (r + (directed ? 3 : 0));
      const c = edgeCls(a, b);
      svg.append(s("line", { class: "edge " + c, x1, y1, x2, y2, "marker-end": directed ? `url(#${id})` : null, style: "color: var(--border-strong)" + (c.includes("hl") ? ";color: var(--accent)" : "") }));
      if (w != null) svg.append(s("text", { class: "label", x: (A.x + B.x) / 2 + 6, y: (A.y + B.y) / 2 - 6, text: w }));
    }
    for (const n of nodes) svg.append(s("g", { class: "node " + nodeCls(n.id) }, s("circle", { cx: n.x, cy: n.y, r }), s("text", { x: n.x, y: n.y, text: n.label ?? n.id })));
  }

  window.V = { el, s, cells, player, binaryTree, layoutTree, graph };
})();
