---
name: nt-implement
description: "Use when implementing nautilus_trader components. Provides templates for Strategy, Actor, Indicator, Custom Data, Execution Algorithm, and Adapters with correct patterns."
---

# Nautilus Trader Implementation

## Overview

Implement nautilus_trader components using correct patterns and templates. This skill provides ready-to-use templates and common implementation patterns for all component types.

## When to Use

- After architecture is defined (via nt-architect)
- When implementing any Nautilus component
- When needing correct method signatures and patterns

## Implementation Workflow

1. Start from architecture document
2. Implement in dependency order:
   - Custom Data Types (if needed)
   - Indicators
   - Actors
   - Strategies
   - Execution Algorithms (if needed)
3. Validate each component before proceeding

## Templates

### Quick Reference: Which Template?

| Need | Template | Key Feature |
|------|----------|-------------|
| Trading logic, orders | `strategy.py` | `submit_order()`, position management |
| Model inference, signals | `actor.py` | `publish_signal()`, `publish_data()` |
| Stateless calculations | `indicator.py` | `handle_bar()`, pure computation |
| Structured data between components | `custom_data.py` | `@customdataclass`, serialization |
| Order execution logic | `exec_algorithm.py` | Child order spawning |
| Exchange/data connectivity | `adapters/` | LiveDataClient, LiveExecutionClient |

### Template Files

Templates are in `templates/` subdirectory:
- `strategy.py` - Trading strategy with order management
- `actor.py` - Actor for model inference and signal publishing
- `indicator.py` - Custom indicator
- `custom_data.py` - Custom data types for message bus
- `exec_algorithm.py` - Execution algorithm
- `adapters/exchange.py` - Exchange adapter (data + execution)
- `adapters/data_provider.py` - Data-only adapter
- `adapters/internal.py` - Internal infrastructure adapter

## Common Patterns

### Model Loading (msgspec preferred)

```python
import msgspec
from pathlib import Path

class ModelState(msgspec.Struct):
    """Serializable model state."""
    weights: list[float]
    threshold: float
    version: str

class RegimeActor(Actor):
    def __init__(self, config: RegimeActorConfig) -> None:
        super().__init__(config)
        self.model: ModelState | None = None

    def on_start(self) -> None:
        # Load model using msgspec
        model_path = Path(self.config.model_path)
        with open(model_path, "rb") as f:
            self.model = msgspec.msgpack.decode(f.read(), type=ModelState)

        self.subscribe_bars(self.config.bar_type)
```

### ONNX Model Inference

```python
import onnxruntime as ort
import numpy as np

class MLActor(Actor):
    def __init__(self, config: MLActorConfig) -> None:
        super().__init__(config)
        self.session: ort.InferenceSession | None = None

    def on_start(self) -> None:
        self.session = ort.InferenceSession(self.config.onnx_model_path)
        self.input_name = self.session.get_inputs()[0].name
        self.subscribe_bars(self.config.bar_type)

    def on_bar(self, bar: Bar) -> None:
        features = self._compute_features(bar)
        inputs = {self.input_name: features.astype(np.float32).reshape(1, -1)}
        outputs = self.session.run(None, inputs)
        prediction = outputs[0][0]
        self.publish_signal(name="prediction", value=float(prediction), ts_event=bar.ts_event)
```

### Feature Computation Pipeline

```python
class FeatureActor(Actor):
    def __init__(self, config: FeatureActorConfig) -> None:
        super().__init__(config)
        self.ema_fast = ExponentialMovingAverage(config.fast_period)
        self.ema_slow = ExponentialMovingAverage(config.slow_period)
        self.rsi = RelativeStrengthIndex(config.rsi_period)
        self.feature_buffer: deque[FeatureData] = deque(maxlen=config.lookback)

    def on_start(self) -> None:
        self.register_indicator_for_bars(self.config.bar_type, self.ema_fast)
        self.register_indicator_for_bars(self.config.bar_type, self.ema_slow)
        self.register_indicator_for_bars(self.config.bar_type, self.rsi)

        self.request_bars(self.config.bar_type)
        self.subscribe_bars(self.config.bar_type)

    def on_bar(self, bar: Bar) -> None:
        if not self.ema_fast.initialized or not self.rsi.initialized:
            return

        feature = FeatureData(
            ema_diff=self.ema_fast.value - self.ema_slow.value,
            rsi=self.rsi.value,
            ts_event=bar.ts_event,
            ts_init=self.clock.timestamp_ns(),
        )
        self.feature_buffer.append(feature)
        self.publish_data(FeatureData, feature)
```

### Position Sizing

