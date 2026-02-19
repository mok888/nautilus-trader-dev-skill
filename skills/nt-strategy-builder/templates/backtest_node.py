"""
Strategy Builder Template: Full Backtest Node

Demonstrates a complete BacktestEngine setup with:
- ParquetDataCatalog as data source
- BacktestVenueConfig with custom FillModel
- Strategy and Actor wiring
- Strategy and Actor wiring
- Result analysis
- Interactive visualization (tearsheet)

Replace MyStrategy / MyStrategyConfig with your actual components.
"""

from decimal import Decimal
from pathlib import Path

from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.models import FillModel
from nautilus_trader.backtest.config import BacktestEngineConfig, BacktestVenueConfig
from nautilus_trader.config import BacktestDataConfig, BacktestRunConfig
from nautilus_trader.model.currencies import USD, USDT
from nautilus_trader.model.enums import AccountType, OmsType
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.model.objects import Money
from nautilus_trader.persistence.catalog import ParquetDataCatalog

# ─── USER IMPORTS ──────────────────────────────────────────────────────────────
# from my_package.strategies import MyStrategy, MyStrategyConfig


# ─── CATALOG SETUP ─────────────────────────────────────────────────────────────

CATALOG_PATH = Path("/path/to/catalog")  # ← change this
catalog = ParquetDataCatalog(CATALOG_PATH)


# ─── FILL MODEL ────────────────────────────────────────────────────────────────

fill_model = FillModel(
    prob_fill_on_limit=0.5,   # Probability a limit order fills (0→1)
    prob_fill_on_stop=1.0,    # Probability a stop order fills (usually 1.0)
    prob_slippage=0.2,        # Probability of one tick slippage on market orders
    random_seed=42,           # Reproducible results
)

# DEX-realistic variant (uncomment for DEX venues):
# dex_fill_model = FillModel(
#     prob_fill_on_limit=0.25,
#     prob_fill_on_stop=1.0,
#     prob_slippage=0.70,
#     random_seed=42,
# )


# ─── VENUE CONFIG ──────────────────────────────────────────────────────────────

# Crypto spot (CASH account, no leverage)
venue_config = BacktestVenueConfig(
    name="SIM",
    oms_type=OmsType.NETTING,
    account_type=AccountType.CASH,
    base_currency=USDT,
    starting_balances=[Money(10_000, USDT)],
    fill_model=fill_model,
    # modules=[],         # Optional: BacktestModule list (e.g. for simulated margin)
    # leverage=None,      # CASH accounts have no leverage
)

# Futures / perps variant (uncomment if needed):
# perp_venue_config = BacktestVenueConfig(
#     name="SIM_PERP",
#     oms_type=OmsType.NETTING,
#     account_type=AccountType.MARGIN,
#     base_currency=USDT,
#     starting_balances=[Money(10_000, USDT)],
#     default_leverage=Decimal("10"),
#     fill_model=fill_model,
# )


# ─── DATA CONFIG ───────────────────────────────────────────────────────────────

data_config = BacktestDataConfig(
    catalog_path=str(catalog.path),
    data_cls="nautilus_trader.model.data:Bar",
    instrument_id="BTCUSDT-PERP.SIM",   # ← match your instrument and venue
    # start_time="2024-01-01",           # Optional: filter to date range
    # end_time="2024-06-30",
)


# ─── ENGINE CONFIG ─────────────────────────────────────────────────────────────

engine_config = BacktestEngineConfig(
    trader_id="BACKTESTER-001",
    logging={"log_level": "WARNING"},    # Reduce noise; use DEBUG for debugging
)


# ─── RUN CONFIG ────────────────────────────────────────────────────────────────

run_config = BacktestRunConfig(
    engine=engine_config,
    venues=[venue_config],
    data=[data_config],
)


# ─── STRATEGY CONFIG ───────────────────────────────────────────────────────────

# strategy_config = MyStrategyConfig(
#     instrument_id="BTCUSDT-PERP.SIM",
#     bar_type="BTCUSDT-PERP.SIM-1-MINUTE-LAST-EXTERNAL",
#     fast_ema_period=10,
#     slow_ema_period=20,
#     risk_per_trade=0.02,
# )


# ─── RUN BACKTEST ──────────────────────────────────────────────────────────────

def run_backtest() -> None:
    engine = BacktestEngine(config=engine_config)

    # Add venue
    engine.add_venue(
        venue=Venue("SIM"),
        oms_type=OmsType.NETTING,
        account_type=AccountType.CASH,
        base_currency=USDT,
        starting_balances=[Money(10_000, USDT)],
        fill_model=fill_model,
    )

    # Load instruments from catalog
    instruments = catalog.instruments()
    for instrument in instruments:
        engine.add_instrument(instrument)

    # Add data from catalog
    bars = catalog.bars()
    engine.add_data(bars)

    # Add strategy
    # engine.add_strategy(MyStrategy(config=strategy_config))

    # Run
    engine.run()

    # Results
    print(engine.trader.generate_account_report(Venue("SIM")))
    print(engine.trader.generate_order_fills_report())
    print(engine.trader.generate_positions_report())

    # Visualization (requires plotly)
    try:
        from nautilus_trader.analysis.visualizer import BacktestVisualizer
        print("Generating tearsheet...")
        visualizer = BacktestVisualizer(results=engine)
        visualizer.tearsheet(output_path="tearsheet.html")
        print("Tearsheet saved to tearsheet.html")
    except ImportError:
        print("Install plotly to generate tearsheet: uv add plotly")

    engine.dispose()


if __name__ == "__main__":
    run_backtest()
