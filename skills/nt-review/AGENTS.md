# nt-review Knowledge Base

**Purpose:** Validate NautilusTrader implementations against conventions, trading correctness, performance, and testability before deployment.

**Entry Point:** `SKILL.md` (955 lines)

## REVIEW DIMENSIONS (8)

1. **Nautilus Conventions** — Lifecycle methods, API usage, naming
2. **Trading Correctness** — Position sizing, order management, risk checks, edge cases
3. **Performance** — Blocking calls, memory management, efficient data handling
4. **Testability** — Backtest compatibility, isolation, logging
5. **Live Trading** — Reconciliation, network resilience, order state management, risk controls
6. **Rust/FFI** — Memory safety, style conventions, PyO3 bindings
7. **Benchmarking** — Criterion/iai structure, profiling
8. **Visualization** — Plotly tearsheet config (v1.221.0+)

## ASSURANCE-DRIVEN ENGINEATION (Core Philosophy)

- **Executable Invariants:** Critical paths (risk, execution) verified by unit tests, property tests, or fuzzers
- **Parity:** Strategy code identical and deterministic across backtest/paper/live
- **Soundness:** Rust code free of memory safety bugs (`#![deny(unsafe_op_in_unsafe_fn)]`)

## REVIEW SEVERITY

| Level | Meaning | Examples |
|-------|---------|---------|
| **Blocker** | Must fix before merge | Runtime/FFI violations, missing reconciliation, execution coupling, secret leakage |
| **Major** | Should fix before merge | Incomplete method contracts, missing fallback/provenance, missing test categories |
| **Minor** | Can fix later | Naming drift, doc gaps with otherwise correct behavior |

## LIFECYCLE METHOD CHECKS

| Method | Required | Red Flags |
|--------|----------|-----------|
| `__init__` | `super().__init__(config)` first | Using `clock`/`logger`/`cache` here (not yet available) |
| `on_start` | Load instrument, models, subscribe | Subscribing before requesting historical data |
| `on_stop` | Cancel orders, unsubscribe | No cleanup |
| `on_reset` | Reset state for reuse | No buffer/cache clearing |

## ADAPTER REVIEW GATE

Fail review if missing:
- Phase compliance (7-phase dependency order with milestone evidence)
- Required interfaces: InstrumentProvider async loaders, LiveDataClient contract, LiveExecutionClient reconciliation
- Factory/config contract: `create(loop, name, config, msgbus, cache, clock)` with safe credential handling
- Runtime/FFI safety: no `tokio::spawn()` in adapters, no `Arc<PyObject>`, no blocking hot handlers
- Testing doctrine: real payload fixtures, no sleep-based timing, cover providers/data/execution/factories

## EVOMAP REVIEW GATE (Optional)

Fail review if present:
- Execution coupling (EvoMap blocks/alters order execution in hot handlers)
- Auto-apply behavior (suggestions merged without explicit approval)
- No degraded-mode plan (missing fallback when EvoMap is down)
- No provenance (missing traceability for payloads and decisions)
- Unsafe payload scope (credentials or account-sensitive fields exported)

## QUICK CHECK (<5 min)

- [ ] All lifecycle methods call `super()`
- [ ] `on_start` fetches instrument from cache with null check
- [ ] `request_bars` before `subscribe_bars`
- [ ] `on_stop` cancels orders and unsubscribes
- [ ] Type hints on all methods
- [ ] No blocking calls in handlers
- [ ] External integrations advisory-only and non-blocking

## FULL REVIEW (15-30 min)

Quick check + Conventions + Trading Correctness + Performance + Testability + (if adapter) Adapter Gate + (if EvoMap) EvoMap Gate + (if Rust) Rust/FFI Checklist.

## COMMON ISSUES BY COMPONENT

| Component | Typical Issues |
|-----------|---------------|
| **Strategy** | Missing rejection handling, no position limits, blocking in `on_bar`, not canceling on stop |
| **Actor** | Model loading in handler (not `on_start`), unbounded signal history, no warmup, missing `on_reset` |
| **Indicator** | Missing `initialized` property, missing `reset` method, wrong handler signature |
| **Adapter** | Blocking HTTP in data handlers, no reconnection, not Rust-first, `tokio::spawn()` misuse |
| **Data Catalog** | Not using `ParquetDataCatalog`, missing `BacktestDataConfig` for custom data, missing `metadata` |

## RUST/FFI CHECKLIST (16 items)

- [ ] Copyright header (2015-2026 Nautech Systems)
- [ ] Module documentation with feature flags
- [ ] `new_checked()` + `new()` constructor pattern
- [ ] `anyhow::bail!` for early returns (not `Err(anyhow::anyhow!(...))`)
- [ ] `FAILED` constant in `.expect()` calls
- [ ] `AHashMap`/`AHashSet` for non-security collections
- [ ] `abort_on_panic` on all FFI functions
- [ ] Matching drop for every constructor
- [ ] Type-specific CVec drops (never generic)
- [ ] No `Arc<PyObject>` (use plain `PyObject` + `clone_py_object`)
- [ ] `py_*` prefix on Rust function names
- [ ] SAFETY comments on all unsafe blocks
- [ ] `#[repr(C)]` on FFI types
- [ ] `#![deny(unsafe_op_in_unsafe_fn)]` in crate root
- [ ] Unit tests covering unsafe code paths
- [ ] No `.clone()` in hot paths, no `.unwrap()` in production

### Rust Doc Mood
- **Indicative:** "Returns the client" ✅
- **Imperative:** "Return the client" ❌

### v1.223.0 Rust Breaking Change
`AddAssign`/`SubAssign` removed from `Price`/`Quantity`/`Money`. Use `x = x + y` not `x += y`.

## LIVE TRADING CHECKLIST (9+ items)

- [ ] Reconciliation enabled with appropriate lookback (≥60 min)
- [ ] Timeouts configured for all connection phases
- [ ] External order claims configured if resuming
- [ ] All order lifecycle events handled (reject, cancel, expire, partial fill)
- [ ] Reconnection logic in adapters with exponential backoff
- [ ] Position limits and circuit breaker configured
- [ ] v1.223.0: `trade_execution` default `True`; set `False` for bar-only
- [ ] v1.223.0: `Quantity - Quantity` returns `Quantity`; `ValueError` if < 0
- [ ] v1.223.0: dYdX v3 adapter removed; use `nautilus_trader.adapters.dydx`

## PERFORMANCE CHECKLIST

- [ ] Criterion for end-to-end scenarios (>100ns)
- [ ] iai for micro-benchmarks (instruction counts)
- [ ] Setup outside timing loops
- [ ] `black_box` on inputs/outputs
- [ ] `harness = false` in Cargo.toml
- [ ] Benchmarks in `benches/` directory
- [ ] Flamegraph for optimization work
- [ ] Before/after comparison documented

## REFERENCES (symlinked)

- `references/developer_guide/` — coding_standards.md, python.md, rust.md, ffi.md, testing.md, benchmarking.md, adapters.md
- `references/concepts/` — backtesting.md, live.md

## PREVIOUS STEP

Components implemented via **nt-implement** skill.
