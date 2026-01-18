"""
Internal Adapter Template for nautilus_trader.

An internal adapter connects to your own infrastructure:
- Internal signal services
- Custom databases
- Proprietary data feeds
- Internal APIs

This is simpler than exchange adapters since you control the API.
"""

import asyncio
from collections.abc import Callable

from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.actor import Actor
from nautilus_trader.common.component import LiveClock
from nautilus_trader.common.component import MessageBus
from nautilus_trader.config import ActorConfig
from nautilus_trader.core.data import Data
from nautilus_trader.model.custom import customdataclass


# =============================================================================
# Custom Data Types for Internal Communication
# =============================================================================

@customdataclass
class InternalSignal(Data):
    """
    Signal from internal signal service.

    Attributes
    ----------
    signal_id : str
        Unique signal identifier.
    instrument : str
        Instrument symbol.
    direction : int
        1 for long, -1 for short, 0 for flat.
    strength : float
        Signal strength (0-1).
    source : str
        Source model/system name.
    """

    signal_id: str
    instrument: str
    direction: int
    strength: float
    source: str


@customdataclass
class InternalFeatures(Data):
    """
    Precomputed features from internal feature store.

    Attributes
    ----------
    instrument : str
        Instrument symbol.
    features : dict
        Feature name to value mapping.
    """

    instrument: str
    features: dict


# =============================================================================
# Internal Signal Service Adapter (Actor-based)
# =============================================================================

class InternalSignalAdapterConfig(ActorConfig):
    """
    Configuration for the internal signal adapter.

    Parameters
    ----------
    service_url : str
        URL of the internal signal service.
    api_token : str
        Authentication token.
    poll_interval_ms : int
        Polling interval in milliseconds.
    instruments : list[str]
        Instruments to subscribe to.
    """

    service_url: str
    api_token: str
    poll_interval_ms: int = 1000
    instruments: list[str] = []


class InternalSignalAdapter(Actor):
    """
    Adapter for receiving signals from internal signal service.

    Polls or streams from internal service and publishes signals
    as custom data for strategies to consume.
    """

    def __init__(self, config: InternalSignalAdapterConfig) -> None:
        """
        Initialize the adapter.

        Parameters
        ----------
        config : InternalSignalAdapterConfig
            The adapter configuration.
        """
        super().__init__(config)

        self._connected: bool = False
        self._ws_task: asyncio.Task | None = None

    def on_start(self) -> None:
        """Start the adapter and connect to internal service."""
        self.log.info(f"Connecting to signal service: {self.config.service_url}")

        # Option 1: Polling
        self._start_polling()

        # Option 2: WebSocket streaming (uncomment if preferred)
        # self._start_streaming()

    def on_stop(self) -> None:
        """Stop the adapter and disconnect."""
        self._connected = False
        if self._ws_task:
            self._ws_task.cancel()

    def _start_polling(self) -> None:
        """Start polling for signals."""
        import pandas as pd

        self._connected = True

        # Set up timer for polling
        self.clock.set_timer(
            name="signal_poll",
            interval=pd.Timedelta(milliseconds=self.config.poll_interval_ms),
            callback=self._on_poll_timer,
        )

    def _on_poll_timer(self, event) -> None:
        """Handle poll timer event."""
        if not self._connected:
            return

        # Fetch signals from internal service
        # This would be async in real implementation
        signals = self._fetch_signals()

        for signal in signals:
            self.publish_data(InternalSignal, signal)

    def _fetch_signals(self) -> list[InternalSignal]:
        """
        Fetch signals from internal service.

        Returns
        -------
        list[InternalSignal]
            List of signals received.
        """
        # Implement HTTP request to internal service
        # Example:
        # response = requests.get(
        #     f"{self.config.service_url}/signals",
        #     headers={"Authorization": f"Bearer {self.config.api_token}"},
        #     params={"instruments": ",".join(self.config.instruments)},
        # )
        # return [self._parse_signal(s) for s in response.json()]
        return []

    def _parse_signal(self, raw: dict) -> InternalSignal:
        """Parse raw signal data into InternalSignal."""
        return InternalSignal(
            signal_id=raw["id"],
            instrument=raw["instrument"],
            direction=raw["direction"],
            strength=raw["strength"],
            source=raw["source"],
            ts_event=raw["timestamp_ns"],
            ts_init=self.clock.timestamp_ns(),
        )


# =============================================================================
# Internal Feature Store Adapter
# =============================================================================

class FeatureStoreAdapterConfig(ActorConfig):
    """
    Configuration for the feature store adapter.

    Parameters
    ----------
    database_url : str
        Connection string for the feature database.
    cache_ttl_seconds : int
        Time-to-live for cached features.
    """

    database_url: str
    cache_ttl_seconds: int = 60


class FeatureStoreAdapter(Actor):
    """
    Adapter for fetching features from internal feature store.

    Caches features locally and publishes updates.
    """

    def __init__(self, config: FeatureStoreAdapterConfig) -> None:
        """
        Initialize the adapter.

        Parameters
        ----------
        config : FeatureStoreAdapterConfig
            The adapter configuration.
        """
        super().__init__(config)

        self._feature_cache: dict[str, InternalFeatures] = {}
        self._subscriptions: set[str] = set()

    def on_start(self) -> None:
        """Start the feature store connection."""
        self.log.info("Connecting to feature store...")
        # Initialize database connection

    def on_stop(self) -> None:
        """Stop and cleanup."""
        self._feature_cache.clear()
        self._subscriptions.clear()

    def subscribe_features(self, instrument: str) -> None:
        """
        Subscribe to features for an instrument.

        Parameters
        ----------
        instrument : str
            The instrument to subscribe to.
        """
        if instrument not in self._subscriptions:
            self._subscriptions.add(instrument)
            self._refresh_features(instrument)

    def _refresh_features(self, instrument: str) -> None:
        """Refresh features from database."""
        # Query feature store
        # features = db.query(f"SELECT * FROM features WHERE instrument = '{instrument}'")

        features = InternalFeatures(
            instrument=instrument,
            features={"ema_20": 100.5, "rsi_14": 55.3},
            ts_event=self.clock.timestamp_ns(),
            ts_init=self.clock.timestamp_ns(),
        )

        self._feature_cache[instrument] = features
        self.publish_data(InternalFeatures, features)

    def get_cached_features(self, instrument: str) -> InternalFeatures | None:
        """Get cached features for instrument."""
        return self._feature_cache.get(instrument)


# =============================================================================
# Usage in Strategy
# =============================================================================
#
# class MyStrategy(Strategy):
#     def on_start(self) -> None:
#         # Subscribe to internal signals
#         self.subscribe_data(InternalSignal)
#         self.subscribe_data(InternalFeatures)
#
#     def on_data(self, data: Data) -> None:
#         if isinstance(data, InternalSignal):
#             if data.direction > 0 and data.strength > 0.7:
#                 self._buy()
#         elif isinstance(data, InternalFeatures):
#             self._update_features(data)
