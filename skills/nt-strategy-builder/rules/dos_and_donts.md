# Strategy Builder — DO and DON'Ts

Curated rules with rationale. Each rule maps to a common production failure mode.

---

## ✅ DOs

### Data & Configuration

**DO** use `ParquetDataCatalog` for all historical data (CeFi and DEX).
```python
catalog = ParquetDataCatalog("/path/to/catalog")
# Write DEX pool snapshots, on-chain trades, bars — all go through catalog
catalog.write_data(instruments)  # Always write instruments first
catalog.write_data(bars)
```
> Why: Ensures reproducible backtests. Raw data normalised to Nautilus types.

**DO** use `msgspec.Struct` for custom data types passed on the message bus.
> Why: significantly faster than standard Python classes or dataclasses (see `docs/serialization.md`).

**DO** define `BacktestVenueConfig` with explicit `account_type` and `starting_balances`.
```python
venue_config = BacktestVenueConfig(
    name="SIM",
    oms_type="NETTING",
    account_type="CASH",
    starting_balances=["10_000 USDT"],
)
```
> Why: Wrong account type silently produces wrong margin/PnL calculations.

**DO** set `base_currency` on the venue when running multi-currency accounts.
> Why: Without it, the portfolio analyzer cannot consolidate PnL across currencies.

**DO** use `instrument.make_qty()` and `instrument.make_price()` for all price/quantity construction.
```python
qty = self.instrument.make_qty(raw_size)
price = self.instrument.make_price(raw_price)
```
> Why: Instruments carry precision/tick-size — raw floats violate exchange constraints.

**DO** clamp position sizes to `[min_quantity, max_quantity]`.
```python
min_qty = float(self.instrument.min_quantity)
max_qty = float(self.instrument.max_quantity or 1e9)
final_size = max(min_qty, min(calculated_size, max_qty))
```

---

### Lifecycle

**DO** call `request_bars()` (historical) BEFORE `subscribe_bars()` (live) in `on_start`.
```python
def on_start(self) -> None:
    self.request_bars(self.bar_type)   # ← warmup first
    self.subscribe_bars(self.bar_type) # ← then live feed
```
> Why: Indicators need historical data to initialise before live ticks arrive.

**DO** null-check `self.cache.instrument()` before use.
```python
instrument = self.cache.instrument(self.config.instrument_id)
if instrument is None:
    self.log.error(f"Instrument not found: {self.config.instrument_id}")
    return
```

**DO** cancel all orders and unsubscribe in `on_stop`.
```python
def on_stop(self) -> None:
    self.cancel_all_orders(self.instrument.id)
    self.unsubscribe_bars(self.bar_type)
```

**DO** clear bounded buffers in `on_reset`.
```python
def on_reset(self) -> None:
    self.bar_buffer.clear()
    self.signal_history.clear()
    self.instrument = None
```

---

### Time

**DO** use `self.clock.utc_now()` / `self.clock.timestamp_ns()` for all time references.
```python
ts = self.clock.timestamp_ns()   # nanoseconds (Nautilus native)
dt = self.clock.utc_now()        # datetime (for display)
```
> Why: `datetime.utcnow()` or `time.time()` break backtest determinism.

---

### Live Trading

**DO** enable reconciliation with adequate lookback.
```python
exec_engine=LiveExecEngineConfig(
    reconciliation=True,
    open_check_lookback_mins=60,     # Never reduce below 60
    inflight_check_interval_ms=2000,
    reconciliation_startup_delay_secs=10.0,
)
```

**DO** configure all connection timeouts on `TradingNodeConfig`.
```python
config = TradingNodeConfig(
    timeout_connection=30.0,
    timeout_reconciliation=10.0,
    timeout_portfolio=10.0,
    timeout_disconnection=10.0,
)
```

**DO** handle all order lifecycle events.
```python
def on_order_rejected(self, event: OrderRejected) -> None: ...
def on_order_canceled(self, event: OrderCanceled) -> None: ...
def on_order_expired(self, event: OrderExpired) -> None: ...
def on_order_filled(self, event: OrderFilled) -> None: ...
```

**DO** claim external orders with `external_order_claims` when a strategy should resume managing existing orders after restart.
```python
config = StrategyConfig(
    external_order_claims=["BTCUSDT-PERP.BINANCE"],
)
```

---

### Risk

