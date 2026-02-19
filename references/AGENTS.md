# REFERENCES

NautilusTrader API documentation and conceptual guides.

## STRUCTURE

```
references/
├── api_reference/     # Per-module API docs (19 files)
│   ├── adapters/      # Adapter APIs
│   ├── model/         # Model types
│   └── *.md           # Core module APIs
├── concepts/          # Conceptual guides (20 files)
│   ├── backtesting.md # BacktestEngine, fill models
│   ├── live.md        # TradingNode, reconciliation
│   ├── orders.md      # Order types, lifecycle
│   └── data.md        # Data types, subscriptions
├── developer_guide/   # Development guides
│   ├── adapters.md    # Rust-first adapter pattern
│   ├── rust.md        # Rust conventions
│   └── ffi.md         # FFI memory contract
├── integrations/      # Integration examples
└── dev_templates/     # Development templates
```

## WHERE TO LOOK

| Topic | File |
|-------|------|
| BacktestEngine | `concepts/backtesting.md` |
| TradingNode | `concepts/live.md` |
| Order types | `concepts/orders.md` |
| Data subscriptions | `concepts/data.md` |
| Actor system | `concepts/actors.md` |
| Cache | `concepts/cache.md` |
| Adapter development | `developer_guide/adapters.md` |
| FFI safety | `developer_guide/ffi.md` |
| Backtest API | `api_reference/backtest.md` |
| Live API | `api_reference/live.md` |
| Model types | `api_reference/model/` |

## KEY CONCEPTS

### Core Files (Read First)
1. `concepts/overview.md` — System overview
2. `concepts/architecture.md` — Component relationships
3. `concepts/backtesting.md` — Backtest patterns
4. `concepts/live.md` — Live trading patterns

### Advanced Topics
- `concepts/message_bus.md` — Pub/sub system
- `concepts/portfolio.md` — Portfolio state
- `concepts/positions.md` — Position tracking
- `concepts/reports.md` — Reporting framework

## USAGE

These references are symlinked into skill directories for context loading. Use relative paths from skill folder:
```
references/concepts/backtesting.md
references/api_reference/live.md
```
