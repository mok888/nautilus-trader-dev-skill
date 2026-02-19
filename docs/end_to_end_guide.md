# End-to-End Strategy Guide: From Research to Live Trading

This guide walks through the complete workflow of building, backtesting, and deploying a trading strategy using the NautilusTrader Development Skills.

**Prerequisites**:
- Installed `uv` (see `docs/uv_guide.md`)
- Installed skills (`nt-architect`, `nt-implement`, `nt-strategy-builder`)

---

## Part 1: Strategy Design & Backtesting

### Step 1: Project Setup

Initialize your project with `uv` for a fast, reproducible environment.

```bash
uv init my-strategy
cd my-strategy
uv add nautilus-trader pandas plotly msgspec
```

### Step 2: Design with `nt-architect`

Before writing code, define your components.
*Reference: `skills/nt-architect/SKILL.md`*

**Key Decisions**:
- **Inputs**: What data bars? On what timeframe? (e.g., `ETHUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL`)
- **Indicators**: What technical indicators do you need? (e.g., EMA cross)
- **Signal Logic**: Trigger conditions for entry/exit?
- **Risk**: Position sizing rules?

### Step 3: Implementation with `nt-implement`

Create your strategy file using the template.
*Reference: `skills/nt-implement/templates/strategy.py`*

1.  Copy `skills/nt-implement/templates/strategy.py` to `my_strategy.py`.
2.  Implement `on_bar`:
    ```python
    def on_bar(self, bar: Bar) -> None:
        # 1. Update indicators
        self.fast_ema.update(bar.close)
        self.slow_ema.update(bar.close)

        # 2. Check warmup
        if not self.slow_ema.initialized:
            return

        # 3. Generate signal
        if self.fast_ema.value > self.slow_ema.value:
            # 4. Execute
            self.buy()
    ```
3.  Implement `buy()` with risk checks from `skills/nt-strategy-builder/rules/dos_and_donts.md`.

### Step 4: Backtest Configuration with `nt-strategy-builder`

Create the backtest runner.
*Reference: `skills/nt-strategy-builder/templates/backtest_node.py`*

1.  Copy `skills/nt-strategy-builder/templates/backtest_node.py` to `run_backtest.py`.
2.  Configure your data catalog path:
    ```python
    CATALOG_PATH = Path("data/catalog")  # Ensure you have data here
    ```
3.  Wire up your strategy:
    ```python
    from my_strategy import MyStrategy, MyStrategyConfig
    # ...
    engine.add_strategy(MyStrategy(config=strategy_config))
    ```
4.  Run the backtest:
    ```bash
    uv run run_backtest.py
    ```
5.  **Visualize Results**: The template automatically generates `tearsheet.html` using `BacktestVisualizer` (`docs/visualization.md`). Open this file in your browser to analyze performance.

---

## Part 2: Live Deployment

Once your strategy is profitable in backtesting and verified with `nt-review`, deploy it.

### Step 1: Live Node Configuration

Create the live trading node.
*Reference: `skills/nt-strategy-builder/templates/live_node.py`*

1.  Copy `skills/nt-strategy-builder/templates/live_node.py` to `run_live.py`.
2.  Configure your adapters (e.g., Binance, or your custom DEX adapter):
    ```python
    # For DEX:
    from my_dex_adapter.factories import MyDEXLiveDataClientFactory, MyDEXLiveExecClientFactory
    node.add_data_client_factory("MYDEX", MyDEXLiveDataClientFactory)
    node.add_exec_client_factory("MYDEX", MyDEXLiveExecClientFactory)
    ```
3.  **Security**: Use environment variables for API keys/private keys.
    ```bash
    export BINANCE_API_KEY="your-key"
    export BINANCE_API_SECRET="your-secret"
    ```

### Step 2: Environment & Resilience

1.  **Persistence**: Enable Redis/Postgres in `TradingNodeConfig` to save state.
    ```python
    database=DatabaseConfig(type="redis", ...)
    ```
2.  **Reconciliation**: Ensure `exec_engine.reconciliation=True` (enabled by default in `live_node.py`).

### Step 3: Pre-Flight Checklist (`nt-review`)

Run through `skills/nt-review/SKILL.md` before starting:
- [ ] Are logs configured to write to file?
- [ ] Is `open_check_lookback_mins` >= 60?
- [ ] Are connection timeouts set?
- [ ] Is risk engine enabled?

### Step 4: Launch

Run the live node:
```bash
uv run run_live.py
```

Monitor `logs/nautilus.log` for successful connection and order placement.

---

## Advanced: DEX Trading

If trading on-chain:
1.  **Build Adapter**: Use `skills/nt-dex-adapter/` templates to build your `InstrumentProvider`, `DataClient`, and `ExecClient`.
2.  **Verify**: Run `skills/nt-dex-adapter/tests/test_dex_compliance.py`.
3.  **Wire In**: Use the factory registration pattern in `run_live.py`.
