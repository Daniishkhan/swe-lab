# §06 Data-Intensive Design

> Core text: Designing Data-Intensive Applications (Kleppmann). Check for the second edition.

Open `index.html` in this folder for the interactive chapter view (status tracking, links to concept pages and exercises).

## Topics

- [ ] `06.01` **[P0]** Indexing: B-tree vs LSM, composite and covering indexes, when an index hurts
- [ ] `06.02` **[P0]** Transactions and ACID; isolation levels and their anomalies (dirty read, non-repeatable read, phantom, write skew)
- [ ] `06.03` **[P0]** SQL fluency: joins, aggregation, window functions, reading an EXPLAIN plan
- [ ] `06.04` **[P0]** Data modeling: normalization vs denormalization, access-pattern-driven design
- [ ] `06.05` **[P1]** MVCC, optimistic vs pessimistic locking
- [ ] `06.06` **[P0]** Partitioning: hash vs range, hot keys, rebalancing, secondary indexes across shards
- [ ] `06.07` **[P1]** Batch vs stream processing; Lambda vs Kappa architecture
- [ ] `06.08` **[P1]** Stream concepts: windowing, watermarks, late data, exactly-once processing
- [ ] `06.09` **[P1]** Schema evolution and serialization (Protobuf, Avro, backward/forward compatibility)
- [ ] `06.10` **[P1]** OLTP vs OLAP, columnar storage, Parquet, data warehouse vs lakehouse
- [ ] `06.11` **[P2]** Online schema migrations and zero-downtime changes
- [ ] `06.12` **[P2]** Data quality, lineage, backfills, reprocessing
- [ ] `06.13` **[P2]** Vector databases and approximate nearest neighbor search (HNSW, IVF)

## Layout

```
06-data-intensive-design/
├── index.html     chapter page (rendered from assets/curriculum.js)
├── concepts/      one HTML page per concept (python tools/new.py concept <topic-id> <slug> "Title")
└── notes.md       your own scratch notes
```

Status: scaffold only. Concept pages and exercises come after chapters 1 and 2.
