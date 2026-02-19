# PROJECT KNOWLEDGE BASE

**Generated:** 2026-02-19
**Stack:** Claude Code Skills for NautilusTrader Development

## OVERVIEW

Claude Code skills repository for building production-grade trading systems with NautilusTrader. Contains 5 specialized skills covering architecture → implementation → execution → review workflow, plus reference documentation and templates.

## STRUCTURE

```
nautilus-trader-dev-skill/
├── skills/                 # 5 specialized skills
│   ├── nt-architect/      # Architecture decomposition (Actor/Indicator/Strategy)
│   ├── nt-implement/      # Strategy/Actor/Indicator implementation
│   ├── nt-strategy-builder/ # BacktestEngine/TradingNode wiring
│   ├── nt-dex-adapter/    # Custom DEX adapter development
│   └── nt-review/         # Pre-deployment code review
├── references/            # NautilusTrader API reference docs
│   ├── api_reference/     # API documentation (19 files)
│   ├── concepts/          # Conceptual guides (20 files)
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

## SKILL WORKFLOW

```
nt-architect → nt-implement → nt-strategy-builder → nt-review
     ↓              ↓                ↓
     └──────────────┴────────────────┴──→ nt-dex-adapter (if DEX)
```

**Sequence:**
1. **nt-architect** — Decompose system into Actor/Indicator/Strategy components
2. **nt-implement** — Write individual components with templates
3. **nt-strategy-builder** — Wire BacktestEngine or TradingNode
4. **nt-dex-adapter** — (Optional) Build custom DEX adapter
5. **nt-review** — Review before live deployment

## CONVENTIONS

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

### Tooling
- `uv` for dependency management (not pip)
- `cargo nextest` for Rust tests (not cargo test)
- `msgspec.Struct` for serialization (faster than dataclasses)

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

## COMMANDS

```bash
# Install dependencies
uv sync --active --all-groups --all-extras

# Build nautilus-trader
uv run --no-sync python build.py

# Python tests
pytest

# Rust tests
cargo nextest run --workspace --features 'python,ffi,high-precision,defi'

# Skill-specific tests
uv run pytest skills/nt-strategy-builder/tests/ -v
uv run pytest skills/nt-dex-adapter/tests/ -v
```

## NOTES

- This is a **skills repo**, not the nautilus-trader source code
- Skills are consumed by Claude Code via SKILL.md files
- Templates use `asyncio.run(main())` pattern (no CLI framework)
- Copyright headers: 2015-2026
