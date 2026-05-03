# NautilusTrader dev-skill latest-sync implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align NautilusTrader dev-skill guidance, live-runtime wording, and static sync checks with current developer-guide evidence.

**Architecture:** Use a bounded documentation-and-tooling migration. First extend the string-based sync checker with RED tests, then update skill and reference docs until those tests pass. Keep `TradingNode` examples where they are Python live/integration-specific, but add `LiveNode` / `TradingNode` boundary language so Rust-backed guidance is not misleading.

**Tech Stack:** Markdown skills/references, Python sync checker, pytest, uv.

---

## File map

- `tools/check_dev_guide_sync.py` — static drift checker; add targeted checks for stale Cap'n Proto, stale command snippets, LD_LIBRARY_PATH precision, DST readiness, dataset metadata, and live-runtime boundary terms.
- `tests/test_dev_guide_sync.py` — pytest coverage for checker RED/GREEN cases.
- `README.md` — high-level public skill inventory and validation status.
- `AGENTS.md` — repo-level agent knowledge base and commands.
- `skills/nt-dev/SKILL.md` — developer workflow skill; update setup, Rust, PyO3, and async guidance.
- `skills/nt-testing/SKILL.md` — testing skill; update commands, DST readiness, and dataset metadata.
- `skills/nt-live/SKILL.md` — live runtime skill; clarify Python `TradingNode` versus Rust/v2 `LiveNode`.
- `skills/nt-strategy-builder/SKILL.md` — strategy wiring skill; clarify `TradingNode` examples as Python live/integration-specific.
- `skills/nt-review/SKILL.md` — review gate; ensure live-runtime boundary is reviewable.
- `references/concepts/live.md` — concept guide; add live-runtime boundary note.
- `skills/nt-learn/curriculum/07-live-trading.md` — learning stage; clarify Python-oriented live examples.
- `references/integrations/*.md` — add contextual labels near high-impact live `TradingNode` sections without converting code examples.

## Task 1: Add sync checker RED coverage

**Files:**
- Modify: `tests/test_dev_guide_sync.py`

- [ ] **Step 1: Add tests for stale Cap'n Proto and LD_LIBRARY_PATH guidance**

Add tests after `test_reports_unqualified_pre_commit_install`:

```python
def test_reports_stale_capnp_version_file(tmp_path: Path) -> None:
    write(tmp_path / "skills/nt-dev/SKILL.md", "Read capnp-version before install.\n")

    result = run_checks(tmp_path)

    assert result.ok is False
    assert "stale cap'n proto version source in skills/nt-dev/SKILL.md" in result.errors


def test_reports_imprecise_ld_library_path_guidance(tmp_path: Path) -> None:
    write(
        tmp_path / "skills/nt-dev/SKILL.md",
        "export LD_LIBRARY_PATH=\"$(python -c 'import sys; print(sys.base_prefix)')/lib:$LD_LIBRARY_PATH\"\n",
    )

    result = run_checks(tmp_path)

    assert result.ok is False
    assert "imprecise LD_LIBRARY_PATH guidance in skills/nt-dev/SKILL.md" in result.errors
```

- [ ] **Step 2: Add tests for stale test commands and missing DST/dataset terms**

Add tests after the LD_LIBRARY_PATH test:

```python
def test_reports_stale_nt_testing_commands(tmp_path: Path) -> None:
    write(
        tmp_path / "skills/nt-testing/SKILL.md",
        "Run pytest tests/ -v and cargo test --workspace as primary checks.\n",
    )

    result = run_checks(tmp_path)

    assert result.ok is False
    assert "stale pytest command in skills/nt-testing/SKILL.md" in result.errors
    assert "stale cargo test command in skills/nt-testing/SKILL.md" in result.errors


def test_reports_missing_testing_policy_deltas(tmp_path: Path) -> None:
    write(tmp_path / "skills/nt-testing/SKILL.md", "Use DataTester and ExecTester evidence.\n")

    result = run_checks(tmp_path)

    assert result.ok is False
    assert "missing invariant 'DST readiness' in skills/nt-testing/SKILL.md" in result.errors
    assert "missing dataset metadata field 'size_bytes' in skills/nt-testing/SKILL.md" in result.errors
```

