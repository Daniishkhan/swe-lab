# §10 Code Quality, Design, and Testing

Open `index.html` in this folder for the interactive chapter view (status tracking, links to concept pages and exercises).

## Topics

- [ ] `10.01` **[P0]** Clean, idiomatic code in your primary language; deep knowledge of its standard library
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
├── concepts/      one HTML page per concept (python tools/new.py concept <topic-id> <slug> "Title")
├── lld/           low-level design worksheets (python tools/new.py lld "Parking lot")
└── notes.md       your own scratch notes
```

Status: scaffold only. Concept pages and exercises come after chapters 1 and 2.
