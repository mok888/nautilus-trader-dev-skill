---
name: nt-architect
description: "Use when translating research outputs (models, signals) into nautilus_trader component architecture. Guides component decomposition, data flow design, and implementation planning."
---

# Nautilus Trader Architecture Design

## Overview

Translate research outputs (trained ML models + signal generation logic) into a nautilus_trader component architecture before writing any code. This skill guides the decomposition of research into Nautilus components and produces an architecture document for implementation.

## When to Use

- After completing research/alpha discovery (e.g., HMM regime detection, meta-learners)
- Before implementing any Nautilus components
- When designing a new trading system from research

## Architecture Design Process

### Phase 1: Intake Research Outputs

Identify and categorize what your research produced:

**Trained Models** (become Actor-hosted inference):
- Regime detection models (HMM, clustering)
- Signal prediction models (meta-learners, classifiers)
- Feature transformation models (PCA, autoencoders)

**Signal Logic** (becomes Strategy or Indicator logic):
- Entry/exit rules based on model outputs
- Position sizing formulas
- Risk thresholds and filters

**Data Requirements**:
- Input data types (bars, ticks, custom features)
- Timeframes and instruments
- Warmup periods for indicators/models

### Phase 2: Component Decomposition

Use this decision tree to assign research elements to Nautilus components:

```
Research Element
    │
    ├─► Does it TRADE (submit orders)?
    │       │
    │       YES ──► STRATEGY
    │       │       - Order management
    │       │       - Position tracking
    │       │       - Entry/exit execution
    │       │
    │       NO ──► Does it produce DATA for other components?
    │               │
    │               ├─► Stateless computation on market data?
    │               │       │
    │               │       YES ──► INDICATOR
    │               │               - Technical indicators
    │               │               - Feature calculations
    │               │               - Stateless transformations
    │               │
    │               ├─► Stateful computation or ML inference?
    │               │       │
    │               │       YES ──► ACTOR
    │               │               - Model hosting
    │               │               - Regime detection
    │               │               - Signal aggregation
    │               │               - Complex state management
    │               │
    │               └─► Custom data flowing through message bus?
    │                       │
    │                       YES ──► CUSTOM DATA TYPE
    │                               - Regime states
    │                               - Signal values
    │                               - Feature vectors
```

### Phase 3: Data Flow Design

#### Message Bus Patterns

**Signals** (lightweight, primitive values — str, float, int, bool, or bytes):
```python
# Publisher (Actor)
self.publish_signal(name="regime_state", value="trending", ts_event=ts)

# Subscriber (Strategy)
self.subscribe_signal("regime_state")
def on_signal(self, signal):
    if signal.value == "trending":
        self.enable_trend_following()
```

**Custom Data with `@customdataclass`** (structured, complex values — auto-generated constructor):
```python
from nautilus_trader.model.custom import customdataclass
from nautilus_trader.core.data import Data
from nautilus_trader.model.identifiers import InstrumentId

@customdataclass
class RegimeData(Data):
    instrument_id: InstrumentId = InstrumentId.from_str("BTCUSDT-PERP.BINANCE")
    regime: str = "unknown"
    confidence: float = 0.0
    transition_prob: float = 0.0

# Publisher (Actor)
self.publish_data(
    DataType(RegimeData, metadata={"instrument_id": "BTCUSDT-PERP.BINANCE"}),
    data,
)

# Subscriber (Strategy)
self.subscribe_data(
    data_type=DataType(RegimeData, metadata={"instrument_id": "BTCUSDT-PERP.BINANCE"}),
)
def on_data(self, data: Data):
    if isinstance(data, RegimeData):
        self.handle_regime(data)
```

**Custom Data with manual `Data` subclass** (full control, explicit ts_event/ts_init):
```python
from nautilus_trader.core.data import Data

class RegimeData(Data):
    def __init__(self, regime: str, confidence: float, ts_event: int, ts_init: int) -> None:
        self.regime = regime
        self.confidence = confidence
        self._ts_event = ts_event
        self._ts_init = ts_init

    @property
    def ts_event(self) -> int:
        return self._ts_event

    @property
    def ts_init(self) -> int:
        return self._ts_init
```

**Order Fill/Cancel Subscriptions** (monitor trading activity from Actors):
```python
# Actor subscribes to order fills for an instrument
self.subscribe_order_fills(instrument_id)
def on_order_filled(self, event: OrderFilled) -> None:
    self.log.info(f"Fill: {event.order_side} {event.last_qty} @ {event.last_px}")

# Actor subscribes to order cancels for an instrument
self.subscribe_order_cancels(instrument_id)
def on_order_canceled(self, event: OrderCanceled) -> None:
    self.log.info(f"Cancel: {event.client_order_id}")
```

#### Typical Data Flow Patterns

**Pattern: ML Model → Signal → Strategy**
```
[Market Data] → [FeatureActor] → [RegimeActor] → publish_signal → [Strategy]
                 (features)       (HMM inference)                  (trades)
```

