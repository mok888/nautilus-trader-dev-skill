"""
DEX Adapter Template: Data Client

Handles market data subscriptions for a custom DEX.
Converts pool state (AMM reserves, on-chain events) into Nautilus data objects.

Phase 3 of the 7-phase DEX adapter implementation sequence.

Key differences from CeFi data clients:
- No WebSocket streams (usually) → polling-based data updates
- Pool state → QuoteTick (AMM price synthesis)
- On-chain swap events → TradeTick
- AMM state deltas → OrderBookDelta (optional, for CLOB DEX)

Replace 'MyDEX' with your actual DEX name throughout.
"""

import asyncio
import sys
from pathlib import Path

_TEMPLATE_DIR = Path(__file__).resolve().parent
if str(_TEMPLATE_DIR) not in sys.path:
    sys.path.append(str(_TEMPLATE_DIR))

from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock, MessageBus
from nautilus_trader.core.uuid import UUID4
from nautilus_trader.live.data_client import LiveMarketDataClient
from nautilus_trader.model.data import (
    Bar,
    BarType,
    DataType,
    OrderBookDelta,
    QuoteTick,
    TradeTick,
)
from nautilus_trader.model.enums import AggressorSide
from nautilus_trader.model.identifiers import ClientId, InstrumentId, TradeId, Venue
from nautilus_trader.model.objects import Price, Quantity

try:
    from .dex_config import MyDEXDataClientConfig
    from .dex_instrument_provider import MyDEXInstrumentProvider
except ImportError:
    from dex_config import MyDEXDataClientConfig
    from dex_instrument_provider import MyDEXInstrumentProvider


