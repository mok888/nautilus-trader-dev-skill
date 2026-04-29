---
source_url: https://nautilustrader.io/docs/latest/developer_guide/design_principles/
source_repo: nautechsystems/nautilus_trader/docs/developer_guide/design_principles.md
sync_date: 2026-04-29
target: latest developer guide
confidence: high
---

# Design Principles

NautilusTrader design favors deterministic, replayable, auditable systems. The
most important agent-facing invariant from the current developer guide is
message immutability: messages should be treated as immutable once constructed
and published.

Message immutability supports deterministic replay, safe concurrency, debugging,
auditability, and future distribution across processes or machines. Agent-built
components should derive new messages or state transitions instead of mutating
published message objects in place.

## Agent checklist

- Treat events, commands, requests, and responses as immutable after creation.
- Do not mutate message payloads after publishing them to a bus, actor, cache, or
  strategy boundary.
- Prefer new value objects when a later step needs adjusted values.
- During review, flag code that changes message fields after publication.