- [ ] **Step 3: Add tests for live-runtime boundary terms**

Add test after `test_reports_missing_required_invariants`:

```python
def test_reports_missing_live_runtime_boundary_terms(tmp_path: Path) -> None:
    write(tmp_path / "skills/nt-live/SKILL.md", "Prefer LiveNode.\n")
    write(tmp_path / "skills/nt-strategy-builder/SKILL.md", "Use TradingNode.\n")
    write(tmp_path / "skills/nt-review/SKILL.md", "Review live nodes.\n")

    result = run_checks(tmp_path)

    assert result.ok is False
    assert "missing live runtime boundary in skills/nt-live/SKILL.md" in result.errors
    assert "missing live runtime boundary in skills/nt-strategy-builder/SKILL.md" in result.errors
    assert "missing live runtime boundary in skills/nt-review/SKILL.md" in result.errors
```

- [ ] **Step 4: Update success test fixture**

Replace the four `write(...SKILL.md...)` calls in `test_success_when_required_files_metadata_paths_and_invariants_exist` with:

```python
    write(
        tmp_path / "skills/nt-live/SKILL.md",
        "Prefer LiveNode for Rust v2; TradingNode remains Python live/integration-specific.\n"
        "Legacy v1/Cython-oriented example.\n",
    )
    write(
        tmp_path / "skills/nt-testing/SKILL.md",
        "Use DataTester and ExecTester evidence.\n"
        "DST readiness uses deterministic runtime seams.\n"
        "Required dataset metadata: file sha256 size_bytes original_url licence added_at.\n",
    )
    write(
        tmp_path / "skills/nt-adapters/SKILL.md",
        "Use nautilus_network::http::HttpClient and get_runtime().spawn().\n",
    )
    write(tmp_path / "skills/nt-architect/SKILL.md", "Preserve message immutability in designs.\n")
    write(
        tmp_path / "skills/nt-dev/SKILL.md",
        "Use tools.toml for Cap'n Proto.\n"
        "PYTHON_LIB_DIR uses sysconfig.get_config_var(\"LIBDIR\").\n",
    )
    write(
        tmp_path / "skills/nt-strategy-builder/SKILL.md",
        "LiveNode for Rust v2; TradingNode remains Python live/integration-specific.\n",
    )
    write(
        tmp_path / "skills/nt-review/SKILL.md",
        "Review LiveNode for Rust v2 and TradingNode as Python live/integration-specific.\n",
    )
```

- [ ] **Step 5: Run tests and verify RED**

Run:

```bash
uv run --with pytest pytest tests/test_dev_guide_sync.py -q
```

Expected: FAIL with missing checker errors for the newly added rules.

## Task 2: Implement sync checker rules

**Files:**
- Modify: `tools/check_dev_guide_sync.py`
- Test: `tests/test_dev_guide_sync.py`

- [ ] **Step 1: Add constants for focused checks**

Add below `INVARIANT_TARGETS`:

```python
DATASET_METADATA_FIELDS = ["file", "sha256", "size_bytes", "original_url", "licence", "added_at"]

LIVE_RUNTIME_BOUNDARY_TARGETS = {
    Path("skills/nt-live/SKILL.md"): ["LiveNode", "TradingNode", "Python live"],
    Path("skills/nt-strategy-builder/SKILL.md"): ["LiveNode", "TradingNode", "Python live"],
    Path("skills/nt-review/SKILL.md"): ["LiveNode", "TradingNode", "Python live"],
}
```

- [ ] **Step 2: Add custom scans inside `run_checks`**

After the loop that checks stale `references/guides/` and `pre-commit install`, add:

```python
        if "capnp-version" in text:
            errors.append(f"stale cap'n proto version source in {relative}")
        if "LD_LIBRARY_PATH" in text and "sysconfig.get_config_var(\"LIBDIR\")" not in text:
            errors.append(f"imprecise LD_LIBRARY_PATH guidance in {relative}")
```

After the invariant loop, add:

