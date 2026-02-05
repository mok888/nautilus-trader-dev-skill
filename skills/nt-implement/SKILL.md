---
name: nt-implement
description: "Use when implementing nautilus_trader components. Provides templates for Strategy, Actor, Indicator, Custom Data, Execution Algorithm, Adapters, and custom simulation models (FillModel, MarginModel, PortfolioStatistic). Includes Rust+PyO3 implementation patterns."
---

# Nautilus Trader Implementation

## Overview

Implement nautilus_trader components using correct patterns and templates. This skill provides ready-to-use templates and common implementation patterns for all component types, including:

- **Python components**: Strategy, Actor, Indicator, Custom Data, Execution Algorithm, Adapters
- **Simulation models**: Custom FillModel, MarginModel, PortfolioStatistic
- **Rust+PyO3 bindings**: High-performance core implementations with Python interop

## Risk Engine

- **Risk Management**: Implement custom risk checks and limits.
- **Position Limits**: Enforce maximum position sizes or exposure.
- **Drawdown Control**: Monitor and react to portfolio drawdowns.

## Exchange-Specific Patterns

- **Order Types**: Implement exchange-specific order types (e.g., Iceberg, Post-Only).
- **Market Data Handling**: Parse and process unique market data streams.
- **API Interaction**: Best practices for interacting with exchange APIs.

## When to Use

- After architecture is defined (via nt-architect)
- When implementing any Nautilus component
- When needing correct method signatures and patterns
- When implementing custom simulation/analysis models
- When implementing performance-critical code in Rust with Python bindings

## Implementation Workflow

1. Start from architecture document
2. Implement in dependency order:
   - Custom Data Types (if needed)
   - Custom Models (FillModel, MarginModel if backtesting)
   - Indicators
   - Actors
   - Strategies
   - Execution Algorithms (if needed)
   - Portfolio Statistics (for analysis)
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
| Custom fill simulation | `fill_model.py` | `prob_fill_on_limit`, queue position |
| Custom margin calculation | `margin_model.py` | `calculate_margin_init/maint` |
| Custom portfolio statistics | `portfolio_statistic.py` | `calculate_from_orders/positions` |

### Template Files

Templates are in `templates/` subdirectory:
- `strategy.py` - Trading strategy with order management
- `actor.py` - Actor for model inference and signal publishing
- `indicator.py` - Custom indicator
- `custom_data.py` - Custom data types for message bus
- `exec_algorithm.py` - Execution algorithm
- `fill_model.py` - Custom fill simulation model
- `margin_model.py` - Custom margin calculation model
- `portfolio_statistic.py` - Custom portfolio statistic
- `adapters/exchange.py` - Exchange adapter (data + execution)
- `adapters/data_provider.py` - Data-only adapter

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

## Custom Simulation Models

### Custom FillModel

Implement custom fill simulation for backtesting. Controls order queue position and execution probability.

```python
from decimal import Decimal
from nautilus_trader.backtest.models import FillModel
from nautilus_trader.model.orders import Order
from nautilus_trader.model.instruments import Instrument

class VolatilityAdjustedFillModel(FillModel):
    """
    Fill model that adjusts probabilities based on market volatility.

    Parameters
    ----------
    base_prob_fill_on_limit : float
        Base probability for limit order fills.
    base_prob_slippage : float
        Base probability for slippage on market orders.
    volatility_multiplier : float
        Multiplier applied based on volatility regime.
    random_seed : int, optional
        Seed for reproducible results.
    """

    def __init__(
        self,
        base_prob_fill_on_limit: float = 0.5,
        base_prob_slippage: float = 0.3,
        volatility_multiplier: float = 1.5,
        random_seed: int | None = None,
    ) -> None:
        super().__init__(
            prob_fill_on_limit=base_prob_fill_on_limit,
            prob_fill_on_stop=1.0,  # Deprecated, use prob_slippage
            prob_slippage=base_prob_slippage,
            random_seed=random_seed,
        )
        self._volatility_multiplier = volatility_multiplier
        self._current_volatility = 1.0  # Updated externally

    def set_volatility(self, volatility: float) -> None:
        """Update current volatility regime."""
        self._current_volatility = volatility

    def is_limit_filled(self) -> bool:
        """Check if limit order fills based on volatility-adjusted probability."""
        # Higher volatility = more likely to get filled (more price movement)
        adjusted_prob = min(1.0, self.prob_fill_on_limit * self._current_volatility)
        return self._random.random() < adjusted_prob

    def is_slipped(self) -> bool:
        """Check if slippage occurs based on volatility-adjusted probability."""
        # Higher volatility = more likely slippage
        adjusted_prob = min(1.0, self.prob_slippage * self._current_volatility * self._volatility_multiplier)
        return self._random.random() < adjusted_prob
```

