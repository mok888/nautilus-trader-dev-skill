"""
Data Provider Adapter Template for nautilus_trader.

A data-only adapter provides market data without execution capabilities.
Use this for data vendors like Databento, Tardis, or custom data sources.
"""

from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock
from nautilus_trader.common.component import MessageBus
from nautilus_trader.config import InstrumentProviderConfig
from nautilus_trader.config import LiveDataClientConfig
from nautilus_trader.core.uuid import UUID4
from nautilus_trader.live.data_client import LiveDataClient
from nautilus_trader.model import ClientId
from nautilus_trader.model import InstrumentId
from nautilus_trader.model import Venue
from nautilus_trader.model.data import Bar
from nautilus_trader.model.data import BarType
from nautilus_trader.model.data import DataType
from nautilus_trader.model.data import QuoteTick
from nautilus_trader.model.data import TradeTick
from nautilus_trader.model.instruments import Instrument


# =============================================================================
# Configuration
# =============================================================================

class MyDataProviderConfig(LiveDataClientConfig):
    """
    Configuration for the data provider.

    Parameters
    ----------
    api_key : str
        API key for authentication.
    base_url : str
        Base URL for REST API.
    ws_url : str
        WebSocket URL for streaming.
    """

    api_key: str
    base_url: str = "https://api.myprovider.com"
    ws_url: str = "wss://ws.myprovider.com"


# =============================================================================
# Data Client
# =============================================================================

class MyDataProviderClient(LiveDataClient):
    """
    Data client for a data-only provider.

    Handles market data subscriptions and historical data requests.
    Does not provide execution capabilities.
    """

    def __init__(
        self,
        loop,
        client_id: ClientId,
        venue: Venue,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
        config: MyDataProviderConfig,
    ) -> None:
        """
        Initialize the data client.

        Parameters
        ----------
        loop : asyncio.AbstractEventLoop
            The event loop.
        client_id : ClientId
            The client identifier.
        venue : Venue
            The venue (can be synthetic for data providers).
        msgbus : MessageBus
            The message bus.
        cache : Cache
            The cache.
        clock : LiveClock
            The clock.
        config : MyDataProviderConfig
            The client configuration.
        """
        super().__init__(
            loop=loop,
            client_id=client_id,
            venue=venue,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
        )
        self._config = config
        self._subscriptions: set[str] = set()

    async def _connect(self) -> None:
        """Connect to the data provider."""
        self._log.info("Connecting to data provider...")
        # Establish connection (REST auth, WebSocket connect)
        pass

    async def _disconnect(self) -> None:
        """Disconnect from the data provider."""
        self._log.info("Disconnecting from data provider...")
        self._subscriptions.clear()

    # ==================== SUBSCRIPTIONS ====================

    async def _subscribe(self, data_type: DataType) -> None:
        """
        Subscribe to custom data type.

        Parameters
        ----------
        data_type : DataType
            The data type to subscribe to.
        """
        topic = str(data_type)
        if topic not in self._subscriptions:
            self._subscriptions.add(topic)
            # Send subscription request

    async def _subscribe_instruments(self, venue: Venue) -> None:
        """Subscribe to instrument updates."""
        pass

    async def _subscribe_quote_ticks(self, instrument_id: InstrumentId) -> None:
        """Subscribe to quote ticks."""
        topic = f"quotes:{instrument_id}"
        self._subscriptions.add(topic)
        # Send subscription to WebSocket

    async def _subscribe_trade_ticks(self, instrument_id: InstrumentId) -> None:
        """Subscribe to trade ticks."""
        topic = f"trades:{instrument_id}"
        self._subscriptions.add(topic)

    async def _subscribe_bars(self, bar_type: BarType) -> None:
        """Subscribe to bars."""
        topic = f"bars:{bar_type}"
        self._subscriptions.add(topic)

    async def _unsubscribe(self, data_type: DataType) -> None:
        """Unsubscribe from custom data type."""
        topic = str(data_type)
        self._subscriptions.discard(topic)

    async def _unsubscribe_quote_ticks(self, instrument_id: InstrumentId) -> None:
        """Unsubscribe from quote ticks."""
        topic = f"quotes:{instrument_id}"
        self._subscriptions.discard(topic)

    async def _unsubscribe_trade_ticks(self, instrument_id: InstrumentId) -> None:
        """Unsubscribe from trade ticks."""
        topic = f"trades:{instrument_id}"
        self._subscriptions.discard(topic)

    async def _unsubscribe_bars(self, bar_type: BarType) -> None:
        """Unsubscribe from bars."""
        topic = f"bars:{bar_type}"
        self._subscriptions.discard(topic)

    # ==================== REQUESTS ====================

    async def _request(
        self,
        data_type: DataType,
        correlation_id: UUID4,
    ) -> None:
        """Request custom data."""
        # Fetch from REST API
        # Parse and publish via self._handle_data(data, correlation_id)
        pass

    async def _request_bars(
        self,
        bar_type: BarType,
        limit: int,
        correlation_id: UUID4,
        start: int | None = None,
        end: int | None = None,
    ) -> None:
        """
        Request historical bars.

        Parameters
        ----------
        bar_type : BarType
            The bar type to request.
        limit : int
            Maximum number of bars.
        correlation_id : UUID4
            Request correlation ID.
        start : int, optional
            Start timestamp (nanoseconds).
        end : int, optional
            End timestamp (nanoseconds).
        """
        # Fetch historical bars from REST API
        bars: list[Bar] = []  # Parse response into Bar objects

        # Publish bars
        self._handle_bars(
            bar_type=bar_type,
            bars=bars,
            partial=bar_type,  # Most recent bar may be partial
            correlation_id=correlation_id,
        )

    async def _request_quote_ticks(
        self,
        instrument_id: InstrumentId,
        limit: int,
        correlation_id: UUID4,
        start: int | None = None,
        end: int | None = None,
    ) -> None:
        """Request historical quote ticks."""
        ticks: list[QuoteTick] = []  # Parse response

        self._handle_quote_ticks(
            instrument_id=instrument_id,
            ticks=ticks,
            correlation_id=correlation_id,
        )

    async def _request_trade_ticks(
        self,
        instrument_id: InstrumentId,
        limit: int,
        correlation_id: UUID4,
        start: int | None = None,
        end: int | None = None,
    ) -> None:
        """Request historical trade ticks."""
        ticks: list[TradeTick] = []  # Parse response

        self._handle_trade_ticks(
            instrument_id=instrument_id,
            ticks=ticks,
            correlation_id=correlation_id,
        )

    # ==================== MESSAGE HANDLING ====================

    def _handle_ws_message(self, raw: bytes) -> None:
        """
        Handle incoming WebSocket message.

        Parameters
        ----------
        raw : bytes
            Raw message bytes.
        """
        # Parse message type
        # Route to appropriate handler
        # Example:
        #   if msg_type == "quote":
        #       tick = self._parse_quote_tick(data)
        #       self._handle_quote_tick(tick)
        #   elif msg_type == "trade":
        #       tick = self._parse_trade_tick(data)
        #       self._handle_trade_tick(tick)
        pass

    def _handle_quote_tick(self, tick: QuoteTick) -> None:
        """Publish quote tick to message bus."""
        self._msgbus.publish(
            topic=f"data.quotes.{tick.instrument_id}",
            msg=tick,
        )

    def _handle_trade_tick(self, tick: TradeTick) -> None:
        """Publish trade tick to message bus."""
        self._msgbus.publish(
            topic=f"data.trades.{tick.instrument_id}",
            msg=tick,
        )
