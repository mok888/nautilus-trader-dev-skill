"""
Strategy Builder Template: DEX Adapter as Venue

Shows how to wire a custom DEX adapter (built with nt-dex-adapter skill) into
BOTH a BacktestEngine and a TradingNode. The adapter is treated identically to
any CeFi adapter from the framework's perspective.

Assumes a DEX adapter package structure produced by nt-dex-adapter:
  my_dex_adapter/
    config.py     ← MyDEXDataClientConfig, MyDEXExecClientConfig
    factory.py    ← MyDEXLiveDataClientFactory, MyDEXLiveExecClientFactory

Replace placeholder names with your actual adapter package.
"""

import asyncio
import os
from decimal import Decimal
from pathlib import Path

from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.models import FillModel
from nautilus_trader.config import (
    BacktestDataConfig,
    LiveExecEngineConfig,
    TradingNodeConfig,
)
from nautilus_trader.live.node import TradingNode
from nautilus_trader.model.currencies import USDT
from nautilus_trader.model.enums import AccountType, OmsType
from nautilus_trader.model.identifiers import TraderId, Venue
from nautilus_trader.model.objects import Money
from nautilus_trader.persistence.catalog import ParquetDataCatalog

# ─── DEX ADAPTER IMPORTS ───────────────────────────────────────────────────────
# Built using nt-dex-adapter skill. Swap with your actual package:
#
# from my_dex_adapter.config import MyDEXDataClientConfig, MyDEXExecClientConfig
# from my_dex_adapter.factory import (
#     MyDEXLiveDataClientFactory,
#     MyDEXLiveExecClientFactory,
# )

# ─── STRATEGY IMPORT ───────────────────────────────────────────────────────────
# from my_package.strategies import MyStrategy, MyStrategyConfig


# =============================================================================
# Option A: BacktestEngine with DEX adapter venue
# =============================================================================

def run_dex_backtest(catalog_path: str = "/path/to/catalog") -> None:
    """
    Run a backtest using DEX data stored in a catalog.

    The DEX data (order book deltas, trade ticks) must be pre-written to the
    catalog in normalised Nautilus format. Use the DEX adapter's data client
    to fetch and write historical data during a data-ingestion step:

        async def ingest_dex_data():
            # Fetch on-chain trade history
            trades = await my_dex.fetch_trades(pool="0x...", days=30)
            catalog.write_data(trades)

    Then run this function using the pre-filled catalog.
    """
    catalog = ParquetDataCatalog(catalog_path)

    # DEX-realistic fill model
    dex_fill_model = FillModel(
        prob_fill_on_limit=0.25,  # DEX limit orders rarely execute at exact price
        prob_fill_on_stop=1.0,
        prob_slippage=0.70,       # High AMM slippage
        random_seed=42,
    )

    engine = BacktestEngine()

    # Add DEX venue — treated as CASH account (no margin on DEX)
    engine.add_venue(
        venue=Venue("UNISWAP_V3"),
        oms_type=OmsType.NETTING,
        account_type=AccountType.CASH,
        base_currency=USDT,
        starting_balances=[Money(10_000, USDT)],
        fill_model=dex_fill_model,
    )

    # Load instruments from catalog (written by DEX adapter's instrument provider)
    for instrument in catalog.instruments():
        engine.add_instrument(instrument)

    # Load DEX data from catalog
    engine.add_data(catalog.trade_ticks())          # On-chain swaps as TradeTick
    engine.add_data(catalog.order_book_deltas())    # AMM pool state deltas

    # Add strategy
    # engine.add_strategy(MyStrategy(MyStrategyConfig(
    #     instrument_id="WETH-USDC.UNISWAP_V3",
    # )))

    engine.run()

    print(engine.trader.generate_account_report(Venue("UNISWAP_V3")))
    print(engine.trader.generate_positions_report())
    engine.dispose()


# =============================================================================
# Option B: Live TradingNode with DEX adapter as execution venue
# =============================================================================

async def run_dex_live_node() -> None:
    """
    Run a live TradingNode connected to a DEX adapter.

    The DEX adapter handles:
    - Instrument discovery (pool addresses → Nautilus instruments)
    - Market data (polling AMM state → QuoteTick / OrderBookDelta)
    - Order execution (wallet-signed on-chain transactions)
    """
    config = TradingNodeConfig(
        trader_id=TraderId("DEX-TRADER-001"),

        timeout_connection=60.0,         # DEX: allow extra time for RPC connection
        timeout_reconciliation=30.0,
        timeout_portfolio=15.0,
        timeout_disconnection=15.0,

        exec_engine=LiveExecEngineConfig(
            reconciliation=True,
            open_check_lookback_mins=60,
        ),

        # ─── DEX data client config ───────────────────────────────────────────
        # data_clients={
        #     "UNISWAP_V3": MyDEXDataClientConfig(
        #         rpc_url=os.environ["ETH_RPC_URL"],
        #         ws_rpc_url=os.environ.get("ETH_WS_RPC_URL"),
        #         wallet_address=os.environ["WALLET_ADDRESS"],
        #         pools=["0xCBCdF9626bC03E24f779434178A73a0B4bad62eD"],  # WBTC/ETH 0.3%
        #         poll_interval_secs=2.0,   # DEX: poll chain every 2s (no WS streaming)
        #         sandbox_mode=False,
        #     ),
        # },

        # ─── DEX execution client config ──────────────────────────────────────
        # exec_clients={
        #     "UNISWAP_V3": MyDEXExecClientConfig(
        #         rpc_url=os.environ["ETH_RPC_URL"],
        #         private_key=SecretStr(os.environ["WALLET_PRIVATE_KEY"]),
        #         max_slippage_bps=50,   # 0.50% max slippage tolerance
        #         gas_limit=300_000,
        #     ),
        # },
    )

    node = TradingNode(config=config)

    # Register DEX adapter factories
    # node.add_data_client_factory("UNISWAP_V3", MyDEXLiveDataClientFactory)
    # node.add_exec_client_factory("UNISWAP_V3", MyDEXLiveExecClientFactory)

    # Add strategy
    # node.trader.add_strategy(MyStrategy(MyStrategyConfig(
    #     instrument_id="WETH-USDC.UNISWAP_V3",
    # )))

    node.build()

    try:
        await node.run_async()
    finally:
        node.dispose()


# ─── ENTRY POINTS ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    mode = sys.argv[1] if len(sys.argv) > 1 else "backtest"

    if mode == "backtest":
        run_dex_backtest()
    elif mode == "live":
        asyncio.run(run_dex_live_node())
    else:
        print(f"Unknown mode: {mode}. Use 'backtest' or 'live'.")