**Usage in backtest:**

```python
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.config import BacktestEngineConfig

fill_model = VolatilityAdjustedFillModel(
    base_prob_fill_on_limit=0.3,
    base_prob_slippage=0.2,
    volatility_multiplier=1.5,
    random_seed=42,
)

engine = BacktestEngine(
    config=BacktestEngineConfig(
        trader_id="TESTER-001",
        fill_model=fill_model,
    )
)
```

### Custom MarginModel

Implement custom margin calculation for different venue types.

```python
from decimal import Decimal
from nautilus_trader.backtest.models import MarginModel
from nautilus_trader.backtest.config import MarginModelConfig
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.model.objects import Money, Quantity, Price
from nautilus_trader.model.enums import PositionSide

class RiskAdjustedMarginModel(MarginModel):
    """
    Margin model that applies risk multipliers based on instrument characteristics.

    Receives configuration through MarginModelConfig.config dict:
    - risk_multiplier: float - Base risk multiplier (default 1.0)
    - use_leverage: bool - Whether to divide by leverage (default False)
    - volatility_buffer: float - Additional buffer for volatile instruments (default 0.0)
    """

    def __init__(self, config: MarginModelConfig) -> None:
        """Initialize with configuration parameters."""
        self.risk_multiplier = Decimal(str(config.config.get("risk_multiplier", 1.0)))
        self.use_leverage = config.config.get("use_leverage", False)
        self.volatility_buffer = Decimal(str(config.config.get("volatility_buffer", 0.0)))

    def calculate_margin_init(
        self,
        instrument: Instrument,
        quantity: Quantity,
        price: Price,
        leverage: Decimal,
        use_quote_for_inverse: bool = False,
    ) -> Money:
        """
        Calculate initial margin for order submission.

        Parameters
        ----------
        instrument : Instrument
            The instrument for the calculation.
        quantity : Quantity
            The order quantity.
        price : Price
            The order price.
        leverage : Decimal
            The account leverage.
        use_quote_for_inverse : bool
            Use quote currency for inverse instruments.

        Returns
        -------
        Money
            The initial margin requirement.
        """
        notional = instrument.notional_value(quantity, price, use_quote_for_inverse)

        if self.use_leverage and leverage > 0:
            adjusted_notional = notional.as_decimal() / leverage
        else:
            adjusted_notional = notional.as_decimal()

        # Apply instrument margin requirement with risk adjustments
        margin = adjusted_notional * instrument.margin_init * self.risk_multiplier
        margin += adjusted_notional * self.volatility_buffer  # Add volatility buffer

        return Money(margin, instrument.quote_currency)

    def calculate_margin_maint(
        self,
        instrument: Instrument,
        side: PositionSide,
        quantity: Quantity,
        price: Price,
        leverage: Decimal,
        use_quote_for_inverse: bool = False,
    ) -> Money:
        """Calculate maintenance margin for open positions."""
        notional = instrument.notional_value(quantity, price, use_quote_for_inverse)

        if self.use_leverage and leverage > 0:
            adjusted_notional = notional.as_decimal() / leverage
        else:
            adjusted_notional = notional.as_decimal()

        margin = adjusted_notional * instrument.margin_maint * self.risk_multiplier

        return Money(margin, instrument.quote_currency)
```

**Usage in backtest config:**

```python
from nautilus_trader.backtest.config import BacktestVenueConfig, MarginModelConfig

venue_config = BacktestVenueConfig(
    name="SIM",
    oms_type="NETTING",
    account_type="MARGIN",
    starting_balances=["1_000_000 USD"],
    margin_model=MarginModelConfig(
        model_type="my_package.my_module:RiskAdjustedMarginModel",
        config={
            "risk_multiplier": 1.5,
            "use_leverage": False,
            "volatility_buffer": 0.02,
        },
    ),
)
```

### Custom PortfolioStatistic

Implement custom portfolio statistics for analysis.

