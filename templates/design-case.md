# {{TITLE}}

> 45 minutes, out loud, timed. Fill each section during the run, then do the
> review at the bottom afterwards. Date: {{DATE}}

| Phase | Target time | Actual |
|---|---|---|
| Requirements & scope | 5 min | |
| Estimates | 5 min | |
| API | 5 min | |
| Data model | 5 min | |
| High-level design | 10 min | |
| Deep dive | 10 min | |
| Bottlenecks & trade-offs | 5 min | |

## 1. Requirements
**Functional**
-

**Non-functional** (latency, availability, consistency, durability, scale)
-

**Out of scope / assumptions stated**
-

## 2. Back-of-envelope estimates
- Users / DAU:
- Read QPS (avg / peak):
- Write QPS (avg / peak):
- Storage per item × items × retention:
- Bandwidth:
- Memory for hot set / cache:

## 3. API
```
POST /...
GET  /...
```
Idempotency, pagination, auth notes:

## 4. Data model
Entities, keys, access patterns, and which store each lives in (and why).

## 5. High-level design
Components and the request path. Sketch a diagram (Excalidraw, paper, or an
HTML page in this folder) and link it here.

## 6. Deep dive
Pick the 1-2 hardest parts and go deep:

## 7. Bottlenecks, failure modes, trade-offs, ops
- What breaks first at 10x?
- What happens when <dependency> is down?
- Consistency choices and what they cost:
- Two SLOs, one symptom alert to page on, and rollout/migration plan:

## Review (after)
- What I missed vs a reference solution:
- What I would say differently:
- Follow-up concepts to study (link section topics):
