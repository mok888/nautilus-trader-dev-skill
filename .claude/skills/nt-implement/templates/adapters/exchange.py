"""
Exchange Adapter Template for nautilus_trader.

A full exchange adapter provides:
- InstrumentProvider: Load instrument definitions
- LiveDataClient: Market data (quotes, trades, bars)
- LiveExecutionClient: Order execution

This template shows the Python layer structure.
For production adapters, see developer_guide/adapters.md for Rust core patterns.
"""

from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock
from nautilus_trader.common.component import MessageBus
from nautilus_trader.config import InstrumentProviderConfig
from nautilus_trader.config import LiveDataClientConfig
from nautilus_trader.config import LiveExecClientConfig
from nautilus_trader.core.uuid import UUID4
from nautilus_trader.live.data_client import LiveMarketDataClient
from nautilus_trader.live.execution_client import LiveExecutionClient
from nautilus_trader.model import AccountId
from nautilus_trader.model import ClientId
from nautilus_trader.model import InstrumentId
from nautilus_trader.model import Venue
from nautilus_trader.model.data import BarType
from nautilus_trader.model.data import DataType
from nautilus_trader.model.enums import AccountType
from nautilus_trader.model.enums import OmsType
from nautilus_trader.model.identifiers import ClientOrderId
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.model.orders import Order


# =============================================================================
# Configuration
# =============================================================================

class MyExchangeInstrumentProviderConfig(InstrumentProviderConfig):
    """Configuration for the instrument provider."""

    api_key: str | None = None
    api_secret: str | None = None
    base_url: str = "https://api.myexchange.com"


class MyExchangeDataClientConfig(LiveDataClientConfig):
    """Configuration for the data client."""

    api_key: str | None = None
    api_secret: str | None = None
    base_url: str = "https://api.myexchange.com"
    ws_url: str = "wss://ws.myexchange.com"


class MyExchangeExecClientConfig(LiveExecClientConfig):
    """Configuration for the execution client."""

    api_key: str
    api_secret: str
    base_url: str = "https://api.myexchange.com"
    ws_url: str = "wss://ws.myexchange.com"
    account_type: AccountType = AccountType.MARGIN


# =============================================================================
# Instrument Provider
# =============================================================================

class MyExchangeInstrumentProvider:
    """
    Instrument provider for MyExchange.

    Loads and caches instrument definitions from the exchange.
    """

    def __init__(self, config: MyExchangeInstrumentProviderConfig) -> None:
        """
        Initialize the instrument provider.

        Parameters
        ----------
        config : MyExchangeInstrumentProviderConfig
            The provider configuration.
        """
        self._config = config
        self._instruments: dict[InstrumentId, Instrument] = {}

    async def load_all_async(self) -> None:
        """Load all available instruments."""
        # Fetch instruments from exchange API
        # Parse and store in self._instruments
        pass

    async def load_ids_async(
        self,
        instrument_ids: list[InstrumentId],
    ) -> None:
        """
        Load specific instruments by ID.

        Parameters
        ----------
        instrument_ids : list[InstrumentId]
            The instrument IDs to load.
        """
        pass

    def get_all(self) -> dict[InstrumentId, Instrument]:
        """Return all loaded instruments."""
        return self._instruments.copy()

    def find(self, instrument_id: InstrumentId) -> Instrument | None:
        """Find instrument by ID."""
        return self._instruments.get(instrument_id)


# =============================================================================
# Data Client
# =============================================================================

