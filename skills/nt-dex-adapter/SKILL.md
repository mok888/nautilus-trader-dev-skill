---
name: nt-dex-adapter
description: "Use when building a custom DEX adapter that fully complies with NautilusTrader's adapter standard. Covers DEX-specific instrument discovery, on-chain data normalisation, wallet-signed order execution, and the 7-phase implementation sequence. Includes DO/DON'Ts rules, a compliance checklist, and a test suite."
---

# Custom DEX Adapter

## Overview

Build a custom on-chain DEX adapter that plugs into NautilusTrader's adapter framework — identical in structure to the built-in OKX, Bybit, or BitMEX adapters, but with DEX-specific plumbing (RPC nodes, wallet signing, pool discovery) instead of REST/WebSocket API keys.

Once built, your adapter is consumed by the `nt-strategy-builder` skill's `dex_venue_input.py` template with zero framework changes.

**Canonical CeFi reference adapters**: OKX, BitMEX, Bybit — study their Python layer and Rust core before customising.

## When to Use

| DEX Type | Notes |
|---|---|
| AMM (Uniswap V2/V3, Curve) | No order book — synthesise `QuoteTick` from pool reserves |
| On-chain CLOB (dYdX v4, Hyperliquid) | Use existing dYdX/Hyperliquid adapters as starting points |
| Perp DEX (GMX, Synthetix) | Use `CryptoPermanentContract` instrument type |
| Cross-chain DEX | Implement per-chain data client; share execution client logic |

## DEX vs CeFi Key Differences

| Aspect | CeFi Adapter | DEX Adapter |
|---|---|---|
| Authentication | API key + secret | Wallet private key + signature |
| Market data | WebSocket streams | RPC polling or event subscription |
| Order book | L2 snapshot + delta | Derived from pool state (AMM) or on-chain updates |
| Order execution | REST/WebSocket | Signed Ethereum/Solana/Cosmos transaction |
| Order lifecycle | Exchange-managed | On-chain confirmation + receipt |
| Account state | REST balance query | On-chain wallet balance |
| Reconciliation | Order status REST | On-chain transaction history |
| Fill price | Exchange-reported | Actual tx output amount |

## 7-Phase Implementation Sequence

This maps directly to the canonical adapter implementation pattern. Complete each phase fully before moving to the next.

### Phase 1: Rust Core Infrastructure (if Rust-first)
- HTTP JSON-RPC client in `crates/adapters/my_dex/` using **`nautilus_network::http::HttpClient`** (not `reqwest` directly — this provides built-in rate limiting, retry logic, and consistent error handling matching the canonical adapters)
- WebSocket event subscription client using `nautilus_network::websocket::WebSocketClient`
- Wallet signing utilities (ECDSA for EVM, ed25519 for Solana) — implement in Rust core, never in Python layer
- Types: config structs, RPC response models

### Phase 2: Instrument Discovery
- `InstrumentProvider.load_all_async()` → fetch pool/market addresses from chain
- Parse pool metadata → `CurrencyPair` or `CryptoPermanentContract`
- Map on-chain tokens to Nautilus `Currency` objects
- Normalise instrument IDs to `{POOL_SYMBOL}.{VENUE}` format

### Phase 3: Market Data
- AMM: synthesise `QuoteTick` from pool reserves (`x*y=k` price)
- CLOB DEX: map order book events → `OrderBookDelta`
- On-chain trades → `TradeTick`
- Polling Actor pattern (if no event subscription available)

### Phase 4: Order Execution
- `_submit_order()` → build + sign tx → submit via RPC
- `_cancel_order()` → on-chain cancel (if supported)
- `_cancel_all_orders()` → batch cancel or position close
- Handle tx inclusion + revert vs success → emit correct Nautilus events

### Phase 5: Account & Position Events
- `generate_account_state()` after each balance-changing tx
- On-chain wallet balance → `AccountBalance`
- Position tracking (DEX perps: on-chain position query)
- `generate_order_status_report()` for reconciliation

