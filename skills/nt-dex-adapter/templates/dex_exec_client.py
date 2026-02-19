"""
DEX Adapter Template: Execution Client

Handles wallet-signed on-chain order submission, cancellation, and account state.

Phases 4–5 of the 7-phase DEX adapter implementation sequence.

Key differences from CeFi execution clients:
- No API keys — uses wallet private key + transaction signing
- Order flow: build tx → sign → broadcast → wait for receipt → emit events
- Fill price is actual output amount from tx receipt (not exchange-reported)
- Gas cost is included as commission in order fill events
- Account state is on-chain wallet balance (queried after each tx)

Replace 'MyDEX' with your actual DEX name throughout.
"""

import asyncio
from decimal import Decimal

from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock, MessageBus
from nautilus_trader.core.uuid import UUID4
from nautilus_trader.live.execution_client import LiveExecutionClient
from nautilus_trader.model.currencies import USDT
from nautilus_trader.model.enums import (
    AccountType,
    LiquiditySide,
    OmsType,
    OrderSide,
    PositionSide,
)
from nautilus_trader.model.identifiers import (
    AccountId,
    ClientId,
    ClientOrderId,
    InstrumentId,
    TradeId,
    VenueOrderId,
    Venue,
)
from nautilus_trader.model.objects import AccountBalance, Money, Price, Quantity
from nautilus_trader.model.orders import Order
from nautilus_trader.model.reports import OrderStatusReport

from .dex_config import MyDEXExecClientConfig
from .dex_instrument_provider import MyDEXInstrumentProvider


