"""
Strategy Builder Template: Multi-Venue Strategy

Demonstrates a strategy that reads data from multiple venues simultaneously.
Common use cases:
- Cross-exchange arbitrage (CeFi A vs CeFi B)
- CEX/DEX arbitrage (Binance spot vs Uniswap pool)
- Signal confirmation (one venue's data confirms another's signal)
- Liquidity routing (send orders to best-priced venue)

This template handles the data routing and signal isolation logic.
"""

import asyncio
from collections import deque
from decimal import Decimal

from nautilus_trader.config import LiveExecEngineConfig, TradingNodeConfig
from nautilus_trader.core.data import Data
from nautilus_trader.live.node import TradingNode
from nautilus_trader.model.data import Bar, BarType, QuoteTick
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.identifiers import InstrumentId, TraderId, Venue
from nautilus_trader.model.objects import Quantity
from nautilus_trader.trading.config import StrategyConfig
from nautilus_trader.trading.strategy import Strategy

# ─── MULTI-VENUE STRATEGY CONFIG ───────────────────────────────────────────────


class MultiVenueStrategyConfig(StrategyConfig, frozen=True):
    """
    Configuration for a two-venue spread / arb strategy.

    Parameters
    ----------
    primary_instrument_id : str
        Primary venue instrument (e.g. 'BTCUSDT-PERP.BINANCE').
    secondary_instrument_id : str
        Secondary venue instrument (e.g. 'BTCUSDT-PERP.BYBIT' or 'WBTC-USDC.UNISWAP_V3').
    min_spread_bps : float
        Minimum spread in basis points before trading.
    max_position_size : float
        Maximum position size per side.
    trade_primary : bool
        If True, trade on primary venue; if False, trade on secondary.
    """

    primary_instrument_id: str
    secondary_instrument_id: str
    min_spread_bps: float = 10.0
    max_position_size: float = 1.0
    trade_primary: bool = True


# ─── MULTI-VENUE STRATEGY ──────────────────────────────────────────────────────


class MultiVenueStrategy(Strategy):
    """
    A spread/arbitrage strategy consuming data from two venues.

    The strategy monitors the price spread between two instruments
    (on different venues) and enters positions when the spread
    exceeds the configured threshold.

    Signals from both venues are kept isolated — each `on_quote_tick`
    dispatch is tagged by `instrument_id` allowing clean routing.
    """

    def __init__(self, config: MultiVenueStrategyConfig) -> None:
        super().__init__(config)

        self.primary_id = InstrumentId.from_str(config.primary_instrument_id)
        self.secondary_id = InstrumentId.from_str(config.secondary_instrument_id)

        self.primary_instrument = None
        self.secondary_instrument = None

        # Latest quotes, keyed separately per venue
        self._primary_quote: QuoteTick | None = None
        self._secondary_quote: QuoteTick | None = None

        # Spread history for monitoring
        self._spread_history: deque[float] = deque(maxlen=100)

    # ─── LIFECYCLE ─────────────────────────────────────────────────────────────

    def on_start(self) -> None:
        # Load instruments — check BOTH venues are available
        self.primary_instrument = self.cache.instrument(self.primary_id)
        if self.primary_instrument is None:
            self.log.error(f"Primary instrument not found: {self.primary_id}")
            self.stop()
            return

        self.secondary_instrument = self.cache.instrument(self.secondary_id)
        if self.secondary_instrument is None:
            self.log.error(f"Secondary instrument not found: {self.secondary_id}")
            self.stop()
            return

        # Subscribe to both venues
        self.subscribe_quote_ticks(self.primary_id)
        self.subscribe_quote_ticks(self.secondary_id)

        self.log.info(
            f"MultiVenueStrategy started: {self.primary_id} ↔ {self.secondary_id}"
        )

    def on_stop(self) -> None:
        self.cancel_all_orders(self.primary_id)
        self.cancel_all_orders(self.secondary_id)
        self.unsubscribe_quote_ticks(self.primary_id)
        self.unsubscribe_quote_ticks(self.secondary_id)

    def on_reset(self) -> None:
        self.primary_instrument = None
        self.secondary_instrument = None
        self._primary_quote = None
        self._secondary_quote = None
        self._spread_history.clear()

    # ─── DATA HANDLERS ─────────────────────────────────────────────────────────

    def on_quote_tick(self, tick: QuoteTick) -> None:
        """Route incoming ticks to the correct venue slot."""
        if tick.instrument_id == self.primary_id:
            self._primary_quote = tick
        elif tick.instrument_id == self.secondary_id:
            self._secondary_quote = tick
        else:
            return  # Unknown instrument — ignore

        # Only evaluate spread when BOTH quotes are fresh
        if self._primary_quote and self._secondary_quote:
            self._evaluate_spread()

    # ─── SPREAD LOGIC ──────────────────────────────────────────────────────────

    def _evaluate_spread(self) -> None:
        """Calculate and act on the spread between the two venues."""
        p_mid = (float(self._primary_quote.ask_price) + float(self._primary_quote.bid_price)) / 2
        s_mid = (float(self._secondary_quote.ask_price) + float(self._secondary_quote.bid_price)) / 2

        if p_mid <= 0 or s_mid <= 0:
            return

        spread_bps = abs(p_mid - s_mid) / min(p_mid, s_mid) * 10_000
        self._spread_history.append(spread_bps)

        self.log.debug(
            f"Spread: {spread_bps:.2f} bps | "
            f"Primary: {p_mid:.4f} | Secondary: {s_mid:.4f}"
        )

        if spread_bps >= self.config.min_spread_bps:
            self._handle_spread_opportunity(p_mid, s_mid, spread_bps)

    def _handle_spread_opportunity(
        self,
        primary_mid: float,
        secondary_mid: float,
        spread_bps: float,
    ) -> None:
        """
        React to a spread opportunity.

        In a real arb strategy, you would:
        1. Determine direction (primary is cheap or expensive)
        2. Validate you're not already positioned
        3. Submit orders on one or both venues simultaneously
        """
        # Validate position limits
        if not self._can_trade():
            return

        if primary_mid < secondary_mid:
            # Primary is cheaper — buy primary, sell secondary
            direction = "BUY_PRIMARY"
        else:
            direction = "SELL_PRIMARY"

        self.log.info(
            f"Spread opportunity: {spread_bps:.2f} bps → {direction}"
        )

        # Determine trading venue from config
        if self.config.trade_primary:
            instrument = self.primary_instrument
            side = OrderSide.BUY if direction == "BUY_PRIMARY" else OrderSide.SELL
        else:
            instrument = self.secondary_instrument
            side = OrderSide.SELL if direction == "BUY_PRIMARY" else OrderSide.BUY

        qty = instrument.make_qty(self.config.max_position_size * 0.1)  # 10% of max
        order = self.order_factory.market(
            instrument_id=instrument.id,
            order_side=side,
            quantity=qty,
        )
        self.submit_order(order)

    def _can_trade(self) -> bool:
        """Check position limits across both venues."""
        primary_pos = abs(float(self.portfolio.net_position(self.primary_id) or 0))
        secondary_pos = abs(float(self.portfolio.net_position(self.secondary_id) or 0))

        if primary_pos >= self.config.max_position_size:
            self.log.warning("Primary position limit reached")
            return False
        if secondary_pos >= self.config.max_position_size:
            self.log.warning("Secondary position limit reached")
            return False
        return True


