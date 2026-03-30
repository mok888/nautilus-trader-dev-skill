# nt-implement Knowledge Base

**Purpose:** Implement NautilusTrader components using correct patterns and templates. Covers Python components, simulation models, Rust+PyO3 bindings, and adapter development.

**Entry Point:** `SKILL.md` (1058 lines)

## TEMPLATE QUICK REFERENCE (15 files)

| Need | Template | Key Feature |
|------|----------|-------------|
| Trading logic, orders | `strategy.py` | `submit_order()`, `market_exit()`, position management |
| Model inference, signals | `actor.py` | `publish_signal()`, `publish_data()` |
| Stateless calculations | `indicator.py` | `handle_bar()`, pure computation |
| Structured data between components | `custom_data.py` | `@customdataclass`, serialization |
| Order execution logic | `exec_algorithm.py` | Child order spawning |
| Exchange connectivity (data+exec) | `adapters/exchange.py` | LiveDataClient, LiveExecutionClient |
| Data-only adapter | `adapters/data_provider.py` | Data streaming only |
| Internal (simulated) adapter | `adapters/internal.py` | Backtest venue adapter |
| Exchange-specific config example | `adapters/kraken_config.py` | Venue configuration patterns |
| Custom fill simulation | `fill_model.py` | `prob_fill_on_limit`, `prob_slippage` |
| Custom margin calculation | `margin_model.py` | `calculate_margin_init/maint` |
| Custom portfolio statistics | `portfolio_statistic.py` | `calculate_from_orders/positions` |
| Risk configuration | `risk_config.py` | Risk check patterns |
| Backtest visualization | `backtest_viz.py` | Plotly tearsheet config |
| Cap'n Proto schema | `capnp_schema.capnp` | Zero-copy serialization schema |

## IMPLEMENTATION WORKFLOW

Dependency order:
1. Custom Data Types (if needed)
2. Custom Models (FillModel, MarginModel if backtesting)
3. Indicators
4. Actors
5. Strategies
6. Execution Algorithms (if needed)
7. Portfolio Statistics (for analysis)

Validate each component before proceeding to the next.

## v1.223.0 API ADDITIONS (2026-02-21)

| Feature | Usage |
|---------|-------|
| `strategy.market_exit(instrument_id)` | Fully close position with market order |
| `StrategyConfig.manage_stop = True` | Auto-calls `market_exit()` on strategy stop |
| `PerpetualContract` | Prefer over `CryptoPerpetual` for new implementations |
| `request_funding_rates()` / `FundingRateUpdate` | Funding rate data streams |
| `BacktestDataConfig.optimize_file_loading` | Faster Parquet loading for large backtests |
| `trade_execution` default `True` | Set `False` explicitly for bar-only matching |

## KEY IMPLEMENTATION PATTERNS

### Model Loading
- **Preferred:** `msgspec.msgpack.decode()` — fast, typed deserialization
- **ONNX:** `ort.InferenceSession` in `on_start`, inference in `on_bar`
- **Never** load models in hot handlers — always `on_start`

### Data Catalog
- `ParquetDataCatalog` for persistence
- Write instruments before other data
- Use `BacktestDataConfig` for custom data with `metadata` dict

### Multi-Timeframe
- Define `BarType` for each timeframe
- Use internal aggregation: `5-MINUTE-LAST-INTERNAL@1-MINUTE-EXTERNAL`
- Request historical for all, then subscribe live

### Position Sizing
- Use `instrument.make_qty()` for precision (never raw `float`)
- Check `min_quantity` / `max_quantity`
- Risk-based: `(equity * risk_per_trade) / (ATR * multiplier)`

### Risk Checks
- Pre-trade validation: position limits, exposure limits, daily loss
- Use `self.portfolio.net_position()` and `self.portfolio.net_exposure()`

## ADAPTER CANONICAL CONTRACT

**7-Phase Implementation Sequence:**
1. Rust core infrastructure (HTTP/WS clients, types, config)
2. Instrument definitions (parsing, normalization)
3. Market data (quotes, trades, order books)
4. Order execution (submit, modify, cancel)
5. Advanced features (account events, position tracking)
6. Configuration and factories
7. Testing and documentation

**Required Python interfaces:**
- `InstrumentProvider`: `load_all_async`, `load_ids_async`, `load_async`
- `LiveDataClient`: `_connect`, `_disconnect`, `_subscribe`, `_unsubscribe`, `_request`
- `LiveExecutionClient`: submit/modify/cancel + reconciliation report generators

**Factory signature:** `create(loop, name, config, msgbus, cache, clock)`

**Testing doctrine:**
- Real captured payload fixtures (not invented schemas)
- No arbitrary sleeps in async tests; use condition-based waiting
- Cover: providers, data, execution, factories

## RUST+PyO3 PATTERNS

### Constructor Pattern
```rust
pub fn new_checked(params) -> anyhow::Result<Self> { ... }
pub fn new(params) -> Self { Self::new_checked(params).expect(FAILED) }
```

### FFI Memory Safety
- `#[repr(C)]` struct wrapping `Box<Inner>`
- `abort_on_panic(|| { ... })` on all FFI functions
- Matching drop for every constructor
- Type-specific CVec drops (never generic)

### PyO3 Conventions
- `py_*` prefix on Rust function names
- `#[pyo3(name = "...")]` for clean Python API
- Plain `PyObject` (never `Arc<PyObject>`)
- Manual `Clone` using `clone_py_object()`

### Runtime
- `get_runtime().spawn()` in adapter code (never `tokio::spawn()` from Python threads)
- `#[rstest]` for all Rust tests
- `#![deny(unsafe_op_in_unsafe_fn)]` in every crate

## CODING STANDARDS

### Python
- Type hints on all signatures: `def on_bar(self, bar: Bar) -> None:`
- NumPy docstrings, imperative mood
- Config classes: `{Component}Config`
- Strategy IDs: `{Class}-{tag}`
- Instrument IDs: `{symbol}.{venue}`
- 100 char line limit, trailing commas

### Rust
- `anyhow::Result<T>` + `anyhow::bail!` for fallible functions
- Fully qualify `anyhow::` and `tokio::` macros
- `log::*` for sync, `tracing::*` for async/adapter code
- Capitalize messages, omit terminal periods
- Rust doc comments: **indicative mood** ("Returns the client", not "Return")

## IMPLEMENTATION CHECKLIST

- Config class defined with all parameters
- Type hints on all methods
- `on_start` initializes state and subscriptions
- `on_stop` cleans up (cancel orders, unsubscribe)
- Historical data requested for warmup
- No blocking calls in handlers
- Proper null checks before using cached data
- Logging at appropriate levels

## REFERENCES (symlinked)

- `references/api_reference/` — trading.md, common.md, backtest.md, analysis.md, live.md
- `references/developer_guide/` — python.md, rust.md, ffi.md, adapters.md, benchmarking.md
- `references/concepts/` — backtesting.md, live.md

## NEXT STEP

After implementation → **nt-review** skill for validation.
