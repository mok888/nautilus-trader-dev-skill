# NT-DEX-ADAPTER

Custom DEX adapter development for NautilusTrader.

## OVERVIEW

Build production-grade DEX adapters identical in structure to built-in OKX/Bybit adapters, but with DEX plumbing (RPC, wallet signing, pool discovery).

## WHEN TO USE

| DEX Type | Approach |
|----------|----------|
| AMM (Uniswap, Curve) | Synthesize QuoteTick from reserves |
| On-chain CLOB (dYdX v4) | Use dYdX adapter as reference |
| Perp DEX (GMX) | CryptoPerpetual instrument |

## DEX vs CeFi

| Aspect | CeFi | DEX |
|--------|------|-----|
| Auth | API key | Wallet private key |
| Data | WebSocket | RPC polling/events |
| Orders | REST | Signed transaction |
| Fills | Exchange-reported | Tx output amount |

## 7-PHASE IMPLEMENTATION

1. **Rust Core** — HTTP JSON-RPC client, WebSocket, wallet signing
2. **Instrument Discovery** — Pool/market addresses → Nautilus instruments
3. **Market Data** — QuoteTick synthesis, TradeTick from on-chain
4. **Order Execution** — Build + sign + submit tx
5. **Account Events** — Balance, position tracking
6. **Config & Factory** — ClientFactory for TradingNode
7. **Testing** — Unit + integration + compliance

## ADAPTER CANONICAL CONTRACT (2026)

- Keep phase order fixed: Rust infra -> instruments -> market data -> execution/reconciliation -> advanced -> config/factory -> tests/docs
- Implement complete provider/data/exec method contracts before marking adapter ready
- Use `get_runtime().spawn()` in adapter Rust runtime paths
- Never use `Arc<PyObject>` in bindings; avoid blocking hot handlers
- Prefer real payload fixtures and condition-based async waits in tests

## ARCHITECTURE

```
crates/adapters/my_dex/     ← Rust core (client, signing, types)
nautilus_trader/adapters/   ← Python layer (config, providers, factory)
```

## TEMPLATES

| Template | Phase | Purpose |
|----------|-------|---------|
| `dex_config.py` | 6 | Provider/data/exec configs |
| `dex_instrument_provider.py` | 2 | Pool → Instrument |
| `dex_data_client.py` | 3 | Pool state → QuoteTick |
| `dex_exec_client.py` | 4-5 | Wallet-signed tx |
| `dex_factory.py` | 6 | ClientFactory |

## CRITICAL DON'Ts

- ❌ Poll chain in handlers — use polling Actor
- ❌ Store private keys as plain str — use SecretStr
- ❌ Skip `generate_order_status_report()`
- ❌ Use `tokio::spawn()` — use `get_runtime().spawn()`
- ❌ Use `Arc<PyObject>` — memory leak

## TESTING

```bash
uv run pytest skills/nt-dex-adapter/tests/ -v
uv run pytest skills/nt-dex-adapter/tests/test_dex_compliance.py -v
```

## REFERENCE ADAPTERS

Study: `_template`, OKX, BitMEX, Bybit (built-in), dYdX v4, Hyperliquid

## NEXT

- Wire adapter → `nt-strategy-builder/dex_venue_input.py`
- Review code → `nt-review` (Rust/FFI checklist)
