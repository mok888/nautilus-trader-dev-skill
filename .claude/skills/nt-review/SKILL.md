---
name: nt-review
description: "Use when reviewing nautilus_trader implementations. Validates conventions, trading correctness, performance, and testability before deployment."
---

# Nautilus Trader Code Review

## Overview

Validate nautilus_trader implementations against conventions, trading correctness, performance, and testability. Use before merging or deploying to catch issues early.

## When to Use

- After implementing components (via nt-implement)
- Before merging to main branch
- When reviewing existing code for issues
- Before deploying to paper/live trading

## Review Dimensions

### 1. Nautilus Conventions

#### Lifecycle Methods

Check that lifecycle methods are correctly implemented:

```python
# REQUIRED: Always call super().__init__()
def __init__(self, config: MyConfig) -> None:
    super().__init__(config)  # Must be first

# REQUIRED: Initialize state in on_start, not __init__
def on_start(self) -> None:
    self.instrument = self.cache.instrument(self.config.instrument_id)
    self.request_bars(self.config.bar_type)  # Historical first
    self.subscribe_bars(self.config.bar_type)  # Then live

# REQUIRED: Cleanup in on_stop
def on_stop(self) -> None:
    self.cancel_all_orders(self.config.instrument_id)
    self.unsubscribe_bars(self.config.bar_type)

# REQUIRED: Reset state for reuse
def on_reset(self) -> None:
    self.instrument = None
```

**Red flags:**
- Using `clock`, `logger`, or `cache` in `__init__` (not yet available)
- Missing null checks on cached instruments
- Subscribing before requesting historical data
- Not cleaning up in `on_stop`

#### API Usage

Check for correct API patterns:

```python
# CORRECT: Use order factory
order = self.order_factory.market(...)
self.submit_order(order)

# CORRECT: Access cache properly
instrument = self.cache.instrument(instrument_id)
if instrument is None:
    self.log.error("Instrument not found")
    return

# CORRECT: Use clock for timestamps
ts = self.clock.timestamp_ns()

# WRONG: Direct construction
order = MarketOrder(...)  # Don't do this

# WRONG: Assuming cache has data
instrument = self.cache.instrument(instrument_id)
price = instrument.make_price(100)  # Crashes if None
```

#### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Config class | `{Component}Config` | `TrendStrategyConfig` |
| Instrument ID | `{symbol}.{venue}` | `BTCUSDT-PERP.BINANCE` |
| Strategy ID | `{Class}-{tag}` | `TrendStrategy-001` |
| Bar type | `{id}-{step}-{agg}-{price}-{source}` | `BTCUSDT-PERP.BINANCE-5-MINUTE-LAST-EXTERNAL` |
| Custom data | `{Purpose}Data` | `RegimeData`, `FeatureData` |

### 2. Trading Correctness

#### Position Sizing

Check for proper position sizing:

```python
# CORRECT: Use instrument methods for precision
quantity = self.instrument.make_qty(calculated_size)
price = self.instrument.make_price(calculated_price)

# CORRECT: Respect instrument limits
min_qty = float(self.instrument.min_quantity)
max_qty = float(self.instrument.max_quantity or 1e9)
final_size = max(min_qty, min(calculated_size, max_qty))

# WRONG: Raw floats
quantity = Quantity.from_str("1.5")  # May violate precision
```

**Red flags:**
- Hardcoded position sizes without instrument validation
- No min/max quantity checks
- Missing precision handling

#### Order Management

Check for proper order handling:

```python
# CORRECT: Handle all order states
def on_order_rejected(self, event: OrderRejected) -> None:
    self.log.warning(f"Order rejected: {event.reason}")
    self._handle_rejection()

def on_order_canceled(self, event: OrderCanceled) -> None:
    self.log.info(f"Order canceled: {event.client_order_id}")

def on_order_filled(self, event: OrderFilled) -> None:
    self.log.info(f"Filled: {event.last_qty} @ {event.last_px}")

# CORRECT: Cancel before closing
def _close_position(self) -> None:
    self.cancel_all_orders(self.instrument.id)
    self.close_position(self.instrument.id)
```

**Red flags:**
- No rejection handling
- Assuming orders always fill
- Not canceling orders before closing positions
- Not handling partial fills

#### Risk Checks

Verify risk controls are present:

```python
# REQUIRED: Pre-trade validation
def _validate_trade(self) -> bool:
    # Check position limits
    net_pos = self.portfolio.net_position(self.instrument.id)
    if abs(net_pos) >= self.config.max_position:
        return False

    # Check exposure limits
    exposure = self.portfolio.net_exposure(self.instrument.id)
    if exposure and float(exposure) > self.config.max_exposure:
        return False

    return True
```

**Red flags:**
- No position size limits
- No loss limits
- No exposure checks
- Trading without checking portfolio state

#### Edge Cases

Check for handling of:

- [ ] First bar after start (indicators not initialized)
- [ ] Gap in data (missing bars)
- [ ] Market close/open transitions
- [ ] Instrument not found in cache
- [ ] Account with insufficient balance
- [ ] Order rejected by venue
- [ ] Partial fills
- [ ] Network reconnection