```python
    nt_testing = root / "skills/nt-testing/SKILL.md"
    if nt_testing.exists():
        text = _read(nt_testing)
        if "pytest tests/ -v" in text:
            errors.append("stale pytest command in skills/nt-testing/SKILL.md")
        if "cargo test --workspace" in text:
            errors.append("stale cargo test command in skills/nt-testing/SKILL.md")
        if "DST readiness" not in text:
            errors.append("missing invariant 'DST readiness' in skills/nt-testing/SKILL.md")
        for field in DATASET_METADATA_FIELDS:
            if field not in text:
                errors.append(
                    f"missing dataset metadata field '{field}' in skills/nt-testing/SKILL.md"
                )

    for relative, required_terms in LIVE_RUNTIME_BOUNDARY_TARGETS.items():
        absolute = root / relative
        if not absolute.exists():
            continue
        text = _read(absolute)
        if not all(term in text for term in required_terms):
            errors.append(f"missing live runtime boundary in {relative.as_posix()}")
```

- [ ] **Step 3: Run tests and verify checker behavior**

Run:

```bash
uv run --with pytest pytest tests/test_dev_guide_sync.py -q
```

Expected: tests for checker logic pass, but full repo checker may still fail until docs are updated.

## Task 3: Update top-level metadata and live-runtime summaries

**Files:**
- Modify: `README.md`
- Modify: `AGENTS.md`

- [ ] **Step 1: Update README overview and summaries**

Change `README.md` line 7 to state latest developer-guide alignment instead of fixed v1.224 validation:

```markdown
These skills encode NautilusTrader best practices, correct patterns, and structured workflows for building production-quality trading systems. They are maintained against the official [NautilusTrader Developer Guide](https://nautilustrader.io/docs/latest/developer_guide/) with version-sensitive notes called out explicitly where they matter.
```

Change the two `nt-live` summaries to mention `LiveNode` / `TradingNode` boundary:

```markdown
│   nt-live         LiveNode / TradingNode boundary, adapters, reconciliation │
```

and:

```markdown
| `nt-live` | Live trading and production ops | LiveNode / TradingNode boundary, adapters, reconciliation |
```

- [ ] **Step 2: Update AGENTS metadata and command snippets**

Change `AGENTS.md` line 7 to:

```markdown
**NautilusTrader Alignment:** Latest developer guide with version-sensitive migration notes
```

Change the structure/sequence labels from `BacktestEngine/TradingNode wiring` and `Wire BacktestEngine or TradingNode` to:

```markdown
├── nt-strategy-builder/ # BacktestEngine and live-node wiring
```

and:

```markdown
4. **nt-strategy-builder** — Wire BacktestEngine, Python TradingNode, or Rust/v2 LiveNode paths
```

Change command block Python/Rust tests to:

```bash
# Python tests
make pytest
make pytest-v2

# Rust tests
make cargo-test
cargo nextest run --workspace --features 'python,ffi,high-precision,defi' --cargo-profile nextest
```

- [ ] **Step 3: Run sync checker**

Run:

```bash
uv run python tools/check_dev_guide_sync.py
```

Expected: still may fail until skill docs are updated, but no README/AGENTS-specific new failures.

## Task 4: Update `nt-dev`

**Files:**
- Modify: `skills/nt-dev/SKILL.md`

- [ ] **Step 1: Replace Cap'n Proto source wording**

Update prerequisite and installation text so it says:

```markdown
| **Cap'n Proto** | Serialization schema compilation | Version pinned in `tools.toml`; install with `./scripts/install-capnp.sh` |
```

Replace `CAPNP_VERSION=$(cat capnp-version)` guidance with:

```bash
# Script (recommended; reads pinned version from tools.toml)
./scripts/install-capnp.sh

# Inspect pinned version used by repo tooling
bash scripts/tool-version.sh capnp
```

- [ ] **Step 2: Replace Linux environment variable snippet**

Use:

```bash
export PYO3_PYTHON="$PWD/.venv/bin/python"

# Linux only: uv-managed Python runtime library path
PYTHON_LIB_DIR="$("$PYO3_PYTHON" -c 'import sysconfig; print(sysconfig.get_config_var("LIBDIR"))')"
export LD_LIBRARY_PATH="$PYTHON_LIB_DIR${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

# Python home for Rust tests
export PYTHONHOME="$("$PYO3_PYTHON" -c 'import sys; print(sys.base_prefix)')"
```

