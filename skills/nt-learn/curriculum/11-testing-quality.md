# Stage 11: Testing & Quality

## Goal

Master the NautilusTrader testing framework — from unit tests to adapter validation specs.

## Prerequisites

- Stage 10 completed (can build NT from source)
- Familiarity with Rust toolchain (`cargo test`)
- Python testing with `pytest`

## Concepts

### Test Categories

NT has 7 test categories forming a comprehensive quality pyramid:

1. **Unit tests** — single functions, types, modules
2. **Integration tests** — multi-component interactions
3. **Acceptance tests** — end-to-end workflows
4. **Performance tests** — Criterion/iai benchmarks
5. **Property-based tests** — invariant checking with `proptest`
6. **Fuzzing** — malformed input resilience
7. **Memory leak tests** — drop verification, ASAN

### Property-Based Testing

Use `proptest` to verify invariants hold for *all* valid inputs:

```rust
use proptest::prelude::*;

proptest! {
    #[test]
    fn price_round_trip(value in any::<f64>().prop_filter("positive", |v| *v > 0.0)) {
        let price = Price::new(value, 8).unwrap();
        let parsed = Price::from_str(&price.to_string()).unwrap();
        assert_eq!(price, parsed);
    }
}
```

### Adapter Testing

Use `DataTesterConfig` and `ExecTesterConfig` to validate adapter behavior:

```python
# Data testing
config = DataTesterConfig(
    client_id=ClientId("BINANCE"),
    instrument_ids=[instrument_id],
).with_subscribe_trades()

# Execution testing
config = ExecTesterConfig(
    strategy_id=StrategyId("test"),
    instrument_id=instrument_id,
    client_id=ClientId("BINANCE"),
    order_qty=Quantity.from_str("0.001"),
).with_enable_limit_buys()
```

### Test Datasets

Three categories:
- **Small** (<1MB): checked into `tests/test_data/<source>/`
- **Large** (>1MB): hosted on R2, downloaded via `ensure_test_data_exists()`
- **User-fetched**: vendor-licensed, requires user's own account

### Benchmarking

- **Criterion**: Statistical benchmarking with HTML reports
- **iai**: Deterministic instruction counting for CI gating

### FFI Memory Contract

Understand the CVec lifecycle for safe FFI:
1. Rust builds `Vec<T>` and leaks via `into()`
2. Foreign code uses data (never modify `ptr`, `len`, `cap`)
3. Foreign code calls type-specific drop helper exactly once

## Exercises

1. **Write a property test**: Create a `proptest` test for `Quantity` that verifies commutativity of addition
2. **Run the full test suite**: `make test` and analyze results
3. **Create a DataTesterConfig**: Set up data tests for an existing adapter
4. **Write a Criterion benchmark**: Benchmark a parsing function in any crate
5. **Run under ASAN**: Build with Address Sanitizer and run tests

## Checkpoint

You can:
- Write all 7 types of tests for NT components
- Use DataTesterConfig/ExecTesterConfig for adapter validation
- Manage test datasets (create, checksum, regenerate)
- Set up benchmarking with Criterion and iai
- Understand the FFI memory contract

## Key Skills

- `nt-testing` — full testing framework reference
- `nt-dev` — benchmarking, FFI, coding standards

## Next

Stage 12: Adapter Development →
