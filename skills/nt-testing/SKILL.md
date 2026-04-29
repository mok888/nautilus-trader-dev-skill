---
name: nt-testing
description: "Use when writing or running tests for NautilusTrader, setting up test fixtures, using DataTesterConfig or ExecTesterConfig, managing test datasets, or configuring CI testing."
---

# nt-testing

## What This Skill Covers

The complete NautilusTrader testing framework:
- **Testing pyramid** — unit, integration, acceptance, performance, property-based, fuzzing, memory leak tests
- **Data testing spec** — DataTesterConfig API for validating adapter data flows
- **Execution testing spec** — ExecTesterConfig API for validating order lifecycle per venue
- **Test datasets** — curation, storage, metadata, and checksum management
- **CI patterns** — Makefile targets, GitHub Actions, pre-commit hooks

## When To Use

- Writing new tests for NT components (Python or Rust)
- Setting up DataTesterConfig or ExecTesterConfig for adapter validation
- Creating or managing test datasets (Parquet, JSON fixtures)
- Configuring CI pipelines for NT contributions
- Writing property-based tests or fuzz targets
- Debugging test failures in CI

## When NOT To Use

- **nt-backtest** — for running backtest simulations (not testing)
- **nt-dev** — for environment setup, coding standards, or release process
- **nt-adapters** — for building adapter internals (testing specs live here, implementation lives there)

## Test Categories

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

NautilusTrader's test suite covers seven categories:

| Category | Scope | Typical Location |
|----------|-------|------------------|
| **Unit tests** | Single functions, types, modules | Inline `#[cfg(test)]` (Rust), `tests/` (Python) |
| **Integration tests** | Multi-component interactions | `tests/` directory |
| **Acceptance tests** | End-to-end workflows | `tests/` with full node setup |
| **Performance tests** | Criterion/iai benchmarks | `benches/` per crate |
| **Property-based tests** | Invariant checking with random inputs | `proptest` strategies inline |
| **Fuzzing** | Malformed input resilience | `fuzz/` targets |
| **Memory leak tests** | Drop verification, ASAN | CI-specific configurations |

## Running Tests

### Python (v1)

```bash
# All Python tests
pytest tests/ -v

# Specific test file
pytest tests/test_trading.py -v

# With coverage
pytest tests/ --cov=nautilus_trader
```

### Rust (v2 / cargo)

```bash
# All Rust tests
cargo test --workspace

# Specific crate
cargo test -p nautilus-core

# With output
cargo test -p nautilus-model -- --nocapture

# Run benchmarks (not tests, but related)
cargo bench -p nautilus-core
```

### Makefile targets

```bash
make test          # Full test suite
make pre-commit    # Format + lint + all checks
make format        # Auto-format (ruff, rustfmt)
make lint          # Lint only (no format changes)
make cargo-test    # Rust-only test suite
```

## Test Style

- **Naming**: `test_<what>_<condition>_<expected>` — descriptive, no abbreviations
- **Assertions**: Use specific assert methods (`assert_eq!`, `assert_ne!`) over boolean `assert!`
- **Fixtures**: Shared setup via `#[fixture]` (Rust) or `conftest.py` (Python)
- **Parameterization**: Use `pytest.mark.parametrize` or proptest `Strategy` combinators
- **Isolation**: Each test must be independent; no ordering dependencies

## Property-Based Testing

Property testing verifies logic holds for *all* valid inputs using `proptest` in Rust.

**Use cases**: Core domain types (`Price`, `Quantity`, `UnixNanos`), accounting engines, matching engines, state machines.

**Example invariants:**
- Round-trip: `parse(to_string(value)) == value`
- Inverse: `(A + B) - B == A`
- Transitivity: `if A < B and B < C, then A < C`

```rust
use proptest::prelude::*;

proptest! {
    #[test]
    fn test_price_round_trip(value in any::<f64>().prop_filter("positive", |v| *v > 0.0)) {
        let price = Price::new(value, 8).unwrap();
        let parsed = Price::from_str(&price.to_string()).unwrap();
        assert_eq!(price, parsed);
    }
}
```

## Fuzzing

Fuzzing verifies the system fails gracefully with unstructured/malformed data.

**Use cases**: Network boundaries, exchange data parsers (JSON, FIX, WebSocket), state machines.

**Goal**: System returns `Result::Err` — never panics, hangs, or leaks memory.

```rust
// Fuzz target structure
fn fuzz_parse_trade(data: &[u8]) {
    let _ = parse_trade(data); // Must return Err, not panic
}
```

## Data Testing Spec

The DataTesterConfig API validates adapter data flows end-to-end. Each adapter has specific data test configurations.

### DataTesterConfig API

```python
from nautilus_trader.test.adapters import DataTesterConfig

# Basic config
config = DataTesterConfig(
    client_id=ClientId("BINANCE"),
    instrument_ids=[instrument_id],
)

# With subscribe methods
config = DataTesterConfig(
    client_id=ClientId("BINANCE"),
    instrument_ids=[instrument_id],
).with_subscribe_quotes()

config = DataTesterConfig(
    client_id=ClientId("BINANCE"),
    instrument_ids=[instrument_id],
).with_subscribe_trades()

config = DataTesterConfig(
    client_id=ClientId("BINANCE"),
    instrument_ids=[instrument_id],
).with_subscribe_bars(bar_type=BarType.MINUTE)

# Order book variants
config = DataTesterConfig(
    client_id=ClientId("BINANCE"),
    instrument_ids=[instrument_id],
).with_subscribe_book_deltas(book_type=BookType.L2_MBP)

config = DataTesterConfig(
    client_id=ClientId("BINANCE"),
    instrument_ids=[instrument_id],
).with_subscribe_book_depth(book_type=BookType.L2_MBP, depth=10)

# Instrument discovery
config = DataTesterConfig(
    client_id=ClientId("BINANCE"),
    instrument_ids=[instrument_id],
).with_request_instruments()

config = DataTesterConfig(
    client_id=ClientId("BINANCE"),
    instrument_ids=[instrument_id],
).with_subscribe_instrument()
```

