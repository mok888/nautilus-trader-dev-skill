# Using `uv` with NautilusTrader

NautilusTrader v1.212.0+ officially supports `uv` for Python project and dependency management. `uv` is significantly faster than `pip` and provides a unified tool for environments and scripts.

## Installation

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Creating a new project

```bash
# Initialize a new project
uv init my-trading-system
cd my-trading-system

# Add NautilusTrader
uv add nautilus-trader
```

## Common Commands

| Command | Purpose |
|---------|---------|
| `uv run script.py` | Run a script in an isolated environment |
| `uv sync` | Sync the environment with `pyproject.toml` |
| `uv add <package>` | Add a dependency |
| `uv venv` | Create a virtual environment |

## Benefits for NautilusTrader
- **Speed**: Virtual environment creation and package installation are near-instant.
- **Reproducibility**: `uv.lock` ensures identical environments across backtesting and live trading.
- **Rust Integration**: `uv` handles compiled dependencies efficiently.
