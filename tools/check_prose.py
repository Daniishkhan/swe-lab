#!/usr/bin/env python3
"""
Report how a chapter's prose does against the writing rules in templates/README.md.

  python3 tools/check_prose.py sections/01-data-structures/concepts/hash-maps.html [more.html]

For each page:
  - words on the main path: everything read top to bottom, so not the
    collapsed asides or the exercises
  - boxes that interrupt the running text: quick checks, key ideas, figures
    and asides
  - sentences with working inside them (arithmetic, arrows, formulas), with
    semicolons or with brackets
  - running text that points at a figure, check or aside
  - to read by eye: sentences with three or more numbers (would a block be
    clearer?), phrases that often start an everyday analogy (at most one per
    chapter), and each section's heading and first sentence (is the heading
    the standard term, does the sentence state the point?)

Every flagged sentence is printed with its section. The targets are aims,
not laws: a miss needs a reason. Exits 1 if a page misses a target.
"""
import re
import sys
from html.parser import HTMLParser

# What a page should hit. Measured 2026-11: articles that read easily had working
# in 1.5% of sentences, brackets in 8%, semicolons in 0.2%; our chapters 14%, 20%, 5%.
# The median chapter then had a main path of 7,100 words and 27 boxes.
TARGETS = {
    "main path": ("words", 6000),
    "boxes": ("", 20),
    "working inside": ("% of sentences", 3),
    "semicolons": ("% of sentences", 0.5),
    "brackets": ("% of sentences", 10),
    "pointers to boxes": ("sentences", 0),
}

SKIP = {"script", "style", "svg", "nav", "select", "option", "input", "label"}  # not prose
WORKING = {"pre", "table"}                                                      # blocks of working
BLOCKS = {"p", "li", "h1", "h2", "h3", "h4", "blockquote", "summary", "button", "div", "ul", "ol", "details", "section", "header"}
VOID = {"br", "img", "hr", "meta", "link", "wbr", "input"}

BIG_O = re.compile(r"\b[OΘΩ]\((?:[^()]|\([^()]*\))*\)")
CODE = re.compile(r"⟦(.*?)⟧")
SYMBOLS = re.compile(r"[×÷≈∝√=^<>≤≥±]|\d\s?/\s?\d|\b[a-zα]\s?/\s?[a-z0-9]\b|\s[%−*+]\s|\d\s?[+*]\s?\d")
ARROWS = re.compile(r"[→←⇒↔]|->")
POINTERS = re.compile(
    r"\b(?:figure|diagram|table|box|chart|code|block|example|picture|list|stepper|slider|playground|check|aside)\s+(?:above|below)\b"
    r"|\b(?:above|below)\s*[.:,)]"
    r"|\bthe (?:figure|stepper|slider|playground|quick check|aside|key idea|box)\b"
    r"|\bstep through\b|\bpress (?:play|next)\b|\bgo deeper\b|\bas shown\b", re.I)
ANALOGY = re.compile(r"\b(?:imagine|picture (?:a|an|the|your)|think of|pretend|as if|is like|like an?|just as an?|analogy)\b", re.I)


