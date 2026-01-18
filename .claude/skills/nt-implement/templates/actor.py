"""
Actor Template for nautilus_trader.

An Actor handles data processing, model inference, and signal generation.
Actors cannot submit orders - use Strategy for trading logic.
"""

from collections import deque

import msgspec

from nautilus_trader.common.actor import Actor
from nautilus_trader.config import ActorConfig
from nautilus_trader.core.data import Data
from nautilus_trader.model import Bar, BarType
from nautilus_trader.model import InstrumentId


class ModelState(msgspec.Struct):
    """
    Serializable model state using msgspec.

    Use msgspec for model serialization (preferred over pickle).
    """

    weights: list[float]
    threshold: float
    version: str


class MyActorConfig(ActorConfig):
    """
    Configuration for MyActor.

    Parameters
    ----------
    instrument_id : InstrumentId
        The instrument to process.
    bar_type : BarType
        The bar type to subscribe to.
    model_path : str
        Path to the serialized model.
    lookback : int
        Number of bars to keep in buffer.
    """

    instrument_id: InstrumentId
    bar_type: BarType
    model_path: str
    lookback: int = 100


class MyActor(Actor):
    """
    Example actor for model inference and signal publishing.

    Hosts ML models, processes data, and publishes signals to strategies.
    """

    def __init__(self, config: MyActorConfig) -> None:
        """
        Initialize the actor.

        Parameters
        ----------
        config : MyActorConfig
            The actor configuration.
        """
        super().__init__(config)

        # Actor state
        self.model: ModelState | None = None
        self.bar_buffer: deque[Bar] = deque(maxlen=config.lookback)
        self.current_regime: str = "unknown"

    # ==================== LIFECYCLE HANDLERS ====================

    def on_start(self) -> None:
        """
        Handle actor start.

        Load models, request historical data, subscribe to live data.
        """
        # 1. Load model (msgspec preferred)
        self._load_model()

        # 2. Request historical data for warmup
        self.request_bars(self.config.bar_type)

        # 3. Subscribe to live data
        self.subscribe_bars(self.config.bar_type)

    def on_stop(self) -> None:
        """Handle actor stop."""
        self.unsubscribe_bars(self.config.bar_type)

    def on_reset(self) -> None:
        """Reset actor state."""
        self.model = None
        self.bar_buffer.clear()
        self.current_regime = "unknown"

    # ==================== DATA HANDLERS ====================

    def on_bar(self, bar: Bar) -> None:
        """
        Handle new bar data.

        Parameters
        ----------
        bar : Bar
            The bar received.
        """
        self.bar_buffer.append(bar)

        if len(self.bar_buffer) < self.config.lookback:
            return  # Not enough data yet

        # Run inference
        regime = self._infer_regime()

        # Publish signal if regime changed
        if regime != self.current_regime:
            self.current_regime = regime
            self.publish_signal(
                name="regime",
                value=regime,
                ts_event=bar.ts_event,
            )

    def on_historical_data(self, data: Data) -> None:
        """
        Handle historical data.

        Parameters
        ----------
        data : Data
            The historical data.
        """
        if isinstance(data, Bar):
            self.bar_buffer.append(data)

    def on_data(self, data: Data) -> None:
        """
        Handle custom data from other actors.

        Parameters
        ----------
        data : Data
            The custom data.
        """
        pass

    # ==================== PRIVATE METHODS ====================

    def _load_model(self) -> None:
        """Load model from disk using msgspec."""
        try:
            with open(self.config.model_path, "rb") as f:
                self.model = msgspec.msgpack.decode(f.read(), type=ModelState)
            self.log.info(f"Loaded model version {self.model.version}")
        except FileNotFoundError:
            self.log.error(f"Model file not found: {self.config.model_path}")
        except Exception as e:
            self.log.error(f"Failed to load model: {e}")

    def _infer_regime(self) -> str:
        """
        Run model inference on buffered data.

        Returns
        -------
        str
            The detected regime.
        """
        if self.model is None:
            return "unknown"

        # Example: compute features and run inference
        bars = list(self.bar_buffer)
        closes = [float(b.close) for b in bars]

        # Simple example: trend detection
        recent_avg = sum(closes[-10:]) / 10
        older_avg = sum(closes[-50:-40]) / 10 if len(closes) >= 50 else recent_avg

        if recent_avg > older_avg * (1 + self.model.threshold):
            return "uptrend"
        elif recent_avg < older_avg * (1 - self.model.threshold):
            return "downtrend"
        else:
            return "ranging"


# =============================================================================
# ONNX Model Actor (Alternative Pattern)
# =============================================================================

# Uncomment and modify if using ONNX models:
#
# import numpy as np
# import onnxruntime as ort
#
# class OnnxActorConfig(ActorConfig):
#     instrument_id: InstrumentId
#     bar_type: BarType
#     onnx_model_path: str
#     feature_count: int = 10
#
# class OnnxActor(Actor):
#     def __init__(self, config: OnnxActorConfig) -> None:
#         super().__init__(config)
#         self.session: ort.InferenceSession | None = None
#         self.input_name: str = ""
#
#     def on_start(self) -> None:
#         self.session = ort.InferenceSession(self.config.onnx_model_path)
#         self.input_name = self.session.get_inputs()[0].name
#         self.subscribe_bars(self.config.bar_type)
#
#     def on_bar(self, bar: Bar) -> None:
#         features = self._compute_features(bar)
#         inputs = {self.input_name: features.astype(np.float32).reshape(1, -1)}
#         outputs = self.session.run(None, inputs)
#         prediction = float(outputs[0][0])
#         self.publish_signal(name="prediction", value=prediction, ts_event=bar.ts_event)
#
#     def _compute_features(self, bar: Bar) -> np.ndarray:
#         # Implement feature computation
#         return np.zeros(self.config.feature_count)