```python
from decimal import Decimal
from nautilus_trader.analysis.statistic import PortfolioStatistic
from nautilus_trader.model.position import Position
from nautilus_trader.model.orders import Order

class WinStreakStatistic(PortfolioStatistic):
    """Calculate maximum winning and losing streaks."""

    def __init__(self) -> None:
        super().__init__()
        self._name = "Win Streak"

    @property
    def name(self) -> str:
        return self._name

    def calculate_from_orders(self, orders: list[Order]) -> dict[str, int]:
        """
        Calculate win/loss streaks from filled orders.

        Returns
        -------
        dict[str, int]
            Dictionary with max_win_streak and max_loss_streak.
        """
        # Implementation for order-based calculation
        return {"max_win_streak": 0, "max_loss_streak": 0}

    def calculate_from_positions(self, positions: list[Position]) -> dict[str, int]:
        """
        Calculate win/loss streaks from closed positions.

        Returns
        -------
        dict[str, int]
            Dictionary with max_win_streak and max_loss_streak.
        """
        if not positions:
            return {"max_win_streak": 0, "max_loss_streak": 0}

        max_win_streak = 0
        max_loss_streak = 0
        current_win_streak = 0
        current_loss_streak = 0

        for position in positions:
            if not position.is_closed:
                continue

            realized_pnl = position.realized_pnl
            if realized_pnl is None:
                continue

            if float(realized_pnl) > 0:
                current_win_streak += 1
                current_loss_streak = 0
                max_win_streak = max(max_win_streak, current_win_streak)
            else:
                current_loss_streak += 1
                current_win_streak = 0
                max_loss_streak = max(max_loss_streak, current_loss_streak)

        return {
            "max_win_streak": max_win_streak,
            "max_loss_streak": max_loss_streak,
        }


class RiskAdjustedReturnStatistic(PortfolioStatistic):
    """Calculate risk-adjusted return metrics."""

    def __init__(self, risk_free_rate: float = 0.0) -> None:
        super().__init__()
        self._name = "Risk Adjusted Return"
        self._risk_free_rate = risk_free_rate

    @property
    def name(self) -> str:
        return self._name

    def calculate_from_positions(self, positions: list[Position]) -> dict[str, float]:
        """
        Calculate Sharpe-like ratio from positions.

        Returns
        -------
        dict[str, float]
            Dictionary with avg_return, volatility, and sharpe_ratio.
        """
        import numpy as np

        returns = []
        for position in positions:
            if position.is_closed and position.realized_pnl is not None:
                # Simplified: use PnL as return proxy
                returns.append(float(position.realized_pnl))

        if len(returns) < 2:
            return {"avg_return": 0.0, "volatility": 0.0, "sharpe_ratio": 0.0}

        avg_return = np.mean(returns)
        volatility = np.std(returns)

        if volatility == 0:
            sharpe_ratio = 0.0
        else:
            sharpe_ratio = (avg_return - self._risk_free_rate) / volatility

        return {
            "avg_return": float(avg_return),
            "volatility": float(volatility),
            "sharpe_ratio": float(sharpe_ratio),
        }
```

**Usage with PortfolioAnalyzer:**

```python
from nautilus_trader.analysis.analyzer import PortfolioAnalyzer

analyzer = PortfolioAnalyzer()

# Register custom statistics
analyzer.register_statistic(WinStreakStatistic())
analyzer.register_statistic(RiskAdjustedReturnStatistic(risk_free_rate=0.02))

# Calculate after backtest
results = engine.run()
analyzer.calculate_statistics(positions=results.positions)
```

## Rust+PyO3 Implementation Patterns

For performance-critical components, NautilusTrader uses Rust with PyO3 bindings. Follow these patterns when implementing core functionality.

### Rust Module Structure

```rust
// -------------------------------------------------------------------------------------------------
//  Copyright (C) 2015-2025 Nautech Systems Pty Ltd. All rights reserved.
//  https://nautechsystems.io
//
//  Licensed under the GNU Lesser General Public License Version 3.0 (the "License");
//  You may not use this file except in compliance with the License.
//  You may obtain a copy of the License at https://www.gnu.org/licenses/lgpl-3.0.en.html
// -------------------------------------------------------------------------------------------------

//! Custom indicator implementation in Rust.

use nautilus_core::correctness::FAILED;
use nautilus_model::data::Bar;

/// Custom momentum indicator.
#[repr(C)]
#[derive(Clone, Debug)]
#[cfg_attr(
    feature = "python",
    pyo3::pyclass(module = "nautilus_trader.indicators")
)]
pub struct CustomMomentum {
    /// The lookback period for momentum calculation.
    pub period: usize,
    /// Whether the indicator has been initialized.
    pub initialized: bool,
    /// Current indicator value.
    value: f64,
    /// Internal price buffer.
    prices: Vec<f64>,
}

impl CustomMomentum {
    /// Creates a new [`CustomMomentum`] instance with correctness checking.
    ///
    /// # Errors
    ///
    /// Returns an error if `period` is zero.
    pub fn new_checked(period: usize) -> anyhow::Result<Self> {
        if period == 0 {
            anyhow::bail!("Period must be positive, was {period}");
        }

        Ok(Self {
            period,
            initialized: false,
            value: 0.0,
            prices: Vec::with_capacity(period + 1),
        })
    }

    /// Creates a new [`CustomMomentum`] instance.
    ///
    /// # Panics
    ///
    /// Panics if `period` is zero.
    pub fn new(period: usize) -> Self {
        Self::new_checked(period).expect(FAILED)
    }

    /// Returns the current indicator value.
    #[must_use]
    pub fn value(&self) -> f64 {
        self.value
    }

    /// Updates the indicator with a new price.
    pub fn update_raw(&mut self, price: f64) {
        self.prices.push(price);

        if self.prices.len() > self.period {
            self.prices.remove(0);
            self.value = price - self.prices[0];
            self.initialized = true;
        }
    }

    /// Resets the indicator state.
    pub fn reset(&mut self) {
        self.prices.clear();
        self.value = 0.0;
        self.initialized = false;
    }
}
```