class Page(HTMLParser):
    """Collects (where, section, text) for every block of prose inside <main>."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.units, self.buf = [], [], None
        self.boxes = {"quick checks": 0, "key ideas": 0, "figures": 0, "asides": 0}
        self.section, self.in_exercises = "(before section 1)", False

    def where(self):
        tags = [t for t, _ in self.stack]
        classes = set().union(*[c for _, c in self.stack]) if self.stack else set()
        if "main" not in tags or SKIP & set(tags) or {"review", "chapter-nav", "viz-stage"} & classes:
            return None
        if self.in_exercises or "exercise" in classes:
            return "exercises"
        if "details" in tags:
            return "aside"
        if WORKING & set(tags):
            return "working"
        if {"h1", "h2", "h3", "h4"} & set(tags):
            return "heading"
        if "check" in classes:
            return "options" if "button" in tags else "check"
        if "keyidea" in classes:
            return "key idea"
        if "figure" in classes:
            return "caption"
        if "chapter-head" in classes or "learn-list" in classes or "muted" in classes:
            return "front"
        return "running"

    def flush(self):
        if self.buf:
            where, parts = self.buf
            text = re.sub(r"\s+", " ", "".join(parts)).strip()
            if text and where:
                self.units.append((where, self.section, text))
                if where == "heading" and self.heading_tag == "h2":
                    self.section = text
        self.buf = None

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            return
        a = dict(attrs)
        if tag in BLOCKS or tag in WORKING:
            self.flush()
        classes = set((a.get("class") or "").split())
        self.stack.append((tag, classes))
        if not self.in_exercises and "main" in [t for t, _ in self.stack]:
            for cls, box in (("check", "quick checks"), ("keyidea", "key ideas"), ("figure", "figures"), ("aside", "asides")):
                self.boxes[box] += cls in classes
        if tag == "h2" and a.get("id") == "exercises":
            self.in_exercises = True
        if tag in ("h1", "h2", "h3", "h4"):
            self.heading_tag = tag
        if tag == "code" and self.buf:
            self.buf[1].append("⟦")

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if tag == "code" and self.buf:
            self.buf[1].append("⟧")
        if tag in BLOCKS or tag in WORKING:
            self.flush()
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if (not data.strip() and not self.buf) or (self.stack and "sec-num" in self.stack[-1][1]):
            return
        if not self.buf:
            self.buf = (self.where(), [])
        self.buf[1].append(data)


def sentences(text):
    text = re.sub(r"\b(e\.g|i\.e|vs|etc)\.", lambda m: m.group(0).replace(".", "§"), text)
    parts = re.split(r'(?<=[.!?])["”)]?\s+(?=[A-Z0-9"“(⟦])', text)
    return [p.replace("§", ".").strip() for p in parts if p.strip()]


def count_words(text):
    return len(re.findall(r"[A-Za-z0-9][\w'’.,-]*", text.replace("⟦", " ").replace("⟧", " ")))


def flags(sentence):
    """Which rules a sentence breaks. Big-O and plain names in code font are allowed."""
    code = CODE.findall(sentence)
    text = CODE.sub(" code ", BIG_O.sub(" big-O ", sentence)).replace("C++", "Cpp")
    out = []
    # In code font, an operator between two operands is working: `hash(key) % m`, not `%` or `d[key]`.
    if SYMBOLS.search(text) or ARROWS.search(text) or any(re.search(r"[\w)\]\"']\s*[=+*/%<>]+\s*[\w(\[\"']", c) for c in code):
        out.append("working inside")
    if ";" in text:
        out.append("semicolons")
    if "(" in text:
        out.append("brackets")
    if len(re.findall(r"\d[\d,.:]*\d|\d", text)) >= 3:
        out.append("three or more numbers")
    return out


def check(path):
    html = open(path, encoding="utf-8").read()
    page = Page()
    page.feed(html)
    page.flush()
    words = {}
    for where, _, text in page.units:
        words[where] = words.get(where, 0) + count_words(text)
    main_path = sum(n for w, n in words.items() if w not in ("aside", "exercises"))

    hits = {k: [] for k in ("working inside", "semicolons", "brackets", "pointers to boxes", "three or more numbers", "analogy cues")}
    total = 0
    openers, seen = [], set()
    for where, section, text in page.units:
        if where not in ("running", "check", "key idea", "caption"):
            continue
        for s in sentences(text):
            total += 1
            for f in flags(s):
                hits[f].append((section, s))
            if where == "running":
                if POINTERS.search(CODE.sub(" ", s)):
                    hits["pointers to boxes"].append((section, s))
                if ANALOGY.search(CODE.sub(" ", s)):
                    hits["analogy cues"].append((section, s))
                if section not in seen:
                    seen.add(section)
                    openers.append((section, s))

    pct = lambda name: round(100 * len(hits[name]) / max(1, total), 1)
    got = {
        "main path": main_path,
        "boxes": sum(page.boxes.values()),
        "working inside": pct("working inside"),
        "semicolons": pct("semicolons"),
        "brackets": pct("brackets"),
        "pointers to boxes": len(hits["pointers to boxes"]),
    }
    show = lambda s: s.replace("⟦", "`").replace("⟧", "`")
    print(f"\n{path}")
    print(f"  running text {words.get('running', 0):,} words · tables and code {words.get('working', 0):,} · collapsed asides {words.get('aside', 0):,}"
          f" · exercises {words.get('exercises', 0):,} · {total} sentences checked")
    print("  " + " · ".join(f"{n} {name}" for name, n in page.boxes.items()))
    missed = 0
    for name, (unit, limit) in TARGETS.items():
        ok = got[name] <= limit
        missed += not ok
        print(f"  {'✓' if ok else '✗'} {name:<18} {got[name]:>6,} {unit}".rstrip() + f"  (aim: at most {limit:,})")
    notes = {"three or more numbers": "would a block be clearer?", "analogy cues": "at most one everyday analogy per chapter"}
    for name, found in hits.items():
        if found:
            print(f"\n  {name} ({len(found)})" + (f", to read by eye: {notes[name]}" if name in notes else "") + ":")
            for section, s in found:
                print(f"    [{section[:28]}] {show(s)}")
    print("\n  Headings and first sentences, to read by eye (standard term? states the point?):")
    for section, s in openers:
        print(f"    {section}\n      {show(s)}")
    return missed


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(1 if sum(check(p) for p in sys.argv[1:]) else 0)