**DO** implement pre-trade risk validation.
```python
def _validate_trade(self, quantity: Quantity) -> bool:
    net_pos = self.portfolio.net_position(self.instrument.id)
    if abs(float(net_pos) + float(quantity)) > self.config.max_position_size:
        self.log.warning("Position limit would be exceeded")
        return False
    return True
```

**DO** use bounded data structures to prevent memory leaks.
```python
from collections import deque
self.bar_buffer: deque[Bar] = deque(maxlen=500)  # ← bounded
```

---

### DEX-Specific DOs

**DO** customise `FillModel` for DEX realism in backtests.
```python
dex_fill_model = FillModel(
    prob_fill_on_limit=0.25,  # DEX limit orders rarely fill at exact price
    prob_slippage=0.70,       # High slippage on AMMs
    random_seed=42,
)
```

**DO** write DEX pool snapshots / on-chain trade ticks to catalog in the same normalised format as CeFi data.
```python
catalog.write_data([dex_trade_tick])   # TradeTick format works for on-chain swaps
catalog.write_data([dex_order_book_delta])
```


**DO** account for gas costs in position sizing when trading on-chain.
```python
# Deduct estimated gas from risk budget
gas_estimate_usd = self._estimate_gas()
adjusted_risk_budget = self.config.risk_per_trade - gas_estimate_usd / equity
```

---

## ❌ DON'Ts

### Performance

**DON'T** block in event handlers.
```python
# ❌ WRONG — blocks the event loop
def on_bar(self, bar: Bar) -> None:
    data = requests.get("https://api.example.com")  # BLOCKS!
    model = pickle.load(open("model.pkl", "rb"))     # BLOCKS!

# ✅ CORRECT — load in on_start, use preloaded
def on_start(self) -> None:
    self.model = self._load_model()

def on_bar(self, bar: Bar) -> None:
    pred = self.model.predict(self._features(bar))
```

**DON'T** use unbounded lists or dicts that grow with data.
```python
# ❌ WRONG — memory leak
self.all_bars: list[Bar] = []

# ✅ CORRECT
self.bar_buffer: deque[Bar] = deque(maxlen=200)
```

**DON'T** call `time.sleep()` anywhere in strategy or actor code.

---

### Correctness

**DON'T** use raw `float` for price/quantity.
```python
# ❌ WRONG
qty = Quantity.from_str("1.5")    # May violate precision
price = Price.from_str("100.00")  # May violate tick size

# ✅ CORRECT
qty = self.instrument.make_qty(1.5)
price = self.instrument.make_price(100.00)
```

**DON'T** assume `self.cache.instrument()` returns a non-None value.

**DON'T** trade without checking indicators are initialised.
```python
def on_bar(self, bar: Bar) -> None:
    if not self.ema.initialized or not self.rsi.initialized:
        return   # ← skip until warmup complete
```

**DON'T** put ML inference in Strategy — always put it in Actor.
> Actors own model state; strategies own order state. Mixing them breaks separation of concerns and makes components untestable in isolation.

**DON'T** submit orders without pre-trade validation.

---

### Live Trading

**DON'T** set `reconciliation=False` for live trading without explicit justification documented in code.

**DON'T** set `open_check_lookback_mins < 60`.
> Lower values cause "missing order" false-positives which trigger incorrect position flattening.

**DON'T** hardcode credentials (API keys, private keys) in config files.
```python
# ❌ WRONG
MyExchangeConfig(api_key="sk_live_abc123")

# ✅ CORRECT
MyExchangeConfig(api_key=os.environ["EXCHANGE_API_KEY"])
# or
MyExchangeConfig(api_key=SecretStr(os.environ["EXCHANGE_API_KEY"]))
```

**DON'T** skip order rejection and expiry handling.

**DON'T** assume orders always fill.

---

### DEX-Specific DON'Ts

**DON'T** poll the chain in `on_bar` / `on_quote_tick` handlers.
> Chain calls are blocking and slow — drive chain polling from a dedicated Actor using `self.clock.set_timer()`.

**DON'T** store private keys as plain `str` in config.
```python
# ❌ WRONG
class MyDEXConfig(LiveExecClientConfig):
    private_key: str  # exposed in logs, repr, etc.

# ✅ CORRECT
from pydantic import SecretStr
class MyDEXConfig(LiveExecClientConfig):
    private_key: SecretStr
```

**DON'T** ignore transaction receipt errors during execution.
> On-chain tx submission can succeed but revert — always check receipt status and emit the appropriate `OrderRejected` event.

**DON'T** use AMM spot price as fill price in backtest without modelling slippage.
> AMM k=xy constant product formula means fill price depends on order size.
