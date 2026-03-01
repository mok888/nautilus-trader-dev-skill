# Brainstorming Skill -> EvoMap Capsule Design

## Overview

Wire `superpowers/brainstorming` to EvoMap Capsule in a bi-directional flow, without relying on existing local integration setup. The skill remains the orchestrator, and EvoMap becomes the external evolution context and refinement source.

## Goal

- Publish brainstorming design deltas to EvoMap Capsule during the session.
- Fetch EvoMap capsule insights back into the same session.
- Keep operation safe under network/auth failures with deterministic fallbacks.

## Recommended Approach

Use a thin gateway (`evomap_capsule_client`) between the skill flow and EvoMap A2A endpoints.

Why this option:
- lower coupling than protocol logic embedded directly in skill text,
- easier testability and protocol-version upgrades,
- supports future migration to async worker mode without redesigning skill behavior.

## Alternatives Considered

1. Native protocol directly inside brainstorming flow
   - Pros: minimal files, maximal control
   - Cons: high coupling, difficult to evolve safely

2. Async queue worker model (publish/fetch out-of-band)
   - Pros: robust under latency/retries
   - Cons: higher infra complexity for initial rollout

## Architecture

### Components

- `brainstorming` skill workflow
  - drives sectioned design interaction and approval gates
- `evomap_capsule_client`
  - builds envelope and calls EvoMap A2A endpoints
  - handles auth headers, retries, idempotency
- `capsule_mapper`
  - maps brainstorming artifacts into EvoMap assets (`Gene`, `Capsule`, `EvolutionEvent`)
- `capsule_policy`
  - enforces publish cadence, payload limits, confidence thresholding
- optional `capsule_state_store`
  - persists node identity and message id continuity

### External Interface

Protocol: `gep-a2a` (v1.0.0)

Primary endpoints used:
- `POST /a2a/hello`
- `POST /a2a/publish`
- `POST /a2a/fetch`
- `POST /a2a/report`

Envelope fields (required):
- `protocol`, `protocol_version`, `message_type`, `message_id`, `sender_id`, `timestamp`, `payload`

## Data Flow

1. Session start
   - perform `hello`/registration if needed and load node identity
   - fetch relevant capsule context by topic/session tags
2. During brainstorming
   - at each approved section, publish a delta capsule bundle
   - include deterministic IDs and content hashes
3. Refinement loop
   - fetch EvoMap suggestions after publish
   - rank/filter suggestions by relevance and confidence
   - inject top suggestions into next section discussion
4. Session finalization
   - publish final design capsule
   - report decisions (accepted/rejected/refined) for traceability

## Error Handling

- Hard fail only for invalid envelope schema or auth denial.
- Soft fail for transient network/API issues:
  - continue local brainstorming,
  - queue deferred publish,
  - surface non-blocking status note.
- Circuit breaker:
  - after N consecutive failures, switch to local-only mode for the session.
- Idempotency:
  - message key includes `session_id + section_id + revision`.

## Security and Governance

- Credentials from env only; never embedded in skill docs.
- Redact sensitive text before publish (policy layer).
- Keep a local decision ledger for suggestions and outcomes.
- No auto-merge of EvoMap proposals into authoritative skill docs.

## Testing Strategy

### Unit
- envelope construction and required-field validation
- deterministic ID/hash generation
- artifact-to-capsule mapping correctness

### Integration
- mocked EvoMap A2A lifecycle (`hello -> publish -> fetch -> report`)
- timeout/retry/backoff and idempotent replay behavior

### End-to-End
- simulated brainstorming session with bi-directional Capsule loop
- local-only fallback verification when EvoMap becomes unavailable

## Rollout

Phase 1 (MVP): publish/fetch/report with mock + staging validation.
Phase 2: confidence ranking improvements and policy tuning.
Phase 3: optional async worker split if throughput or latency demands it.

## Non-Goals

- Replacing brainstorming process semantics.
- Auto-promoting EvoMap outputs directly into production skill text.
- Depending on legacy local integration stack.
