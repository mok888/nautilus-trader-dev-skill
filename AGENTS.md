# PROJECT KNOWLEDGE BASE

**Generated:** 2026-03-30
**Commit:** 618653c
**Branch:** main
**Stack:** AI Agent Skills (Claude Code, Gemini CLI, Codex) for NautilusTrader development
**NautilusTrader Version:** v1.224.0 Beta (released 2026-03-03)

## OVERVIEW

AI agent skills repository for building production-grade trading systems with NautilusTrader. Contains specialized skills covering architecture → implementation → integration → execution → review workflow, plus reference documentation and templates.

## STRUCTURE

```
nautilus-trader-dev-skill/
├── skills/                 # Specialized skills
│   ├── nt-architect/      # Architecture decomposition (Actor/Indicator/Strategy)
│   ├── nt-implement/      # Strategy/Actor/Indicator implementation
│   ├── nt-evomap-integration/ # EvoMap advisory sidecar integration
│   ├── nt-strategy-builder/ # BacktestEngine/TradingNode wiring
│   ├── nt-dex-adapter/    # Custom DEX adapter development
│   └── nt-review/         # Pre-deployment code review
├── references/            # NautilusTrader API reference docs
│   ├── api_reference/     # API documentation
│   ├── concepts/          # Conceptual guides
│   ├── developer_guide/   # Development guides
│   └── integrations/      # Integration examples
└── docs/                  # Usage guides (uv, serialization, visualization)
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Design component architecture | `skills/nt-architect/` | Start here for new projects |
| Implement Strategy/Actor | `skills/nt-implement/` | Templates + conventions |
| Wire backtest or live node | `skills/nt-strategy-builder/templates/` | backtest_node.py, live_node.py |
| Build DEX adapter | `skills/nt-dex-adapter/` | 7-phase implementation |
| Review before deployment | `skills/nt-review/` | FFI/Rust/Performance checklist |
| Find API docs | `references/api_reference/` | Per-module API reference |
| Understand concepts | `references/concepts/` | backtesting, live, orders, cache |
| Adapter dev guide | `references/developer_guide/adapters.md` | Rust-first pattern |
| End-to-End Workflow | `docs/end_to_end_guide.md` | **NEW** Full walkthrough |

## SKILL WORKFLOW

```
nt-architect → nt-implement → nt-strategy-builder → nt-review
                    ↓                ↓
     nt-evomap-integration (if EvoMap)  nt-dex-adapter (if DEX)
```

**Sequence:**
1. **nt-architect** — Decompose system into Actor/Indicator/Strategy components
2. **nt-implement** — Write individual components with templates
3. **nt-evomap-integration** — (Optional) Add governed EvoMap advisory workflow
4. **nt-strategy-builder** — Wire BacktestEngine or TradingNode
5. **nt-dex-adapter** — (Optional) Build custom DEX adapter
6. **nt-review** — Review before live deployment

## CONVENTIONS (PROJECT-SPECIFIC)

### Python
- Ruff linting, 100 char lines
- PEP 604 union syntax: `X | None` (not `Optional[X]`)
- NumPy docstrings, imperative mood
- Type hints required everywhere

### Rust
- `AHashMap` for hot paths
- `get_runtime().spawn()` (NEVER `tokio::spawn()` from Python threads)
- `anyhow::bail!` for errors
- `#![deny(unsafe_op_in_unsafe_fn)]`
- No box-style banner comments

### Lifecycle Rules (all components)
- `super().__init__(config)` must be first call in `__init__`
- `on_start`: load instrument from cache (null check), load models, `request_bars` then `subscribe_bars`
- `on_stop`: cancel orders, unsubscribe, cleanup state
- `on_reset`: clear buffers and state for reuse
- Never use `clock`/`logger`/`cache` in `__init__` (not yet available)

### Tooling
- `uv` for dependency management and test execution (not pip)
- `cargo nextest` for Rust tests (not cargo test)
- `msgspec.Struct` favored for high-throughput serialization
- Skills and references are markdown-first; keep guidance concise and executable

## ANTI-PATTERNS (CRITICAL)

| Pattern | Consequence |
|---------|-------------|
| Panic across FFI | Undefined behavior |
| CVec double-free | Crash |
| `tokio::spawn()` from Python | Panic |
| `.clone()` in hot paths | Performance degradation |
| `.unwrap()` in production | Potential panic |
| Raw `float` for Price/Quantity | Precision loss |
| `time.sleep()` in handlers | Blocks event loop |
| Unbounded lists | Memory leak |
| `reconciliation=False` live | State drift |
| `Arc<PyObject>` | Memory leak |
| `prob_fill_on_stop` in FillModel | Deprecated — use `prob_slippage` |
| `from nautilus_trader.adapters.dydx_v4` | **Removed in v1.223.0** — use `nautilus_trader.adapters.dydx` |
| `listen_key_ping_max_failures` in Binance config | **Removed in v1.223.0** — Binance now uses WebSocket API auth |
| `subscribe_order_book_snapshots()` | **Removed in v1.223.0** — use `_subscribe_order_book_depth` |
| `Quantity - Quantity` expecting `Decimal` result | **v1.223.0**: returns `Quantity`; negative result raises `ValueError` |
| `trade_execution=True` in bar-only backtests | **v1.223.0**: default changed to `True`; set `False` explicitly for bar-only |
| `x += y` for `Price`/`Quantity`/`Money` in Rust | **v1.223.0**: `AddAssign`/`SubAssign` removed — use `x = x + y` |
| `fill_limit_at_touch` in FillModel | **v1.224.0**: Renamed to `fill_limit_inside_spread` |
| Coinbase International adapter (`COINBASE_INTX`) | **v1.224.0**: Entire package removed — use different venue |
| `InstrumentProvider.load_ids_async` override | **v1.224.0**: Now has default — only `load_all_async` required |
| Hyperliquid `builder_fee_refresh_mins` | **v1.224.0**: Config removed |

## COMMANDS

```bash
# Install dependencies
uv sync --active --all-groups --all-extras

# Build nautilus-trader
uv run --no-sync python build.py

# Python tests
uv run pytest

# Rust tests
cargo nextest run --workspace --features 'python,ffi,high-precision,defi'

# Skill-specific tests
uv run pytest skills/nt-strategy-builder/tests/ -v
uv run pytest skills/nt-dex-adapter/tests/ -v
```

## NOTES

- This is a **skills repo**, not the nautilus-trader source code
- Skills are consumed by AI agents (Claude Code, Gemini CLI, Codex, etc.) via SKILL.md files
- Templates use `asyncio.run(main())` pattern (no CLI framework)
- Copyright headers: 2015-2026
