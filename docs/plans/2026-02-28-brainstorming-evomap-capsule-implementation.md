# Brainstorming EvoMap Capsule Wiring Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add bi-directional EvoMap Capsule wiring to the brainstorming workflow so sessions can publish design deltas and fetch refinement insights.

**Architecture:** Implement a thin gateway client for EvoMap A2A protocol, plus mapping and policy layers. Keep brainstorming as orchestration logic and route all network/protocol concerns through dedicated modules. Add deterministic IDs, retries, and graceful fallback to local-only mode.

**Tech Stack:** Python, requests/httpx (existing project preference), pytest, mock servers/fixtures, markdown plan artifacts.

---

### Task 1: Create EvoMap gateway module skeleton

**Files:**
- Create: `skills/brainstorming_evomap/evomap_capsule_client.py`
- Create: `skills/brainstorming_evomap/__init__.py`
- Test: `skills/brainstorming_evomap/tests/test_client_contract.py`

**Step 1: Write the failing test**

```python
def test_client_exposes_required_methods():
    from skills.brainstorming_evomap.evomap_capsule_client import EvoMapCapsuleClient
    client = EvoMapCapsuleClient(base_url="https://evomap.ai", api_key="x")
    for name in ["hello", "publish", "fetch", "report"]:
        assert hasattr(client, name)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest skills/brainstorming_evomap/tests/test_client_contract.py -v`
Expected: FAIL due missing module/class.

**Step 3: Write minimal implementation**

Add class with method stubs and constructor for base URL + auth.

**Step 4: Run test to verify it passes**

Run: `uv run pytest skills/brainstorming_evomap/tests/test_client_contract.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add skills/brainstorming_evomap/evomap_capsule_client.py skills/brainstorming_evomap/__init__.py skills/brainstorming_evomap/tests/test_client_contract.py
git commit -m "feat: scaffold evomap capsule client"
```

### Task 2: Implement A2A envelope builder and validation

**Files:**
- Create: `skills/brainstorming_evomap/envelope.py`
- Test: `skills/brainstorming_evomap/tests/test_envelope.py`

**Step 1: Write the failing test**

```python
def test_envelope_contains_required_fields():
    from skills.brainstorming_evomap.envelope import build_envelope
    msg = build_envelope(message_type="publish", sender_id="node_1", payload={"k": "v"})
    for key in ["protocol", "protocol_version", "message_type", "message_id", "sender_id", "timestamp", "payload"]:
        assert key in msg
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest skills/brainstorming_evomap/tests/test_envelope.py -v`
Expected: FAIL due missing function.

**Step 3: Write minimal implementation**

Implement deterministic envelope creation with protocol defaults: `gep-a2a`, version `1.0.0`.

**Step 4: Run test to verify it passes**

Run: `uv run pytest skills/brainstorming_evomap/tests/test_envelope.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add skills/brainstorming_evomap/envelope.py skills/brainstorming_evomap/tests/test_envelope.py
git commit -m "feat: add evomap a2a envelope builder"
```

### Task 3: Add capsule mapper for brainstorming artifacts

**Files:**
- Create: `skills/brainstorming_evomap/capsule_mapper.py`
- Test: `skills/brainstorming_evomap/tests/test_capsule_mapper.py`

**Step 1: Write the failing test**

```python
def test_mapper_builds_capsule_bundle_with_assets():
    from skills.brainstorming_evomap.capsule_mapper import map_section_delta
    bundle = map_section_delta(session_id="s1", section_id="architecture", content="text")
    assert "assets" in bundle and bundle["assets"]
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest skills/brainstorming_evomap/tests/test_capsule_mapper.py -v`
Expected: FAIL.

**Step 3: Write minimal implementation**

Implement mapper that emits bundle assets for Gene/Capsule/EvolutionEvent metadata.

**Step 4: Run test to verify it passes**

Run: `uv run pytest skills/brainstorming_evomap/tests/test_capsule_mapper.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add skills/brainstorming_evomap/capsule_mapper.py skills/brainstorming_evomap/tests/test_capsule_mapper.py
git commit -m "feat: map brainstorming deltas to capsule assets"
```

### Task 4: Add policy and fallback behavior

**Files:**
- Create: `skills/brainstorming_evomap/capsule_policy.py`
- Test: `skills/brainstorming_evomap/tests/test_capsule_policy.py`

**Step 1: Write the failing test**

