"""
DEX Adapter Template: Client Factory

Registers the DEX adapter's data and execution clients with a TradingNode.

Phase 6 of the 7-phase DEX adapter implementation sequence.

Usage in TradingNode:
    node = TradingNode(config=config)
    node.add_data_client_factory("MYDEX", MyDEXLiveDataClientFactory)
    node.add_exec_client_factory("MYDEX", MyDEXLiveExecClientFactory)

Replace 'MyDEX' with your actual DEX name throughout.
"""

import sys
from pathlib import Path

_TEMPLATE_DIR = Path(__file__).resolve().parent
if str(_TEMPLATE_DIR) not in sys.path:
    sys.path.append(str(_TEMPLATE_DIR))

from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock, MessageBus
from nautilus_trader.live.factories import LiveDataClientFactory, LiveExecClientFactory
from nautilus_trader.model.identifiers import AccountId, ClientId, Venue

try:
    from .dex_config import MyDEXDataClientConfig, MyDEXExecClientConfig
    from .dex_data_client import MyDEXDataClient
    from .dex_exec_client import MyDEXExecutionClient
    from .dex_instrument_provider import (
        MyDEXInstrumentProvider,
        MyDEXInstrumentProviderConfig,
    )
except ImportError:
    from dex_config import MyDEXDataClientConfig, MyDEXExecClientConfig
    from dex_data_client import MyDEXDataClient
    from dex_exec_client import MyDEXExecutionClient
    from dex_instrument_provider import (
        MyDEXInstrumentProvider,
        MyDEXInstrumentProviderConfig,
    )


VENUE_NAME = "MYDEX"  # ← Change to your actual venue name (e.g. "UNISWAP_V3")


# =============================================================================
# Data Client Factory
# =============================================================================


class MyDEXLiveDataClientFactory(LiveDataClientFactory):
    """
    Factory for creating MyDEX live data clients.

    Registered with TradingNode via:
        node.add_data_client_factory("MYDEX", MyDEXLiveDataClientFactory)
    """

    @staticmethod
    def create(
        loop,
        name: str,
        config: MyDEXDataClientConfig,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
    ) -> MyDEXDataClient:
        """
        Create and return a MyDEX data client.

        Parameters
        ----------
        loop : asyncio.AbstractEventLoop
            The event loop (passed by TradingNode).
        name : str
            The client name (matches the key in data_clients config dict).
        config : MyDEXDataClientConfig
            The data client configuration.
        msgbus : MessageBus
            The Nautilus message bus.
        cache : Cache
            The Nautilus cache.
        clock : LiveClock
            The Nautilus clock.
        """
        # Share instrument provider between data and exec clients
        # Use a simple module-level cache to avoid double-loading
        provider = _get_or_create_instrument_provider(config)

        return MyDEXDataClient(
            client_id=ClientId(name),
            venue=Venue(name),
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            instrument_provider=provider,
            config=config,
        )


# =============================================================================
# Execution Client Factory
# =============================================================================


class MyDEXLiveExecClientFactory(LiveExecClientFactory):
    """
    Factory for creating MyDEX live execution clients.

    Registered with TradingNode via:
        node.add_exec_client_factory("MYDEX", MyDEXLiveExecClientFactory)
    """

    @staticmethod
    def create(
        loop,
        name: str,
        config: MyDEXExecClientConfig,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
        account_id: AccountId,
    ) -> MyDEXExecutionClient:
        """
        Create and return a MyDEX execution client.

        Parameters
        ----------
        loop : asyncio.AbstractEventLoop
            The event loop.
        name : str
            The client name (matches the key in exec_clients config dict).
        config : MyDEXExecClientConfig
            The exec client configuration (includes private key as SecretStr).
        msgbus : MessageBus
            The Nautilus message bus.
        cache : Cache
            The Nautilus cache.
        clock : LiveClock
            The Nautilus clock.
        account_id : AccountId
            The account identifier derived from wallet address.
        """
        provider = _get_or_create_instrument_provider(config)

        return MyDEXExecutionClient(
            client_id=ClientId(name),
            venue=Venue(name),
            account_id=account_id,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            instrument_provider=provider,
            config=config,
        )


# =============================================================================
# Shared Instrument Provider Cache
# =============================================================================

_instrument_providers: dict[str, MyDEXInstrumentProvider] = {}


def _get_or_create_instrument_provider(config) -> MyDEXInstrumentProvider:
    """
    Get or create a shared instrument provider for the given RPC URL.

    Data and execution clients share one provider to avoid double-loading
    pool metadata from the chain.
    """
    key = getattr(config, "rpc_url", "default")

    if key not in _instrument_providers:
        sandbox_mode = getattr(config, "sandbox_mode", False)
        pools = getattr(config, "pool_addresses", None) or getattr(config, "pools", [])

        provider_config = MyDEXInstrumentProviderConfig(
            rpc_url=key,
            pools=pools,
            sandbox_mode=sandbox_mode,
        )
        _instrument_providers[key] = MyDEXInstrumentProvider(config=provider_config)

    return _instrument_providers[key]
