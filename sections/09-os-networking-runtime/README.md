# §09 Operating Systems, Networking, and Runtime Internals

Open `index.html` in this folder for the interactive chapter view (status tracking, links to concept pages and exercises).

## Topics

- [ ] `09.01` **[P0]** Processes, threads, context switches, scheduling
- [ ] `09.02` **[P0]** Virtual memory, paging, stack vs heap, page cache
- [ ] `09.03` **[P0]** HTTP/1.1 vs HTTP/2 vs HTTP/3; TLS handshake; DNS resolution
- [ ] `09.04` **[P0]** TCP vs UDP: handshake, flow control, congestion control, connection reuse
- [ ] `09.05` **[P1]** File systems, file descriptors, blocking vs non-blocking I/O, fsync and durability
- [ ] `09.06` **[P1]** What happens when you type a URL and press enter, at depth
- [ ] `09.07` **[P1]** Garbage collection strategies vs manual memory vs ownership/RAII
- [ ] `09.08` **[P1]** Containers: namespaces, cgroups, images; Kubernetes scheduling basics
- [ ] `09.09` **[P2]** CPU caches, cache locality, branch prediction, SIMD awareness
- [ ] `09.10` **[P2]** NUMA, zero-copy I/O, mmap, io_uring
- [ ] `09.11` **[P2]** Proxies, service mesh, NAT, connection pooling pitfalls

## Layout

```
09-os-networking-runtime/
├── index.html     chapter page (rendered from assets/curriculum.js)
├── concepts/      one HTML page per concept (python tools/new.py concept <topic-id> <slug> "Title")
└── notes.md       your own scratch notes
```

Status: scaffold only. Concept pages and exercises come after chapters 1 and 2.