### PyO3 Bindings

```rust
#[cfg(feature = "python")]
mod python {
    use pyo3::prelude::*;
    use super::CustomMomentum;

    #[pymethods]
    impl CustomMomentum {
        #[new]
        #[pyo3(signature = (period))]
        fn py_new(period: usize) -> PyResult<Self> {
            Self::new_checked(period).map_err(|e| {
                pyo3::exceptions::PyValueError::new_err(e.to_string())
            })
        }

        #[getter]
        fn period(&self) -> usize {
            self.period
        }

        #[getter]
        fn initialized(&self) -> bool {
            self.initialized
        }

        #[getter]
        fn value(&self) -> f64 {
            self.value
        }

        #[pyo3(name = "update_raw")]
        fn py_update_raw(&mut self, price: f64) {
            self.update_raw(price);
        }

        #[pyo3(name = "reset")]
        fn py_reset(&mut self) {
            self.reset();
        }

        fn __repr__(&self) -> String {
            format!(
                "CustomMomentum(period={}, initialized={}, value={})",
                self.period, self.initialized, self.value
            )
        }
    }
}
```

### FFI Memory Safety (for Cython interop)

When exposing Rust types to Cython via C FFI, follow the memory contract:

```rust
use crate::ffi::abort_on_panic;

/// Box-backed API wrapper for FFI.
#[repr(C)]
pub struct CustomMomentum_API(Box<CustomMomentum>);

/// Creates a new CustomMomentum instance.
///
/// # Safety
///
/// The returned pointer must be freed with `custom_momentum_drop`.
#[unsafe(no_mangle)]
pub extern "C" fn custom_momentum_new(period: usize) -> CustomMomentum_API {
    abort_on_panic(|| {
        CustomMomentum_API(Box::new(CustomMomentum::new(period)))
    })
}

/// Drops a CustomMomentum instance.
///
/// # Safety
///
/// This function must be called exactly once per instance.
#[unsafe(no_mangle)]
pub extern "C" fn custom_momentum_drop(indicator: CustomMomentum_API) {
    drop(indicator);  // Box drops and frees memory
}

/// Updates the indicator with a new price.
#[unsafe(no_mangle)]
pub extern "C" fn custom_momentum_update(
    indicator: &mut CustomMomentum_API,
    price: f64,
) {
    abort_on_panic(|| {
        indicator.0.update_raw(price);
    })
}
```

### Key Rust Conventions

1. **Error Handling**:
   - Use `anyhow::Result<T>` for fallible functions
   - Use `anyhow::bail!` for early returns with errors
   - Provide `new_checked()` + `new()` pattern for constructors

2. **Type Qualification**:
   - Fully qualify `anyhow::` macros
   - Fully qualify `tokio::` types
   - Import Nautilus domain types directly

3. **Logging**:
   - Use `log::*` in synchronous core crates
   - Use `tracing::*` in async/adapter code
   - Capitalize messages, omit terminal periods

4. **Python Memory Management**:
   - Never use `Arc<PyObject>` (causes reference cycles)
   - Use `clone_py_object()` for cloning Python callbacks
   - Implement manual `Clone` for callback-holding structs

5. **Testing**:
   - Use `#[rstest]` for all tests
   - No AAA separator comments
   - Use descriptive test names

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
- `references/api_reference/backtest.md` - BacktestEngine, FillModel, venues
- `references/api_reference/analysis.md` - PortfolioAnalyzer, statistics
- `references/api_reference/live.md` - LiveDataClient, LiveExecutionClient
- `references/developer_guide/adapters.md` - Adapter development
- `references/developer_guide/coding_standards.md` - Style guide
- `references/developer_guide/rust.md` - Rust style and conventions
- `references/developer_guide/ffi.md` - FFI memory contract

For concept understanding:
- `references/concepts/backtesting.md` - Backtesting concepts and models
- `references/concepts/live.md` - Live trading configuration

## Next Step

After implementation, use **nt-review** skill to validate the code.