class MyExchangeDataClient(LiveMarketDataClient):
    """
    Data client for MyExchange.

    Handles market data subscriptions and historical data requests.
    """

    def __init__(
        self,
        loop,
        client_id: ClientId,
        venue: Venue,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
        instrument_provider: MyExchangeInstrumentProvider,
        config: MyExchangeDataClientConfig,
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
            The venue.
        msgbus : MessageBus
            The message bus.
        cache : Cache
            The cache.
        clock : LiveClock
            The clock.
        instrument_provider : MyExchangeInstrumentProvider
            The instrument provider.
        config : MyExchangeDataClientConfig
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
        self._instrument_provider = instrument_provider
        self._config = config

    async def _connect(self) -> None:
        """Connect to the exchange."""
        # Establish WebSocket connection
        # Load instruments
        await self._instrument_provider.load_all_async()

    async def _disconnect(self) -> None:
        """Disconnect from the exchange."""
        # Close WebSocket connection
        pass

    async def _subscribe_quote_ticks(self, instrument_id: InstrumentId) -> None:
        """Subscribe to quote ticks."""
        # Send subscription message to WebSocket
        pass

    async def _subscribe_trade_ticks(self, instrument_id: InstrumentId) -> None:
        """Subscribe to trade ticks."""
        pass

    async def _subscribe_bars(self, bar_type: BarType) -> None:
        """Subscribe to bars."""
        pass

    async def _unsubscribe_quote_ticks(self, instrument_id: InstrumentId) -> None:
        """Unsubscribe from quote ticks."""
        pass

    async def _unsubscribe_trade_ticks(self, instrument_id: InstrumentId) -> None:
        """Unsubscribe from trade ticks."""
        pass

    async def _unsubscribe_bars(self, bar_type: BarType) -> None:
        """Unsubscribe from bars."""
        pass

    async def _request_bars(
        self,
        bar_type: BarType,
        limit: int,
        correlation_id: UUID4,
        start: int | None = None,
        end: int | None = None,
    ) -> None:
        """Request historical bars."""
        # Fetch from REST API
        # Parse and publish via self._handle_bars(bars, bar_type, correlation_id)
        pass


# =============================================================================
# Execution Client
# =============================================================================

class MyExchangeExecutionClient(LiveExecutionClient):
    """
    Execution client for MyExchange.

    Handles order submission, modification, and cancellation.
    """

    def __init__(
        self,
        loop,
        client_id: ClientId,
        venue: Venue,
        account_id: AccountId,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
        instrument_provider: MyExchangeInstrumentProvider,
        config: MyExchangeExecClientConfig,
    ) -> None:
        """
        Initialize the execution client.

        Parameters
        ----------
        loop : asyncio.AbstractEventLoop
            The event loop.
        client_id : ClientId
            The client identifier.
        venue : Venue
            The venue.
        account_id : AccountId
            The account identifier.
        msgbus : MessageBus
            The message bus.
        cache : Cache
            The cache.
        clock : LiveClock
            The clock.
        instrument_provider : MyExchangeInstrumentProvider
            The instrument provider.
        config : MyExchangeExecClientConfig
            The client configuration.
        """
        super().__init__(
            loop=loop,
            client_id=client_id,
            venue=venue,
            oms_type=OmsType.NETTING,
            account_type=config.account_type,
            base_currency=None,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
        )
        self._instrument_provider = instrument_provider
        self._config = config
        self._account_id = account_id

    async def _connect(self) -> None:
        """Connect to the exchange."""
        # Establish authenticated WebSocket connection
        pass

    async def _disconnect(self) -> None:
        """Disconnect from the exchange."""
        pass

    async def _submit_order(self, order: Order) -> None:
        """
        Submit an order to the exchange.

        Parameters
        ----------
        order : Order
            The order to submit.
        """
        # Convert Nautilus order to exchange format
        # Send via REST or WebSocket
        # Generate OrderSubmitted event
        pass

    async def _modify_order(
        self,
        order: Order,
        quantity: int | None = None,
        price: float | None = None,
    ) -> None:
        """
        Modify an existing order.

        Parameters
        ----------
        order : Order
            The order to modify.
        quantity : int, optional
            New quantity.
        price : float, optional
            New price.
        """
        pass

    async def _cancel_order(self, order: Order) -> None:
        """
        Cancel an order.

        Parameters
        ----------
        order : Order
            The order to cancel.
        """
        pass

    async def _cancel_all_orders(self, instrument_id: InstrumentId | None = None) -> None:
        """Cancel all orders, optionally filtered by instrument."""
        pass

    async def _query_order(self, client_order_id: ClientOrderId) -> None:
        """Query order status from exchange."""
        pass


# =============================================================================
# Factory (for integration with TradingNode)
# =============================================================================
#
# def create_myexchange_data_client(
#     loop,
#     msgbus: MessageBus,
#     cache: Cache,
#     clock: LiveClock,
#     config: MyExchangeDataClientConfig,
# ) -> MyExchangeDataClient:
#     """Factory function for data client."""
#     provider = MyExchangeInstrumentProvider(
#         config=MyExchangeInstrumentProviderConfig(
#             api_key=config.api_key,
#             api_secret=config.api_secret,
#         )
#     )
#     return MyExchangeDataClient(
#         loop=loop,
#         client_id=ClientId("MYEXCHANGE"),
#         venue=Venue("MYEXCHANGE"),
#         msgbus=msgbus,
#         cache=cache,
#         clock=clock,
#         instrument_provider=provider,
#         config=config,
#     )