### Phase 6: Configuration & Factory
- `InstrumentProviderConfig`, `DataClientConfig`, `ExecClientConfig`
- `ClientFactory` class registered with `TradingNode`
- `sandbox_mode: bool` flag for test networks / local fork

### Phase 7: Testing & Documentation
- Unit tests: instrument parsing, quote synthesis, tx building
- Integration test: BacktestEngine with mock DEX data
- Compliance checklist: `rules/compliance_checklist.md`
- README: RPC requirements, supported pool types, gas configuration

## Rust-First Architecture

```
crates/adapters/my_dex/           ← Rust core
  src/
    lib.rs
    client.rs        ← HTTP JSON-RPC client
    ws_client.rs     ← WebSocket event client (if available)
    signing.rs       ← Wallet key management + tx signing
    types.rs         ← RPC response structs, pool state types
    python/          ← PyO3 bindings

nautilus_trader/adapters/my_dex/  ← Python layer
  __init__.py
  config.py          ← Pydantic configs
  providers.py       ← InstrumentProvider
  data.py            ← LiveMarketDataClient
  execution.py       ← LiveExecutionClient
  factory.py         ← ClientFactory
  utils.py           ← DEX-specific helpers (AMM math, ABI decoding)
```

## Template Quick Reference

| Template | Phase | Purpose |
|---|---|---|
| `dex_config.py` | 6 | Provider, data, exec configs |
| `dex_instrument_provider.py` | 2 | On-chain pool → Nautilus instrument |
| `dex_data_client.py` | 3 | Pool state polling → QuoteTick/OrderBookDelta |
| `dex_exec_client.py` | 4–5 | Wallet-signed tx submission + account state |
| `dex_factory.py` | 6 | ClientFactory wiring |
| `dex_order_book_builder.py` | 3 | AMM pool reserves → L2 order book |

## DO and DON'Ts

See `rules/dos_and_donts.md` for the full ruleset.

### Critical DEX-Specific Rules (red flags)

- ❌ Never poll chain in `on_bar`/`on_quote_tick` handlers — use a polling Actor or timer
- ❌ Never store private keys as plain `str` — use `SecretStr` or env-var injection
- ❌ Never skip `generate_order_status_report()` — needed for reconciliation
- ❌ Never use `tokio::spawn()` in adapter Rust code — use `get_runtime().spawn()`
- ❌ Never use `Arc<PyObject>` — use plain `PyObject` with `clone_py_object()`
- ❌ Don't treat AMM spot price as fill price without modelling slippage

## Compliance Checklist

Every adapter must clear `rules/compliance_checklist.md` before use. Run the structural compliance test:

```bash
uv run pytest skills/nt-dex-adapter/tests/test_dex_compliance.py -v
```

## Modern Tooling Standards
- **Dependencies**: Use `uv` for managing the adapter dev environment.
- **Serialization**: For internal data passing, `msgspec` structs are faster than standard classes.
- **Visualization**: Verify your data feed quality using `BacktestVisualizer` on recorded data.

## Testing Strategy

```bash
# All DEX adapter tests
uv run pytest skills/nt-dex-adapter/tests/ -v

# Structural compliance only (fastest gate)
uv run pytest skills/nt-dex-adapter/tests/test_dex_compliance.py -v
```

## References

Load these for detailed API information (relative to nt-implement skill folder):
- `references/developer_guide/adapters.md` — Rust-first adapter development guide
- `references/developer_guide/rust.md` — Rust conventions, async runtime patterns
- `references/developer_guide/ffi.md` — FFI memory contract, CVec, abort_on_panic
- `references/api_reference/live.md` — LiveMarketDataClient, LiveExecutionClient APIs
- `references/integrations/dydx.md` — On-chain CLOB reference adapter
- `references/integrations/hyperliquid.md` — DEX perp reference adapter

## Next Steps

- Wire your adapter: use **nt-strategy-builder** `dex_venue_input.py`
- Review code: use **nt-review** Rust/FFI checklist before deployment