**Pattern: Multi-Timeframe Aggregation**
```
[1-min bars] → [Indicator] → [AggregatorActor] → publish_data → [Strategy]
[5-min bars] → [Indicator] ↗
[1-hour bars] → [Indicator] ↗
```

**Pattern: Ensemble Signals**
```
[Model1Actor] → signal1 ↘
[Model2Actor] → signal2 → [EnsembleActor] → final_signal → [Strategy]
[Model3Actor] → signal3 ↗
```

### Phase 4: State Management

#### Where State Lives

| State Type | Location | Access Pattern |
|------------|----------|----------------|
| Orders, Positions | Cache | `self.cache.orders()`, `self.cache.positions()` |
| Instruments, Accounts | Cache | `self.cache.instrument()`, `self.cache.account()` |
| Market Data | Cache | `self.cache.quote_tick()`, `self.cache.bar()` |
| Model State (weights, params) | Actor attribute | `self.model`, loaded in `on_start` |
| Regime/Signal State | Actor attribute | `self.current_regime` |
| Strategy-specific State | Strategy attribute | `self.is_position_open` |

#### State Initialization in `on_start`

```python
def on_start(self) -> None:
    # 1. Load instrument from cache
    self.instrument = self.cache.instrument(self.config.instrument_id)

    # 2. Load models (msgspec preferred for serialization)
    self.model = load_model(self.config.model_path)

    # 3. Initialize indicators
    self.ema = ExponentialMovingAverage(self.config.ema_period)
    self.register_indicator_for_bars(self.config.bar_type, self.ema)

    # 4. Request historical data for warmup
    self.request_bars(self.config.bar_type)

    # 5. Subscribe to live data
    self.subscribe_bars(self.config.bar_type)
```

### Phase 5: Lifecycle Planning

#### Initialization Order

Components are initialized in dependency order:

1. **Custom Data Types** - Define data structures first
2. **Indicators** - Stateless computations
3. **Actors** - Model hosting, feature generation
4. **Strategies** - Trading logic (consumes outputs from above)

#### Warmup Requirements

Document warmup needs for each component:

| Component | Warmup Requirement | Method |
|-----------|-------------------|--------|
| EMA(20) | 20 bars minimum | `request_bars()` in `on_start` |
| HMM Regime | 100+ bars for stable regime | Historical inference in `on_historical_data` |
| Custom Features | Depends on lookback | Calculate on historical before live |

#### Dependency Graph Example

```
CustomDataTypes (RegimeData, FeatureData)
        │
        ▼
   Indicators (EMA, RSI, custom features)
        │
        ▼
   FeatureActor (aggregates features, publishes FeatureData)
        │
        ▼
   RegimeActor (runs HMM on features, publishes RegimeData)
        │
        ▼
   TradingStrategy (consumes RegimeData, executes trades)
```


After completing the design, produce a document with:

```markdown
# [System Name] Architecture

## Research Summary
- Models: [list trained models and their purpose]
- Signals: [list trading signals/rules]
- Data: [required market data]

## Component Breakdown

### Custom Data Types
- `RegimeData`: regime state with confidence
- `FeatureData`: computed features for models

### Indicators
- `FeatureIndicator`: computes [X] from bars

### Actors
- `RegimeActor`: hosts HMM model, publishes RegimeData

### Strategies
- `TrendStrategy`: trades based on regime signals

## Data Flow Diagram
[ASCII diagram or description]

## Implementation Sequence
1. Define RegimeData in custom_data.py
2. Implement FeatureIndicator
3. Implement RegimeActor
4. Implement TrendStrategy
5. Integration test with backtest

## Warmup Requirements
- FeatureIndicator: 50 bars
- HMM RegimeActor: 100 bars historical inference
```

## Key Principles

1. **Actors for ML, Strategies for Orders** - Never put model inference in Strategy
2. **Signals for Simple, Data for Complex** - Use `publish_signal` for primitives (str/float/int/bool/bytes), `publish_data` for structured data
3. **Cache for Framework State** - Orders, positions, instruments live in Cache
4. **Warmup Before Live** - Always `request_bars` before `subscribe_bars`
5. **Single Thread Model** - Nautilus runs on single thread; no async model inference in hot path
6. **Actor Subscriptions** - Actors can subscribe to order fills/cancels via `subscribe_order_fills()` / `subscribe_order_cancels()`
7. **@customdataclass for Quick Custom Data** - Use `@customdataclass` decorator for auto-generated constructors; use manual `Data` subclass for full control

## References

Load these for detailed API information (relative to this skill folder):
- `references/concepts/architecture.md`
- `references/concepts/strategies.md`
- `references/concepts/actors.md`
- `references/concepts/message_bus.md`
- `references/concepts/data.md`

For implementation patterns:
- `references/developer_guide/python.md` - Python conventions
- `references/developer_guide/adapters.md` - Adapter development guide
- `references/developer_guide/coding_standards.md` - Style guide

## Next Step

After architecture is defined, use **nt-implement** skill to implement components with templates.
