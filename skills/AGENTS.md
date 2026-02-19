# SKILLS OVERVIEW

5 specialized skills for NautilusTrader development. Follow the workflow sequence.

## WORKFLOW

```
nt-architect → nt-implement → nt-strategy-builder → nt-review
                                        ↓
                                  nt-dex-adapter (if DEX)
```

## SKILL INDEX

| Skill | Purpose | Entry Point |
|-------|---------|-------------|
| **nt-architect** | Decompose system into Actor/Indicator/Strategy | `nt-architect/SKILL.md` |
| **nt-implement** | Implement Strategy/Actor/Indicator components | `nt-implement/SKILL.md` |
| **nt-strategy-builder** | Wire BacktestEngine/TradingNode | `nt-strategy-builder/SKILL.md` |
| **nt-dex-adapter** | Build custom DEX adapter | `nt-dex-adapter/SKILL.md` |
| **nt-review** | Pre-deployment code review | `nt-review/SKILL.md` |

## COMMON PATTERNS

### All Skills Share
- `SKILL.md` — Skill definition (description, when to use, workflow)
- `templates/` — Executable Python templates
- `references/` — API reference docs (symlinked to root)
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