# ─── MULTI-VENUE TRADING NODE SETUP ────────────────────────────────────────────

async def run_multi_venue_node() -> None:
    """
    Run a TradingNode with two venues.

    Subscribe both to the TradingNode — each venue adapter is independent
    but both feed the same strategy via the message bus.
    """
    config = TradingNodeConfig(
        trader_id=TraderId("MULTI-001"),

        timeout_connection=30.0,
        timeout_reconciliation=10.0,
        timeout_portfolio=10.0,
        timeout_disconnection=10.0,

        exec_engine=LiveExecEngineConfig(
            reconciliation=True,
            open_check_lookback_mins=60,
        ),

        # ── Two separate data clients ─────────────────────────────────────────
        # data_clients={
        #     "BINANCE": BinanceDataClientConfig(...),
        #     "BYBIT": BybitDataClientConfig(...),
        # },
        # exec_clients={
        #     "BINANCE": BinanceExecClientConfig(...),
        #     "BYBIT": BybitExecClientConfig(...),
        # },
        #
        # For CeFi + DEX:
        # data_clients={
        #     "BINANCE": BinanceDataClientConfig(...),
        #     "UNISWAP_V3": MyDEXDataClientConfig(rpc_url="...", pools=["0x..."]),
        # },
        # exec_clients={
        #     "BINANCE": BinanceExecClientConfig(...),
        #     "UNISWAP_V3": MyDEXExecClientConfig(rpc_url="...", private_key=...),
        # },
    )

    strategy_config = MultiVenueStrategyConfig(
        strategy_id="MultiVenueStrategy-001",
        primary_instrument_id="BTCUSDT-PERP.BINANCE",
        secondary_instrument_id="BTCUSDT-PERP.BYBIT",
        min_spread_bps=10.0,
        max_position_size=0.1,
        trade_primary=True,
    )

    node = TradingNode(config=config)

    # Register factories for both adapters
    # node.add_data_client_factory("BINANCE", BinanceLiveDataClientFactory)
    # node.add_exec_client_factory("BINANCE", BinanceLiveExecClientFactory)
    # node.add_data_client_factory("BYBIT", BybitLiveDataClientFactory)
    # node.add_exec_client_factory("BYBIT", BybitLiveExecClientFactory)

    node.trader.add_strategy(MultiVenueStrategy(config=strategy_config))
    node.build()

    try:
        await node.run_async()
    finally:
        node.dispose()


if __name__ == "__main__":
    asyncio.run(run_multi_venue_node())
