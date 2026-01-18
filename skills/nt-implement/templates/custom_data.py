"""
Custom Data Types Template for nautilus_trader.

Custom data types enable structured communication between components
via the message bus. Use @customdataclass for serialization support.
"""

from nautilus_trader.core.data import Data
from nautilus_trader.model.custom import customdataclass


# =============================================================================
# Basic Custom Data
# =============================================================================

@customdataclass
class RegimeData(Data):
    """
    Market regime data.

    Attributes
    ----------
    regime : str
        The current regime (e.g., "uptrend", "downtrend", "ranging").
    confidence : float
        Confidence score for the regime detection (0-1).
    transition_prob : float
        Probability of regime transition.
    """

    regime: str
    confidence: float
    transition_prob: float


@customdataclass
class FeatureData(Data):
    """
    Computed features for ML models.

    Attributes
    ----------
    ema_diff : float
        Difference between fast and slow EMA.
    rsi : float
        RSI indicator value.
    volatility : float
        Current volatility measure.
    """

    ema_diff: float
    rsi: float
    volatility: float


@customdataclass
class SignalData(Data):
    """
    Trading signal data.

    Attributes
    ----------
    direction : int
        Signal direction: 1 (long), -1 (short), 0 (neutral).
    strength : float
        Signal strength (0-1).
    model_id : str
        Identifier of the model that generated this signal.
    """

    direction: int
    strength: float
    model_id: str


# =============================================================================
# Publishing Custom Data (in Actor)
# =============================================================================
#
# class MyActor(Actor):
#     def on_bar(self, bar: Bar) -> None:
#         regime = RegimeData(
#             regime="uptrend",
#             confidence=0.85,
#             transition_prob=0.1,
#             ts_event=bar.ts_event,
#             ts_init=self.clock.timestamp_ns(),
#         )
#         self.publish_data(RegimeData, regime)


# =============================================================================
# Subscribing to Custom Data (in Strategy)
# =============================================================================
#
# class MyStrategy(Strategy):
#     def on_start(self) -> None:
#         self.subscribe_data(RegimeData)
#
#     def on_data(self, data: Data) -> None:
#         if isinstance(data, RegimeData):
#             self.log.info(f"Regime: {data.regime} (confidence: {data.confidence})")


# =============================================================================
# Notes on @customdataclass
# =============================================================================
#
# The @customdataclass decorator:
# - Adds ts_event and ts_init attributes if not present
# - Provides serialization: to_dict(), from_dict(), to_bytes(), to_arrow()
# - Enables data persistence and external communication
# - Ensures proper ordering in backtests based on timestamps
#
# Without @customdataclass, you inherit from Data directly but lose:
# - Automatic timestamp handling
# - Serialization methods
# - Data catalog integration
