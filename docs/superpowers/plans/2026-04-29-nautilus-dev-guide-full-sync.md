# NautilusTrader Developer Guide Full Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refresh this skill repository so its NautilusTrader developer-guide references, shared contracts, high-risk skills, and drift checks agree with the current official developer guide.

**Architecture:** Implement the sync in four independently reviewable layers: reference truth, canonical contracts, skill alignment, and validation. Add the static validation harness before changing content so every later phase has executable checks.

**Tech Stack:** Markdown skill/reference files, Python 3 standard library validation script, pytest tests run with `uv run --with pytest pytest`, Git semantic commits.

---

## File structure and responsibilities

### New validation files

- `tools/check_dev_guide_sync.py` — repository-local static drift checker. It validates required guide files, source metadata, stale local paths, stale setup wording, required invariant terms, and high-risk adapter/live/testing wording.
- `tests/test_dev_guide_sync.py` — pure pytest tests for the drift checker. Tests use temporary repositories so they do not depend on the repository being already fixed.

### New reference files

- `references/developer_guide/design_principles.md` — local mirror summary of official design principles, especially message immutability.
- `references/developer_guide/spec_data_testing.md` — local mirror summary of official Data Testing Spec.
- `references/developer_guide/spec_exec_testing.md` — local mirror summary of official Execution Testing Spec.
- `references/developer_guide/test_datasets.md` — local mirror summary of official Test Datasets guidance.
- `references/developer_guide/contracts/environment_tooling.md` — canonical environment/tooling contract.
- `references/developer_guide/contracts/testing_policy.md` — canonical testing policy contract.
- `references/developer_guide/contracts/adapter_contract.md` — canonical adapter implementation/review contract.
- `references/developer_guide/contracts/live_runtime_contract.md` — canonical live runtime v1/v2 contract.
- `references/developer_guide/contracts/design_principles.md` — canonical design-principles contract used by skills.

### Existing files to modify

- `references/developer_guide/index.md` — add missing official guide pages and contract links.
- `skills/nt-dev/SKILL.md` — update setup/tooling and contract references.
- `skills/nt-testing/SKILL.md` — add latest testing policy, DataTester/ExecTester evidence, PyO3 abort guidance, and correct reference paths.
- `skills/nt-adapters/SKILL.md` — align Rust HTTP/runtime examples and adapter contract references.
- `skills/nt-dex-adapter/SKILL.md` — align DEX canonical contract, InstrumentProvider defaults, command/request signatures, reconciliation requirements, and lifecycle gates.
- `skills/nt-dex-adapter/tests/test_dex_compliance.py` — strengthen structural checks for command/request signature names and reconciliation method set.
- `skills/nt-live/SKILL.md` — clarify `LiveNode` versus legacy `TradingNode` usage.
- `skills/nt-strategy-builder/SKILL.md` — reflect live-runtime contract and legacy labels.
- `skills/nt-review/SKILL.md` — add evidence gates for message immutability, testing policy, adapter reconciliation, and live runtime choice.
- `skills/nt-architect/SKILL.md` — add message immutability and contract-aware design checkpoints.
- `skills/nt-implement/SKILL.md` — add contract-aware implementation checkpoints.
- `skills/AGENTS.md` — update the skill inventory from 6 workflow skills to the current 16-skill map.
- `AGENTS.md` and `README.md` — update coverage and command notes only where they currently make stale claims.

---

## Task 1: Add drift-check test harness

**Files:**
- Create: `tests/test_dev_guide_sync.py`
- Create: `tools/check_dev_guide_sync.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_dev_guide_sync.py` with this content:

