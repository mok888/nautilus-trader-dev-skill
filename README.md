# NautilusTrader Development Skills for AI Agents

A collection of AI agent skills (Claude Code, Gemini CLI, Codex) for developing trading systems with [NautilusTrader](https://github.com/nautechsystems/nautilus_trader) - a high-performance algorithmic trading platform written in Rust with Python bindings.

## Overview

These skills provide a structured workflow for implementing trading strategies, actors, indicators, and custom components in NautilusTrader. They encode best practices, correct patterns, and review checklists to help you write production-quality trading code. All skills are validated against **NautilusTrader v1.224.0** (released 2026-03-03) and comply with the official [NautilusTrader Developer Guide](https://nautilustrader.io/docs/latest/developer_guide/).

## Skills Map

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   DESIGN                 IMPLEMENT              VALIDATE                 │
│                                                                          │
│  nt-architect  ──────► nt-implement ──────────► nt-review               │
│                              │                                           │
│  Design component            │ (use components in)                       │
│  architecture                ▼                                           │
│                        nt-strategy-builder ◄── nt-dex-adapter           │
│                                                                          │
│                        Wire & run systems       Build on-chain           │
│                        (backtest, paper, live)  DEX venues               │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Typical Workflows

| Goal | Skills to use |
|---|---|
| New strategy from research | `nt-architect` → `nt-implement` → `nt-strategy-builder` → `nt-review` |
| Integrate `evomap.ai` advisory loop | `nt-architect` → `nt-evomap-integration` → `nt-strategy-builder` → `nt-review` |
| Backtest on historical data | `nt-strategy-builder` (backtest template) |
| Build a DEX data/execution adapter | `nt-dex-adapter` → `nt-strategy-builder` (wire it in) → `nt-review` |
| Review code before deployment | `nt-review` |

---

## Skill Details

### nt-architect
**Purpose**: Translate research outputs (ML models, signals, trading ideas) into NautilusTrader component architecture.
- Component decomposition decision tree
- Data flow patterns (signals vs custom data)
- State management and lifecycle planning

### nt-implement
**Purpose**: Implement NautilusTrader components using correct patterns and templates.
- Ready-to-use Python templates for all component types
- Custom model templates (fill, margin, portfolio statistics)
- Rust+PyO3 implementation patterns

### nt-review
**Purpose**: Validate implementations against conventions, trading correctness, performance, and testability.
- Review dimensions: Conventions, Correctness, Performance, Testability, Live Trading, Rust/FFI

### nt-strategy-builder
**Purpose**: Wire components into running systems (backtest, paper, live) with CeFi and DEX venues.
- Templates for `BacktestEngine` and `TradingNode`
- Multi-venue and DEX wiring guidance

### nt-dex-adapter
**Purpose**: Build custom on-chain DEX adapters that integrate with NautilusTrader.
- 7-phase implementation sequence for DEX adapters
- Instrument provider, data client, and execution client templates

### nt-evomap-integration
**Purpose**: Implement and govern `evomap.ai` advisory integration.
- Sidecar architecture and component boundaries
- Deterministic fallback and decision provenance

---

## Installation

### For Gemini CLI

1. Clone the repository to your preferred location.
2. Link the skills to your local Gemini configuration:
   ```bash
   gemini skills link ./skills/nt-architect
   gemini skills link ./skills/nt-implement
   gemini skills link ./skills/nt-review
   gemini skills link ./skills/nt-strategy-builder
   gemini skills link ./skills/nt-dex-adapter
   gemini skills link ./skills/nt-evomap-integration
   ```
3. Verify installation:
   ```bash
   gemini skills list
   ```

### For Claude Code

1. Clone the repository.
2. Link or copy the skills to the Claude Code skills directory:
   ```bash
   ln -s "$(pwd)/skills/nt-architect" ~/.claude/skills/nt-architect
   # ... repeat for other skills
   ```
3. The skills will be available as `/nt-architect`, `/nt-implement`, etc.

### For Codex

Place the skill directories in your project's `.agents/skills/` folder or follow your specific Codex configuration for custom skills.

## Usage

Once installed, you can trigger these skills by mentioning them or their purpose in your prompts.

### Example Prompts:
- "Use **nt-architect** to design a strategy for HMM regime detection."
- "Implement a new Strategy using the **nt-implement** template."
- "Review my adapter implementation with **nt-review**."
- "Wire up a backtest for this strategy using **nt-strategy-builder**."

---

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

The skills include curated reference documentation from NautilusTrader, aligned with the official [Developer Guide](https://nautilustrader.io/docs/latest/developer_guide/):

### Developer Guide
- **Environment Setup** - Development environment, uv, Cap'n Proto, Rust toolchain
- **Coding Standards** - Universal formatting, shell script portability, naming conventions
- **Python** - PEP-8 compliance, type hints, NumPy docstrings, Ruff linting
- **Rust** - Cargo conventions, error handling, async patterns, adapter runtime patterns
- **Testing** - pytest, cargo-nextest, mixed debugging, coverage
- **Adapters** - Rust-first adapter development, HTTP/WebSocket patterns
- **Benchmarking** - Criterion and iai frameworks, flamegraph generation
- **FFI Memory Contract** - CVec lifecycle, PyCapsule patterns
- **Docs Style** - Documentation conventions and best practices

### API Reference
- Trading, Execution, Risk APIs
- Data types and models (instruments, orders, positions)
- Cache, Portfolio, Analysis modules
- Adapter APIs for 15+ exchanges (Binance, Bybit, OKX, BitMEX, Coinbase IntX, IB, dYdX, Databento, Betfair, Tardis, Polymarket, MT5, Hyperliquid, and more)

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
- PyO3 bindings with `py_*` prefix naming convention
- FFI memory safety with `abort_on_panic`
- CVec memory contract for Cython interop
- Adapter runtime patterns with `get_runtime().spawn()`
- Hash collections guidance (AHashMap vs HashMap vs DashMap)
- GIL-based cloning for Rust-Python memory management
- Unsafe Rust safety policy (`#![deny(unsafe_op_in_unsafe_fn)]`)

## Key Conventions (from Official Docs)

### Python
- Use PEP 604 union syntax: `Instrument | None` (not `Optional[Instrument]`)
- NumPy docstring format with imperative mood
- Type hints required on all function signatures
- Use `ruff` for linting

### Rust
- Copyright header with current year (2015-2026)
- Use `anyhow::bail!` for early error returns
- Use `AHashMap` for hot paths, standard `HashMap` for network clients
- Use `get_runtime().spawn()` instead of `tokio::spawn()` in adapters
- No box-style banner comments

### Testing
- Use `pytest` for Python, `cargo-nextest` for Rust
- Polling helpers (`eventually`, `wait_until_async`) instead of sleeps
- Mixed debugging available via VS Code

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
