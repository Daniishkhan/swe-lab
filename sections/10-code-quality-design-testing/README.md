# §10 Code Quality, Design, and Testing

Open `index.html` in this folder for the interactive chapter view (status tracking, links to concept pages and exercises).

## Topics

- [ ] `10.13` **[P0]** Python control flow, loops, and functions (`python-control-flow.html`)
- [ ] `10.14` **[P0]** Python's built-in data structures: `list`, `tuple`, `str`, `dict`, and `set` (`python-data-structures.html` + `py_foundations.py`)
- [ ] `10.10` **[P0]** How Python holds data in memory: names vs objects, copies, defaults & closures (`python-memory-model.html`)
- [ ] `10.11` **[P0]** Transforming and streaming data: comprehensions, `itertools` & lazy generators (`python-idioms.html` + `py_idioms.py`)
- [ ] `10.12` **[P0]** Python decorators and clean building blocks: `@dataclass`, `@memoize` & `@contextmanager` (`python-building-blocks.html` + `py_internals.py`)
- [ ] `10.01` **[P0]** Clean, idiomatic code in your primary language; deep knowledge of its standard library (`python-toolkit.html` + `py_toolkit.py`)
- [ ] `10.02` **[P0]** Object-oriented and functional design; composition over inheritance; SOLID as trade-offs, not rules
- [ ] `10.03` **[P0]** Testing strategy: unit, integration, end-to-end, contract; what to mock and what not to
- [ ] `10.04` **[P1]** Low-level design exercises: in-memory KV store with transactions, in-memory file system, banking ledger, LRU cache, spreadsheet engine
- [ ] `10.05` **[P1]** API and interface design: naming, error handling, extensibility, backward compatibility
- [ ] `10.06` **[P1]** Common design patterns and when they are overkill
- [ ] `10.07` **[P1]** Refactoring legacy code safely; characterization tests
- [ ] `10.08` **[P2]** Property-based testing, fuzzing, load testing, chaos testing
- [ ] `10.09` **[P2]** Dependency management, build systems, monorepo trade-offs

## Layout

```
10-code-quality-design-testing/
├── index.html     chapter page (rendered from assets/curriculum.js)
├── concepts/      6 full Phase 0 Python book chapters (`10.13`, `10.14`, `10.10`, `10.11`, `10.12`, `10.01`)
├── exercises/     4 work-measuring Python suites (`py_foundations`, `py_idioms`, `py_internals`, `py_toolkit`)
├── lld/           low-level design worksheets (python tools/new.py lld "Parking lot")
└── notes.md       your own scratch notes
```
