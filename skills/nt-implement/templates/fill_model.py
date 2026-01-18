# -------------------------------------------------------------------------------------------------
#  Copyright (C) 2015-2025 Nautech Systems Pty Ltd. All rights reserved.
#  https://nautechsystems.io
#
#  Licensed under the GNU Lesser General Public License Version 3.0 (the "License");
#  You may not use this file except in compliance with the License.
#  You may obtain a copy of the License at https://www.gnu.org/licenses/lgpl-3.0.en.html
# -------------------------------------------------------------------------------------------------
"""
Custom FillModel template for backtesting.

The FillModel simulates order queue position and execution probability during backtesting.
It addresses the fundamental challenge that even with perfect historical market data,
we cannot fully simulate how orders would have interacted with other market participants.

Key parameters:
- prob_fill_on_limit: Probability a limit order fills when price matches (0.0-1.0)
- prob_slippage: Probability of 1-tick slippage on market orders (0.0-1.0)
- random_seed: Optional seed for reproducible results

Usage:
    fill_model = CustomFillModel(
        prob_fill_on_limit=0.5,
        prob_slippage=0.3,
        random_seed=42,
    )

    engine = BacktestEngine(
        config=BacktestEngineConfig(
            trader_id="TESTER-001",
            fill_model=fill_model,
        )
    )
"""

from nautilus_trader.backtest.models import FillModel


class CustomFillModel(FillModel):
    """
    Custom fill model for backtesting simulation.

    This template provides a starting point for implementing custom fill logic.
    Override methods to implement venue-specific or strategy-specific fill behavior.

    Parameters
    ----------
    prob_fill_on_limit : float, default 1.0
        Probability that a limit order fills when price matches the limit.
        - 0.0: Never fills (back of queue)
        - 0.5: 50% chance (middle of queue)
        - 1.0: Always fills (front of queue)
    prob_slippage : float, default 0.0
        Probability of experiencing 1-tick slippage on market orders.
        Only applies to L1 data types (quotes, trades, bars).
    random_seed : int, optional
        Seed for random number generator for reproducible results.
    """

    def __init__(
        self,
        prob_fill_on_limit: float = 1.0,
        prob_slippage: float = 0.0,
        random_seed: int | None = None,
    ) -> None:
        super().__init__(
            prob_fill_on_limit=prob_fill_on_limit,
            prob_fill_on_stop=1.0,  # Deprecated: use prob_slippage
            prob_slippage=prob_slippage,
            random_seed=random_seed,
        )
        # Add custom state here
        self._custom_state: dict = {}

    def is_limit_filled(self) -> bool:
        """
        Check if a limit order should be filled.

        Called when the market price touches (but doesn't cross) the limit price.
        Override this method to implement custom fill logic based on:
        - Current market volatility
        - Order size relative to typical volume
        - Time in queue
        - Instrument-specific characteristics

        Returns
        -------
        bool
            True if the order should fill, False otherwise.
        """
        # Default: use probability-based fill
        return self._random.random() < self.prob_fill_on_limit

    def is_slipped(self) -> bool:
        """
        Check if a market order should experience slippage.

        Called for market-type orders (MARKET, MARKET_TO_LIMIT, STOP_MARKET).
        Only applies to L1 data; L2/L3 order book data handles slippage naturally.

        Returns
        -------
        bool
            True if the order should slip 1 tick, False otherwise.
        """
        # Default: use probability-based slippage
        return self._random.random() < self.prob_slippage

    # Custom methods for extending functionality

    def set_market_conditions(self, volatility: float, liquidity: float) -> None:
        """
        Update market conditions for adaptive fill simulation.

        Parameters
        ----------
        volatility : float
            Current market volatility measure (e.g., ATR ratio).
        liquidity : float
            Current liquidity measure (e.g., typical volume ratio).
        """
        self._custom_state["volatility"] = volatility
        self._custom_state["liquidity"] = liquidity

    def reset_state(self) -> None:
        """Reset custom state between simulation runs."""
        self._custom_state.clear()


# Example: Volatility-adjusted fill model
class VolatilityAdjustedFillModel(FillModel):
    """
    Fill model that adjusts probabilities based on market volatility.

    Higher volatility increases fill probability (more price movement crosses levels)
    but also increases slippage probability (faster markets, wider spreads).
    """

    def __init__(
        self,
        base_prob_fill_on_limit: float = 0.5,
        base_prob_slippage: float = 0.3,
        volatility_fill_multiplier: float = 1.0,
        volatility_slip_multiplier: float = 1.5,
        random_seed: int | None = None,
    ) -> None:
        super().__init__(
            prob_fill_on_limit=base_prob_fill_on_limit,
            prob_fill_on_stop=1.0,
            prob_slippage=base_prob_slippage,
            random_seed=random_seed,
        )
        self._base_fill_prob = base_prob_fill_on_limit
        self._base_slip_prob = base_prob_slippage
        self._vol_fill_mult = volatility_fill_multiplier
        self._vol_slip_mult = volatility_slip_multiplier
        self._current_volatility = 1.0

    def set_volatility(self, volatility_ratio: float) -> None:
        """
        Set current volatility as ratio to historical average.

        Parameters
        ----------
        volatility_ratio : float
            Ratio of current volatility to average (1.0 = average).
        """
        self._current_volatility = max(0.1, volatility_ratio)

    def is_limit_filled(self) -> bool:
        """Higher volatility = more likely to fill (price moves through levels)."""
        adjusted = min(1.0, self._base_fill_prob * self._current_volatility * self._vol_fill_mult)
        return self._random.random() < adjusted

    def is_slipped(self) -> bool:
        """Higher volatility = more likely to slip (faster markets)."""
        adjusted = min(1.0, self._base_slip_prob * self._current_volatility * self._vol_slip_mult)
        return self._random.random() < adjusted


# Example: Time-based fill model
class TimeBasedFillModel(FillModel):
    """
    Fill model that considers time-in-queue for limit orders.

    Simulates the realistic scenario where limit orders sitting longer
    at a price level are more likely to get filled.
    """

    def __init__(
        self,
        base_prob_fill_on_limit: float = 0.3,
        prob_increase_per_touch: float = 0.1,
        max_prob_fill: float = 0.9,
        random_seed: int | None = None,
    ) -> None:
        super().__init__(
            prob_fill_on_limit=base_prob_fill_on_limit,
            prob_fill_on_stop=1.0,
            prob_slippage=0.0,
            random_seed=random_seed,
        )
        self._base_prob = base_prob_fill_on_limit
        self._prob_increase = prob_increase_per_touch
        self._max_prob = max_prob_fill
        self._touch_count = 0

    def is_limit_filled(self) -> bool:
        """Probability increases each time price touches the limit."""
        current_prob = min(
            self._max_prob,
            self._base_prob + (self._touch_count * self._prob_increase),
        )
        self._touch_count += 1
        return self._random.random() < current_prob

    def reset_touch_count(self) -> None:
        """Reset touch count (call when order is modified or new order placed)."""
        self._touch_count = 0
