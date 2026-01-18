"""
Indicator Template for nautilus_trader.

Indicators perform stateless computations on market data.
They are automatically updated when registered with bars/ticks.
"""

from nautilus_trader.indicators.base.indicator import Indicator
from nautilus_trader.model import Bar
from nautilus_trader.model import QuoteTick
from nautilus_trader.model import TradeTick


class MyIndicator(Indicator):
    """
    Example custom indicator.

    Computes a simple moving average of bar closes.

    Parameters
    ----------
    period : int
        The lookback period.
    """

    def __init__(self, period: int) -> None:
        """
        Initialize the indicator.

        Parameters
        ----------
        period : int
            The lookback period for the calculation.
        """
        super().__init__([period])

        self.period = period
        self._prices: list[float] = []
        self._value: float = 0.0

    @property
    def name(self) -> str:
        """Return the indicator name."""
        return f"MyIndicator({self.period})"

    @property
    def has_inputs(self) -> bool:
        """Return whether the indicator has received inputs."""
        return len(self._prices) > 0

    @property
    def initialized(self) -> bool:
        """Return whether the indicator is initialized (has enough data)."""
        return len(self._prices) >= self.period

    @property
    def value(self) -> float:
        """Return the current indicator value."""
        return self._value

    def handle_bar(self, bar: Bar) -> None:
        """
        Handle bar update.

        Parameters
        ----------
        bar : Bar
            The bar to process.
        """
        self._update(float(bar.close))

    def handle_quote_tick(self, tick: QuoteTick) -> None:
        """
        Handle quote tick update.

        Parameters
        ----------
        tick : QuoteTick
            The tick to process.
        """
        mid_price = (float(tick.bid_price) + float(tick.ask_price)) / 2
        self._update(mid_price)

    def handle_trade_tick(self, tick: TradeTick) -> None:
        """
        Handle trade tick update.

        Parameters
        ----------
        tick : TradeTick
            The tick to process.
        """
        self._update(float(tick.price))

    def _update(self, price: float) -> None:
        """
        Update indicator with new price.

        Parameters
        ----------
        price : float
            The new price value.
        """
        self._prices.append(price)

        # Keep only necessary history
        if len(self._prices) > self.period:
            self._prices.pop(0)

        # Calculate value
        if len(self._prices) >= self.period:
            self._value = sum(self._prices) / self.period

    def reset(self) -> None:
        """Reset the indicator to initial state."""
        self._prices.clear()
        self._value = 0.0


# =============================================================================
# Usage in Strategy
# =============================================================================
#
# class MyStrategy(Strategy):
#     def __init__(self, config: MyStrategyConfig) -> None:
#         super().__init__(config)
#         self.indicator = MyIndicator(period=20)
#
#     def on_start(self) -> None:
#         self.register_indicator_for_bars(self.config.bar_type, self.indicator)
#         self.request_bars(self.config.bar_type)
#         self.subscribe_bars(self.config.bar_type)
#
#     def on_bar(self, bar: Bar) -> None:
#         if not self.indicator.initialized:
#             return
#         signal = self.indicator.value
#         # Use signal for trading logic