class MyDEXDataClient(LiveMarketDataClient):
    """
    Market data client for MyDEX.

    Polls the RPC node for AMM pool state updates and emits:
    - QuoteTick: synthesised from pool reserves (bid/ask around AMM price)
    - TradeTick: from confirmed on-chain swap events
    - OrderBookDelta: for on-chain CLOB DEX (optional)

    Parameters
    ----------
    client_id : ClientId
        The client identifier (e.g. ClientId("MYDEX")).
    venue : Venue
        The venue (e.g. Venue("MYDEX")).
    msgbus : MessageBus
        The Nautilus message bus.
    cache : Cache
        The Nautilus cache.
    clock : LiveClock
        The Nautilus clock.
    instrument_provider : MyDEXInstrumentProvider
        Loaded instrument definitions.
    config : MyDEXDataClientConfig
        Client configuration.
    """

    def __init__(
        self,
        client_id: ClientId,
        venue: Venue,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
        instrument_provider: MyDEXInstrumentProvider,
        config: MyDEXDataClientConfig,
    ) -> None:
        super().__init__(
            client_id=client_id,
            venue=venue,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
        )
        self._instrument_provider = instrument_provider
        self._config = config

        # Pool subscriptions: instrument_id → polling task
        self._poll_tasks: dict[InstrumentId, asyncio.Task] = {}
        # NOTE: Wrap your RPC client in a MyDEXHttpClient that uses
        # nautilus_network::http::HttpClient (via PyO3), NOT reqwest::Client directly.
        # This gives you built-in rate limiting, retry logic, and consistent error handling.
        # self._http_client = MyDEXHttpClient(rpc_url=config.rpc_url)
        # self._ws_client: MyDEXWebSocketClient | None = None

    # ─── LIFECYCLE ─────────────────────────────────────────────────────────────

    async def _connect(self) -> None:
        """
        Connect to the DEX data feed.

        1. Loads all instruments from the instrument provider.
        2. Starts WebSocket event stream (if available) or prepares polling loop.
        """
        self.log.info("Connecting to MyDEX data feed...")

        # Load instruments first — required before any data can be handled
        await self._instrument_provider.load_all_async()
        self.log.info(
            f"Loaded {len(self._instrument_provider.get_all())} instruments from MyDEX"
        )

        # Optional: connect to WS RPC for event subscriptions
        # if self._config.ws_rpc_url:
        #     self._ws_client = MyDEXWebSocketClient(self._config.ws_rpc_url)
        #     await self._ws_client.connect()

    async def _disconnect(self) -> None:
        """Disconnect and cancel all polling tasks."""
        for task in self._poll_tasks.values():
            task.cancel()
        self._poll_tasks.clear()

        # if self._ws_client:
        #     await self._ws_client.disconnect()

    # ─── SUBSCRIPTIONS ─────────────────────────────────────────────────────────

    async def _subscribe_quote_ticks(self, instrument_id: InstrumentId) -> None:
        """
        Subscribe to quote ticks for a pool.

        Starts a polling loop that fetches pool reserves at the configured
        interval and synthesises QuoteTick objects.
        """
        if instrument_id in self._poll_tasks:
            return  # Already subscribed

        self.log.info(f"Subscribing to quote ticks: {instrument_id}")

        task = asyncio.ensure_future(self._poll_pool_state(instrument_id))
        self._poll_tasks[instrument_id] = task

    async def _subscribe_trade_ticks(self, instrument_id: InstrumentId) -> None:
        """
        Subscribe to on-chain swap events (trade ticks).

        For EVM chains, subscribe to the Swap event log from the pool contract.
        These become TradeTick objects in Nautilus.
        """
        self.log.info(f"Subscribing to trade ticks: {instrument_id}")
        # If WS available: subscribe to Swap event
        # if self._ws_client:
        #     await self._ws_client.subscribe_swap_events(pool_address, self._on_swap_event)

    async def _subscribe_order_book_deltas(self, instrument_id: InstrumentId) -> None:
        """
        Subscribe to order book deltas.

        For AMM DEX: not applicable (AMM has no discrete order book).
        For on-chain CLOB DEX: subscribe to Maker/Taker events.
        """
        self.log.info(
            f"OrderBookDelta subscription: {instrument_id} (AMM: derived from pool)"
        )
        # AMM implementation: synthesise L1 snapshot from pool reserves
        # CLOB implementation: subscribe to on-chain order events

    async def _unsubscribe_quote_ticks(self, instrument_id: InstrumentId) -> None:
        task = self._poll_tasks.pop(instrument_id, None)
        if task:
            task.cancel()

    async def _unsubscribe_trade_ticks(self, instrument_id: InstrumentId) -> None:
        self.log.info(f"Unsubscribed trade ticks: {instrument_id}")

    async def _unsubscribe_order_book_deltas(self, instrument_id: InstrumentId) -> None:
        self.log.info(f"Unsubscribed order book: {instrument_id}")

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

        For DEX: fetch historical swap events from chain or subgraph,
        aggregate into OHLCV bars.
        """
        # bars = await self._client.fetch_historical_bars(bar_type, limit, start, end)
        # self._handle_bars(bars, bar_type, correlation_id)
        self.log.warning(f"Historical bar request not yet implemented for {bar_type}")

    # ─── POLLING LOOP ──────────────────────────────────────────────────────────

    async def _poll_pool_state(self, instrument_id: InstrumentId) -> None:
        """
        Continuously poll pool state and emit QuoteTick objects.

        Runs until the task is cancelled (on unsubscribe or disconnect).

        Each poll:
        1. Fetches pool reserves from RPC
        2. Synthesises bid/ask from AMM formula
        3. Emits QuoteTick via self._handle_quote_tick()
        """
        while True:
            try:
                await asyncio.sleep(self._config.poll_interval_secs)

                # Fetch pool reserves (implement with your RPC client)
                # reserves = await self._http_client.fetch_pool_reserves(pool_address)
                # quote_tick = self._reserves_to_quote_tick(instrument_id, reserves)
                # self._handle_quote_tick(quote_tick)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.log.error(f"Error polling pool {instrument_id}: {e}")
                # Backoff and retry
                await asyncio.sleep(self._config.poll_interval_secs * 2)

    # ─── DATA CONVERSION HELPERS ───────────────────────────────────────────────

    def _reserves_to_quote_tick(
        self,
        instrument_id: InstrumentId,
        reserve0: int,
        reserve1: int,
        decimals0: int = 18,
        decimals1: int = 6,
    ) -> QuoteTick:
        """
        Synthesise a QuoteTick from AMM pool reserves.

        Uses the constant product formula (Uniswap V2-style):
            price = reserve1 / reserve0  (adjusted for decimals)

        The fee is applied to produce realistic bid/ask spread.

        Parameters
        ----------
        instrument_id : InstrumentId
            The pool's instrument identifier.
        reserve0 : int
            Token0 reserve (raw, without decimal adjustment).
        reserve1 : int
            Token1 reserve (raw, without decimal adjustment).
        decimals0 : int
            Token0 decimal places (e.g. 18 for WETH).
        decimals1 : int
            Token1 decimal places (e.g. 6 for USDC).
        """
        instrument = self._instrument_provider.find(instrument_id)
        if instrument is None:
            raise ValueError(f"Instrument not found: {instrument_id}")

        # Adjust reserves for decimals
        adjusted_r0 = reserve0 / (10**decimals0)
        adjusted_r1 = reserve1 / (10**decimals1)

        if adjusted_r0 == 0:
            raise ValueError("reserve0 is zero — pool is empty")

        mid_price = adjusted_r1 / adjusted_r0
        fee_rate = float(instrument.taker_fee)

        # AMM effective buy/sell prices include fee
        ask = mid_price * (1 + fee_rate)  # Cost to buy token0
        bid = mid_price * (1 - fee_rate)  # Revenue from selling token0

        return QuoteTick(
            instrument_id=instrument_id,
            bid_price=Price.from_str(f"{bid:.6f}"),
            ask_price=Price.from_str(f"{ask:.6f}"),
            bid_size=Quantity.from_str(f"{adjusted_r0:.8f}"),  # Pool depth as size
            ask_size=Quantity.from_str(f"{adjusted_r0:.8f}"),
            ts_event=self.clock.timestamp_ns(),
            ts_init=self.clock.timestamp_ns(),
        )

    def _swap_event_to_trade_tick(
        self,
        instrument_id: InstrumentId,
        amount_in: float,
        amount_out: float,
        tx_hash: str,
        block_timestamp_ns: int,
        is_buy: bool,
    ) -> TradeTick:
        """
        Convert an on-chain Swap event to a TradeTick.

        Parameters
        ----------
        instrument_id : InstrumentId
            The pool's instrument identifier.
        amount_in : float
            Amount of input token (decimal-adjusted).
        amount_out : float
            Amount of output token (decimal-adjusted).
        tx_hash : str
            Transaction hash (used as unique trade ID).
        block_timestamp_ns : int
            Block timestamp in Unix nanoseconds.
        is_buy : bool
            True if base token is being bought.
        """
        execution_price = amount_out / amount_in if amount_in > 0 else 0.0

        return TradeTick(
            instrument_id=instrument_id,
            price=Price.from_str(f"{execution_price:.6f}"),
            size=Quantity.from_str(f"{amount_in:.8f}"),
            aggressor_side=AggressorSide.BUYER if is_buy else AggressorSide.SELLER,
            trade_id=TradeId(tx_hash),
            ts_event=block_timestamp_ns,
            ts_init=self.clock.timestamp_ns(),
        )
