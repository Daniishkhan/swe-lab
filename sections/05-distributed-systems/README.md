# §05 Distributed Systems Theory

Open `index.html` in this folder for the interactive chapter view (status tracking, links to concept pages and exercises).

## Topics

- [ ] `05.01` **[P0]** CAP and PACELC, and what they do and do not say
- [ ] `05.02` **[P0]** Consistency models: linearizable, sequential, causal, eventual, read-your-writes
- [ ] `05.03` **[P0]** Delivery semantics: at-most-once, at-least-once, effectively-once via idempotency
- [ ] `05.04` **[P0]** Consensus: Raft in detail, Paxos at a conceptual level; leader election
- [ ] `05.05` **[P1]** Quorums, sloppy quorums, hinted handoff, read repair, anti-entropy (Merkle trees)
- [ ] `05.06` **[P1]** Time and ordering: clock skew, Lamport clocks, vector clocks, hybrid logical clocks, TrueTime intuition
- [ ] `05.07` **[P1]** Distributed transactions: 2PC, sagas, outbox pattern, change data capture
- [ ] `05.08` **[P1]** Failure modes: partitions, split brain, gray failure, thundering herd, cascading failure, retry storms
- [ ] `05.09` **[P1]** Distributed locks, fencing tokens, leases
- [ ] `05.10` **[P2]** CRDTs and conflict resolution
- [ ] `05.11` **[P2]** Gossip protocols, membership, failure detection
- [ ] `05.12` **[P2]** Landmark papers: Bigtable, Spanner, GFS, MapReduce, Dynamo, Kafka, Raft

## Layout

```
05-distributed-systems/
├── index.html     chapter page (rendered from assets/curriculum.js)
├── concepts/      one HTML page per concept (python tools/new.py concept <topic-id> <slug> "Title")
└── notes.md       your own scratch notes
```

Status: scaffold only. Concept pages and exercises come after chapters 1 and 2.
