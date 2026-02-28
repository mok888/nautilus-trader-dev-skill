---
name: nt-strategy-builder
description: "Use when building backtesting or live-trading systems in NautilusTrader. Covers BacktestEngine, TradingNode, multi-venue data wiring (CeFi + custom DEX adapters), fill/margin model configuration, and paper trading. Includes explicit DO/DON'Ts rules and a test suite."
---

# Strategy Builder

## Overview

This skill guides you from **idea → running system** — whether you are running a historical backtest, paper-trading on live market data, or deploying a live-trading node. It handles all supported venue data inputs: standard CeFi adapters (Binance, Bybit, OKX, …), custom DEX adapters built with `nt-dex-adapter`, Databento/Tardis data feeds, and mixed multi-venue setups.

Complements the existing skills:
- **nt-architect** – use first to decide component decomposition (Actor/Indicator/Strategy split)
- **nt-implement** – use to write the individual Strategy/Actor components
- **nt-dex-adapter** – use to build a custom DEX adapter that plugs into this skill's venue wiring

## When to Use

| Scenario | Approach |
|---|---|
| Replay historical data, no live connection | `BacktestEngine` + `ParquetDataCatalog` |
| Test strategy on live data without real orders | `TradingNode` in paper-trading mode |
| Deploy to production with CeFi exchange | `TradingNode` + standard adapter |
| Deploy with custom DEX venue | `TradingNode` + `nt-dex-adapter` factory |
| Multi-venue arb or signal aggregation | Multi-venue `TradingNode` or `BacktestEngine` |

## Decision Tree: Which Execution Mode?

```
Are you using live market data?
│
├─ NO  ──► BacktestEngine
│           ├─ Single venue  → templates/backtest_node.py
│           ├─ DEX venue     → templates/dex_venue_input.py
│           └─ Multi-venue   → templates/multi_venue_strategy.py
│
└─ YES ──► TradingNode
            ├─ Real orders?
            │   ├─ YES → templates/live_node.py
            │   └─ NO  → templates/paper_node.py
            └─ With DEX adapter → templates/dex_venue_input.py
```

## Venue Data Input Types

### 1. Standard CeFi Adapters (Built-in)

NautilusTrader ships adapters for Binance, Bybit, OKX, Coinbase IntX, dYdX, IB, Databento, Tardis, and more.

Use venue/integration availability from the current NautilusTrader release and prefer dYdX v4 guidance for on-chain CLOB workflows.

```python
from nautilus_trader.adapters.binance.factories import BinanceLiveDataClientFactory
from nautilus_trader.config import TradingNodeConfig, LiveDataEngineConfig

config = TradingNodeConfig(
    data_clients={
        "BINANCE": BinanceDataClientConfig(
            api_key=os.environ["BINANCE_API_KEY"],
            api_secret=os.environ["BINANCE_API_SECRET"],
            testnet=False,
        ),
    },
)
```

### 2. Custom DEX Adapter (nt-dex-adapter)

After building a DEX adapter with the `nt-dex-adapter` skill, wire it in exactly like a CeFi adapter:

```python
from my_dex_adapter.factory import MyDEXLiveDataClientFactory, MyDEXLiveExecClientFactory

config = TradingNodeConfig(
    data_clients={"MYDEX": MyDEXDataClientConfig(rpc_url="https://...", wallet_address="0x...")},
    exec_clients={"MYDEX": MyDEXExecClientConfig(rpc_url="https://...", private_key=SecretStr(...))},
    data_client_factories={"MYDEX": MyDEXLiveDataClientFactory},
    exec_client_factories={"MYDEX": MyDEXLiveExecClientFactory},
)
```

See `templates/dex_venue_input.py` for a complete wiring example.

### 3. Catalog Data (Backtest / Replay)

Use `ParquetDataCatalog` for any historical data — CeFi, DEX, or custom:

```python
from nautilus_trader.persistence.catalog import ParquetDataCatalog
from nautilus_trader.config import BacktestDataConfig

catalog = ParquetDataCatalog("/path/to/catalog")

data_config = BacktestDataConfig(
    catalog_path=str(catalog.path),
    data_cls="nautilus_trader.model.data:Bar",
    instrument_id="WETH-USDC.UNISWAP_V3",
    start_time="2024-01-01",
    end_time="2024-12-31",
)
```

### 4. Multi-Venue (Mixed CeFi + DEX)

Wire multiple venues into a single `TradingNode` or `BacktestEngine`. Each venue gets its own:
- `data_client` entry
- `exec_client` entry (if trading)
- `BacktestVenueConfig` (backtest) / `LiveDataEngineConfig` (live)

See `templates/multi_venue_strategy.py`.

## Template Quick Reference

| Template | When to use |
|---|---|
| `backtest_node.py` | Full backtest with catalog data, custom FillModel/MarginModel |
| `live_node.py` | Production TradingNode with reconciliation, timeouts, persistence |
| `paper_node.py` | Paper-trading: real market data, simulated execution |
| `dex_venue_input.py` | Wire a custom DEX adapter as venue (backtest or live) |
| `multi_venue_strategy.py` | Strategy consuming data from 2+ venues simultaneously |

