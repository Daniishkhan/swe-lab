#!/usr/bin/env python3
"""
Regenerate assets/curriculum.js, the data file every HTML page reads.

It combines:
  - curriculum.json                     the topic list (source of truth)
  - sections/*/concepts/*.html          concept pages (via <meta name="topic">)
  - sections/*/exercises/*.py           exercises (via the "Topic: XX.YY" docstring line)
  - .test-results.json (optional)       pass/fail counts, written by --run-tests

Usage:
  python tools/build.py               # rebuild data only
  python tools/build.py --run-tests   # also run pytest and record results per exercise
"""
from __future__ import annotations

import datetime as dt
import html
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / ".test-results.json"

META_TOPIC = re.compile(r'<meta\s+name="topic"\s+content="([^"]+)"', re.I)
TITLE = re.compile(r"<title>(.*?)</title>", re.I | re.S)
EX_TOPIC = re.compile(r"^Topic:\s*([\d.]+)(.*)$", re.M)
TOPIC_ID = re.compile(r"\b\d{2}\.\d{2}\b")


def scan_concepts(section_dir: Path) -> list[dict]:
    out = []
    for f in sorted((section_dir / "concepts").glob("*.html")):
        text = f.read_text(encoding="utf-8")
        m = META_TOPIC.search(text)
        if not m:
            continue
        t = TITLE.search(text)
        out.append({"file": f.name, "topic": m.group(1), "title": html.unescape(t.group(1).strip()) if t else f.stem})
    return out


def scan_exercises(section_dir: Path, results: dict) -> list[dict]:
    out = []
    for f in sorted((section_dir / "exercises").glob("*.py")):
        if f.name.startswith(("test_", "_")) or f.name == "conftest.py":
            continue
        text = f.read_text(encoding="utf-8")
        m = EX_TOPIC.search(text)
        topics = [m.group(1)] + TOPIC_ID.findall(m.group(2)) if m else []
        doc_title = text.split('"""')[1].strip().splitlines()[0] if text.startswith('"""') else f.stem
        out.append({"file": f.name, "module": f.stem, "title": doc_title, "topics": topics,
                    "result": results.get(f.stem)})
    return out


def run_tests() -> dict:
    xml_path = ROOT / ".pytest-report.xml"
    subprocess.run([sys.executable, "-m", "pytest", "-q", "--no-header", "-p", "no:cacheprovider",
                    f"--junitxml={xml_path}"], cwd=ROOT)
    results: dict[str, dict] = {}
    if xml_path.exists():
        for case in ET.parse(xml_path).getroot().iter("testcase"):
            mod = case.get("classname", "").split(".")[-1]  # test_hash_map
            name = mod[5:] if mod.startswith("test_") else mod
            r = results.setdefault(name, {"passed": 0, "total": 0})
            r["total"] += 1
            if not any(child.tag in ("failure", "error", "skipped") for child in case):
                r["passed"] += 1
        xml_path.unlink()
    RESULTS.write_text(json.dumps(results, indent=2))
    return results