```python
def test_policy_switches_to_local_only_after_retries_exhausted():
    from skills.brainstorming_evomap.capsule_policy import CapsulePolicy
    p = CapsulePolicy(max_failures=3)
    for _ in range(3):
        p.record_failure()
    assert p.local_only_mode is True
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest skills/brainstorming_evomap/tests/test_capsule_policy.py -v`
Expected: FAIL.

**Step 3: Write minimal implementation**

Implement failure counting, local-only toggle, and idempotency key helper.

**Step 4: Run test to verify it passes**

Run: `uv run pytest skills/brainstorming_evomap/tests/test_capsule_policy.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add skills/brainstorming_evomap/capsule_policy.py skills/brainstorming_evomap/tests/test_capsule_policy.py
git commit -m "feat: add capsule policy and fallback controls"
```

### Task 5: Integrate publish/fetch hooks into brainstorming flow

**Files:**
- Modify: `skills/brainstorming/SKILL.md`
- Create: `skills/brainstorming_evomap/brainstorming_hooks.py`
- Test: `skills/brainstorming_evomap/tests/test_hooks_flow.py`

**Step 1: Write the failing test**

```python
def test_hooks_execute_fetch_then_publish_then_fetch():
    from skills.brainstorming_evomap.brainstorming_hooks import run_section_cycle
    trace = run_section_cycle(session_id="s1", section="components")
    assert trace == ["fetch_pre", "publish_delta", "fetch_refine"]
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest skills/brainstorming_evomap/tests/test_hooks_flow.py -v`
Expected: FAIL.

**Step 3: Write minimal implementation**

Implement hook pipeline and update brainstorming guidance for bi-directional capsule checkpoints.

**Step 4: Run test to verify it passes**

Run: `uv run pytest skills/brainstorming_evomap/tests/test_hooks_flow.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add skills/brainstorming/SKILL.md skills/brainstorming_evomap/brainstorming_hooks.py skills/brainstorming_evomap/tests/test_hooks_flow.py
git commit -m "feat: wire brainstorming flow to evomap capsule hooks"
```

### Task 6: Integration tests for EvoMap lifecycle

**Files:**
- Create: `skills/brainstorming_evomap/tests/test_evomap_integration.py`
- Create: `skills/brainstorming_evomap/tests/fixtures/a2a_payloads.json`

**Step 1: Write the failing test**

```python
def test_end_to_end_publish_fetch_report_cycle(mock_server):
    from skills.brainstorming_evomap.evomap_capsule_client import EvoMapCapsuleClient
    c = EvoMapCapsuleClient(base_url=mock_server.url, api_key="k")
    assert c.hello()["ok"]
    assert c.publish({"assets": []})["ok"]
    assert "items" in c.fetch({"query": "brainstorming"})
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest skills/brainstorming_evomap/tests/test_evomap_integration.py -v`
Expected: FAIL.

**Step 3: Write minimal implementation**

Add request/response handling in client and fixture-backed mock responses.

**Step 4: Run test to verify it passes**

Run: `uv run pytest skills/brainstorming_evomap/tests/test_evomap_integration.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add skills/brainstorming_evomap/tests/test_evomap_integration.py skills/brainstorming_evomap/tests/fixtures/a2a_payloads.json skills/brainstorming_evomap/evomap_capsule_client.py
git commit -m "test: validate evomap a2a publish fetch report lifecycle"
```

### Task 7: Full verification and docs updates

**Files:**
- Modify: `docs/plans/2026-02-28-brainstorming-evomap-capsule-design.md` (if clarifications needed)
- Create: `docs/plans/2026-02-28-brainstorming-evomap-capsule-runbook.md`

**Step 1: Run targeted test suite**

Run: `uv run pytest skills/brainstorming_evomap/tests/ -v`
Expected: PASS.

**Step 2: Run broader project checks**

Run: `uv run pytest -q`
Expected: PASS or documented pre-existing unrelated failures.

**Step 3: Add runbook**

Document env vars, rollout flags, fallback behavior, and troubleshooting.

**Step 4: Final commit**

```bash
git add docs/plans/2026-02-28-brainstorming-evomap-capsule-design.md docs/plans/2026-02-28-brainstorming-evomap-capsule-runbook.md skills/brainstorming_evomap/
git commit -m "feat: add bi-directional evomap capsule wiring for brainstorming"
```