- [ ] **Step 3: Add current Rust/PyO3 deltas**

Under Rust conventions, add a compact subsection:

```markdown
### Current Rust/PyO3 Deltas

- PyO3 properties: use `#[getter]` only for cheap, side-effect-free, attribute-like values. Use methods for actions, mutations, I/O, arguments, non-trivial work, or collection clones.
- Python stubs: annotate Python-exposed Rust APIs with `pyo3-stub-gen` (`gen_stub_pyclass`, `gen_stub_pyclass_enum`, `gen_stub_pymethods`, `gen_stub_pyfunction`) and regenerate with `make py-stubs-v2`.
- PyO3 enums: do not combine the `hash` pyclass attribute with `eq_int`; implement manual `__hash__` returning the discriminant.
- DST-observable iteration: use `IndexMap` / `IndexSet` when iteration order feeds observable behavior. Use `AHashMap` / `AHashSet` for lookup-only hot paths, immutable `Arc<AHashMap<...>>` for read-only sharing, and `DashMap` for concurrent reads/writes.
- Async functions: document cancellation safety for control-plane futures. Adapter sync-to-async bridges should use `get_runtime().block_on()`; Python-thread-sensitive tasks should use `get_runtime().spawn()`.
```

- [ ] **Step 4: Run checker**

Run:

```bash
uv run python tools/check_dev_guide_sync.py
```

Expected: `nt-dev` stale Cap'n Proto and LD_LIBRARY_PATH failures are gone.

## Task 5: Update `nt-testing`

**Files:**
- Modify: `skills/nt-testing/SKILL.md`

- [ ] **Step 1: Replace primary command section**

Replace direct command examples with:

```bash
# v1 legacy Python tests
make pytest
# or
uv run --active --no-sync pytest --new-first --failed-first

# Rust-backed PyO3 Python tests
make pytest-v2

# Rust tests
make cargo-test
# or
cargo nextest run --workspace --features "python,ffi,high-precision,defi" --cargo-profile nextest

# Optional feature coverage
make cargo-test EXTRA_FEATURES="capnp"

# Performance tests
make test-performance
```

- [ ] **Step 2: Add DST readiness section**

Add after current testing policy contract:

```markdown
## DST readiness

Before promoting async/runtime modules to deterministic simulation testing (DST), verify:

