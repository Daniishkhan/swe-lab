# §04 System Design Fundamentals

> At Google L5, system design is often the make-or-break leveling round. Drive the room, quantify constraints, and be ready when the interviewer opens any black box.

Open `index.html` in this folder for the interactive chapter view (status tracking, links to concept pages and exercises).

## Topics

- [ ] `04.01` **[P0]** Requirements gathering: functional vs non-functional, scoping, stating assumptions
- [ ] `04.02` **[P0]** Back-of-envelope estimation: QPS, storage, bandwidth, memory
- [ ] `04.03` **[P0]** Latency numbers every engineer should know; p50/p95/p99 thinking
- [ ] `04.04` **[P0]** Load balancing: L4 vs L7, algorithms, health checks
- [ ] `04.05` **[P0]** Caching: cache-aside, write-through, write-behind, TTLs, invalidation, stampede protection
- [ ] `04.06` **[P0]** Database choice: relational vs document vs key-value vs wide-column vs graph vs search
- [ ] `04.07` **[P0]** Replication (leader-follower, multi-leader, leaderless) and sharding/partitioning strategies
- [ ] `04.08` **[P0]** Message queues and event streams (Kafka, SQS, RabbitMQ): ordering, delivery guarantees
- [ ] `04.09` **[P0]** API design: REST, gRPC, GraphQL; pagination, versioning, idempotency keys
- [ ] `04.10` **[P0]** CDNs, edge caching, object storage
- [ ] `04.11` **[P1]** Stateless services, session handling, horizontal scaling
- [ ] `04.12` **[P0]** Rate limiting, load shedding, circuit breakers, retries with jitter, timeouts, bulkheads
- [ ] `04.13` **[P1]** Multi-region design: active-active vs active-passive, failover, data residency
- [ ] `04.14` **[P1]** Real-time delivery: WebSockets, SSE, long polling, pub/sub fan-out
- [ ] `04.15` **[P1]** Search and indexing: inverted index, scatter-gather, ranking basics
- [ ] `04.16` **[P2]** Cost as a design constraint; build vs buy
- [ ] `04.17` **[P1]** Migration strategy: dual writes, backfills, shadow traffic, strangler pattern

## Layout

```
04-system-design-fundamentals/
├── index.html     chapter page (rendered from assets/curriculum.js)
├── concepts/      one HTML page per concept (python tools/new.py concept <topic-id> <slug> "Title")
└── notes.md       your own scratch notes
```

Status: scaffold only. Concept pages and exercises come after chapters 1 and 2.
