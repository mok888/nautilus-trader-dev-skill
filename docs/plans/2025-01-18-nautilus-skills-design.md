# Nautilus Trader Development Skills Design

## Overview

Three lifecycle-based skills for developing trading systems on nautilus_trader, designed for consistency, speed, and knowledge capture.

## User Workflow

```
Research (external: exploration, modeling, alpha discovery)
       ↓
nt-architect  →  Architecture doc
       ↓
nt-implement  →  Working components
       ↓
nt-review     →  Validated, production-ready code
       ↓
Deploy (backtest → paper trade → live)
```

## Skills

### 1. nt-architect

**Purpose:** Translate research outputs (trained models + signal logic) into Nautilus component architecture.

**Trigger:** After research/alpha discovery, before implementation.

**Responsibilities:**
- Intake research outputs (models, signal logic, data requirements)
- Guide component decomposition (Strategy vs Actor vs Indicator)
- Design data flow (message bus topics, custom data types)
- Plan state management (Cache vs component state)
- Define lifecycle/initialization order
- Output architecture document with implementation sequence

**References:**
- `concepts/architecture.md`
- `concepts/strategies.md`
- `concepts/actors.md`
- `concepts/message_bus.md`
- `concepts/data.md`

---

### 2. nt-implement

**Purpose:** Fast, consistent implementation using templates and patterns.

**Trigger:** After architecture defined, when implementing components.

**Component Coverage:**
- **Strategy** - Trading logic, order management, position handling
- **Actor** - Signal generation, model inference, monitoring
- **Indicator** - Stateless computations on market data
- **Custom Data Types** - Domain-specific data for message bus
- **Execution Algorithm** - Order slicing, adaptive execution
- **Adapters** - Exchange, data provider, internal infrastructure

**Patterns Library:**
- Model loading/inference (pickle/msgspec/ONNX in Actors)
- Feature computation pipelines
- Position sizing utilities
- Risk check integration
- Multi-timeframe data handling

**Implementation Workflow:**
1. Start from architecture doc
2. Implement in dependency order (data types → indicators → actors → strategy)
3. Validate each component before proceeding

**References:**
- `api_reference/*` (method signatures)
- `developer_guide/adapters.md`
- `developer_guide/coding_standards.md`

**Templates:** Separate files in `templates/` subdirectory

---

### 3. nt-review

**Purpose:** Validate implementations before deployment.

**Trigger:** After implementation, before merging/deploying.

**Review Dimensions:**

1. **Nautilus Conventions**
   - Lifecycle methods (`on_start`, `on_stop`, `on_reset`, `on_dispose`)
   - API usage (order factory, cache, clock)
   - Naming conventions
   - Message bus patterns

2. **Trading Correctness**
   - Position sizing validation
   - Order management edge cases
   - Risk checks present
   - State consistency
   - Warmup handling

3. **Performance**
   - No blocking calls in hot paths
   - Efficient data handling
   - Memory management
   - Async patterns

4. **Testability**
   - Backtestable in isolation
   - Mock-friendly design
   - Deterministic behavior
   - Proper logging

**References:**
- `developer_guide/coding_standards.md`
- `developer_guide/testing.md`
- `concepts/backtesting.md`

---

## File Structure

```
.claude/skills/
├── nt-architect/
│   └── SKILL.md
├── nt-implement/
│   ├── SKILL.md
│   └── templates/
│       ├── strategy.py
│       ├── actor.py
│       ├── indicator.py
│       ├── custom_data.py
│       ├── exec_algorithm.py
│       └── adapters/
│           ├── exchange.py
│           ├── data_provider.py
│           └── internal.py
└── nt-review/
    └── SKILL.md
```

## Documentation Dependencies

| Skill | Primary References |
|-------|-------------------|
| nt-architect | `concepts/*` |
| nt-implement | `api_reference/*`, `developer_guide/adapters.md`, `developer_guide/coding_standards.md` |
| nt-review | `developer_guide/coding_standards.md`, `developer_guide/testing.md`, `concepts/backtesting.md` |

## Installation

Skills created in `.claude/skills/` within this repo, then copied to `~/.claude/skills/` for global availability.