class MyDEXExecutionClient(LiveExecutionClient):
    """
    Execution client for MyDEX.

    Submits orders as wallet-signed on-chain transactions and maps
    transaction outcomes back to Nautilus order lifecycle events.

    Parameters
    ----------
    client_id : ClientId
        The client identifier (e.g. ClientId("MYDEX")).
    venue : Venue
        The venue (e.g. Venue("MYDEX")).
    account_id : AccountId
        The account identifier.
    msgbus : MessageBus
        The Nautilus message bus.
    cache : Cache
        The Nautilus cache.
    clock : LiveClock
        The Nautilus clock.
    instrument_provider : MyDEXInstrumentProvider
        Loaded instrument definitions.
    config : MyDEXExecClientConfig
        Client configuration (includes private key as SecretStr).
    """

    def __init__(
        self,
        client_id: ClientId,
        venue: Venue,
        account_id: AccountId,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
        instrument_provider: MyDEXInstrumentProvider,
        config: MyDEXExecClientConfig,
    ) -> None:
        super().__init__(
            client_id=client_id,
            venue=venue,
            oms_type=OmsType.NETTING,
            account_type=AccountType.CASH,
            base_currency=None,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
        )
        self._instrument_provider = instrument_provider
        self._config = config
        self._account_id = account_id

        # DEX execution state
        self._pending_txs: dict[ClientOrderId, str] = {}  # order_id → tx_hash

        # Private key is accessed via SecretStr.get_secret_value() in the Rust client
        # self._signing_client = MyDEXSigningClient(
        #     rpc_url=config.rpc_url,
        #     private_key=config.private_key.get_secret_value(),
        #     chain_id=config.chain_id,
        # )

    # ─── LIFECYCLE ─────────────────────────────────────────────────────────────

    async def _connect(self) -> None:
        """
        Connect to the DEX execution layer.

        1. Verifies RPC connectivity
        2. Loads initial account state from on-chain wallet
        3. Instruments must already be loaded by the data client
        """
        self.log.info(f"Connecting to MyDEX execution (wallet: {self._config.wallet_address})")

        # Fetch and report initial account state
        await self._update_account_state()

    async def _disconnect(self) -> None:
        """Disconnect gracefully — no open orders to cancel on AMM."""
        self.log.info("Disconnecting from MyDEX execution")

    # ─── ORDER COMMANDS ────────────────────────────────────────────────────────

    async def _submit_order(self, order: Order) -> None:
        """
        Submit an order as a signed on-chain transaction.

        Flow:
        1. Get instrument from provider
        2. Calculate min_amount_out from slippage tolerance
        3. Build + sign tx via Rust signing client
        4. Broadcast tx
        5. Emit OrderSubmitted event
        6. Wait for receipt (async), then emit OrderFilled or OrderRejected

        Parameters
        ----------
        order : Order
            The Nautilus order to submit.
        """
        instrument = self._instrument_provider.find(order.instrument_id)
        if instrument is None:
            self.generate_order_rejected(
                order=order,
                reason=f"Instrument not found: {order.instrument_id}",
                ts_event=self.clock.timestamp_ns(),
            )
            return

        # Calculate minimum output (slippage protection)
        slippage_rate = Decimal(str(self._config.max_slippage_bps)) / Decimal("10000")
        # min_amount_out = order.quantity * (1 - slippage_rate)

        try:
            # ── Build and sign transaction ──
            # tx_hash = await self._signing_client.submit_swap(
            #     pool_address=instrument.info.get("pool_address"),
            #     amount_in=float(order.quantity),
            #     min_amount_out=float(min_amount_out),
            #     deadline_secs=30,
            # )

            # Emit submitted event immediately (tx in mempool)
            self.generate_order_submitted(
                order=order,
                ts_event=self.clock.timestamp_ns(),
            )

            # Track pending tx
            # self._pending_txs[order.client_order_id] = tx_hash

            # Monitor tx completion asynchronously
            # asyncio.ensure_future(self._wait_for_receipt(order, tx_hash))

        except Exception as e:
            self.generate_order_rejected(
                order=order,
                reason=str(e),
                ts_event=self.clock.timestamp_ns(),
            )

    async def _cancel_order(self, order: Order) -> None:
        """
        Cancel a pending order.

        Note: Most AMM DEX swaps cannot be cancelled once submitted to the mempool.
        Implement speed-bump cancellation (replace-by-fee) or raise NotImplementedError
        with a clear explanation.
        """
        self.log.warning(
            f"Order cancellation not supported on AMM DEX: {order.client_order_id}. "
            "AMM swaps execute atomically; cancel via replace-by-fee if tx is pending."
        )
        # For perp DEX / on-chain CLOB with cancel support:
        # tx_hash = await self._signing_client.cancel_order(order.venue_order_id)
        # ...

    async def _cancel_all_orders(self, instrument_id: InstrumentId | None = None) -> None:
        """Cancel all open orders (AMM: usually no-op; perp DEX: close open positions)."""
        self.log.info("cancel_all_orders: not applicable for AMM DEX")

    async def _modify_order(self, order: Order, quantity: Quantity | None = None, price: Price | None = None) -> None:
        """Modify is not supported on most DEX venues."""
        self.log.warning(f"Order modification not supported on DEX: {order.client_order_id}")

    async def _query_order(self, client_order_id: ClientOrderId) -> None:
        """Query order status by checking on-chain tx receipt."""
        tx_hash = self._pending_txs.get(client_order_id)
        if tx_hash is None:
            self.log.warning(f"No tx hash found for order: {client_order_id}")
            return
        # receipt = await self._signing_client.get_receipt(tx_hash)
        # self._handle_receipt(client_order_id, receipt)

    # ─── ACCOUNT STATE ─────────────────────────────────────────────────────────

    async def _update_account_state(self) -> None:
        """
        Fetch on-chain wallet balances and emit AccountState.

        Must be called:
        - On connect
        - After every trade execution
        - Periodically to stay in sync (use a timer in the actor)
        """
        try:
            # balances = await self._signing_client.fetch_balances()
            # self.generate_account_state(
            #     balances=[
            #         AccountBalance(
            #             total=Money(balances["USDT"], USDT),
            #             locked=Money(0, USDT),
            #             free=Money(balances["USDT"], USDT),
            #         ),
            #     ],
            #     margins=[],
            #     reported=True,
            #     ts_event=self.clock.timestamp_ns(),
            # )
            pass
        except Exception as e:
            self.log.error(f"Failed to fetch account state: {e}")

    # ─── RECONCILIATION ────────────────────────────────────────────────────────

    async def generate_order_status_report(
        self,
        instrument_id: InstrumentId,
        client_order_id: ClientOrderId | None = None,
        venue_order_id: VenueOrderId | None = None,
    ) -> OrderStatusReport | None:
        """
        Generate an order status report for reconciliation.

        For DEX: query on-chain tx receipt by tx_hash (venue_order_id).
        Returns None if the tx cannot be found.
        """
        self.log.debug(
            f"generate_order_status_report: {client_order_id} / {venue_order_id}"
        )
        # tx_hash = str(venue_order_id) if venue_order_id else None
        # if tx_hash:
        #     receipt = await self._signing_client.get_receipt(tx_hash)
        #     return self._receipt_to_order_status_report(receipt, instrument_id, client_order_id)
        return None

    # ─── TX RECEIPT HANDLER ────────────────────────────────────────────────────

    async def _wait_for_receipt(self, order: Order, tx_hash: str) -> None:
        """
        Wait for transaction confirmation and emit order lifecycle events.

        On success → generate_order_filled
        On revert  → generate_order_rejected
        On timeout → generate_order_expired
        """
        try:
            # Timeout after 120 seconds
            receipt = None  # TODO: await self._signing_client.wait_for_receipt(tx_hash, timeout=120)

            if receipt is None:
                self.generate_order_expired(
                    order=order,
                    ts_event=self.clock.timestamp_ns(),
                )
                return

            if True:  # receipt.status == 1 (success)
                instrument = self._instrument_provider.find(order.instrument_id)

                # In a real implementation, parse actual amount from receipt logs
                # actual_amount_out = parse_swap_event(receipt)
                # gas_cost = receipt.gas_used * receipt.effective_gas_price / 1e18

                self.generate_order_filled(
                    order=order,
                    venue_order_id=VenueOrderId(tx_hash),
                    venue_position_id=None,
                    trade_id=TradeId(tx_hash),
                    position_side=PositionSide.FLAT,
                    last_qty=order.quantity,
                    last_px=Price.from_str("1.000000"),  # Replace with actual fill price
                    quote_currency=instrument.quote_currency if instrument else USDT,
                    commission=Money(0, USDT),            # Replace with actual gas cost
                    liquidity_side=LiquiditySide.TAKER,
                    ts_event=self.clock.timestamp_ns(),
                    ts_init=self.clock.timestamp_ns(),
                )
            else:
                self.generate_order_rejected(
                    order=order,
                    reason=f"Transaction reverted: {tx_hash}",
                    ts_event=self.clock.timestamp_ns(),
                )

            # Update account state after every completed tx
            await self._update_account_state()

        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.log.error(f"Error waiting for tx receipt {tx_hash}: {e}")
            self.generate_order_rejected(
                order=order,
                reason=f"Receipt error: {e}",
                ts_event=self.clock.timestamp_ns(),
            )
        finally:
            self._pending_txs.pop(order.client_order_id, None)