### Data Validation Flow

1. Configure `DataTesterConfig` with subscription type
2. Runner subscribes and collects data for a configurable duration
3. Validates received data against expected schema
4. Checks for gaps, stale data, or malformed messages
5. Reports pass/fail per subscription type

**Full spec**: See `references/developer_guide/spec_data_testing.md` for per-adapter test configurations.

## Execution Testing Spec

The ExecTesterConfig API validates order lifecycle per venue. Each adapter has specific execution test configs.

### ExecTesterConfig API

```python
from nautilus_trader.test.adapters import ExecTesterConfig

# Basic execution test
config = ExecTesterConfig(
    strategy_id=StrategyId("test-strat"),
    instrument_id=instrument_id,
    client_id=ClientId("BINANCE"),
    order_qty=Quantity.from_str("0.001"),
)

# With specific features
config = ExecTesterConfig(
    strategy_id=StrategyId("test-strat"),
    instrument_id=instrument_id,
    client_id=ClientId("BINANCE"),
    order_qty=Quantity.from_str("0.01"),
).with_enable_limit_buys()

config = ExecTesterConfig(
    strategy_id=StrategyId("test-strat"),
    instrument_id=instrument_id,
    client_id=ClientId("BINANCE"),
    order_qty=Quantity.from_str("0.01"),
).with_enable_limit_sells()

config = ExecTesterConfig(
    strategy_id=StrategyId("test-strat"),
    instrument_id=instrument_id,
    client_id=ClientId("BINANCE"),
    order_qty=Quantity.from_str("0.01"),
).with_use_post_only()

# Reject tests
config = ExecTesterConfig(
    strategy_id=StrategyId("test-strat"),
    instrument_id=instrument_id,
    client_id=ClientId("BINANCE"),
    order_qty=Quantity.from_str("0.01"),
).with_test_reject_post_only()
```

### Execution Validation Flow

1. Configure `ExecTesterConfig` with order parameters
2. Runner submits orders via the adapter
3. Monitors order state transitions (SUBMITTED → ACCEPTED → FILLED, etc.)
4. Validates fills, rejects, and cancellations against expected behavior
5. Reports pass/fail per order type

**Full spec**: See `references/developer_guide/spec_exec_testing.md` for per-adapter execution test configurations.

## Test Datasets

### Categories

| Category | Size | Storage | Access |
|----------|------|---------|--------|
| **Small data** | < 1 MB | `tests/test_data/<source>/` | Always available |
| **Large data** | > 1 MB | R2 bucket (Parquet) | Downloaded on first use |
| **User-fetched** | Any | Local only | Requires vendor account |

### Required Metadata

Every dataset has a `metadata.json`:

```json
{
  "source": "binance",
  "instrument_id": "BTCUSDT-PERP.BINANCE",
  "data_type": "trade_ticks",
  "time_range": {"start": "2024-01-01T00:00:00Z", "end": "2024-01-01T23:59:59Z"},
  "record_count": 1440000,
  "sha256": "abc123..."
}
```

### Large Data: Checksums

`tests/test_data/large/checksums.json` records SHA-256 for each file. The `ensure_test_data_exists()` helper:
1. Checks if file exists locally
2. Downloads from R2 if missing
3. Verifies SHA-256 checksum
4. Raises on integrity failure

### Regenerating Datasets

When schema changes invalidate Parquet files:

```bash
# Regenerate from source
pytest tests/test_data_curation/ -v

# Verify new checksums
sha256sum /tmp/<output_file>
# Update checksums.json
```

## Memory Leak Testing

- **Valgrind**: Run under valgrind to detect leaks
- **ASAN**: Address Sanitizer for Rust builds (`RUSTFLAGS="-Z sanitizer=address"`)
- **Drop verification**: Ensure `Drop` implementations free all resources

## CI Patterns

### GitHub Actions

- Tests run on every PR and push
- Rust tests use `cargo test --workspace`
- Python tests use `pytest tests/ -n auto`
- Pre-commit hooks run: `ruff format`, `ruff check`, `rustfmt`, `clippy`

### Local CI Parity

```bash
# Before pushing, run locally:
make format && make pre-commit
```

## Key Conventions

- Tests are executable specifications — they document intended behavior
- Each test must be independent and deterministic
- Use `proptest` for invariant checking, not just example-based tests
- Adapter tests use DataTesterConfig/ExecTesterConfig specs, not custom harnesses
- Large test data is never checked into git — use R2 + checksums
- Test dataset metadata must be complete and accurate
- CI must pass before merge — fix locally first with `make pre-commit`

## References

- `references/developer_guide/testing.md` — Full testing guide
- `references/developer_guide/spec_data_testing.md` — Data testing spec per adapter
- `references/developer_guide/spec_exec_testing.md` — Execution testing spec per adapter
- `references/developer_guide/test_datasets.md` — Dataset curation standards
- `references/developer_guide/contracts/testing_policy.md` — Current testing policy contract