```python
def calculate_position_size(
    self,
    signal_strength: float,
    volatility: float,
) -> Quantity:
    """Calculate position size based on signal and volatility."""
    account = self.portfolio.account(self.instrument.venue)
    equity = account.balance_total(self.instrument.quote_currency)

    # Risk-based sizing: risk X% of equity per trade
    risk_amount = float(equity) * self.config.risk_per_trade

    # Adjust for volatility (ATR-based)
    stop_distance = volatility * self.config.atr_multiplier
    if stop_distance <= 0:
        return self.instrument.make_qty(0)

    raw_size = risk_amount / stop_distance

    # Scale by signal strength
    adjusted_size = raw_size * abs(signal_strength)

    # Clamp to instrument limits
    min_qty = float(self.instrument.min_quantity)
    max_qty = float(self.instrument.max_quantity or 1e9)
    final_size = max(min_qty, min(adjusted_size, max_qty))

    return self.instrument.make_qty(final_size)
```

### Multi-Timeframe Data

```python
class MultiTimeframeStrategy(Strategy):
    def __init__(self, config: MTFConfig) -> None:
        super().__init__(config)
        self.bar_1m: Bar | None = None
        self.bar_5m: Bar | None = None
        self.bar_1h: Bar | None = None

    def on_start(self) -> None:
        self.instrument = self.cache.instrument(self.config.instrument_id)

        # Define bar types
        self.bar_type_1m = BarType.from_str(f"{self.config.instrument_id}-1-MINUTE-LAST-EXTERNAL")
        self.bar_type_5m = BarType.from_str(f"{self.config.instrument_id}-5-MINUTE-LAST-INTERNAL@1-MINUTE-EXTERNAL")
        self.bar_type_1h = BarType.from_str(f"{self.config.instrument_id}-1-HOUR-LAST-INTERNAL@1-MINUTE-EXTERNAL")

        # Request historical for warmup
        self.request_bars(self.bar_type_1m)
        self.request_bars(self.bar_type_5m)
        self.request_bars(self.bar_type_1h)

        # Subscribe to live
        self.subscribe_bars(self.bar_type_1m)
        self.subscribe_bars(self.bar_type_5m)
        self.subscribe_bars(self.bar_type_1h)

    def on_bar(self, bar: Bar) -> None:
        if bar.bar_type == self.bar_type_1m:
            self.bar_1m = bar
        elif bar.bar_type == self.bar_type_5m:
            self.bar_5m = bar
        elif bar.bar_type == self.bar_type_1h:
            self.bar_1h = bar
            self._check_signals()  # Only trade on higher timeframe close

    def _check_signals(self) -> None:
        if self.bar_1m is None or self.bar_5m is None or self.bar_1h is None:
            return
        # Trading logic using all timeframes
```

### Risk Check Integration

```python
def _validate_order(self, order_side: OrderSide, quantity: Quantity) -> bool:
    """Pre-submission risk validation."""
    # Check position limits
    net_position = self.portfolio.net_position(self.instrument.id)
    if order_side == OrderSide.BUY:
        new_position = net_position + float(quantity)
    else:
        new_position = net_position - float(quantity)

    if abs(new_position) > self.config.max_position_size:
        self.log.warning(f"Order rejected: would exceed max position {self.config.max_position_size}")
        return False

    # Check daily loss limit
    realized_pnl = self.portfolio.realized_pnl(self.instrument.id)
    if realized_pnl and float(realized_pnl) < -self.config.max_daily_loss:
        self.log.warning("Order rejected: daily loss limit reached")
        return False

    return True
```

## Coding Standards

Follow these nautilus_trader conventions:

### Type Hints

All signatures must include comprehensive type annotations:
```python
def __init__(self, config: MyStrategyConfig) -> None:
def on_bar(self, bar: Bar) -> None:
def on_save(self) -> dict[str, bytes]:
```

### Docstrings

Use NumPy docstring format, imperative mood for Python:
```python
def calculate_signal(self, bar: Bar) -> float:
    """
    Calculate trading signal from bar data.

    Parameters
    ----------
    bar : Bar
        The bar to analyze.

    Returns
    -------
    float
        Signal value between -1 and 1.
    """
```

### Naming Conventions

- Config classes: `{Component}Config` (e.g., `TrendStrategyConfig`)
- Strategy IDs: `{StrategyClass}-{order_id_tag}` (e.g., `TrendStrategy-001`)
- Instrument IDs: `{symbol}.{venue}` (e.g., `BTCUSDT-PERP.BINANCE`)
- Bar types: `{instrument_id}-{step}-{aggregation}-{price_type}-{source}`

### Formatting

- 100 character line limit
- Trailing commas for multi-line arguments
- Spaces only (no tabs)

## Implementation Checklist

Before marking a component complete:

- [ ] Config class defined with all parameters
- [ ] Type hints on all methods
- [ ] `on_start` initializes state and subscriptions
- [ ] `on_stop` cleans up (cancel orders, unsubscribe)
- [ ] Historical data requested for warmup
- [ ] No blocking calls in handlers
- [ ] Proper null checks before using cached data
- [ ] Logging at appropriate levels

## References

For API details, load (relative to this skill folder):
- `references/api_reference/trading.md` - Strategy API
- `references/api_reference/common.md` - Actor, OrderFactory
- `references/developer_guide/adapters.md` - Adapter development
- `references/developer_guide/coding_standards.md` - Style guide

## Next Step

After implementation, use **nt-review** skill to validate the code.
