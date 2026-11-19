# §08 Debugging, Code Reading, and Trace Analysis

Open `index.html` in this folder for the interactive chapter view (status tracking, links to concept pages and exercises).

## Topics

- [ ] `08.01` **[P0]** Systematic debugging: reproduce, isolate, hypothesize, bisect, verify the fix
- [ ] `08.02` **[P0]** Reading stack traces across languages; following a failure through async boundaries
- [ ] `08.03` **[P0]** Reading unfamiliar code quickly: entry points, data flow, invariants
- [ ] `08.04` **[P0]** Finding bugs in provided code: off-by-one, null handling, races, resource leaks, wrong boundary conditions
- [ ] `08.05` **[P1]** Logs, metrics, traces: structured logging, correlation IDs, distributed tracing (OpenTelemetry), reading a flame graph
- [ ] `08.06` **[P1]** Profiling CPU and memory; identifying hot paths, allocation pressure, GC pauses
- [ ] `08.07` **[P1]** Memory issues: leaks, use-after-free, heap dumps, sanitizers (ASan, TSan)
- [ ] `08.08` **[P1]** Debugging concurrency: nondeterministic failures, deadlock dumps, thread dumps
- [ ] `08.09` **[P1]** Production triage: is it the deploy, the dependency, the data, or the load?
- [ ] `08.10` **[P1]** Linux tooling: top/htop, strace, lsof, ss/netstat, tcpdump, perf, dmesg, /proc
- [ ] `08.11` **[P2]** Core dumps and debuggers (gdb, lldb)
- [ ] `08.12` **[P2]** Tail latency investigation: queueing, head-of-line blocking, noisy neighbors
- [ ] `08.13` **[P2]** Reviewing a pull request live: correctness, readability, tests, failure modes
- [ ] `08.14` **[P2]** Reviewing AI-generated code: spotting plausible-but-wrong logic, hallucinated APIs, missing edge cases

## Layout

```
08-debugging-code-reading/
├── index.html     chapter page (rendered from assets/curriculum.js)
├── concepts/      one HTML page per concept (python tools/new.py concept <topic-id> <slug> "Title")
└── notes.md       your own scratch notes
```

Status: scaffold only. Concept pages and exercises come after chapters 1 and 2.