```python
from pathlib import Path

from tools.check_dev_guide_sync import CheckResult
from tools.check_dev_guide_sync import run_checks


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_reports_missing_required_guide_files(tmp_path: Path) -> None:
    write(tmp_path / "references/developer_guide/index.md", "# Developer Guide\n")

    result = run_checks(tmp_path)

    assert result.ok is False
    assert "missing required guide file: references/developer_guide/design_principles.md" in result.errors
    assert "missing required guide file: references/developer_guide/spec_data_testing.md" in result.errors
    assert "missing required guide file: references/developer_guide/spec_exec_testing.md" in result.errors
    assert "missing required guide file: references/developer_guide/test_datasets.md" in result.errors


def test_reports_missing_source_metadata(tmp_path: Path) -> None:
    for relative in [
        "references/developer_guide/design_principles.md",
        "references/developer_guide/spec_data_testing.md",
        "references/developer_guide/spec_exec_testing.md",
        "references/developer_guide/test_datasets.md",
    ]:
        write(tmp_path / relative, "# Guide\n\nNo metadata here.\n")

    result = run_checks(tmp_path)

    assert result.ok is False
    assert any("missing source metadata" in error for error in result.errors)


def test_reports_stale_references_guides_path(tmp_path: Path) -> None:
    write(
        tmp_path / "skills/nt-testing/SKILL.md",
        "Read references/guides/spec_data_testing.md before testing.\n",
    )

    result = run_checks(tmp_path)

    assert result.ok is False
    assert "stale references/guides path in skills/nt-testing/SKILL.md" in result.errors


def test_reports_unqualified_pre_commit_install(tmp_path: Path) -> None:
    write(tmp_path / "skills/nt-dev/SKILL.md", "Run pre-commit install during setup.\n")

    result = run_checks(tmp_path)

    assert result.ok is False
    assert "unqualified pre-commit install in skills/nt-dev/SKILL.md" in result.errors


def test_reports_missing_required_invariants(tmp_path: Path) -> None:
    write(tmp_path / "skills/nt-live/SKILL.md", "# Live\n")
    write(tmp_path / "skills/nt-testing/SKILL.md", "# Testing\n")
    write(tmp_path / "skills/nt-adapters/SKILL.md", "# Adapters\n")
    write(tmp_path / "skills/nt-architect/SKILL.md", "# Architect\n")

    result = run_checks(tmp_path)

    assert result.ok is False
    assert "missing invariant 'LiveNode' in skills/nt-live/SKILL.md" in result.errors
    assert "missing invariant 'DataTester' in skills/nt-testing/SKILL.md" in result.errors
    assert "missing invariant 'ExecTester' in skills/nt-testing/SKILL.md" in result.errors
    assert "missing invariant 'nautilus_network::http::HttpClient' in skills/nt-adapters/SKILL.md" in result.errors
    assert "missing invariant 'message immutability' in skills/nt-architect/SKILL.md" in result.errors


def test_success_when_required_files_metadata_paths_and_invariants_exist(tmp_path: Path) -> None:
    metadata = """---
source_url: https://nautilustrader.io/docs/latest/developer_guide/design_principles/
source_repo: nautechsystems/nautilus_trader/docs/developer_guide/design_principles.md
sync_date: 2026-04-29
target: latest developer guide
confidence: high
---
"""
    for name in [
        "design_principles.md",
        "spec_data_testing.md",
        "spec_exec_testing.md",
        "test_datasets.md",
    ]:
        write(tmp_path / "references/developer_guide" / name, metadata + f"# {name}\n")

    write(tmp_path / "skills/nt-live/SKILL.md", "Prefer LiveNode; label TradingNode legacy.\n")
    write(tmp_path / "skills/nt-testing/SKILL.md", "Use DataTester and ExecTester evidence.\n")
    write(tmp_path / "skills/nt-adapters/SKILL.md", "Use nautilus_network::http::HttpClient and get_runtime().spawn().\n")
    write(tmp_path / "skills/nt-architect/SKILL.md", "Preserve message immutability in designs.\n")

    result = run_checks(tmp_path)

    assert result == CheckResult(ok=True, errors=[])
```

- [ ] **Step 2: Run tests to verify they fail because the checker does not exist**

Run:

```bash
uv run --with pytest pytest tests/test_dev_guide_sync.py -q
```

Expected: FAIL during import with `ModuleNotFoundError: No module named 'tools'` or `No module named 'tools.check_dev_guide_sync'`.

- [ ] **Step 3: Add the minimal checker implementation**

Create `tools/check_dev_guide_sync.py` with this content:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


REQUIRED_GUIDE_FILES = [
    Path("references/developer_guide/design_principles.md"),
    Path("references/developer_guide/spec_data_testing.md"),
    Path("references/developer_guide/spec_exec_testing.md"),
    Path("references/developer_guide/test_datasets.md"),
]

METADATA_KEYS = ["source_url:", "source_repo:", "sync_date:", "target:", "confidence:"]

INVARIANT_TARGETS = {
    Path("skills/nt-live/SKILL.md"): ["LiveNode"],
    Path("skills/nt-testing/SKILL.md"): ["DataTester", "ExecTester"],
    Path("skills/nt-adapters/SKILL.md"): [
        "nautilus_network::http::HttpClient",
        "get_runtime().spawn()",
    ],
    Path("skills/nt-architect/SKILL.md"): ["message immutability"],
}


@dataclass(frozen=True)
class CheckResult:
    ok: bool
    errors: list[str]


def _iter_markdown_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.md") if ".git" not in path.parts)


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def run_checks(root: Path) -> CheckResult:
    errors: list[str] = []

    for relative in REQUIRED_GUIDE_FILES:
        absolute = root / relative
        if not absolute.exists():
            errors.append(f"missing required guide file: {relative.as_posix()}")
            continue
        text = _read(absolute)
        missing_keys = [key for key in METADATA_KEYS if key not in text]
        if missing_keys:
            errors.append(
                f"missing source metadata in {relative.as_posix()}: {', '.join(missing_keys)}"
            )

    for markdown_file in _iter_markdown_files(root):
        text = _read(markdown_file)
        relative = _relative(markdown_file, root)
        if "references/guides/" in text:
            errors.append(f"stale references/guides path in {relative}")
        if "pre-commit install" in text and "prek install" not in text:
            errors.append(f"unqualified pre-commit install in {relative}")

    for relative, required_terms in INVARIANT_TARGETS.items():
        absolute = root / relative
        if not absolute.exists():
            continue
        text = _read(absolute)
        for term in required_terms:
            if term not in text:
                errors.append(f"missing invariant '{term}' in {relative.as_posix()}")

    return CheckResult(ok=not errors, errors=errors)


