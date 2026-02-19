"""
Strategy Builder Template: Live Trading Node

Demonstrates a production-ready TradingNode with:
- Reconciliation and resilience timeouts
- Persistence and state recovery
- Proper adapter factory wiring (CeFi or DEX)
- Logging, monitoring

Run with: uv run skills/nt-strategy-builder/templates/live_node.py

Replace MyStrategy, MyExchange* with your actual adapters and strategies.
"""

import asyncio
import os

from nautilus_trader.config import (
    DatabaseConfig,
    LiveDataEngineConfig,
    LiveExecEngineConfig,
    LiveRiskEngineConfig,
    LoggingConfig,
    TradingNodeConfig,
)
from nautilus_trader.live.node import TradingNode
from nautilus_trader.model.identifiers import TraderId

# ─── USER IMPORTS ──────────────────────────────────────────────────────────────
# from nautilus_trader.adapters.binance.config import BinanceDataClientConfig, BinanceExecClientConfig
# from nautilus_trader.adapters.binance.factories import BinanceLiveDataClientFactory, BinanceLiveExecClientFactory
# from my_package.strategies import MyStrategy, MyStrategyConfig


# ─── NODE CONFIG ───────────────────────────────────────────────────────────────

config = TradingNodeConfig(
    trader_id=TraderId("TRADER-001"),

    # ── Connection timeouts ─────────────────────────────────────────────────────
    timeout_connection=30.0,         # Time to establish adapter connections
    timeout_reconciliation=10.0,     # Time to reconcile state with venue
    timeout_portfolio=10.0,          # Time to initialise portfolio
    timeout_disconnection=10.0,      # Time for graceful shutdown

    # ── Data engine ─────────────────────────────────────────────────────────────
    data_engine=LiveDataEngineConfig(
        time_bars_timestamp_on_close=True,
    ),

    # ── Execution engine ────────────────────────────────────────────────────────
    exec_engine=LiveExecEngineConfig(
        reconciliation=True,                     # ALWAYS True for live trading
        inflight_check_interval_ms=2000,
        open_check_interval_secs=10.0,
        open_check_lookback_mins=60,             # Never reduce below 60
        reconciliation_startup_delay_secs=10.0,  # Never reduce below 10
    ),

    # ── Risk engine ─────────────────────────────────────────────────────────────
    risk_engine=LiveRiskEngineConfig(
        bypass=False,        # Never bypass in production
        max_order_submit_rate="100/00:00:01",
        max_order_modify_rate="100/00:00:01",
        max_notional_per_order={
            "BTCUSDT-PERP.SIM": 100_000,  # $100k max notional per order
        },
    ),

    # ── State persistence (optional, recommended for production) ─────────────────
    # database=DatabaseConfig(
    #     type="redis",
    #     host=os.environ.get("REDIS_HOST", "localhost"),
    #     port=int(os.environ.get("REDIS_PORT", 6379)),
    # ),

    # ── Logging ─────────────────────────────────────────────────────────────────
    logging=LoggingConfig(
        log_level="INFO",
        log_level_file="DEBUG",
        log_directory="logs",
        log_file_format="json",   # Machine-parseable for monitoring
    ),

    # ── Data clients ─────────────────────────────────────────────────────────────
    # Replace with your actual adapter configs:
    # data_clients={
    #     "BINANCE": BinanceDataClientConfig(
    #         api_key=os.environ["BINANCE_API_KEY"],
    #         api_secret=os.environ["BINANCE_API_SECRET"],
    #         testnet=False,
    #     ),
    # },

    # ── Execution clients ─────────────────────────────────────────────────────────
    # exec_clients={
    #     "BINANCE": BinanceExecClientConfig(
    #         api_key=os.environ["BINANCE_API_KEY"],
    #         api_secret=os.environ["BINANCE_API_SECRET"],
    #         testnet=False,
    #     ),
    # },
)


# ─── STRATEGY CONFIG ───────────────────────────────────────────────────────────

# strategy_config = MyStrategyConfig(
#     instrument_id="BTCUSDT-PERP.BINANCE",
#     bar_type="BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL",
#     fast_ema_period=10,
#     slow_ema_period=20,
#     risk_per_trade=0.01,
#     # Claim any existing orders from prior session
#     external_order_claims=["BTCUSDT-PERP.BINANCE"],
# )


# ─── BUILD AND RUN ─────────────────────────────────────────────────────────────

async def main() -> None:
    node = TradingNode(config=config)

    # Register adapter factories
    # node.add_data_client_factory("BINANCE", BinanceLiveDataClientFactory)
    # node.add_exec_client_factory("BINANCE", BinanceLiveExecClientFactory)

    # Add strategies
    # node.trader.add_strategy(MyStrategy(config=strategy_config))

    # Build and run
    node.build()

    try:
        await node.run_async()
    finally:
        node.dispose()


if __name__ == "__main__":
    asyncio.run(main())
