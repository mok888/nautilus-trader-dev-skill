# NautilusTrader Development Skills for Claude Code

A collection of Claude Code skills for developing trading systems with [NautilusTrader](https://github.com/nautechsystems/nautilus_trader) - a high-performance algorithmic trading platform written in Rust with Python bindings.

## Overview

These skills provide a structured workflow for implementing trading strategies, actors, indicators, and custom components in NautilusTrader. They encode best practices, correct patterns, and review checklists to help you write production-quality trading code.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  nt-architect   │────▶│  nt-implement   │────▶│   nt-review     │
│                 │     │                 │     │                 │
│ Design component│     │ Write code from │     │ Validate before │
│ architecture    │     │ templates       │     │ deployment      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Skills

### nt-architect

**Purpose**: Translate research outputs (ML models, signals, trading ideas) into NautilusTrader component architecture.

**Use when**:
- Starting a new trading system implementation
- Deciding which components to use (Strategy vs Actor vs Indicator)
- Designing data flow between components

**Key features**:
- Component decomposition decision tree
- Data flow patterns (signals vs custom data)
- State management guidance
- Lifecycle and warmup planning

### nt-implement

**Purpose**: Implement NautilusTrader components using correct patterns and templates.

**Use when**:
- Writing Strategy, Actor, Indicator, or Adapter code
- Implementing custom simulation models (FillModel, MarginModel)
- Creating custom portfolio statistics
- Writing Rust+PyO3 core implementations

**Key features**:
- Ready-to-use Python templates for all component types
- Custom model templates (fill simulation, margin calculation, portfolio statistics)
- Rust+PyO3 implementation patterns with FFI memory safety
- Common patterns (model loading, ONNX inference, multi-timeframe data)

**Templates included**:
| Template | Purpose |
|----------|---------|
| `strategy.py` | Trading strategy with order management |
| `actor.py` | Actor for model inference and signal publishing |
| `indicator.py` | Custom indicator |
| `custom_data.py` | Custom data types for message bus |
| `exec_algorithm.py` | Execution algorithm |
| `fill_model.py` | Custom fill simulation models |
| `margin_model.py` | Custom margin calculation models |
| `portfolio_statistic.py` | Custom portfolio statistics |
| `adapters/*.py` | Exchange, data provider, internal adapters |

### nt-review

**Purpose**: Validate implementations against conventions, trading correctness, performance, and testability.

**Use when**:
- Before merging to main branch
- Before deploying to paper/live trading
- Reviewing Rust/FFI code
- Validating performance-critical code

**Review dimensions**:
1. **Nautilus Conventions** - Lifecycle methods, API patterns, naming
2. **Trading Correctness** - Position sizing, order management, risk checks
3. **Performance** - No blocking calls, memory management, efficient data handling
4. **Testability** - Backtest compatibility, deterministic behavior
5. **Live Trading** - Reconciliation, network resilience, order state management
6. **Rust/FFI** - Memory safety, style conventions, PyO3 bindings
7. **Benchmarking** - Criterion/iai setup, profiling, optimization verification

## Installation

### Option 1: Copy to Claude Code skills directory

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/nautilus-trader-dev-skill.git
cd nautilus-trader-dev-skill

# Copy skills to Claude Code directory
cp -r skills/nt-architect ~/.claude/skills/
cp -r skills/nt-implement ~/.claude/skills/
cp -r skills/nt-review ~/.claude/skills/
```

### Option 2: Symlink for easy updates

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/nautilus-trader-dev-skill.git
cd nautilus-trader-dev-skill

# Create symlinks
ln -s "$(pwd)/skills/nt-architect" ~/.claude/skills/nt-architect
ln -s "$(pwd)/skills/nt-implement" ~/.claude/skills/nt-implement
ln -s "$(pwd)/skills/nt-review" ~/.claude/skills/nt-review
```

### Verify installation

```bash
ls ~/.claude/skills/
# Should show: nt-architect  nt-implement  nt-review
```

## Usage

### In Claude Code

The skills are automatically available in Claude Code. Invoke them by name:

```
/nt-architect   # Design component architecture
/nt-implement   # Implement components from templates
/nt-review      # Review code before deployment
```

### Typical Workflow

1. **Architecture Phase** (`/nt-architect`)
   - Describe your trading idea or research output
   - Get component recommendations (Strategy, Actor, Indicator)
   - Receive data flow design and lifecycle planning

2. **Implementation Phase** (`/nt-implement`)
   - Start from provided templates
   - Follow patterns for your component type
   - Use common patterns for model loading, risk checks, etc.

3. **Review Phase** (`/nt-review`)
   - Run quick check (< 5 min) or full review (15-30 min)
   - Address issues by dimension
   - Verify with checklists before deployment

## Repository Structure

```
nautilus-trader-dev-skill/
├── skills/
│   ├── nt-architect/
│   │   ├── SKILL.md                    # Skill definition
│   │   └── references/concepts/        # Architecture concepts
│   │
│   ├── nt-implement/
│   │   ├── SKILL.md                    # Skill definition
│   │   ├── templates/                  # Ready-to-use code templates
│   │   │   ├── strategy.py
│   │   │   ├── actor.py
│   │   │   ├── indicator.py
│   │   │   ├── custom_data.py
│   │   │   ├── exec_algorithm.py
│   │   │   ├── fill_model.py
│   │   │   ├── margin_model.py
│   │   │   ├── portfolio_statistic.py
│   │   │   └── adapters/
│   │   └── references/
│   │       ├── api_reference/          # NautilusTrader API docs
│   │       ├── concepts/               # Backtesting, live trading
│   │       └── developer_guide/        # Coding standards, Rust, FFI
│   │
│   └── nt-review/
│       ├── SKILL.md                    # Skill definition
│       └── references/
│           ├── concepts/               # Live trading concepts
│           └── developer_guide/        # Testing, benchmarking, Rust, FFI
│
├── references/                         # Source reference documentation
│   ├── api_reference/
│   ├── concepts/
│   ├── developer_guide/
│   └── integrations/
│
└── docs/                               # Additional documentation
```

## Reference Documentation

The skills include curated reference documentation from NautilusTrader:

### API Reference
- Trading, Execution, Risk APIs
- Data types and models (instruments, orders, positions)
- Cache, Portfolio, Analysis modules
- Adapter APIs for 10+ exchanges

### Concepts
- Architecture and design philosophy
- Actors, Strategies, Message Bus
- Backtesting and Live Trading
- Data handling and order flow


## Custom Models

The skills include patterns for implementing custom simulation and analysis models:

### FillModel
Control order queue position and execution probability in backtests:
- `VolatilityAdjustedFillModel` - Adjust fill probability based on market volatility
- `LiquidityAwareFillModel` - Consider order size relative to typical volume
- `TimeOfDayFillModel` - Vary fill rates by trading session

### MarginModel
Custom margin calculation for different venue types:
- `RiskAdjustedMarginModel` - Apply risk multipliers
- `TieredMarginModel` - Different rates by position size
- `VolatilityMarginModel` - Dynamic margin based on ATR

### PortfolioStatistic
Custom metrics for performance analysis:
- `WinStreakStatistic` - Consecutive win/loss tracking
- `RiskAdjustedReturnStatistic` - Sharpe and Sortino ratios
- `DrawdownStatistic` - Max drawdown and duration
- `ProfitFactorStatistic` - Gross profit / gross loss
- `ExpectancyStatistic` - Expected value per trade

## Rust+PyO3 Patterns

For performance-critical code, the skills include Rust implementation patterns:

- Module structure with proper documentation
- `new_checked()` + `new()` constructor pattern
- PyO3 bindings with naming conventions
- FFI memory safety with `abort_on_panic`
- CVec memory contract for Cython interop

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Update skills and/or references
4. Submit a pull request

### Updating References

Reference documentation is sourced from NautilusTrader. To update:

1. Copy relevant `.md` files to `references/`
2. Copy to skill-specific `references/` folders as needed
3. Update `SKILL.md` if new references are added

## License

This project is licensed under the MIT License. The NautilusTrader reference documentation is subject to its own license (LGPL-3.0).

## Acknowledgments

- [NautilusTrader](https://github.com/nautechsystems/nautilus_trader) - The high-performance trading platform these skills support
- [Nautech Systems](https://nautechsystems.io) - Creators of NautilusTrader
