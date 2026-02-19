"""
Strategy Builder Template: Paper Trading Node

Paper trading connects to live market data but routes all orders through a
simulated execution venue — no real money at risk while using real price feeds.

Key difference from live_node.py:
- exec_clients uses a simulated (paper) execution client
- Reconciliation still recommended so the node tracks its own paper state

Replace MyExchange* data client with your actual market data adapter.
"""

import asyncio
import os

from nautilus_trader.config import (
    LiveDataEngineConfig,
    LiveExecEngineConfig,
    LoggingConfig,
    TradingNodeConfig,
)
from nautilus_trader.live.node import TradingNode
from nautilus_trader.model.identifiers import TraderId

# ─── USER IMPORTS ──────────────────────────────────────────────────────────────
# from nautilus_trader.adapters.binance.config import BinanceDataClientConfig
# from nautilus_trader.adapters.binance.factories import BinanceLiveDataClientFactory
# from my_package.strategies import MyStrategy, MyStrategyConfig


# ─── NODE CONFIG ───────────────────────────────────────────────────────────────

config = TradingNodeConfig(
    trader_id=TraderId("PAPER-001"),

    timeout_connection=30.0,
    timeout_reconciliation=10.0,
    timeout_portfolio=10.0,
    timeout_disconnection=10.0,

    data_engine=LiveDataEngineConfig(
        time_bars_timestamp_on_close=True,
    ),

    exec_engine=LiveExecEngineConfig(
        reconciliation=True,
        open_check_lookback_mins=60,
    ),

    logging=LoggingConfig(
        log_level="INFO",
        log_directory="logs/paper",
    ),

    # ── Live market data (real feed) ────────────────────────────────────────────
    # data_clients={
    #     "BINANCE": BinanceDataClientConfig(
    #         api_key=os.environ.get("BINANCE_API_KEY"),
    #         api_secret=os.environ.get("BINANCE_API_SECRET"),
    #         testnet=True,   # use testnet for data in paper mode
    #     ),
    # },

    # ── Paper execution (simulated) ─────────────────────────────────────────────
    # NautilusTrader does not ship a built-in paper execution client.
    # There are two common approaches:
    #
    # Option A: Use exchange testnet (recommended if available)
    #   exec_clients={"BINANCE": BinanceExecClientConfig(..., testnet=True)}
    #
    # Option B: Use a BacktestEngine running alongside TradingNode
    #   (advanced — see NautilusTrader sandbox documentation)
    #
    # Both approaches allow validating execution flow without real funds.
)


# ─── STRATEGY CONFIG ───────────────────────────────────────────────────────────

# strategy_config = MyStrategyConfig(
#     instrument_id="BTCUSDT-PERP.BINANCE",
#     bar_type="BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL",
# )


# ─── BUILD AND RUN ─────────────────────────────────────────────────────────────

async def main() -> None:
    node = TradingNode(config=config)

    # node.add_data_client_factory("BINANCE", BinanceLiveDataClientFactory)
    # node.trader.add_strategy(MyStrategy(config=strategy_config))

    node.build()

    try:
        await node.run_async()
    finally:
        node.dispose()


if __name__ == "__main__":
    asyncio.run(main())