- Time, task, runtime, and signal primitives route through deterministic seams rather than direct Tokio or OS calls.
- Wall-clock reads go through the project time seam, not direct `SystemTime::now()` at call sites.
- Ordering-sensitive maps use `IndexMap` / `IndexSet`.
- Control-plane `tokio::select!` blocks use `biased` when poll order affects behavior.
- `Instant::now()`, `SystemTime::now()`, `tokio::signal::ctrl_c`, `std::thread::spawn`, and `tokio::task::spawn_blocking` do not escape reviewed seams.
- Replay-sensitive IDs are pure functions of their inputs.
```

- [ ] **Step 3: Update dataset metadata**

Replace the metadata example so it includes:

```json
{
  "file": "binance_btcusdt_2024-01-01_trade_ticks.parquet",
  "sha256": "abc123...",
  "size_bytes": 1048576,
  "original_url": "https://example.com/source",
  "licence": "exchange terms",
  "added_at": "2026-05-03T00:00:00Z"
}
```

Add a user-fetched note:

```markdown
User-fetched datasets must also document distribution, fetch method/reference, auth requirements, transform version, redistribution terms, and public mirror status. Commit manifests and metadata only when redistribution is restricted; tests must skip cleanly when local user-fetched data is absent.
```

- [ ] **Step 4: Run checker**

Run:

```bash
uv run python tools/check_dev_guide_sync.py
```

Expected: `nt-testing` stale command, DST, and dataset metadata failures are gone.

## Task 6: Update live-runtime boundary wording across skills

**Files:**
- Modify: `skills/nt-live/SKILL.md`
- Modify: `skills/nt-strategy-builder/SKILL.md`
- Modify: `skills/nt-review/SKILL.md`

- [ ] **Step 1: Update `nt-live` boundary section**

Ensure the section says:

```markdown
Use `nautilus_trader.live.LiveNode` for Rust v2 / Rust-backed live-node work. Python live connectivity examples may still use `nautilus_trader.live.node.TradingNode`; label those examples as Python live or integration-specific rather than universal defaults.
```

- [ ] **Step 2: Update `nt-strategy-builder` decision text**

Ensure the decision tree says Python live/integration-specific `TradingNode`, while Rust v2 uses `LiveNode`.

- [ ] **Step 3: Update `nt-review` gate**

Ensure review gates check for `LiveNode` for Rust v2 and `TradingNode` as Python live/integration-specific.

- [ ] **Step 4: Run checker**

Run:

```bash
uv run python tools/check_dev_guide_sync.py
```

Expected: live-runtime boundary failures are gone.

## Task 7: Update broader references and templates

**Files:**
- Modify: `references/concepts/live.md`
- Modify: `skills/nt-learn/curriculum/07-live-trading.md`
- Modify: selected `references/integrations/*.md`
- Modify: selected `skills/nt-strategy-builder/templates/*.py`

- [ ] **Step 1: Add concept-guide boundary note**

Add near the top of `references/concepts/live.md`:

```markdown
> **Live runtime boundary:** Python live-trading examples in this guide use `TradingNode`. Rust v2 / Rust-backed live-node work should use `LiveNode` where the official Rust live path applies.
```

- [ ] **Step 2: Add curriculum boundary note**

Add near the top of `skills/nt-learn/curriculum/07-live-trading.md`:

```markdown
> **Runtime note:** This stage teaches Python live trading with `TradingNode`. For Rust v2 / Rust-backed live-node work, use the `LiveNode` path documented in `nt-live`.
```

- [ ] **Step 3: Add integration-specific labels**

For integration docs where a section begins with live `TradingNode` setup, add one concise note above the first setup snippet:

```markdown
> **Runtime note:** This is a Python live/integration-specific `TradingNode` example. Use `LiveNode` for Rust v2 / Rust-backed live-node work where applicable.
```

Prioritize `references/integrations/binance.md`, `bybit.md`, `okx.md`, `hyperliquid.md`, `dydx.md`, `ib.md`, `mt5.md`, and `databento.md`.

- [ ] **Step 4: Add template labels without changing code**

For Python `TradingNode` templates in `skills/nt-strategy-builder/templates/`, add module docstring wording that this is a Python live/integration-specific template.

- [ ] **Step 5: Run checks**

Run:

```bash
uv run python tools/check_dev_guide_sync.py
uv run --with pytest pytest tests/test_dev_guide_sync.py -q
uv run pytest skills/nt-strategy-builder/tests/ -q
```

Expected: all pass.

## Task 8: Final verification and commits

**Files:**
- All changed files from Tasks 1-7

- [ ] **Step 1: Run required verification**

Run:

```bash
uv run python tools/check_dev_guide_sync.py
uv run --with pytest pytest tests/test_dev_guide_sync.py -q
uv run pytest skills/nt-strategy-builder/tests/ -q
```

Expected: all pass.

- [ ] **Step 2: Inspect git diff**

Run:

```bash
git diff --stat
git diff -- README.md AGENTS.md tools/check_dev_guide_sync.py tests/test_dev_guide_sync.py
```

Expected: changes match this plan; no unrelated edits.

- [ ] **Step 3: Commit in bounded semantic commits**

Recommended commits:

```bash
git add README.md AGENTS.md skills/nt-live/SKILL.md skills/nt-strategy-builder/SKILL.md skills/nt-review/SKILL.md references/concepts/live.md skills/nt-learn/curriculum/07-live-trading.md
git commit -m "docs: clarify Nautilus live runtime guidance"

git add skills/nt-dev/SKILL.md skills/nt-testing/SKILL.md
git commit -m "docs: update Nautilus developer guide skills"

git add tools/check_dev_guide_sync.py tests/test_dev_guide_sync.py
git commit -m "test: extend Nautilus guide sync checks"

git add references/integrations/*.md skills/nt-strategy-builder/templates/*.py
git commit -m "docs: label Python live integration examples"
```

Adjust commit grouping if fewer files change, but keep tests with checker changes.
