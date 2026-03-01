---
name: nt-evomap-integration
description: Use when integrating evomap.ai advisory workflows into NautilusTrader systems with non-blocking execution, explicit approval gates, and auditable decision provenance.
---

# nt-evomap-integration

Integrate `evomap.ai` as an external advisory sidecar for NautilusTrader without coupling external availability to trade execution.

## When to use

- You want to publish strategy or actor artifacts to EvoMap for cross-agent refinement.
- You want to fetch EvoMap suggestions and selectively apply them under operator control.
- You need repeatable governance for external intelligence in backtest, paper, or live.

Do not use this skill for building venue adapters. Use `nt-dex-adapter` for adapter construction.

## Core invariants

1. Nautilus remains the only execution authority.
2. EvoMap remains advisory-only and never auto-applies to live behavior.
3. No external network I/O in hot handlers (`on_bar`, `on_quote_tick`, `on_order_book_deltas`).
4. EvoMap failures must degrade safely to local-only operation.
5. Every accepted or rejected suggestion must be traceable.

## Integration architecture

Use four explicit components:

- `EvoMapCapsuleClient`: thin gateway for `hello`, `publish`, `fetch`, `report`.
- `CapsuleMapper`: transforms internal events and model outputs into bounded payloads.
- `CapsulePolicy`: enforces allowlists, retry budgets, approval gate, and payload redaction.
- `ProvenanceStore`: records `event_id`, `capsule_id`, suggestion hash, decision reason.

## Recommended flow

1. Emit lightweight internal events from Strategy/Actor to a bounded queue.
2. On timer events, batch queue items and call `publish`.
3. Fetch suggestions on timer boundaries, validate through policy, and stage for review.
4. Apply only approved changes and persist outcome metadata.
5. Report results back to EvoMap using `report`.

## Implementation checklist

- [ ] Create sidecar client and keep endpoint semantics isolated from trading logic.
- [ ] Add timer-driven sync loop and bounded queue.
- [ ] Implement policy checks for field allowlist and approval gate.
- [ ] Add deterministic fallback when EvoMap is unavailable.
- [ ] Add provenance logging for all suggestion decisions.
- [ ] Cover behavior in tests for success, timeout, and degraded mode.

## Safety review checklist

- [ ] No EvoMap calls on hot handlers.
- [ ] No secrets in payloads or logs.
- [ ] No auto-merge of external suggestions.
- [ ] Rejected suggestions include reason codes.
- [ ] Fallback mode is explicit and observable.

## Example invocation prompts

Use these copy-paste prompts with the skill to accelerate common workflows.

### 1) Architecture boundary definition

```text
Design an EvoMap integration boundary for our NautilusTrader system.
Constraints:
- EvoMap must remain advisory-only
- No network I/O in hot handlers
- Deterministic local fallback when EvoMap is unavailable
- Include provenance fields for every accept/reject decision
Deliverable:
- Component diagram (client/mapper/policy/store)
- Lifecycle placement (`on_start`, timer loop, `on_stop`)
- Failure-mode table
```

### 2) Implementation planning

```text
Create an implementation plan for adding EvoMap sidecar support.
Include:
- `EvoMapCapsuleClient` interface (`hello`, `publish`, `fetch`, `report`)
- Timer-driven queue processing design
- Payload allowlist and redaction policy
- Test matrix for success, timeout, and degraded mode
Output should be ordered as: files to edit, code skeletons, tests, rollout steps.
```

### 3) Runtime wiring and rollout

```text
Wire EvoMap sidecar into our strategy runtime.
Requirements:
- Publish/fetch/report runs on timer boundaries only
- Approval gate required before behavior changes
- Emit metrics for queue size, publish success rate, fallback activation
- Keep backtest behavior deterministic
Return a rollout checklist for dev -> paper -> live.
```

### 4) Pre-deployment review

```text
Review EvoMap integration for live readiness.
Verify:
- advisory-only enforcement
- no secret leakage in payloads/logs
- explicit degraded-mode behavior
- full provenance coverage and decision reason codes
Classify findings as blocker/major/minor with concrete fixes.
```

## Verification commands

```bash
# Run relevant tests in your project
pytest -q

# Validate strategy wiring if used
python examples/live_node.py
```

## Works with

- `nt-architect` for boundary definition and lifecycle placement.
- `nt-implement` for component-level implementation patterns.
- `nt-strategy-builder` for runtime wiring in backtest/paper/live nodes.
- `nt-review` for final safety and readiness checks.
