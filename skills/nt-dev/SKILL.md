---
name: nt-dev
description: "Use when setting up NautilusTrader development environment, writing code that follows project conventions, running tests, benchmarks, managing releases, or understanding FFI memory contracts."
---

# nt-dev

## What This Skill Covers

NautilusTrader **developer workflow** — environment setup, coding standards, testing, benchmarking, FFI memory contracts, documentation style, and release process.

**Scope**: Cross-cutting concerns that apply to all NautilusTrader development, regardless of domain.

## When To Use

- Setting up a development environment (uv, Rust toolchain, Cap'n Proto, IDE configs)
- Writing code that follows project conventions (formatting, naming, comments)
- Running tests (unit, integration, property-based, fuzzing, memory leak)
- Writing or running benchmarks (Criterion, iai, flamegraph)
- Understanding or modifying FFI/memory boundaries between Rust and Python
- Curating test datasets
- Writing or reviewing documentation
- Managing releases (develop/nightly/master branch model)

## When NOT To Use

- **Strategy or trading logic** → use `nt-trading`
- **Backtest configuration** → use `nt-backtest`
- **Adapter integration** → use `nt-adapters`
- **Domain model types** → use `nt-model`

## Development Environment

### Prerequisites

| Tool | Purpose | Install |
|------|---------|---------|
| **uv** | Python venv & dependency management | [docs.astral.sh/uv](https://docs.astral.sh/uv) |
| **Rust** | Core platform implementation | [rust-lang.org/tools/install](https://www.rust-lang.org/tools/install) |
| **Cap'n Proto** | Serialization schema compilation | Version pinned in `tools.toml`; install with `./scripts/install-capnp.sh` |
| **prek** | Automated formatting/linting at commit | `make install-tools`, then `prek install` |

### Initial Setup

```bash
# 1. Install all dependencies (dev + test)
uv sync --active --all-groups --all-extras
# Or: make install

# 2. Debug build (faster iteration)
make install-debug

# 3. Set up hooks with current official tooling
make install-tools
prek install
```

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

### Environment Variables (Linux/macOS)

Required for Rust/PyO3 when using Python installed via `uv`:

```bash
# PyO3 Python interpreter path (reduces recompilation)
export PYO3_PYTHON="$PWD/.venv/bin/python"

# Linux only: uv-managed Python runtime library path
PYTHON_LIB_DIR="$("$PYO3_PYTHON" -c 'import sysconfig; print(sysconfig.get_config_var("LIBDIR"))')"
export LD_LIBRARY_PATH="$PYTHON_LIB_DIR${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

# Python home for Rust tests
export PYTHONHOME="$("$PYO3_PYTHON" -c 'import sys; print(sys.base_prefix)')"
```

Verify: `python -c "import sys; print(sys.executable)"` and check `$PYO3_PYTHON` / `$PYTHONHOME`.

### Cap'n Proto Installation

```bash
# Script (recommended; reads pinned version from tools.toml)
./scripts/install-capnp.sh

# Inspect pinned version used by repo tooling
bash scripts/tool-version.sh capnp

# macOS
brew install capnp
```

### Builds & Rebuilds

```bash
make build          # Release build
make build-debug    # Debug build (significantly faster)
make format         # Auto-format all code
make pre-commit     # Run full pre-commit suite
```

After any changes to `.rs`, `.pyx`, or `.pxd` files, rebuild with `make build` or `make build-debug`.

### IDE Configuration

**VS Code (rust-analyzer)**: Set `VIRTUAL_ENV`, `CC=clang`, `CXX=clang++` in `rust-analyzer.cargo.extraEnv`, `check.extraEnv`, and `runnables.extraEnv`. Enable `features = "all"` and `testExplorer = true`.

**Faster builds (optional)**: Use cranelift backend on nightly toolchain. See `references/developer_guide/environment_setup.md` for the Cargo.toml patch. **Do not commit** the cranelift patch.

### Dependency Management

- `pyproject.toml` pins `required-version` for uv and enforces `exclude-newer = "3 days"` cooldown
- Bypass cooldown: `uv lock --exclude-newer "0 seconds"`
- Workspace deps: use `serde = { workspace = true }` for shared deps

## Coding Conventions

### Universal Rules (All Source Files)

- **Spaces only**, never hard tabs
- Lines **< 100 characters**; wrap thoughtfully
- **American English** spelling (`color`, `serialize`, `behavior`)

### Comment Conventions

1. One blank line above every comment block/docstring
2. **Sentence case** — capitalize first letter, rest lowercase (except proper nouns)
3. No double spaces after periods
4. Single-line comments: no trailing period (unless URL/link)
5. Multi-line comments: commas between sentences, period on final line
6. Keep comments concise — *less is more*
7. No emoji

### Formatting

- Align at next logical indent (not hanging vanity alignment)
- Closing parenthesis on new line at logical indent
- Trailing comma on multi-line parameter/argument lists

### Error Messages & Naming

- Avoid "got" — use "was", "received", "found"
- Use `e` (not `err` or `error`) for caught errors: `Err(e)`, `except SomeError as e:`
- Internal fields: abbreviations OK (`_price_prec`)
- Public API: full descriptive names (`price_precision`)
- User-facing: never abbreviate

### Rust Doc Mood → **Indicative**: "Returns a cached client."
### Python Doc Mood → **Imperative**: "Return a cached client."

### Shell Portability

- Shebang: `#!/usr/bin/env bash`
- Avoid bash 4+ features in user-facing scripts (macOS ships bash 3.2)
- Use portable alternatives: `sed -i.bak` instead of `sed -i`, `-E` instead of `-E`, etc.

### Commit Messages

- Subject ≤ 60 chars, capitalized, no trailing period
- Imperative voice ("Add feature" not "Added feature")
- Optional body under 100 char width

### Python Conventions

- **PEP-8** generally; one departure: use `is None`/`is not None` (not truthiness) for None checks
- Use truthiness for **empty collections**: `if not my_list:`
- **Type hints required** on all function/method signatures
- **PEP 604** union syntax: `Instrument | None` (not `Optional[Instrument]`)
- **NumPy docstrings** for public API
- **No docstrings** on private methods (`_prefix`) — use inline `#` comments instead
- Test naming: descriptive scenario names `test_currency_with_negative_precision_raises_overflow_error`

### Rust Conventions

- Copyright header required on all files (automated enforcement via pre-commit)
- **Cargo manifest layout**: internal crates first (alphabetical), blank line, external deps (alphabetical), blank line, optional deps
- Feature flags: `default = []`, additive, documented at crate level
- **Imports**: auto-formatted by rustfmt (std → external → local)
- **One blank line** between functions and above doc comments
- **Inline format strings**: `anyhow::bail!("Failed: {n}")` not positional
- **Fully qualify**: `anyhow::*`, `log::*`, `tokio::*` — but not Nautilus domain types
- **Error handling**: `anyhow::Result<T>` primary; `thiserror` for domain errors; `?` for propagation
- **Logging**: `log::info!`, `log::warn!` etc. — always fully qualified
- **Async**: `get_runtime().spawn()` in adapters (not `tokio::spawn()`); `#[tokio::test]` OK in tests

### Current Rust/PyO3 Deltas

- PyO3 properties: use `#[getter]` only for cheap, side-effect-free,
  attribute-like values. Use methods for actions, mutations, I/O, arguments,
  non-trivial work, or collection clones.
- Python stubs: annotate Python-exposed Rust APIs with `pyo3-stub-gen`
  (`gen_stub_pyclass`, `gen_stub_pyclass_enum`, `gen_stub_pymethods`,
  `gen_stub_pyfunction`) and regenerate with `make py-stubs-v2`.
- PyO3 enums: do not combine the `hash` pyclass attribute with `eq_int`;
  implement manual `__hash__` returning the discriminant.
- DST-observable iteration: use `IndexMap` / `IndexSet` when iteration order
  feeds observable behavior. Use `AHashMap` / `AHashSet` for lookup-only hot
  paths, immutable `Arc<AHashMap<...>>` for read-only sharing, and `DashMap`
  for concurrent reads/writes.
- Async functions: document cancellation safety for control-plane futures.
  Adapter sync-to-async bridges should use `get_runtime().block_on()`;
  Python-thread-sensitive tasks should use `get_runtime().spawn()`.

## Testing & Benchmarking

### Test Categories

| Category | Tool | Purpose |
|----------|------|---------|
| Unit tests | pytest / cargo nextest | Individual component correctness |
| Integration tests | pytest / cargo nextest | Cross-component interaction |
| Acceptance tests | DataTester | Live adapter data validation |
| Property-based | proptest (Rust) | Invariant verification for all valid inputs |
| Fuzzing | Custom | Malformed input resilience |
| Memory leak | Custom | FFI allocation tracking |
| Performance | pytest-benchmark / codspeed | Hot-path timing |

### Running Tests

```bash
# v1 legacy Python tests (tests/)
make pytest

# v2 Python tests (python/tests/) — uses debug Rust extension
make pytest-v2

# Rust tests
make cargo-test
# With optional features:
make cargo-test EXTRA_FEATURES="capnp hypersync"

# Performance tests
make test-performance
```

### Test Style

- **Python** (`python/tests/`): pytest-style free functions, no test classes. Use `@pytest.fixture`, `@pytest.mark.parametrize`.
- **Rust**: Use `unwrap`/`expect` freely in tests. Do not capture log output to assert on messages.
- **Waiting for async**: Use `await eventually(...)` and `wait_until_async(...)` instead of arbitrary sleeps.
- **Mocks**: Prefer hand-written stubs over `MagicMock`. Never mock the object under test.

### Property-Based Testing (proptest)

Use for: core domain types, accounting engines, matching engines, state machines.

Example invariants:
- Round-trip: `parse(to_string(value)) == value`
- Inverse: `(A + B) - B == A`
- Transitivity: `A < B and B < C → A < C`

### Benchmarking

Two frameworks:

| Framework | Measures | When to use |
|-----------|----------|-------------|
| **Criterion** | Wall-clock time with confidence intervals | End-to-end, >100ns scenarios, visual comparisons |
| **iai** | CPU instruction counts (deterministic) | Ultra-fast functions, CI regression gating |

**Directory layout**: `crates/<crate>/benches/` with `foo_criterion.rs` and `foo_iai.rs`.

```bash
cargo bench -p nautilus-core                          # Single crate
cargo bench -p nautilus-core --bench time             # Single benchmark
make cargo-ci-benches                                  # CI benches
```

**Flamegraph**: `cargo flamegraph --bench <name> -p <crate> --profile bench`

### Data Type Testing

New data types need tests at all layers: DataEngine, DataActor (Rust), PyO3 dispatch, Python Actor, Backtest client, Adapter spec. See `references/developer_guide/testing.md` and `references/developer_guide/contracts/testing_policy.md` for the full test layer matrix.

## FFI & Memory

### Core Rules

1. **Rust panics must never unwind across FFI** — wrap every `extern "C"` function in `abort_on_panic(|| { ... })`
2. **CVec lifecycle**: Rust builds `Vec<T>` → converts with `into()` (leaks allocation) → foreign code uses data → foreign code calls **type-specific drop helper** exactly once
3. **Never call drop helper twice** (double-free) and **never forget it** (memory leak)
4. **No generic `cvec_drop`** — always use type-specific helpers (`vec_drop_book_levels`, etc.)
5. **PyCapsule with destructor**: Always use `PyCapsule::new_with_destructor`, never `PyCapsule::new(..., None)`
6. **Box-backed `*_API` wrappers**: Every `*_new` must have a matching `*_drop`. Validate params before allocation.

### CVec Lifecycle

| Step | Owner | Action |
|------|-------|--------|
| 1 | Rust | Build `Vec<T>`, convert with `into()` — leaks and transfers ownership |
| 2 | Foreign | Use data while `CVec` is in scope. **Do not modify ptr/len/cap** |
| 3 | Foreign | Call type-specific drop helper **exactly once** |

### PyCapsule Pattern (Rust → Python)

```rust
let my_data = Box::new(MyStruct::new());
let ptr = Box::into_raw(my_data);
let capsule = PyCapsule::new_with_destructor(py, ptr, None, |ptr, _| {
    let _ = unsafe { Box::from_raw(ptr) };
}).expect("capsule creation failed");
```

## Test Datasets

### Categories

| Category | Size | Storage | Availability |
|----------|------|---------|-------------|
| **Small** | < 1 MB | Checked into `tests/test_data/<source>/` | Always |
| **Large** | > 1 MB | R2 bucket as Parquet | Downloaded on first use |
| **User-fetched** | Any | Local only | Manual download with user's credentials |

### Required Metadata (`metadata.json`)

| Field | Description |
|-------|-------------|
| `file` | Filename |
| `sha256` | SHA-256 hash |
| `size_bytes` | File size |
| `original_url` | Source download URL |
| `licence` | License terms |
| `added_at` | ISO 8601 timestamp |

### Storage Format

New datasets → **Nautilus Parquet** (ZSTD level 3, 1M row groups). Not raw vendor formats.

### Naming Convention

```
<source>_<instrument>_<date>_<datatype>.parquet
```

### Curation

```bash
scripts/curate-dataset.sh <slug> <filename> <download-url> <licence>
```

User-fetched datasets: commit manifest + metadata only. Tests skip cleanly when data absent.

## Release Process

### Three-Branch Model

| Branch | Purpose | Publishes |
|--------|---------|-----------|
| **`develop`** | Active development | Dev wheels to R2 |
| **`nightly`** | Pre-release testing | Alpha wheels + CLI binaries |
| **`master`** | Stable releases | PyPI, Docker, docs |

### Versioning

- Python package version in `pyproject.toml` (e.g., `1.223.0`) — drives release tag
- Rust workspace version in `Cargo.toml` (e.g., `0.53.0`) — independent

### Release Checklist

**Pre-release (on `develop`)**:
- [ ] Finalize `RELEASES.md`
- [ ] Verify versions in `pyproject.toml` and `Cargo.toml`
- [ ] All CI passes

**Release**:
- [ ] Merge `develop` → `nightly` → verify CI
- [ ] Merge `nightly` → `master`
- [ ] Verify build workflow (wheels, tag, PyPI)
- [ ] Verify docker workflow
- [ ] Verify docs rebuild

**Post-release (on `develop`)**:
- [ ] Update release date in `RELEASES.md`
- [ ] Add `---` separator
- [ ] Add next version template
- [ ] Bump `pyproject.toml` version

### Release Notes Sections

Order: Enhancements → Breaking Changes → Security → Fixes → Internal Improvements → Documentation Updates → Deprecations

Start items with: "Added", "Removed", "Renamed", "Changed", "Fixed", "Implemented", "Improved", "Upgraded"

### Docs Style

- **Admonitions**: `:::note`, `:::info`, `:::tip`, `:::warning`, `:::danger` (use sparingly)
- **Headings**: Title case for `#`, sentence case for `##` and below
- **Lists**: Hyphens (`-`), not `*` or `+`
- **Tables**: `✓` for supported, `-` for unsupported
- **Code**: backticks for inline, code blocks for multi-line
- **NumPy docstrings** for Python API docs

## References

- `references/developer_guide/environment_setup.md` — Full environment setup guide
- `references/developer_guide/coding_standards.md` — Formatting, comments, commit messages
- `references/developer_guide/rust.md` — Rust conventions summary (Cargo, features, async, attrs)
- `references/developer_guide/python.md` — Python style, type hints, docstrings
- `references/developer_guide/testing.md` — Test categories, running, style, data type test matrix
- `references/developer_guide/benchmarking.md` — Criterion, iai, flamegraph, directory layout
- `references/developer_guide/ffi.md` — CVec lifecycle, PyCapsule, abort_on_panic, ownership
- `references/developer_guide/test_datasets.md` — Dataset categories, metadata, curation workflow
- `references/developer_guide/releases.md` — Branch model, versioning, checklist, release notes
- `references/developer_guide/docs_style.md` — Docs types, admonitions, MDX components, style guide
- `references/developer_guide/contracts/environment_tooling.md` — Current tooling contract
