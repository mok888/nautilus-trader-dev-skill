# Design Principles Contract

Sources:

- `references/developer_guide/design_principles.md`

## Required guidance

- Preserve message immutability across actor, strategy, adapter, cache, and
  message-bus boundaries.
- Use new value objects or state transitions instead of mutating published
  messages in place.
- Treat determinism, replayability, concurrency safety, auditability, and
  debuggability as production design constraints.

## Review rule

Code or examples that mutate events, commands, requests, or responses after they
are published need redesign or a documented local-only exception.
