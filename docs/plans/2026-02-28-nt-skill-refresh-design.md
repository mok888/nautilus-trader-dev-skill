# NautilusTrader Skill Refresh Design (Adapter Guide Alignment)

## Overview

Refresh the existing five NautilusTrader skills to align with the latest adapter guidance in `docs/developer_guide/adapters.md` and current official adapter patterns in `nautechsystems/nautilus_trader`.

Scope is limited to improving existing skills:

- `skills/nt-dex-adapter/SKILL.md`
- `skills/nt-implement/SKILL.md`
- `skills/nt-review/SKILL.md`
- `skills/nt-architect/SKILL.md`
- `skills/nt-strategy-builder/SKILL.md`

## Goals

- Keep the current skill workflow and avoid a disruptive skill-suite rewrite.
- Add explicit adapter contracts so required methods and phase gates are unambiguous.
- Encode runtime/FFI safety rules that repeatedly cause production issues.
- Strengthen test doctrine around real payload fixtures and deterministic async tests.
- Keep guidance balanced: strict where safety/correctness matters, flexible where style differs by venue.

## Constraints

- Preserve existing skill identities and entry points.
- Do not require new skills for this pass.
- Keep content practical and directly actionable for implementation/review loops.
- Align with Rust-first adapter architecture and official factory patterns.

## Findings Used

- Latest adapter guide emphasizes fixed 7-phase sequencing and phase milestones.
- Python adapter layer requires complete contracts for provider, data client, and execution client methods.
- Runtime and FFI safety patterns are explicit (`get_runtime().spawn()`, avoid `Arc<PyObject>`, no blocking in hot handlers).
- Factory and config conventions are stable across official adapters (`create(loop, name, config, msgbus, cache, clock)`).
- Testing doctrine is stricter: real payload fixtures, condition-based waiting, multi-layer integration coverage.

## Approaches Considered

1. **Surgical alignment (selected)**
   - Add canonical contract sections and review gates inside existing skills.
   - Pros: fast adoption, low disruption, immediate quality gains.
   - Cons: contract text duplicated across files.

2. **Heavy enforcement rewrite**
   - Add larger compliance frameworks and expanded test suites in each skill.
   - Pros: strongest enforcement.
   - Cons: higher complexity and maintenance overhead.

3. **Single adapter-core skill refactor**
   - Centralize adapter rules into one core skill, make others thin wrappers.
   - Pros: minimal duplication long-term.
   - Cons: risky migration and larger user workflow change.

## Selected Design

### 1) Shared Adapter Canonical Contract

Add/refresh adapter contract guidance across the five skills, covering:

- Mandatory 7-phase order and milestone discipline.
- Required Python interface contracts (`InstrumentProvider`, `LiveDataClient`, `LiveExecutionClient`).
- Runtime/FFI invariants for async and binding safety.
- Factory/config expectations and credential handling patterns.
- Testing doctrine and required integration-test coverage categories.

### 2) Skill-Specific Responsibility Split

- `nt-dex-adapter`: DEX-specific implementation constraints, red flags, and readiness checks.
- `nt-implement`: implementation-side adapter contracts and template obligations.
- `nt-review`: adapter review fail conditions and severity gates.
- `nt-architect`: architecture-phase constraints and phase-to-validation mapping.
- `nt-strategy-builder`: deployment/wiring invariants before enabling live order flow.

### 3) Deprecation-Aware References

- Prefer dYdX v4 framing for on-chain CLOB guidance.
- Emphasize `_template` adapter skeleton as canonical starting point.
- Keep references current with latest NautilusTrader docs/release posture.

## Validation Plan

- Verify modified files are syntactically valid markdown and consistent with existing style.
- Verify key contract terms are present in each updated skill.
- Run skill-repo test subset where available.

## Out of Scope

- Creating new skills (`nt-testing`, `nt-debugging`, etc.) in this pass.
- Reorganizing the entire skill workflow graph.
- Building new adapter code templates beyond current scope.

## Implementation Transition

After design approval, execution should follow a small implementation plan:

1. Apply contract/review-gate updates to five skill files.
2. Run local validation and skill tests.
3. Produce a concise changelog summary for users of this skill suite.
