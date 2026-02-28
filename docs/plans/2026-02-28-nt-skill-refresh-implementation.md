# NautilusTrader Skill Refresh Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Update the five NautilusTrader skills so adapter guidance matches the latest official adapter developer guide and repository conventions.

**Architecture:** Keep the existing 5-skill topology and inject a shared adapter canonical contract in each relevant skill section. Enforce strict behavior for runtime safety, method contracts, factory/config patterns, and testing doctrine while preserving skill-specific responsibilities.

**Tech Stack:** Markdown skill docs, pytest-based skill checks, NautilusTrader adapter references.

---

### Task 1: Add canonical adapter contract to nt-dex-adapter

**Files:**
- Modify: `skills/nt-dex-adapter/SKILL.md`
- Test: `skills/nt-dex-adapter/tests/test_dex_compliance.py`

**Step 1: Write the failing test**

Add/extend assertions in `skills/nt-dex-adapter/tests/test_dex_compliance.py` so the test expects the following phrases in `SKILL.md`:
- `Adapter Canonical Contract (2026 Guide Alignment)`
- `7-phase`
- `get_runtime().spawn()`
- `LiveExecutionClient`
- `condition-based`

**Step 2: Run test to verify it fails**

Run: `uv run pytest skills/nt-dex-adapter/tests/test_dex_compliance.py -v`
Expected: FAIL because new contract section does not exist yet.

**Step 3: Write minimal implementation**

Update `skills/nt-dex-adapter/SKILL.md` with:
- fixed 7-phase order and milestones
- required provider/data/exec method contracts
- runtime/FFI invariants (`get_runtime().spawn()`, no `Arc<PyObject>`)
- factory signature and credential/config standards
- test doctrine and readiness checklist

**Step 4: Run test to verify it passes**

Run: `uv run pytest skills/nt-dex-adapter/tests/test_dex_compliance.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add skills/nt-dex-adapter/SKILL.md skills/nt-dex-adapter/tests/test_dex_compliance.py
git commit -m "docs: align dex adapter skill with latest adapter contract"
```

### Task 2: Add adapter contract to nt-implement

**Files:**
- Modify: `skills/nt-implement/SKILL.md`
- Test: `skills/nt-implement/tests/` (create if missing)

**Step 1: Write the failing test**

Create a markdown-content test that checks `skills/nt-implement/SKILL.md` includes:
- required method contracts for provider/data/execution
- factory `create(loop, name, config, msgbus, cache, clock)`
- runtime/FFI constraints
- fixture and async test doctrine

**Step 2: Run test to verify it fails**

Run: `uv run pytest skills/nt-implement/tests/ -v`
Expected: FAIL on missing/old wording.

**Step 3: Write minimal implementation**

Insert `Adapter Canonical Contract (2026 Guide Alignment)` section under adapter architecture and encode the required rules.

**Step 4: Run test to verify it passes**

Run: `uv run pytest skills/nt-implement/tests/ -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add skills/nt-implement/SKILL.md skills/nt-implement/tests/
git commit -m "docs: update nt-implement adapter contract requirements"
```

### Task 3: Add adapter review gate to nt-review

**Files:**
- Modify: `skills/nt-review/SKILL.md`
- Test: `skills/nt-review/tests/` (create if missing)

**Step 1: Write the failing test**

Add a content test requiring:
- `Adapter Review Gate (2026 Guide Alignment)` section
- blocker/major/minor severity model
- fail criteria for missing contracts/runtime/testing doctrine

**Step 2: Run test to verify it fails**

Run: `uv run pytest skills/nt-review/tests/ -v`
Expected: FAIL before doc update.

**Step 3: Write minimal implementation**

Add adapter-specific fail conditions and severity mapping to `skills/nt-review/SKILL.md`.

**Step 4: Run test to verify it passes**

Run: `uv run pytest skills/nt-review/tests/ -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add skills/nt-review/SKILL.md skills/nt-review/tests/
git commit -m "docs: add adapter review gates for 2026 guide alignment"
```

### Task 4: Add adapter-aware architecture constraints to nt-architect

**Files:**
- Modify: `skills/nt-architect/SKILL.md`
- Test: `skills/nt-architect/tests/` (create if missing)

**Step 1: Write the failing test**

Add a content test expecting:
- `Adapter-Aware Architecture Constraints (2026 Guide Alignment)`
- Rust/Python responsibility boundaries
- phase-to-validation mapping

**Step 2: Run test to verify it fails**

Run: `uv run pytest skills/nt-architect/tests/ -v`
Expected: FAIL before update.

**Step 3: Write minimal implementation**

Update `skills/nt-architect/SKILL.md` with adapter-specific architecture constraints and validation mapping.

**Step 4: Run test to verify it passes**

Run: `uv run pytest skills/nt-architect/tests/ -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add skills/nt-architect/SKILL.md skills/nt-architect/tests/
git commit -m "docs: add adapter-aware architecture constraints"
```

### Task 5: Add adapter wiring contract to nt-strategy-builder

**Files:**
- Modify: `skills/nt-strategy-builder/SKILL.md`
- Test: `skills/nt-strategy-builder/tests/`

**Step 1: Write the failing test**

Extend tests to assert:
- `Adapter Wiring Contract (2026 Guide Alignment)`
- prerequisite phase completion for live order flow
- reconciliation/report gating before production

**Step 2: Run test to verify it fails**

Run: `uv run pytest skills/nt-strategy-builder/tests/ -v`
Expected: FAIL before update.

**Step 3: Write minimal implementation**

Add wiring invariants and deployment-block rule to `skills/nt-strategy-builder/SKILL.md`.

**Step 4: Run test to verify it passes**

Run: `uv run pytest skills/nt-strategy-builder/tests/ -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add skills/nt-strategy-builder/SKILL.md skills/nt-strategy-builder/tests/
git commit -m "docs: enforce adapter wiring contract in strategy builder skill"
```

### Task 6: Cross-skill verification and consistency pass

**Files:**
- Modify: `docs/plans/2026-02-28-nt-skill-refresh-design.md` (if needed)
- Create: `docs/plans/2026-02-28-nt-skill-refresh-implementation.md` (this file)

**Step 1: Run markdown consistency checks**

Run:
- `rg -n "Adapter Canonical Contract|Guide Alignment|get_runtime\(\)\.spawn\(\)|Arc<PyObject>|condition-based" skills`

Expected: matching entries in all targeted skills.

**Step 2: Run targeted test suites**

Run:
- `uv run pytest skills/nt-dex-adapter/tests/ -v`
- `uv run pytest skills/nt-strategy-builder/tests/ -v`

Expected: PASS.

**Step 3: Run repo-level test sanity (if feasible)**

Run: `uv run pytest -q`
Expected: PASS or documented pre-existing failures.

**Step 4: Final commit**

```bash
git add docs/plans/2026-02-28-nt-skill-refresh-design.md docs/plans/2026-02-28-nt-skill-refresh-implementation.md skills/nt-dex-adapter/SKILL.md skills/nt-implement/SKILL.md skills/nt-review/SKILL.md skills/nt-architect/SKILL.md skills/nt-strategy-builder/SKILL.md
git commit -m "docs: refresh NautilusTrader skills for latest adapter guide"
```
