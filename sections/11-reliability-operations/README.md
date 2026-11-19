# §11 Reliability, Observability, and Operations

Open `index.html` in this folder for the interactive chapter view (status tracking, links to concept pages and exercises).

## Topics

- [ ] `11.01` **[P0]** SLIs, SLOs, error budgets
- [ ] `11.02` **[P0]** Deployment safety: canary, blue-green, feature flags, automated rollback
- [ ] `11.03` **[P1]** Incident response: mitigation before root cause, communication, blameless postmortems
- [ ] `11.04` **[P1]** Capacity planning, autoscaling, load testing
- [ ] `11.05` **[P1]** Alert design: symptom-based alerts, avoiding alert fatigue
- [ ] `11.06` **[P1]** CI/CD pipelines and infrastructure as code
- [ ] `11.07` **[P2]** Disaster recovery: RPO/RTO, backups, restore drills
- [ ] `11.08` **[P2]** Dependency failure planning: degrade gracefully, static fallbacks

## Layout

```
11-reliability-operations/
├── index.html     chapter page (rendered from assets/curriculum.js)
├── concepts/      one HTML page per concept (python tools/new.py concept <topic-id> <slug> "Title")
└── notes.md       your own scratch notes
```

Status: scaffold only. Concept pages and exercises come after chapters 1 and 2.
