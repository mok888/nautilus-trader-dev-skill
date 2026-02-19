"""
DEX Adapter Template: Instrument Provider

Discovers on-chain pools/markets and converts them to Nautilus instrument objects.

Phase 2 of the 7-phase DEX adapter implementation sequence.

Replace 'MyDEX' with your actual DEX name and fill in the RPC client calls.
"""

from decimal import Decimal

from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock
from nautilus_trader.config import InstrumentProviderConfig
from nautilus_trader.model.identifiers import InstrumentId, Symbol, Venue
from nautilus_trader.model.instruments import CurrencyPair, CryptoPermanentContract
from nautilus_trader.model.currencies import Currency
from nautilus_trader.model.objects import Price, Quantity

from .dex_config import MyDEXInstrumentProviderConfig


class MyDEXInstrumentProvider:
    """
    Instrument provider for MyDEX.

    Fetches on-chain pool/market definitions and converts them into
    NautilusTrader instrument objects.

    The provider must be called before any data or execution clients
    attempt to look up instruments.

    Parameters
    ----------
    config : MyDEXInstrumentProviderConfig
        The provider configuration.
    """

    VENUE = Venue("MYDEX")

    def __init__(self, config: MyDEXInstrumentProviderConfig) -> None:
        self._config = config
        self._instruments: dict[InstrumentId, CurrencyPair] = {}
        # self._http_client = MyDEXHttpClient(rpc_url=config.rpc_url)

    # ─── PUBLIC API (required by NautilusTrader adapter framework) ─────────────

    async def load_all_async(self) -> None:
        """
        Load all available pools from the DEX.

        Fetches pool addresses from on-chain registry or known deployment list,
        then loads pool metadata (token addresses, fee tiers, tick spacing).
        """
        if self._config.sandbox_mode:
            self._load_sandbox_instruments()
            return

        # Fetch pool list from on-chain registry or static config
        pool_addresses = self._config.pools or await self._fetch_all_pool_addresses()

        for address in pool_addresses:
            try:
                pool_metadata = await self._fetch_pool_metadata(address)
                instrument = self._parse_pool_to_instrument(pool_metadata)
                self._instruments[instrument.id] = instrument
            except Exception as e:
                # Log and continue — don't fail all pools for one bad address
                print(f"Warning: failed to load pool {address}: {e}")

    async def load_ids_async(self, instrument_ids: list[InstrumentId]) -> None:
        """
        Load specific instruments by ID.

        Used by the framework during targeted reconnects or when only
        specific instruments are subscribed.

        Parameters
        ----------
        instrument_ids : list[InstrumentId]
            The instrument IDs to load.
        """
        for iid in instrument_ids:
            if iid in self._instruments:
                continue  # Already loaded

            # Reverse-map symbol to pool address
            pool_address = self._symbol_to_address(iid.symbol.value)
            if pool_address is None:
                continue

            pool_metadata = await self._fetch_pool_metadata(pool_address)
            instrument = self._parse_pool_to_instrument(pool_metadata)
            self._instruments[instrument.id] = instrument

    def get_all(self) -> dict[InstrumentId, CurrencyPair]:
        """Return all loaded instruments."""
        return self._instruments.copy()

    def find(self, instrument_id: InstrumentId) -> CurrencyPair | None:
        """Find an instrument by ID."""
        return self._instruments.get(instrument_id)

    # ─── PARSING HELPERS ───────────────────────────────────────────────────────

    def _parse_pool_to_instrument(self, pool_metadata: dict) -> CurrencyPair:
        """
        Convert on-chain pool metadata to a NautilusTrader CurrencyPair.

        Parameters
        ----------
        pool_metadata : dict
            Raw pool data from chain (token0, token1, fee, address, etc.)

        Returns
        -------
        CurrencyPair
            A fully-specified instrument ready for use in the framework.
        """
        token0_symbol = pool_metadata["token0_symbol"]
        token1_symbol = pool_metadata["token1_symbol"]
        fee_tier = pool_metadata["fee"]  # e.g. 3000 for 0.3%

        # Build symbol: e.g. WETH-USDC
        pool_symbol = f"{token0_symbol}-{token1_symbol}"

        # Map fee tier to decimal rate
        fee_rate = Decimal(str(fee_tier)) / Decimal("1000000")

        instrument_id = InstrumentId(Symbol(pool_symbol), self.VENUE)

        return CurrencyPair(
            instrument_id=instrument_id,
            raw_symbol=Symbol(pool_symbol),
            base_currency=None,               # AMM: no separate base currency object for now
            quote_currency=Currency.from_str(token1_symbol),
            price_precision=6,
            size_precision=8,
            price_increment=Price.from_str("0.000001"),
            size_increment=Quantity.from_str("0.00000001"),
            lot_size=None,
            max_quantity=None,
            min_quantity=Quantity.from_str(str(pool_metadata.get("min_trade_size", "0.001"))),
            max_notional=None,
            min_notional=None,
            max_price=None,
            min_price=None,
            margin_init=Decimal("0"),
            margin_maint=Decimal("0"),
            maker_fee=fee_rate,
            taker_fee=fee_rate,
            ts_event=0,
            ts_init=0,
        )

    # ─── RPC CALLS (implement with your actual client) ─────────────────────────

    async def _fetch_all_pool_addresses(self) -> list[str]:
        """
        Fetch all pool addresses from on-chain registry.

        Implement using your RPC client:
        - Uniswap V3: query Factory contract event logs
        - Curve: query Address Provider contract
        - Hyperliquid: fetch from REST API
        """
        raise NotImplementedError("Implement _fetch_all_pool_addresses()")

    async def _fetch_pool_metadata(self, address: str) -> dict:
        """
        Fetch pool metadata from chain.

        Should return a dict with at minimum:
          token0_symbol, token1_symbol, fee (int), min_trade_size (str)

        Implement using your RPC client (eth_call to pool contract).
        """
        raise NotImplementedError("Implement _fetch_pool_metadata()")

    def _symbol_to_address(self, symbol: str) -> str | None:
        """Reverse-map pool symbol (e.g. 'WETH-USDC') to on-chain address."""
        raise NotImplementedError("Implement _symbol_to_address()")

    # ─── SANDBOX HELPERS ───────────────────────────────────────────────────────

    def _load_sandbox_instruments(self) -> None:
        """Load synthetic instruments for testing (no chain connection required)."""
        test_instrument = self._parse_pool_to_instrument({
            "token0_symbol": "WETH",
            "token1_symbol": "USDC",
            "fee": 3000,         # 0.3%
            "min_trade_size": "0.001",
        })
        self._instruments[test_instrument.id] = test_instrument
