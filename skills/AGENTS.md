# SKILLS OVERVIEW

16 specialized skills for NautilusTrader development. Use workflow skills for
architecture, implementation, wiring, and review; use domain skills for focused
NautilusTrader concepts; use developer-guide skills for setup and testing.

## WORKFLOW

```
nt-architect → nt-implement → nt-strategy-builder → nt-review
                    ↓                    ↓
      nt-evomap-integration (if EvoMap)  nt-dex-adapter (if DEX)
```

## SKILL INDEX

| Skill | Purpose | Entry Point |
|-------|---------|-------------|
| **nt-architect** | Decompose systems into Actor/Indicator/Strategy architecture | `nt-architect/SKILL.md` |
| **nt-implement** | Implement NautilusTrader components from templates | `nt-implement/SKILL.md` |
| **nt-review** | Review code before deployment | `nt-review/SKILL.md` |
| **nt-strategy-builder** | Wire backtest, paper, and live systems | `nt-strategy-builder/SKILL.md` |
| **nt-dex-adapter** | Build custom DEX adapters | `nt-dex-adapter/SKILL.md` |
| **nt-evomap-integration** | Integrate EvoMap advisory sidecars safely | `nt-evomap-integration/SKILL.md` |
| **nt-trading** | Orders, events, positions, and portfolio concepts | `nt-trading/SKILL.md` |
| **nt-signals** | Indicators, order books, and signal analysis | `nt-signals/SKILL.md` |
| **nt-data** | Market data types, subscriptions, and catalogs | `nt-data/SKILL.md` |
| **nt-backtest** | Backtest engine, venues, actors, and fill models | `nt-backtest/SKILL.md` |
| **nt-live** | Live trading, runtime selection, adapters, reconciliation | `nt-live/SKILL.md` |
| **nt-adapters** | CeFi adapter specification and production patterns | `nt-adapters/SKILL.md` |
| **nt-model** | Instruments, identifiers, and value objects | `nt-model/SKILL.md` |
| **nt-dev** | Developer guide alignment, setup, FFI, benchmarking | `nt-dev/SKILL.md` |
| **nt-testing** | Testing policy, DataTester, ExecTester, datasets | `nt-testing/SKILL.md` |
| **nt-learn** | Structured NautilusTrader learning curriculum | `nt-learn/SKILL.md` |

## COMMON PATTERNS

### All Skills Share
- `SKILL.md` — Skill definition (description, when to use, workflow)
- `templates/` — Executable Python templates
- `references/` — API reference docs (symlinked from root `references/`)
- `rules/` — DO/DON'T rulesets (some skills)

### Template Pattern
All templates use `asyncio.run(main())` — no CLI framework.

## ANTI-PATTERNS

| Pattern | Why Bad |
|---------|---------|
| Skipping nt-architect | Unstructured codebase |
| Ignoring nt-review | Bugs in production |
| Copy-paste without understanding | Maintenance nightmare |

## WHERE TO LOOK

| I need to... | Go to |
|--------------|-------|
| Design architecture | `nt-architect/` |
| Write a strategy | `nt-implement/` |
| Run a backtest | `nt-strategy-builder/templates/backtest_node.py` |
| Go live | `nt-strategy-builder/templates/live_node.py` |
| Add DEX support | `nt-dex-adapter/` |
| Review before deploy | `nt-review/` |
| Check setup/tooling | `nt-dev/` |
| Check test policy | `nt-testing/` |
