"""
Strategy Template for nautilus_trader.

A Strategy handles trading logic: receiving data, making decisions, submitting orders.
Strategy inherits from Actor, so all Actor capabilities are available.
"""

from decimal import Decimal

from nautilus_trader.config import StrategyConfig
from nautilus_trader.core.data import Data
from nautilus_trader.model import Bar, BarType
from nautilus_trader.model import InstrumentId
from nautilus_trader.model import OrderSide
from nautilus_trader.model import Quantity
from nautilus_trader.model.events import OrderFilled
from nautilus_trader.model.events import PositionChanged
from nautilus_trader.model.events import PositionClosed
from nautilus_trader.model.events import PositionOpened
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.model.orders import MarketOrder
from nautilus_trader.trading.strategy import Strategy


class MyStrategyConfig(StrategyConfig):
    """
    Configuration for MyStrategy.

    Parameters
    ----------
    instrument_id : InstrumentId
        The instrument to trade.
    bar_type : BarType
        The bar type to subscribe to.
    trade_size : Decimal
        The size of each trade.
    order_id_tag : str
        Unique tag for this strategy instance (required for multiple instances).
    """

    instrument_id: InstrumentId
    bar_type: BarType
    trade_size: Decimal
    order_id_tag: str


class MyStrategy(Strategy):
    """
    Example trading strategy.

    Receives bar data, generates signals, and manages orders/positions.
    """

    def __init__(self, config: MyStrategyConfig) -> None:
        """
        Initialize the strategy.

        Parameters
        ----------
        config : MyStrategyConfig
            The strategy configuration.
        """
        super().__init__(config)

        # Strategy state (custom attributes)
        self.instrument: Instrument | None = None

    # ==================== LIFECYCLE HANDLERS ====================

    def on_start(self) -> None:
        """
        Handle strategy start.

        Initialize state, fetch instruments, register indicators,
        request historical data, and subscribe to live data.
        """
        # 1. Fetch instrument from cache
        self.instrument = self.cache.instrument(self.config.instrument_id)
        if self.instrument is None:
            self.log.error(f"Could not find instrument {self.config.instrument_id}")
            self.stop()
            return

        # 2. Register indicators (if any)
        # self.register_indicator_for_bars(self.config.bar_type, self.ema)

        # 3. Request historical data for warmup
        self.request_bars(self.config.bar_type)

        # 4. Subscribe to live data
        self.subscribe_bars(self.config.bar_type)

    def on_stop(self) -> None:
        """
        Handle strategy stop.

        Cancel open orders and unsubscribe from data.
        """
        self.cancel_all_orders(self.config.instrument_id)
        self.unsubscribe_bars(self.config.bar_type)

    def on_reset(self) -> None:
        """Reset strategy state for reuse."""
        self.instrument = None

    # ==================== DATA HANDLERS ====================

    def on_bar(self, bar: Bar) -> None:
        """
        Handle new bar data.

        Parameters
        ----------
        bar : Bar
            The bar received.
        """
        if self.instrument is None:
            return

        # Generate signal and trade
        signal = self._calculate_signal(bar)
        if signal > 0:
            self._buy()
        elif signal < 0:
            self._sell()

    def on_historical_data(self, data: Data) -> None:
        """
        Handle historical data (from requests).

        Parameters
        ----------
        data : Data
            The historical data received.
        """
        if isinstance(data, Bar):
            self.log.debug(f"Historical bar: {data}")

    def on_data(self, data: Data) -> None:
        """
        Handle custom data (from publish_data).

        Parameters
        ----------
        data : Data
            The custom data received.
        """
        pass  # Handle custom data types here

    def on_signal(self, signal: Data) -> None:
        """
        Handle signal data (from publish_signal).

        Parameters
        ----------
        signal : Data
            The signal received.
        """
        pass  # Handle signals from Actors here

    # ==================== ORDER HANDLERS ====================

    def on_order_filled(self, event: OrderFilled) -> None:
        """
        Handle order fill event.

        Parameters
        ----------
        event : OrderFilled
            The fill event.
        """
        self.log.info(f"Order filled: {event.last_qty} @ {event.last_px}")

    # ==================== POSITION HANDLERS ====================

    def on_position_opened(self, event: PositionOpened) -> None:
        """
        Handle position opened event.

        Parameters
        ----------
        event : PositionOpened
            The event.
        """
        self.log.info(f"Position opened: {event.position}")

    def on_position_changed(self, event: PositionChanged) -> None:
        """
        Handle position changed event.

        Parameters
        ----------
        event : PositionChanged
            The event.
        """
        pass

    def on_position_closed(self, event: PositionClosed) -> None:
        """
        Handle position closed event.

        Parameters
        ----------
        event : PositionClosed
            The event.
        """
        self.log.info(f"Position closed: {event.position}")

    # ==================== STATE PERSISTENCE ====================

    def on_save(self) -> dict[str, bytes]:
        """
        Save strategy state for persistence.

        Returns
        -------
        dict[str, bytes]
            State to persist.
        """
        return {}

    def on_load(self, state: dict[str, bytes]) -> None:
        """
        Load persisted strategy state.

        Parameters
        ----------
        state : dict[str, bytes]
            Previously saved state.
        """
        pass

    # ==================== PRIVATE METHODS ====================

    def _calculate_signal(self, bar: Bar) -> float:
        """
        Calculate trading signal from bar.

        Parameters
        ----------
        bar : Bar
            The bar to analyze.

        Returns
        -------
        float
            Signal value: positive for buy, negative for sell, zero for no action.
        """
        # Implement signal logic here
        return 0.0

    def _buy(self) -> None:
        """Submit a buy order."""
        if self.instrument is None:
            return

        order: MarketOrder = self.order_factory.market(
            instrument_id=self.config.instrument_id,
            order_side=OrderSide.BUY,
            quantity=self.instrument.make_qty(self.config.trade_size),
        )
        self.submit_order(order)

    def _sell(self) -> None:
        """Submit a sell order."""
        if self.instrument is None:
            return

        order: MarketOrder = self.order_factory.market(
            instrument_id=self.config.instrument_id,
            order_side=OrderSide.SELL,
            quantity=self.instrument.make_qty(self.config.trade_size),
        )
        self.submit_order(order)
