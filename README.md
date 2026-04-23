# NautilusTrader Development Skills for AI Agents

A collection of AI agent skills (Claude Code, Gemini CLI, Codex, Hermes) for developing trading systems with [NautilusTrader](https://github.com/nautechsystems/nautilus_trader) — a high-performance algorithmic trading platform written in Rust with Python bindings.

## Overview

These skills encode NautilusTrader best practices, correct patterns, and structured workflows for building production-quality trading systems. Validated against **NautilusTrader v1.224.0** (released 2026-03-03) and aligned with the official [NautilusTrader Developer Guide](https://nautilustrader.io/docs/latest/developer_guide/).

## Skills Map

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   DESIGN                 IMPLEMENT                 VALIDATE                  │
│                                                                              │
│  nt-architect  ──────► nt-implement  ──────────► nt-review                  │
│  Design component        Code components          Review conventions,       │
│  architecture            from templates           correctness, perf         │
│                              │                                              │
│                              ▼                                              │
│                     nt-strategy-builder ◄── nt-dex-adapter                 │
│                     Wire & run systems        Build on-chain                │
│                     (backtest, paper, live)   DEX venues                    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                        DOMAIN KNOWLEDGE (7 skills)                           │
│                                                                              │
│   nt-trading      Orders, events, positions, portfolio                      │
│   nt-signals      Indicators, order books, data analysis                     │
│   nt-data         Market data types, subscriptions, catalogs                │
│   nt-backtest     BacktestEngine, venues, actors, fill models               │
│   nt-live         TradingNode, live adapters, reconciliation                │
│   nt-adapters     CeFi adapter spec (Binance, OKX, Bybit…), 7-phase build   │
│   nt-model        Core domain objects, identifiers, instruments             │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                     DEVELOPER GUIDE & TESTING (2 skills)                     │
│                                                                              │
│   nt-dev          Coding standards, Rust/Python conventions, FFI,            │
│                   benchmarking, releases, environment setup                  │
│   nt-testing      Full testing pyramid, DataTesterConfig, ExecTesterConfig,  │
│                   property-based testing, fuzzing, test datasets             │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                        LEARNING & INTEGRATION                                │
│                                                                              │
│   nt-learn            12-stage structured curriculum                         │
│   nt-evomap-integ.    EvoMap.ai advisory sidecar integration                 │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Typical Workflows

| Goal | Skills to use |
|---|---|
| Design a new trading system | `nt-architect` → `nt-implement` |
| Build a CeFi adapter (Binance, OKX…) | `nt-adapters` + `nt-dev` |
| Build a DEX adapter (on-chain) | `nt-dex-adapter` + `nt-implement` |
| Run a backtest | `nt-strategy-builder` + `nt-backtest` |
| Deploy live trading | `nt-strategy-builder` + `nt-live` |
| Review code before merge | `nt-review` + `nt-testing` |
| Learn NautilusTrader | `nt-learn` (12-stage curriculum) |
| Contribute to NautilusTrader core | `nt-dev` + `nt-testing` |

## Skill Inventory (16 skills)

### Workflow Pipeline (6)
| Skill | Description | Key Content |
|---|---|---|
| `nt-architect` | Research → component architecture decomposition | Design patterns, data flow planning |
| `nt-implement` | Templates for all NT component types | Strategy, Actor, Indicator, Adapter, FillModel, Rust+PyO3 |
| `nt-review` | Code review for NT conventions | Trading correctness, FFI safety, perf benchmarks |
| `nt-strategy-builder` | Idea → running system (backtest/paper/live) | Multi-venue wiring, fill models, DO/DON'Ts |
| `nt-dex-adapter` | Custom DEX adapter development | RPC nodes, wallet signing, pool discovery, test suite |
| `nt-evomap-integration` | EvoMap.ai advisory sidecar | Non-blocking execution, approval gates |

### Domain Knowledge (7)
| Skill | Description | Key Content |
|---|---|---|
| `nt-trading` | Trading domain: orders, events, positions | Order lifecycle, event-driven architecture |
| `nt-signals` | Indicators, order books, analysis | Technical indicators, book imbalance |
| `nt-data` | Market data types and pipelines | Subscriptions, catalogs, data model |
| `nt-backtest` | Backtesting engine and config | BacktestEngine, actors, fill models |
| `nt-live` | Live trading and production ops | TradingNode, adapters, reconciliation |
| `nt-adapters` | CeFi adapter specification | 7-phase implementation, 118KB official spec |
| `nt-model` | Core domain objects | Instruments, identifiers, value objects |

### Developer Guide (2)
| Skill | Description | Key Content |
|---|---|---|
| `nt-dev` | Official dev guide alignment | Coding standards, Rust/Python conventions, FFI memory, releases |
| `nt-testing` | Testing pyramid and specs | DataTesterConfig, ExecTesterConfig, property-based, fuzzing |

### Learning (1)
| Skill | Description | Key Content |
|---|---|---|
| `nt-learn` | Structured 12-stage curriculum | From basics to adapter development |

## Official Developer Guide Coverage

| Dev Guide Section | Skill | Status |
|---|---|---|
| Environment Setup | `nt-dev` | ✅ Full reference |
| Coding Standards | `nt-dev` | ✅ Full reference |
| Design Principles | `nt-architect` | ✅ Workflow skill |
| Rust | `nt-dev` | ✅ Full reference |
| Python | `nt-dev` | ✅ Full reference |
| Testing | `nt-testing` | ✅ Full reference + specs |
| Spec Data Testing | `nt-testing` | ✅ 877-line spec |
| Spec Exec Testing | `nt-testing` | ✅ 1867-line spec |
| Test Datasets | `nt-testing` | ✅ Full reference |
| Docs Style | `nt-dev` | ✅ Full reference |
| Releases | `nt-dev` | ✅ Full reference |
| Adapters | `nt-adapters` + `nt-dex-adapter` | ✅ CeFi + DEX |
| Benchmarking | `nt-dev` | ✅ Full reference |
| FFI | `nt-dev` | ✅ Memory contract spec |

## Reference Architecture

Skills use two reference patterns:

1. **Shared `references/` directory** — workflow skills (nt-architect, nt-implement, nt-review) symlink to the root `references/` directory containing API docs, concepts, developer guide, integrations, and dev templates.

2. **Per-skill `references/` directories** — domain skills (nt-trading, nt-signals, etc.) keep domain-specific references locally, with cross-skill deduplication via symlinks (e.g., nt-adapters → nt-dev for shared guides).

## Agent Compatibility

These skills work with:
- **Claude Code** (Anthropic) — via AGENTS.md per-skill
- **Gemini CLI** — via AGENTS.md
- **Codex** (OpenAI) — via AGENTS.md
- **Hermes Agent** — via SKILL.md + references/
- **OpenCode** — via SKILL.md + references/

## Source

- Official docs: [nautilustrader.io/docs/latest/developer_guide](https://nautilustrader.io/docs/latest/developer_guide/)
- NautilusTrader repo: [nautechsystems/nautilus_trader](https://github.com/nautechsystems/nautilus_trader)
- Skill repo: [Martingale42/nautilus-dev](https://github.com/Martingale42/nautilus-dev)