## Modern Tooling Standards
- **Project Management**: Use `uv` for lightning-fast dependency resolution and environment management (see `docs/uv_guide.md`).
- **Serialization**: Prefer `msgspec.Struct` for custom data types over standard dataclasses for 10-100x speedups (see `docs/serialization.md`).
- **Visualization**: Use the new `BacktestVisualizer` (Plotly-based) for interactive tearsheets instead of static matplotlib plots (see `docs/visualization.md`).

## Implementation Workflow

1. **Design** components with `nt-architect`
2. **Implement** Strategy/Actor/Indicator with `nt-implement`
3. **Wire venue(s)** using templates in this skill:
   a. Choose backtest / paper / live mode
   b. Configure venues (CeFi builtin or DEX via `nt-dex-adapter`)
   c. Configure data sources (catalog or live feeds)
4. **Configure simulation models** (FillModel, MarginModel) for backtest realism
5. **Review** with `nt-review` before live deployment

## Adapter Wiring Contract (2026 Guide Alignment)

When wiring any custom adapter into `TradingNode` or `BacktestEngine`, verify these invariants:

- Adapter implementation reached at least phases 1-4 before live order flow is enabled.
- Data and execution factories expose canonical static `create(loop, name, config, msgbus, cache, clock)` signatures.
- Provider + data + execution method contracts are complete (no placeholder methods).
- Reconciliation/report paths are enabled and validated before production mode.
- Adapter tests include provider/data/execution/factory integration coverage using realistic fixture payloads.

If any invariant fails, block deployment and return to `nt-dex-adapter` + `nt-review` loops.

## Simulation Model Patterns

### FillModel — Backtest Realism

```python
from nautilus_trader.backtest.models import FillModel

# DEX-realistic: high slippage, lower limit fill probability
dex_fill_model = FillModel(
    prob_fill_on_limit=0.3,   # DEX: limit orders rarely at exact price
    prob_fill_on_stop=1.0,    # Stop → market on DEX
    prob_slippage=0.7,        # DEX: high slippage probability
    random_seed=42,
)

# CeFi realistic
cefi_fill_model = FillModel(
    prob_fill_on_limit=0.5,
    prob_fill_on_stop=1.0,
    prob_slippage=0.2,
    random_seed=42,
)
```

### BacktestVenueConfig — Account Types

```python
from nautilus_trader.backtest.config import BacktestVenueConfig

# Crypto spot
venue_config = BacktestVenueConfig(
    name="BINANCE",
    oms_type="NETTING",
    account_type="CASH",
    base_currency="USDT",
    starting_balances=["10_000 USDT", "1 BTC"],
    fill_model=fill_model,
)

# DEX (treat as CASH, no margin)
dex_venue_config = BacktestVenueConfig(
    name="UNISWAP_V3",
    oms_type="NETTING",
    account_type="CASH",
    base_currency="USDT",
    starting_balances=["10_000 USDT"],
    fill_model=dex_fill_model,
)

# Futures / perps
perp_venue_config = BacktestVenueConfig(
    name="BYBIT",
    oms_type="NETTING",
    account_type="MARGIN",
    base_currency="USDT",
    starting_balances=["10_000 USDT"],
    default_leverage=Decimal("10"),
    fill_model=fill_model,
)
```

## DO and DON'Ts

See `rules/dos_and_donts.md` for the full curated ruleset with rationale.

### Critical DON'Ts (red flags)

- ❌ Never block in `on_bar` / handlers (no HTTP, no file I/O, no `time.sleep()`)
- ❌ Never assume `self.cache.instrument()` is non-None
- ❌ Never use raw `float` for Price/Quantity on instrument
- ❌ Never set `reconciliation=False` for live trading without documented justification
- ❌ Never put ML inference inside Strategy (use Actor)
- ❌ Never use `datetime.utcnow()` — use `self.clock.utc_now()`

## Testing

New code built from these templates should pass the included test suite:

```bash
# From repo root
uv run pytest skills/nt-strategy-builder/tests/ -v
```

Tests cover:
- `test_backtest_patterns.py` — venue config, fill model, catalog round-trip
- `test_live_node_config.py` — TradingNode config builds without error
- `test_dex_as_venue.py` — DEX adapter wired into BacktestEngine
- `test_multi_venue.py` — multi-venue data routing

## References

Load these for detailed API information (relative to nt-implement skill folder):
- `references/concepts/backtesting.md` — BacktestEngine, venue config, fill models
- `references/concepts/live.md` — TradingNode, reconciliation, timeouts
- `references/api_reference/backtest.md` — BacktestEngine, BacktestVenueConfig API
- `references/api_reference/live.md` — LiveDataClient, LiveExecutionClient API
- `references/developer_guide/adapters.md` — Adapter development guide

## Next Steps

- To build a custom DEX adapter: use **nt-dex-adapter**
- To implement Strategy/Actor components: use **nt-implement**
- To review before deployment: use **nt-review**