### 3. Performance

#### Blocking Calls

**Never block in handlers.** Check for:

```python
# WRONG: Blocking I/O in handler
def on_bar(self, bar: Bar) -> None:
    data = requests.get("http://api.example.com")  # BLOCKS!
    model = pickle.load(open("model.pkl", "rb"))  # BLOCKS!

# CORRECT: Load in on_start, use cached
def on_start(self) -> None:
    self.model = self._load_model()

def on_bar(self, bar: Bar) -> None:
    result = self.model.predict(features)  # Uses preloaded model
```

**Red flags:**
- HTTP requests in `on_bar`, `on_quote_tick`, etc.
- File I/O in hot paths
- Database queries in handlers
- `time.sleep()` anywhere

#### Memory Management

Check for memory leaks:

```python
# CORRECT: Bounded buffer
self.bar_buffer: deque[Bar] = deque(maxlen=100)

# WRONG: Unbounded growth
self.all_bars: list[Bar] = []  # Grows forever!

# CORRECT: Clear on reset
def on_reset(self) -> None:
    self.bar_buffer.clear()
    self.feature_cache.clear()
```

**Red flags:**
- Unbounded lists/dicts that grow with data
- No cleanup in `on_reset`
- Storing references to large objects unnecessarily

#### Efficient Data Handling

```python
# CORRECT: Use numpy for vectorized operations
import numpy as np
closes = np.array([float(b.close) for b in self.bars])
mean = np.mean(closes)

# LESS EFFICIENT: Python loops
total = 0
for bar in self.bars:
    total += float(bar.close)
mean = total / len(self.bars)
```

### 4. Testability

#### Backtest Compatibility

Check that components work in backtest:

```python
# CORRECT: Use self.clock for time (works in backtest and live)
current_time = self.clock.utc_now()

# WRONG: System time (breaks backtest determinism)
import datetime
current_time = datetime.datetime.utcnow()

# CORRECT: Deterministic behavior
def _calculate_signal(self, bar: Bar) -> float:
    return self.ema.value - self.sma.value

# WRONG: Non-deterministic
import random
def _calculate_signal(self, bar: Bar) -> float:
    return random.random()  # Different each run!
```

#### Isolation

Check components can be tested independently:

```python
# GOOD: Dependencies are injected via config
class MyStrategy(Strategy):
    def __init__(self, config: MyConfig) -> None:
        super().__init__(config)
        # No hardcoded dependencies

# BAD: Hardcoded dependencies
class MyStrategy(Strategy):
    def __init__(self, config: MyConfig) -> None:
        super().__init__(config)
        self.external_api = ExternalAPI("hardcoded-key")
```

#### Logging

Check for appropriate logging:

```python
# GOOD: Appropriate levels
self.log.debug(f"Processing bar: {bar}")  # Debug for verbose
self.log.info(f"Order submitted: {order.client_order_id}")  # Info for actions
self.log.warning(f"Unusual spread: {spread}")  # Warning for concerns
self.log.error(f"Failed to load model: {e}")  # Error for failures

# BAD: Wrong levels
self.log.info(f"Bar received: {bar}")  # Too verbose for info
self.log.error(f"No signal")  # Not an error
```

## Review Checklist

### Quick Check (< 5 min)

- [ ] All lifecycle methods call `super()`
- [ ] `on_start` fetches instrument from cache with null check
- [ ] `request_bars` before `subscribe_bars`
- [ ] `on_stop` cancels orders and unsubscribes
- [ ] Type hints on all methods
- [ ] No blocking calls in handlers

### Full Review (15-30 min)

**Conventions:**
- [ ] Config class follows naming convention
- [ ] All parameters typed and documented
- [ ] Lifecycle methods correctly implemented
- [ ] Proper use of order factory and cache

**Trading Correctness:**
- [ ] Position sizing uses instrument methods
- [ ] Min/max quantity respected
- [ ] Order rejection handled
- [ ] Position limits enforced
- [ ] Warmup period handled

**Performance:**
- [ ] No blocking I/O in handlers
- [ ] Bounded data structures
- [ ] Cleanup in `on_reset`
- [ ] Efficient calculations

**Testability:**
- [ ] Uses `self.clock` not system time
- [ ] Deterministic behavior
- [ ] Dependencies injectable
- [ ] Appropriate logging levels

## Common Issues by Component

### Strategy
- Missing order rejection handling
- No position limits
- Blocking in `on_bar`
- Not canceling orders on stop

### Actor
- Model loading in handler instead of `on_start`
- Unbounded signal history
- No warmup handling
- Missing `on_reset` cleanup

### Indicator
- Not implementing `initialized` property
- Missing `reset` method
- Wrong handler signature

### Adapter
- Blocking HTTP in data handlers
- No reconnection logic
- Missing error handling
- Not validating responses

## References

For detailed standards:
- `@references/developer_guide/coding_standards.md`
- `@references/developer_guide/testing.md`
- `@references/concepts/backtesting.md`
