from nautilus_trader.adapters.kraken.config import KrakenDataClientConfig
from nautilus_trader.adapters.kraken.config import KrakenExecClientConfig
from nautilus_trader.adapters.kraken.config import KrakenInstrumentProviderConfig
from nautilus_trader.config import TradingNodeConfig

def get_kraken_config(
    api_key: str,
    api_secret: str,
    instrument_ids: list[str] = None
) -> TradingNodeConfig:
    """
    Create a TradingNodeConfig for Kraken (v1.222.0+).
    """
    
    # 1. Instrument Provider
    # Configures how instruments are loaded from Kraken
    instrument_provider = KrakenInstrumentProviderConfig(
        load_ids=frozenset(instrument_ids) if instrument_ids else None,
        load_all=False if instrument_ids else True,
    )
    
    # 2. Data Client
    # Handles WebSocket market data connection
    data_client = KrakenDataClientConfig(
        api_key=api_key,
        api_secret=api_secret,
        # subscription_type="book" or "ticker" etc. handled per subscription
    )
    
    # 3. Execution Client
    # Handles order execution and account management
    exec_client = KrakenExecClientConfig(
        api_key=api_key,
        api_secret=api_secret,
    )
    
    return TradingNodeConfig(
        trader_id="KRAKEN-NODE-001",
        data_clients={"KRAKEN": data_client},
        exec_clients={"KRAKEN": exec_client},
        instrument_providers={"KRAKEN": instrument_provider},
    )