def main() -> int:
    result = run_checks(Path.cwd())
    if result.ok:
        print("Developer guide sync checks passed.")
        return 0
    print("Developer guide sync checks failed:")
    for error in result.errors:
        print(f"- {error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests to verify the checker passes its isolated tests**

Run:

```bash
uv run --with pytest pytest tests/test_dev_guide_sync.py -q
```

Expected: PASS for all tests in `tests/test_dev_guide_sync.py`.

- [ ] **Step 5: Run the checker against the current repository to capture RED state**

Run:

```bash
uv run python tools/check_dev_guide_sync.py
```

Expected: FAIL with actionable messages for missing required guide files, stale paths, missing metadata, or missing invariants. This failure is expected before Tasks 2-5.

- [ ] **Step 6: Commit the validation harness**

```bash
GIT_MASTER=1 git add tests/test_dev_guide_sync.py tools/check_dev_guide_sync.py
GIT_MASTER=1 git commit -m "test: add developer guide sync drift checks" -m "Ultraworked with [Sisyphus](https://github.com/code-yeongyu/oh-my-openagent)" -m "Co-authored-by: Sisyphus <clio-agent@sisyphuslabs.ai>"
```

---

## Task 2: Add missing developer-guide reference files

**Files:**
- Create: `references/developer_guide/design_principles.md`
- Create: `references/developer_guide/spec_data_testing.md`
- Create: `references/developer_guide/spec_exec_testing.md`
- Create: `references/developer_guide/test_datasets.md`
- Modify: `references/developer_guide/index.md`

- [ ] **Step 1: Write the RED check for required guide files**

Run:

```bash
uv run python tools/check_dev_guide_sync.py
```

Expected: FAIL with missing-file errors for the four files listed above.

- [ ] **Step 2: Create `design_principles.md`**

Write `references/developer_guide/design_principles.md`:

```markdown
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
```

- [ ] **Step 3: Create `spec_data_testing.md`**

Write `references/developer_guide/spec_data_testing.md`:

```markdown
---
source_url: https://nautilustrader.io/docs/latest/developer_guide/spec_data_testing/
source_repo: nautechsystems/nautilus_trader/docs/developer_guide/spec_data_testing.md
sync_date: 2026-04-29
target: latest developer guide
confidence: high
---

# Data Testing Spec

The Data Testing Spec defines acceptance evidence for market-data adapters and
data clients. Agent work should not treat method presence as sufficient for data
adapter readiness.

## Required evidence themes

- Subscription and unsubscription behavior for supported data types.
- Correct conversion from venue payloads into Nautilus data objects.
- Instrument cache interaction before live subscriptions depend on instruments.
- Condition-based async waits instead of fixed sleeps in tests.
- Realistic fixtures for venue payloads, including malformed or partial payloads
  where the adapter claims to handle them.

## Agent checklist

- Use DataTester or the official data tester pattern when the adapter surface is
  compatible with it.
- Require concrete data-type coverage instead of generic adapter smoke tests.
- Pair data-client behavior changes with tests that prove the emitted Nautilus
  object fields, timestamps, and identifiers.
```

- [ ] **Step 4: Create `spec_exec_testing.md`**

Write `references/developer_guide/spec_exec_testing.md`:

```markdown
---
source_url: https://nautilustrader.io/docs/latest/developer_guide/spec_exec_testing/
source_repo: nautechsystems/nautilus_trader/docs/developer_guide/spec_exec_testing.md
sync_date: 2026-04-29
target: latest developer guide
confidence: high
---

# Execution Testing Spec

The Execution Testing Spec defines acceptance evidence for execution adapters and
execution clients. Agent work should prove order submission, cancellation,
modification, reconciliation, and status-report behavior before claiming live
readiness.

## Required evidence themes

- Submit, cancel, cancel-all, modify, and query command handling.
- Order status reports, fill reports, position status reports, and mass status
  generation where required by the official adapter contract.
- Startup reconciliation and account-state emission before connected state is
  announced.
- Rejection, timeout, and venue error mapping into safe Nautilus behavior.

## Agent checklist

- Use ExecTester or the official execution tester pattern when available.
- Require reconciliation report coverage for production adapters.
- Do not mark execution adapters ready when only structural method presence is
  tested.
```

- [ ] **Step 5: Create `test_datasets.md`**

Write `references/developer_guide/test_datasets.md`:

```markdown
---
source_url: https://nautilustrader.io/docs/latest/developer_guide/test_datasets/
source_repo: nautechsystems/nautilus_trader/docs/developer_guide/test_datasets.md
sync_date: 2026-04-29
target: latest developer guide
confidence: high
---

# Test Datasets

Test datasets should make adapter and system tests reproducible without hiding
network, license, or freshness assumptions.

## Dataset standards

- Keep fixture data small enough for repository tests unless the dataset is
  explicitly documented as external.
- Document source, license, generation command, and refresh date for fetched or
  generated datasets.
- Skip tests with clear reasons when external datasets are intentionally absent.
- Prefer deterministic local fixtures for unit tests and reserve large datasets
  for integration or acceptance runs.

## Agent checklist

- Do not fetch large datasets implicitly during normal unit tests.
- Add metadata beside generated fixtures.
- Keep dataset-dependent tests serializable when shared caches or file paths are
  involved.
```

- [ ] **Step 6: Update `references/developer_guide/index.md`**

Add these entries under `## Contents` after Coding Standards and Testing as appropriate:

```markdown
- [Design Principles](design_principles.md)
- [Data Testing Spec](spec_data_testing.md)
- [Execution Testing Spec](spec_exec_testing.md)
- [Test Datasets](test_datasets.md)
```

Also add this subsection after the contents list:

```markdown
## Local Contracts

- [Environment Tooling Contract](contracts/environment_tooling.md)
- [Testing Policy Contract](contracts/testing_policy.md)
- [Adapter Contract](contracts/adapter_contract.md)
- [Live Runtime Contract](contracts/live_runtime_contract.md)
- [Design Principles Contract](contracts/design_principles.md)
```

- [ ] **Step 7: Run the checker**

Run:

```bash
uv run python tools/check_dev_guide_sync.py
```

Expected: the four missing-file errors are gone. Other failures remain until later tasks.

- [ ] **Step 8: Commit the reference files**

```bash
GIT_MASTER=1 git add references/developer_guide/design_principles.md references/developer_guide/spec_data_testing.md references/developer_guide/spec_exec_testing.md references/developer_guide/test_datasets.md references/developer_guide/index.md
GIT_MASTER=1 git commit -m "docs: add missing developer guide references" -m "Ultraworked with [Sisyphus](https://github.com/code-yeongyu/oh-my-openagent)" -m "Co-authored-by: Sisyphus <clio-agent@sisyphuslabs.ai>"
```

---

## Task 3: Add canonical developer-guide contracts

**Files:**
- Create: `references/developer_guide/contracts/environment_tooling.md`
- Create: `references/developer_guide/contracts/testing_policy.md`
- Create: `references/developer_guide/contracts/adapter_contract.md`
- Create: `references/developer_guide/contracts/live_runtime_contract.md`
- Create: `references/developer_guide/contracts/design_principles.md`

- [ ] **Step 1: Create contracts directory and environment tooling contract**

Write `references/developer_guide/contracts/environment_tooling.md`:

```markdown
# Environment Tooling Contract

Sources:

- `references/developer_guide/environment_setup.md`
- Official developer guide environment setup page

## Required guidance

- Use `uv` for Python environment and command execution in this skill repo.
- For NautilusTrader core setup, prefer the official latest setup path:
  `make install-tools`, pinned tools from `tools.toml`, and `prek install`.
- Preserve command names that are still official make targets, even when they
  include the phrase `pre-commit`.

## Review rule

Unqualified setup instructions that say only `pre-commit install` are stale. Use
`prek install` or explain that a legacy repository still requires pre-commit.
```

- [ ] **Step 2: Create testing policy contract**

Write `references/developer_guide/contracts/testing_policy.md`:

```markdown
# Testing Policy Contract

Sources:

- `references/developer_guide/testing.md`
- `references/developer_guide/spec_data_testing.md`
- `references/developer_guide/spec_exec_testing.md`
- `references/developer_guide/test_datasets.md`

## Required guidance

- Choose the smallest test mechanism that proves the production behavior.
- Use DataTester evidence for data adapter behavior when the adapter surface is
  compatible with the official data tester pattern.
- Use ExecTester evidence for execution adapter behavior when the adapter surface
  is compatible with the official execution tester pattern.
- Isolate PyO3 panic/abort behavior in subprocess-style tests when a failure
  would abort the interpreter.
- Keep unit tests deterministic and avoid implicit network or dataset downloads.

## Review rule

Structural method presence is not enough for production readiness. Adapter and
live-runtime claims need behavior evidence, fixtures, or explicit unsupported
scope labels.
```

- [ ] **Step 3: Create adapter contract**

Write `references/developer_guide/contracts/adapter_contract.md`:

```markdown
# Adapter Contract

Sources:

- `references/developer_guide/adapters.md`
- `references/developer_guide/spec_data_testing.md`
- `references/developer_guide/spec_exec_testing.md`

## Required guidance

- Keep Rust-core and Python-integration boundaries explicit.
- Use `nautilus_network::http::HttpClient` for Rust HTTP client examples unless
  official source evidence requires another client.
- Use `get_runtime().spawn()` for Python-runtime-sensitive async Rust paths; do
  not teach `tokio::spawn()` as the default from Python-driven adapter code.
- Align Python adapter methods with current command/request object signatures.
- Treat `InstrumentProvider.load_all_async()` as the required load method for
  current v1.224-era guidance; override targeted load methods only for venue
  semantics or efficiency.
- Require order status reports, fill reports, position status reports, and mass
  status generation where the official execution client contract requires them.

## Review rule

An adapter is not ready when it only has provider/data/exec class shells. It must
prove command handling, subscriptions, reconciliation, account state, and factory
wiring for the claimed venue scope.
```

- [ ] **Step 4: Create live runtime contract**

Write `references/developer_guide/contracts/live_runtime_contract.md`:

```markdown
# Live Runtime Contract

Sources:

- `references/concepts/live.md`
- Official developer guide testing and adapter pages

## Required guidance

- Prefer `nautilus_trader.live.LiveNode` for new Rust-backed PyO3 adapter and v2
  live-runtime examples.
- Treat `nautilus_trader.live.node.TradingNode` as legacy v1/Cython-oriented
  guidance unless the skill is documenting an existing integration that still
  uses it.
- Keep reconciliation enabled for production live execution unless a documented
  adapter limitation makes it impossible.
- Refresh account state and satisfy startup reconciliation before announcing a
  production live client as connected.

## Review rule

Unqualified “use TradingNode” guidance in new adapter work is stale. Either use
`LiveNode` or label the example as legacy/integration-specific.
```

- [ ] **Step 5: Create design principles contract**

Write `references/developer_guide/contracts/design_principles.md`:

```markdown
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
```

- [ ] **Step 6: Run the checker**

Run:

```bash
uv run python tools/check_dev_guide_sync.py
```

Expected: contract creation does not add new failures. Existing skill-alignment failures may remain.

- [ ] **Step 7: Commit the contracts**

```bash
GIT_MASTER=1 git add references/developer_guide/contracts
GIT_MASTER=1 git commit -m "docs: add developer guide sync contracts" -m "Ultraworked with [Sisyphus](https://github.com/code-yeongyu/oh-my-openagent)" -m "Co-authored-by: Sisyphus <clio-agent@sisyphuslabs.ai>"
```

---

## Task 4: Align developer and testing skills

**Files:**
- Modify: `skills/nt-dev/SKILL.md`
- Modify: `skills/nt-testing/SKILL.md`

- [ ] **Step 1: Run RED checks for stale paths and setup wording**

Run:

```bash
uv run python tools/check_dev_guide_sync.py
```

Expected: FAIL if `skills/nt-dev/SKILL.md` contains unqualified `pre-commit install`, if either skill references `references/guides/*`, or if testing invariants are missing.

- [ ] **Step 2: Update `skills/nt-dev/SKILL.md` environment setup section**

Replace stale setup bullets that say to run `pre-commit install` directly with this guidance:

```markdown
### Environment setup contract

Follow `references/developer_guide/contracts/environment_tooling.md` before
changing setup instructions.

For current NautilusTrader core development:

```bash
uv sync --active --all-groups --all-extras
make install-tools
prek install
```

Use `prek install` for hook installation. Keep official make target names that
still include `pre-commit`, but do not present `pre-commit install` as the
current default unless the target repository explicitly remains on legacy
pre-commit tooling.
```

If the file has a references section containing `references/guides/`, replace those paths with `references/developer_guide/` paths.

- [ ] **Step 3: Update `skills/nt-testing/SKILL.md` testing policy section**

Add this section near the top of the skill workflow:

```markdown
## Current testing policy contract

Read `references/developer_guide/contracts/testing_policy.md` before designing
adapter, live-runtime, or PyO3 tests.

Required testing rules:

- Choose the smallest mechanism that proves the production behavior.
- Use DataTester evidence for compatible data adapter behavior.
- Use ExecTester evidence for compatible execution adapter behavior.
- Do not treat method presence as production readiness.
- Isolate PyO3 panic or abort paths in subprocess-style tests when the failure
  can terminate the interpreter.
- Keep unit tests deterministic and do not implicitly download datasets.
```

Replace stale `references/guides/spec_data_testing.md`, `references/guides/spec_exec_testing.md`, and `references/guides/test_datasets.md` references with:

```markdown
- `references/developer_guide/spec_data_testing.md`
- `references/developer_guide/spec_exec_testing.md`
- `references/developer_guide/test_datasets.md`
- `references/developer_guide/contracts/testing_policy.md`
```

- [ ] **Step 4: Run focused checks**

Run:

```bash
uv run python tools/check_dev_guide_sync.py
uv run --with pytest pytest tests/test_dev_guide_sync.py -q
```

Expected: no failures related to `skills/nt-dev/SKILL.md` setup wording, `skills/nt-testing/SKILL.md` stale paths, DataTester, or ExecTester.

- [ ] **Step 5: Commit developer/testing alignment**

```bash
GIT_MASTER=1 git add skills/nt-dev/SKILL.md skills/nt-testing/SKILL.md
GIT_MASTER=1 git commit -m "docs: align developer and testing skills with guide contracts" -m "Ultraworked with [Sisyphus](https://github.com/code-yeongyu/oh-my-openagent)" -m "Co-authored-by: Sisyphus <clio-agent@sisyphuslabs.ai>"
```

---

## Task 5: Align adapter and DEX skills plus DEX compliance tests

**Files:**
- Modify: `skills/nt-adapters/SKILL.md`
- Modify: `skills/nt-dex-adapter/SKILL.md`
- Modify: `skills/nt-dex-adapter/tests/test_dex_compliance.py`

- [ ] **Step 1: Add RED compliance tests for current adapter expectations**

Modify `skills/nt-dex-adapter/tests/test_dex_compliance.py` imports:

```python
from inspect import signature
```

Add this test class after `TestExecutionClientInterface`:

```python
class TestOfficialAdapterContractNames:
    """Checks template signatures mention current command/request object names."""

    DATA_COMMAND_METHODS = {
        "_subscribe_quote_ticks": "command",
        "_subscribe_trade_ticks": "command",
        "_subscribe_order_book_deltas": "command",
        "_unsubscribe_quote_ticks": "command",
        "_unsubscribe_trade_ticks": "command",
        "_unsubscribe_order_book_deltas": "command",
        "_request_bars": "request",
    }

    EXEC_COMMAND_METHODS = {
        "_submit_order": "command",
        "_cancel_order": "command",
        "_cancel_all_orders": "command",
        "_modify_order": "command",
        "_query_order": "command",
    }

    @pytest.mark.parametrize(("method", "expected_param"), DATA_COMMAND_METHODS.items())
    def test_data_client_uses_command_or_request_parameter(self, method, expected_param):
        params = signature(getattr(MyDEXDataClient, method)).parameters
        assert expected_param in params, f"{method} should accept {expected_param}"

    @pytest.mark.parametrize(("method", "expected_param"), EXEC_COMMAND_METHODS.items())
    def test_exec_client_uses_command_parameter(self, method, expected_param):
        params = signature(getattr(MyDEXExecutionClient, method)).parameters
        assert expected_param in params, f"{method} should accept {expected_param}"

    @pytest.mark.parametrize(
        "method",
        [
            "generate_order_status_report",
            "generate_order_status_reports",
            "generate_fill_reports",
            "generate_position_status_reports",
            "generate_mass_status",
        ],
    )
    def test_full_execution_reconciliation_method_set_exists(self, method):
        assert hasattr(MyDEXExecutionClient, method), f"Missing: {method}"
        assert iscoroutinefunction(getattr(MyDEXExecutionClient, method)), f"Not async: {method}"
```

- [ ] **Step 2: Run the RED DEX compliance test**

Run:

```bash
uv run --with pytest pytest skills/nt-dex-adapter/tests/test_dex_compliance.py -q
```

Expected: FAIL until DEX templates and/or guidance are updated. If imports fail because NautilusTrader dependencies are absent, record the import failure and continue with static checker verification for this task.

- [ ] **Step 3: Update `skills/nt-adapters/SKILL.md` adapter contract section**

Add or replace the canonical adapter rule block with:

```markdown
## Current adapter contract

Read `references/developer_guide/contracts/adapter_contract.md` before creating
or reviewing adapter code.

Current high-risk rules:

- Use `nautilus_network::http::HttpClient` in Rust HTTP examples.
- Use `get_runtime().spawn()` for Python-runtime-sensitive async Rust paths;
  do not teach `tokio::spawn()` as the default from Python-driven adapter code.
- Keep Python data and execution client methods aligned with current
  command/request object signatures.
- Treat `InstrumentProvider.load_all_async()` as the required v1.224-era method;
  override targeted methods only for venue-specific semantics or efficiency.
- Require data tester and execution tester evidence for adapter readiness.
```

Replace any example struct that teaches `reqwest::Client` as the primary adapter HTTP client with `nautilus_network::http::HttpClient`. Replace any default recommendation to use `tokio::spawn()` from Python-driven adapter paths with `get_runtime().spawn()`.

- [ ] **Step 4: Update `skills/nt-dex-adapter/SKILL.md` DEX contract section**

Add or replace the DEX canonical contract block with:

```markdown
## Adapter canonical contract

Read `references/developer_guide/contracts/adapter_contract.md` and
`references/developer_guide/contracts/testing_policy.md` before claiming a DEX
adapter is ready.

DEX adapter readiness requires:

- provider/data/execution methods aligned to current Nautilus command/request
  object signatures;
- `InstrumentProvider.load_all_async()` implemented, with targeted load methods
  overridden only for DEX-specific semantics or efficiency;
- data connect lifecycle: bootstrap instruments, cache instruments, emit
  instruments, prepare WebSocket cache, then connect subscriptions;
- execution connect lifecycle: initialize instruments, connect private stream,
  subscribe, refresh account state, wait for account registration, then mark
  connected;
- reconciliation coverage for order status reports, fill reports, position
  status reports, and mass status where supported by the venue;
- DataTester and ExecTester or equivalent acceptance evidence.
```

- [ ] **Step 5: Update DEX templates if present signatures are stale**

If `skills/nt-dex-adapter/templates/dex_data_client.py` has methods like `_subscribe_quote_ticks(self, instrument_id: InstrumentId)`, change them to command/request style, for example:

```python
async def _subscribe_quote_ticks(self, command: SubscribeQuoteTicks) -> None:
    instrument_id = command.instrument_id
    await self._subscribe_pool_quotes(instrument_id)
```

If `skills/nt-dex-adapter/templates/dex_exec_client.py` has methods like `_submit_order(self, order: Order)`, change them to command style, for example:

```python
async def _submit_order(self, command: SubmitOrder) -> None:
    order = command.order
    await self._submit_signed_order(order)
```

Add async reconciliation stubs that fail safe rather than claiming fabricated state:

```python
async def generate_order_status_reports(self, *args, **kwargs):
    return []


async def generate_fill_reports(self, *args, **kwargs):
    return []


async def generate_position_status_reports(self, *args, **kwargs):
    return []


async def generate_mass_status(self, *args, **kwargs):
    return None
```

- [ ] **Step 6: Run adapter checks**

Run:

```bash
uv run python tools/check_dev_guide_sync.py
uv run --with pytest pytest tests/test_dev_guide_sync.py -q
uv run --with pytest pytest skills/nt-dex-adapter/tests/test_dex_compliance.py -q
```

Expected: drift checker passes adapter invariants. DEX compliance passes if NautilusTrader template dependencies are importable; otherwise, the only acceptable failure is an environment import failure unrelated to the edited assertions.

- [ ] **Step 7: Commit adapter alignment**

```bash
GIT_MASTER=1 git add skills/nt-adapters/SKILL.md skills/nt-dex-adapter/SKILL.md skills/nt-dex-adapter/templates/dex_data_client.py skills/nt-dex-adapter/templates/dex_exec_client.py skills/nt-dex-adapter/tests/test_dex_compliance.py
GIT_MASTER=1 git commit -m "docs: align adapter skills with guide contracts" -m "Ultraworked with [Sisyphus](https://github.com/code-yeongyu/oh-my-openagent)" -m "Co-authored-by: Sisyphus <clio-agent@sisyphuslabs.ai>"
```

---

## Task 6: Align live runtime, architecture, implementation, and review skills

**Files:**
- Modify: `skills/nt-live/SKILL.md`
- Modify: `skills/nt-strategy-builder/SKILL.md`
- Modify: `skills/nt-review/SKILL.md`
- Modify: `skills/nt-architect/SKILL.md`
- Modify: `skills/nt-implement/SKILL.md`

- [ ] **Step 1: Run RED drift checks**

Run:

```bash
uv run python tools/check_dev_guide_sync.py
```

Expected: FAIL if `LiveNode` or `message immutability` invariants are missing from target skills.

- [ ] **Step 2: Update `skills/nt-live/SKILL.md`**

Add this section before examples that use `TradingNode`:

```markdown
## Live runtime contract

Read `references/developer_guide/contracts/live_runtime_contract.md` before
choosing a live runtime.

- Prefer `nautilus_trader.live.LiveNode` for new Rust-backed PyO3 adapter and v2
  live-runtime examples.
- Treat `nautilus_trader.live.node.TradingNode` examples as legacy v1/Cython or
  integration-specific unless the current official adapter docs say otherwise.
- Keep reconciliation enabled for production execution clients unless a venue
  limitation is documented and reviewed.
```

Label existing `TradingNode` examples with: `Legacy v1/Cython-oriented example`.

- [ ] **Step 3: Update `skills/nt-strategy-builder/SKILL.md`**

Add this live wiring note near the decision tree:

```markdown
### Live runtime selection

For new Rust-backed PyO3 adapters, start from the `LiveNode` path described in
`references/developer_guide/contracts/live_runtime_contract.md`. Use
`TradingNode` only for legacy v1/Cython integrations or existing examples that
are explicitly still built on that runtime.
```

- [ ] **Step 4: Update `skills/nt-architect/SKILL.md`**

Add this design invariant near the architecture checklist:

```markdown
### Design principles invariant

Preserve message immutability across actor, strategy, adapter, cache, and
message-bus boundaries. Design components to publish new messages or state
transitions rather than mutating events, commands, requests, or responses after
publication. See `references/developer_guide/contracts/design_principles.md`.
```

- [ ] **Step 5: Update `skills/nt-implement/SKILL.md`**

Add this implementation checkpoint near component templates:

```markdown
### Contract-aware implementation checkpoint

Before writing implementation code, check the relevant contract:

- environment/tooling: `references/developer_guide/contracts/environment_tooling.md`
- testing: `references/developer_guide/contracts/testing_policy.md`
- adapters: `references/developer_guide/contracts/adapter_contract.md`
- live runtime: `references/developer_guide/contracts/live_runtime_contract.md`
- design principles: `references/developer_guide/contracts/design_principles.md`

Do not mutate published Nautilus messages in place; preserve message immutability
unless an official source explicitly documents a local mutable builder pattern.
```

- [ ] **Step 6: Update `skills/nt-review/SKILL.md`**

Add this review gate near the pre-deployment checklist:

```markdown
### Developer guide sync review gates

Block production-readiness claims unless review evidence covers:

- message immutability across published events, commands, requests, and
  responses;
- DataTester or equivalent evidence for claimed data adapter behavior;
- ExecTester or equivalent evidence for claimed execution adapter behavior;
- complete adapter reconciliation reports for claimed live execution scope;
- `LiveNode` use for new Rust-backed PyO3 adapter paths, or an explicit legacy
  label for `TradingNode` examples;
- environment setup that uses current `prek`/`make install-tools` guidance.
```

- [ ] **Step 7: Run checks**

Run:

```bash
uv run python tools/check_dev_guide_sync.py
uv run --with pytest pytest tests/test_dev_guide_sync.py -q
```

Expected: no failures for `LiveNode`, `message immutability`, or other invariant terms.

- [ ] **Step 8: Commit live/architecture/review alignment**

```bash
GIT_MASTER=1 git add skills/nt-live/SKILL.md skills/nt-strategy-builder/SKILL.md skills/nt-review/SKILL.md skills/nt-architect/SKILL.md skills/nt-implement/SKILL.md
GIT_MASTER=1 git commit -m "docs: align live and review skills with guide contracts" -m "Ultraworked with [Sisyphus](https://github.com/code-yeongyu/oh-my-openagent)" -m "Co-authored-by: Sisyphus <clio-agent@sisyphuslabs.ai>"
```

---

## Task 7: Update repository inventory and coverage claims

**Files:**
- Modify: `skills/AGENTS.md`
- Modify: `AGENTS.md`
- Modify: `README.md`

- [ ] **Step 1: Verify current skill count**

Run:

```bash
python - <<'PY'
from pathlib import Path
skills = sorted(path.parent.name for path in Path('skills').glob('*/SKILL.md'))
print(len(skills))
print('\n'.join(skills))
PY
```

Expected: prints `16` and the current skill directory names.

- [ ] **Step 2: Replace `skills/AGENTS.md` inventory header**

Replace line `6 specialized skills for NautilusTrader development. Follow the workflow sequence.` with:

```markdown
16 specialized skills for NautilusTrader development. Use workflow skills for
architecture, implementation, wiring, and review; use domain skills for focused
NautilusTrader concepts; use developer-guide skills for setup and testing.
```

Replace the skill index table with rows for all 16 skills:

```markdown
| Skill | Purpose | Entry Point |
|-------|---------|-------------|
| **nt-architect** | Decompose systems into Actor/Indicator/Strategy architecture | `nt-architect/SKILL.md` |
| **nt-implement** | Implement NautilusTrader components from templates | `nt-implement/SKILL.md` |
| **nt-review** | Review code before deployment | `nt-review/SKILL.md` |
| **nt-strategy-builder** | Wire backtest, paper, and live systems | `nt-strategy-builder/SKILL.md` |
| **nt-dex-adapter** | Build custom DEX adapters | `nt-dex-adapter/SKILL.md` |
| **nt-evomap-integration** | Integrate EvoMap advisory sidecars safely | `nt-evomap-integration/SKILL.md` |
| **nt-trading** | Orders, events, positions, and portfolio concepts | `nt-trading/SKILL.md` |
| **nt-signals** | Indicators, order books, and signal analysis | `nt-signals/SKILL.md` |
| **nt-data** | Market data types, subscriptions, and catalogs | `nt-data/SKILL.md` |
| **nt-backtest** | Backtest engine, venues, actors, and fill models | `nt-backtest/SKILL.md` |
| **nt-live** | Live trading, runtime selection, adapters, reconciliation | `nt-live/SKILL.md` |
| **nt-adapters** | CeFi adapter specification and production patterns | `nt-adapters/SKILL.md` |
| **nt-model** | Instruments, identifiers, and value objects | `nt-model/SKILL.md` |
| **nt-dev** | Developer guide alignment, setup, FFI, benchmarking | `nt-dev/SKILL.md` |
| **nt-testing** | Testing policy, DataTester, ExecTester, datasets | `nt-testing/SKILL.md` |
| **nt-learn** | Structured NautilusTrader learning curriculum | `nt-learn/SKILL.md` |
```

- [ ] **Step 3: Update top-level coverage claims if stale**

In `README.md` and `AGENTS.md`, ensure developer-guide coverage claims do not say “full reference” for pages that are intentionally summarized. Use this wording where needed:

```markdown
Current developer-guide sync status is verified by `tools/check_dev_guide_sync.py`.
Local references summarize official pages and include source metadata; skills use
canonical contracts under `references/developer_guide/contracts/` for
agent-actionable rules.
```

- [ ] **Step 4: Run checks**

Run:

```bash
uv run python tools/check_dev_guide_sync.py
uv run --with pytest pytest tests/test_dev_guide_sync.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit inventory updates**

```bash
GIT_MASTER=1 git add skills/AGENTS.md AGENTS.md README.md
GIT_MASTER=1 git commit -m "docs: update skill inventory and guide coverage claims" -m "Ultraworked with [Sisyphus](https://github.com/code-yeongyu/oh-my-openagent)" -m "Co-authored-by: Sisyphus <clio-agent@sisyphuslabs.ai>"
```

---

## Task 8: Document and verify the final sync workflow

**Files:**
- Modify: `README.md`
- Modify: `docs/superpowers/specs/2026-04-29-nautilus-dev-guide-full-sync-design.md` only if implementation discoveries require a spec correction

- [ ] **Step 1: Add the validation command to `README.md`**

Add this section near the existing command or developer-guide coverage area:

```markdown
## Developer Guide Sync Verification

Run the static drift checks after changing references, contracts, or skills:

```bash
uv run python tools/check_dev_guide_sync.py
uv run --with pytest pytest tests/test_dev_guide_sync.py -q
```

The checker validates required local developer-guide pages, source metadata,
stale reference paths, and high-risk NautilusTrader invariants used by the skill
suite.
```

- [ ] **Step 2: Run full available verification**

Run:

```bash
uv run python tools/check_dev_guide_sync.py
uv run --with pytest pytest tests/test_dev_guide_sync.py -q
uv run --with pytest pytest skills/nt-dex-adapter/tests/test_dex_compliance.py -q
```

Expected:

- drift checker: PASS;
- `tests/test_dev_guide_sync.py`: PASS;
- DEX compliance: PASS if NautilusTrader dependencies are available, otherwise document the exact import failure as environment-limited.

- [ ] **Step 3: Inspect final repository status**

Run:

```bash
GIT_MASTER=1 git status --short --branch
GIT_MASTER=1 git log --oneline -8
```

Expected: only intended README/spec corrections are uncommitted before the final commit.

- [ ] **Step 4: Commit final verification docs**

```bash
GIT_MASTER=1 git add README.md docs/superpowers/specs/2026-04-29-nautilus-dev-guide-full-sync-design.md
GIT_MASTER=1 git commit -m "docs: document developer guide sync verification" -m "Ultraworked with [Sisyphus](https://github.com/code-yeongyu/oh-my-openagent)" -m "Co-authored-by: Sisyphus <clio-agent@sisyphuslabs.ai>"
```

If the spec file was not changed, omit it from `git add`.

---

## Final verification checklist

- [ ] `uv run python tools/check_dev_guide_sync.py` passes.
- [ ] `uv run --with pytest pytest tests/test_dev_guide_sync.py -q` passes.
- [ ] `uv run --with pytest pytest skills/nt-dex-adapter/tests/test_dex_compliance.py -q` passes or has a documented dependency-only failure.
- [ ] `GIT_MASTER=1 git status --short --branch` shows a clean working tree after commits.
- [ ] `GIT_MASTER=1 git log --oneline -8` shows focused semantic commits by phase.
- [ ] No changed skill makes a production-readiness claim without reference, contract, or test evidence.
- [ ] Open confirmation items from the spec remain labeled if unresolved: target NautilusTrader branch/release, benchmarking `divan` versus `iai`, and Martingale42 production architecture porting.

## Plan self-review

- Spec coverage: covered reference layer in Tasks 2-3, skill layer in Tasks 4-7, validation layer in Tasks 1 and 8, and risk handling through explicit source metadata and open confirmation rules.
- Placeholder scan: no implementation step uses TBD, TODO, “fill in details,” or unspecified tests.
- Type consistency: checker API is consistently `CheckResult` and `run_checks(root: Path)` across tests and implementation.
- Scope check: the plan is broad but bounded to the approved full guide sync; it does not implement new NautilusTrader adapters or trading systems.