def check_track(data: dict) -> list[str]:
    """The track is the learning order. Nothing may come before what it builds on.

    - every step and milestone names a real topic, and no topic appears twice
    - each step's `requires` all come earlier in the track (a "pick" stage, such
      as a company pack, may also use anything from the main stages)
    - a required step never depends on an optional one
    """
    topics = {t["id"]: t for s in data["sections"] for t in s["topics"]}
    errors = [f"{tid} requires unknown topic {r}" for tid, t in topics.items() for r in t.get("requires", []) if r not in topics]
    stages = data["track"]["stages"]
    seen_ids, main, placed = set(), {}, {}
    for st in stages:
        for key in ("id",):
            if st[key] in seen_ids:
                errors.append(f"duplicate stage or milestone id {st[key]}")
            seen_ids.add(st[key])
        if st.get("milestone"):
            mid, fmt = st["milestone"]["id"], st["milestone"].get("format")
            if mid in seen_ids:
                errors.append(f"duplicate stage or milestone id {mid}")
            seen_ids.add(mid)
            if fmt and fmt not in topics:
                errors.append(f"milestone {mid} names unknown format {fmt}")
    final = {step["topic"]: st["id"] for st in stages for step in st["steps"]}
    picking = False
    for st in stages:
        if picking and not st.get("pick"):
            errors.append(f"stage {st['id']} comes after a pick stage; pick stages go last")
        picking = picking or bool(st.get("pick"))
        local = {}  # what this pick stage has placed so far
        for step in st["steps"]:
            tid = step["topic"]
            if tid not in topics:
                errors.append(f"{st['id']}: unknown topic {tid}")
                continue
            if tid in placed:
                errors.append(f"{tid} appears twice in the track ({placed[tid]} and {st['id']})")
            for r in topics[tid].get("requires", []):
                before = main.get(r) if r in main else local.get(r)
                if before is None:
                    where = final.get(r)
                    errors.append(f"{tid} ({st['id']}) requires {r}, which "
                                  + (f"comes later ({where})" if where else "is not in the track before it"))
                elif before == "optional" and not step.get("optional"):
                    errors.append(f"{tid} ({st['id']}) is required but builds on optional step {r}")
            kind = "optional" if step.get("optional") else "required"
            placed[tid] = st["id"]
            (local if st.get("pick") else main)[tid] = kind
    return errors


HOW_TO_READ = re.compile(r"How to read this(.*?)</p>", re.S)
HREF = re.compile(r'href="([^"#]+\.html)')


def check_requires_against_pages(data: dict) -> list[str]:
    """Warn when a chapter's "How to read this" line names a chapter its `requires` leaves out."""
    by_file = {}
    for sec in data["sections"]:
        for c in sec["concepts"]:
            by_file[(sec["slug"], c["file"])] = c["topic"]
    topics = {t["id"]: t for s in data["sections"] for t in s["topics"]}
    warnings = []
    for sec in data["sections"]:
        for c in sec["concepts"]:
            text = (ROOT / "sections" / sec["slug"] / "concepts" / c["file"]).read_text(encoding="utf-8")
            m = HOW_TO_READ.search(text)
            if not m:
                continue
            for href in HREF.findall(m.group(1)):
                parts = href.split("/")
                slug = parts[-3] if len(parts) >= 3 else sec["slug"]
                named = by_file.get((slug, parts[-1]))
                if named and named != c["topic"] and named not in topics[c["topic"]].get("requires", []):
                    warnings.append(f"{c['topic']} {c['file']}: 'How to read this' names {named}, missing from its requires")
    return warnings


def main() -> None:
    results = run_tests() if "--run-tests" in sys.argv else (
        json.loads(RESULTS.read_text()) if RESULTS.exists() else {})
    data = json.loads((ROOT / "curriculum.json").read_text(encoding="utf-8"))
    for sec in data["sections"]:
        d = ROOT / "sections" / sec["slug"]
        sec["concepts"] = scan_concepts(d)
        sec["exercises"] = scan_exercises(d, results)
    for w in check_requires_against_pages(data):
        print("warning:", w)
    errors = check_track(data)
    if errors:
        print("The track in curriculum.json breaks the prerequisite order:", *errors, sep="\n  ")
        sys.exit(1)
    data["generated"] = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    js = "// Generated by tools/build.py. Do not edit; edit curriculum.json instead.\n"
    js += "window.CURRICULUM = " + json.dumps(data, indent=1, ensure_ascii=False) + ";\n"
    (ROOT / "assets" / "curriculum.js").write_text(js, encoding="utf-8")
    n_c = sum(len(s["concepts"]) for s in data["sections"])
    n_e = sum(len(s["exercises"]) for s in data["sections"])
    print(f"assets/curriculum.js: {len(data['sections'])} sections, {n_c} concept pages, {n_e} exercises")


if __name__ == "__main__":
    main()
