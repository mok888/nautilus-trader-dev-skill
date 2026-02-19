# DEX Adapter Compliance Checklist

Every custom DEX adapter must clear this checklist before use in backtesting or live trading.
Run the structural compliance test first:

```bash
uv run pytest skills/nt-dex-adapter/tests/test_dex_compliance.py -v
```

Then complete the manual checklist below.

---

## Python Layer

### InstrumentProvider

- [ ] `load_all_async()` implemented and fetches from chain/RPC
- [ ] `load_ids_async(instrument_ids)` implemented
- [ ] `get_all()` returns `dict[InstrumentId, Instrument]`
- [ ] `find(instrument_id)` returns `Instrument | None`
- [ ] Instrument IDs formatted as `{SYMBOL}.{VENUE}`
- [ ] Token fee tier mapped to `maker_fee` / `taker_fee` on instrument
- [ ] Minimum quantity set from pool/market minimum trade size
- [ ] `sandbox_mode` skips mainnet RPC calls during tests

### LiveMarketDataClient

- [ ] `_connect()` calls `load_all_async()` on instrument provider
- [ ] `_disconnect()` cancels polling tasks / closes WS connections
- [ ] `_subscribe_quote_ticks(instrument_id)` implemented
- [ ] `_subscribe_trade_ticks(instrument_id)` implemented
- [ ] `_subscribe_order_book_deltas(instrument_id)` implemented (or documented as N/A for AMM)
- [ ] `_unsubscribe_quote_ticks` / `_unsubscribe_trade_ticks` / `_unsubscribe_order_book_deltas` implemented
- [ ] `_handle_quote_tick()` called for each new pool state
- [ ] `_handle_trade_tick()` called for each confirmed on-chain swap
- [ ] No blocking RPC calls in any handler method
- [ ] Reconnection logic with exponential backoff

### LiveExecutionClient

- [ ] `_connect()` verifies wallet balance and establishes stream
- [ ] `_disconnect()` shuts down cleanly
- [ ] `_submit_order(order)` builds, signs, and broadcasts tx
- [ ] `_cancel_order(order)` supported or raises `NotImplementedError` with explanation
- [ ] `_cancel_all_orders(instrument_id)` supported or raises `NotImplementedError`
- [ ] `_query_order(client_order_id)` queries on-chain status
- [ ] `generate_account_state()` called after every balance-changing tx
- [ ] `generate_order_status_report()` implemented for reconciliation
- [ ] Transaction revert → `generate_order_rejected()` (NOT silent drop)
- [ ] Gas cost included as `commission` in `generate_order_filled()`
- [ ] Slippage tolerance applied to `min_amount_out` before submission

### Configuration

- [ ] Private key uses `SecretStr` (not plain `str`)
- [ ] RPC URL configurable via env var or config field (not hardcoded)
- [ ] `sandbox_mode: bool` flag present on exec client config
- [ ] `max_slippage_bps: int` configurable
- [ ] Gas limit configurable with safe default
- [ ] `InstrumentProviderConfig`, `DataClientConfig`, `ExecClientConfig` all defined

### Factory

- [ ] `ClientFactory` class defined with:
  - `create_live_data_client()` class method
  - `create_live_exec_client()` class method
- [ ] Factory registered with `TradingNode` via:
  ```python
  node.add_data_client_factory("VENUE_NAME", MyDEXLiveDataClientFactory)
  node.add_exec_client_factory("VENUE_NAME", MyDEXLiveExecClientFactory)
  ```

---

## Rust Core (if applicable)

- [ ] Copyright header on every source file (`2015-2026 Nautech Systems Pty Ltd`)
- [ ] Module-level `//!` documentation
- [ ] `new_checked()` + `new()` constructor pattern on all types
- [ ] `anyhow::bail!` for early error returns (not `Err(anyhow::anyhow!(...))`)
- [ ] `FAILED` constant used in `.expect()` calls
- [ ] `AHashMap`/`AHashSet` for price/instrument caches
- [ ] Standard `HashMap` for RPC client configuration
- [ ] `get_runtime().spawn()` for all async tasks (NOT `tokio::spawn()`)
- [ ] `abort_on_panic` wrapper on every `extern "C"` FFI function
- [ ] Matching `drop` function for every FFI constructor
- [ ] Type-specific CVec drop functions (if CVec used)
- [ ] No `Arc<PyObject>` (use plain `PyObject` + `clone_py_object()`)
- [ ] `py_*` prefix on all Rust functions exposed via PyO3
- [ ] `SAFETY:` comment on every `unsafe` block
- [ ] `#[repr(C)]` on all FFI types
- [ ] `#![deny(unsafe_op_in_unsafe_fn)]` in crate root
- [ ] No `.unwrap()` in production code
- [ ] No `.clone()` in hot paths

---

## Testing

- [ ] **Unit: instrument parsing** — pool metadata → Nautilus instrument round-trip
- [ ] **Unit: quote synthesis** — pool reserves → `QuoteTick` correct mid-price
- [ ] **Unit: order book builder** — pool state → L2 order book levels
- [ ] **Unit: slippage model** — `amount_in` → `execution_price` follows AMM formula
- [ ] **Unit: signing interface** — tx builder produces deterministic output (mock key)
- [ ] **Integration: BacktestEngine** — adapter wired into engine with mock DEX data, runs without error
- [ ] **Compliance structural test** — `test_dex_compliance.py` passes all method presence checks
- [ ] **No live RPC required** — all tests run offline with mocks/fixtures

---

## Documentation

- [ ] README: supported pool/market types
- [ ] README: RPC endpoint requirements and rate limits
- [ ] README: gas configuration guidance
- [ ] README: testnet / local fork configuration
- [ ] README: known limitations (e.g., cancel not supported on AMM, no partial fills)
- [ ] CHANGELOG or version history if adapter is updated

---

## Sign-Off

| Item | Status | Notes |
|---|---|---|
| Python layer complete | ☐ / ✓ | |
| Rust core complete (if applicable) | ☐ / ✓ | N/A if Python-only |
| All tests pass offline | ☐ / ✓ | |
| Compliance structural test passes | ☐ / ✓ | |
| Documentation complete | ☐ / ✓ | |
| Reviewed with nt-review Rust/FFI checklist | ☐ / ✓ | |
| **APPROVED FOR USE** | ☐ / ✓ | |
