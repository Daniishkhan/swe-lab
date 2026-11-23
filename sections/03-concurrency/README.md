# §03 Concurrency and Parallelism

> Core pillar for Anthropic (can appear as early as technical screens) and a strong senior differentiator in Google coding follow-ups and system design.

Open `index.html` in this folder for the interactive chapter view (status tracking, links to concept pages and exercises).

## Topics

- [ ] `03.01` **[P0]** Threads vs processes vs coroutines; when each is the right tool
- [ ] `03.02` **[P0]** Race conditions, critical sections, atomicity, visibility
- [ ] `03.03` **[P0]** Mutexes, read-write locks, semaphores, condition variables
- [ ] `03.04` **[P0]** Deadlock, livelock, starvation: the four deadlock conditions and how to break them
- [ ] `03.05` **[P0]** Thread pools, work queues, backpressure
- [ ] `03.06` **[P0]** Async I/O and event loops (epoll/kqueue model, async/await semantics, cancellation)
- [ ] `03.07` **[P0]** Classic concurrency patterns: producer-consumer, bounded buffer, thread-safe LRU, single-flight coalescing
- [ ] `03.08` **[P1]** Memory model basics: happens-before, volatile/atomic, false sharing
- [ ] `03.09` **[P1]** Compare-and-swap, lock-free vs wait-free, the ABA problem
- [ ] `03.10` **[P1]** Futures/promises, structured concurrency, cancellation and timeouts
- [ ] `03.11` **[P1]** Language specifics: Python GIL and multiprocessing, Go channels, C++ std::thread/std::atomic, Swift actors
- [ ] `03.12` **[P2]** Actor model and CSP
- [ ] `03.13` **[P2]** Parallelism limits: Amdahl's law, contention, cache effects
- [ ] `03.14` **[P2]** Implement from scratch: thread-safe queue, rate limiter, connection pool, scheduler, read-through cache with single-flight

## Layout

```
03-concurrency/
├── index.html     chapter page (rendered from assets/curriculum.js)
├── concepts/      one HTML page per concept (python tools/new.py concept <topic-id> <slug> "Title")
└── notes.md       your own scratch notes
```

Status: scaffold only. Concept pages and exercises come after chapters 1 and 2.
