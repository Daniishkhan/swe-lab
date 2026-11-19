# §07 System Design Case Studies

> Practice each as a 45-minute exercise: requirements, estimates, API, data model, high-level design, deep dive, bottlenecks, trade-offs.

Open `index.html` in this folder for the interactive chapter view (status tracking, links to concept pages and exercises).

## Topics

- [ ] `07.01` **[Classic]** URL shortener; pastebin
- [ ] `07.02` **[Classic]** Rate limiter (single node, then distributed)
- [ ] `07.03` **[Classic]** News feed / timeline (fan-out on write vs read)
- [ ] `07.04` **[Classic]** Chat and messaging (1:1, group, presence, delivery receipts)
- [ ] `07.05` **[Classic]** Notification system (multi-channel, dedup, preferences)
- [ ] `07.06` **[Classic]** Typeahead / autocomplete
- [ ] `07.07` **[Classic]** Web crawler
- [ ] `07.08` **[Classic]** Distributed key-value store
- [ ] `07.09` **[Classic]** Distributed cache
- [ ] `07.10` **[Classic]** Job scheduler / distributed cron / task queue
- [ ] `07.11` **[Classic]** Unique ID generator (Snowflake-style)
- [ ] `07.12` **[Classic]** File sync and storage (Dropbox-style)
- [ ] `07.13` **[Classic]** Ride matching / geospatial proximity (geohash, quadtree, S2)
- [ ] `07.14` **[Classic]** Payment system and ledger (idempotency, reconciliation, double-entry)
- [ ] `07.15` **[Classic]** Ticketing / inventory with contention (flash sale)
- [ ] `07.16` **[Classic]** Collaborative editor (OT vs CRDT)
- [ ] `07.17` **[Classic]** Metrics, monitoring, and alerting pipeline
- [ ] `07.18` **[Classic]** Log aggregation and search
- [ ] `07.19` **[Classic]** Ad click aggregation; top-k / leaderboard
- [ ] `07.20` **[Netflix]** Video streaming: ingest, transcoding pipeline, adaptive bitrate, CDN placement
- [ ] `07.21` **[Netflix]** Recommendation system serving and feature pipelines
- [ ] `07.22` **[Netflix]** A/B testing and experimentation platform
- [ ] `07.23` **[Netflix]** Playback telemetry at scale
- [ ] `07.24` **[Netflix]** Resilience design: chaos engineering, regional evacuation, graceful degradation
- [ ] `07.25` **[Anthropic]** LLM inference API: request routing, batching, streaming tokens, GPU scheduling
- [ ] `07.26` **[Anthropic]** Multi-tenant rate limiting and quota by tokens rather than requests
- [ ] `07.27` **[Anthropic]** Prompt/response caching (prefix caching, KV cache reuse)
- [ ] `07.28` **[Anthropic]** RAG system: ingestion, chunking, embedding, retrieval, reranking, freshness
- [ ] `07.29` **[Anthropic]** Agent execution platform: sandboxing, tool calls, long-running tasks, checkpointing
- [ ] `07.30` **[Anthropic]** Evaluation platform: datasets, graders, regression tracking
- [ ] `07.31` **[Anthropic]** Training data pipeline and distributed job orchestration
- [ ] `07.32` **[Anthropic]** Abuse detection and safety filtering in the request path

## Layout

```
07-system-design-cases/
├── index.html     chapter page (rendered from assets/curriculum.js)
├── concepts/      one HTML page per concept (python tools/new.py concept <topic-id> <slug> "Title")
├── cases/         45-minute design write-ups (python tools/new.py case "URL shortener")
└── notes.md       your own scratch notes
```

Status: scaffold only. Concept pages and exercises come after chapters 1 and 2.
