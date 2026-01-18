# -------------------------------------------------------------------------------------------------
#  Copyright (C) 2015-2025 Nautech Systems Pty Ltd. All rights reserved.
#  https://nautechsystems.io
#
#  Licensed under the GNU Lesser General Public License Version 3.0 (the "License");
#  You may not use this file except in compliance with the License.
#  You may obtain a copy of the License at https://www.gnu.org/licenses/lgpl-3.0.en.html
# -------------------------------------------------------------------------------------------------
"""
Custom PortfolioStatistic templates for performance analysis.

PortfolioStatistic classes calculate metrics from orders and/or positions
after a backtest or live trading session. Register custom statistics with
the PortfolioAnalyzer to extend the built-in metrics.

Usage:
    from nautilus_trader.analysis.analyzer import PortfolioAnalyzer

    analyzer = PortfolioAnalyzer()
    analyzer.register_statistic(WinStreakStatistic())
    analyzer.register_statistic(RiskAdjustedReturnStatistic(risk_free_rate=0.02))

    # After backtest
    results = engine.run()
    stats = analyzer.calculate_statistics(positions=results.positions)
"""

from typing import Any

import numpy as np

from nautilus_trader.analysis.statistic import PortfolioStatistic
from nautilus_trader.model.orders import Order
from nautilus_trader.model.position import Position


class CustomPortfolioStatistic(PortfolioStatistic):
    """
    Template for custom portfolio statistic.

    Override calculate_from_orders and/or calculate_from_positions
    depending on what data your metric requires.
    """

    def __init__(self) -> None:
        super().__init__()
        self._name = "Custom Statistic"

    @property
    def name(self) -> str:
        """Return the statistic name for display."""
        return self._name

    def calculate_from_orders(self, orders: list[Order]) -> Any:
        """
        Calculate statistic from order history.

        Parameters
        ----------
        orders : list[Order]
            List of orders from the trading session.

        Returns
        -------
        Any
            The calculated statistic value.
        """
        # Implement order-based calculation
        return None

    def calculate_from_positions(self, positions: list[Position]) -> Any:
        """
        Calculate statistic from position history.

        Parameters
        ----------
        positions : list[Position]
            List of positions from the trading session.

        Returns
        -------
        Any
            The calculated statistic value.
        """
        # Implement position-based calculation
        return None


class WinStreakStatistic(PortfolioStatistic):
    """
    Calculate maximum consecutive winning and losing streaks.

    Useful for understanding strategy consistency and drawdown patterns.
    """

    def __init__(self) -> None:
        super().__init__()
        self._name = "Win/Loss Streaks"

    @property
    def name(self) -> str:
        return self._name

    def calculate_from_positions(self, positions: list[Position]) -> dict[str, int]:
        """
        Calculate streaks from closed positions.

        Returns
        -------
        dict[str, int]
            Dictionary with max_win_streak, max_loss_streak, current_streak.
        """
        if not positions:
            return {"max_win_streak": 0, "max_loss_streak": 0, "current_streak": 0}

        max_win_streak = 0
        max_loss_streak = 0
        current_win_streak = 0
        current_loss_streak = 0

        for position in positions:
            if not position.is_closed:
                continue

            realized_pnl = position.realized_pnl
            if realized_pnl is None:
                continue

            if float(realized_pnl) > 0:
                current_win_streak += 1
                current_loss_streak = 0
                max_win_streak = max(max_win_streak, current_win_streak)
            elif float(realized_pnl) < 0:
                current_loss_streak += 1
                current_win_streak = 0
                max_loss_streak = max(max_loss_streak, current_loss_streak)
            # Zero PnL resets both streaks
            else:
                current_win_streak = 0
                current_loss_streak = 0

        # Current streak (positive = winning, negative = losing)
        current = current_win_streak if current_win_streak > 0 else -current_loss_streak

        return {
            "max_win_streak": max_win_streak,
            "max_loss_streak": max_loss_streak,
            "current_streak": current,
        }


class RiskAdjustedReturnStatistic(PortfolioStatistic):
    """
    Calculate risk-adjusted return metrics including Sharpe-like ratio.

    Parameters
    ----------
    risk_free_rate : float, default 0.0
        Annualized risk-free rate for Sharpe calculation.
    """

    def __init__(self, risk_free_rate: float = 0.0) -> None:
        super().__init__()
        self._name = "Risk Adjusted Returns"
        self._risk_free_rate = risk_free_rate

    @property
    def name(self) -> str:
        return self._name

    def calculate_from_positions(self, positions: list[Position]) -> dict[str, float]:
        """
        Calculate risk metrics from closed positions.

        Returns
        -------
        dict[str, float]
            Dictionary with avg_return, std_return, sharpe_ratio, sortino_ratio.
        """
        returns = []
        for position in positions:
            if position.is_closed and position.realized_pnl is not None:
                returns.append(float(position.realized_pnl))

        if len(returns) < 2:
            return {
                "avg_return": 0.0,
                "std_return": 0.0,
                "sharpe_ratio": 0.0,
                "sortino_ratio": 0.0,
            }

        returns_array = np.array(returns)
        avg_return = float(np.mean(returns_array))
        std_return = float(np.std(returns_array))

        # Sharpe ratio (using total std)
        if std_return > 0:
            sharpe_ratio = (avg_return - self._risk_free_rate) / std_return
        else:
            sharpe_ratio = 0.0

        # Sortino ratio (using downside std only)
        negative_returns = returns_array[returns_array < 0]
        if len(negative_returns) > 0:
            downside_std = float(np.std(negative_returns))
            if downside_std > 0:
                sortino_ratio = (avg_return - self._risk_free_rate) / downside_std
            else:
                sortino_ratio = 0.0
        else:
            sortino_ratio = float("inf") if avg_return > 0 else 0.0

        return {
            "avg_return": avg_return,
            "std_return": std_return,
            "sharpe_ratio": float(sharpe_ratio),
            "sortino_ratio": float(sortino_ratio),
        }


class HoldingPeriodStatistic(PortfolioStatistic):
    """
    Analyze position holding periods.

    Useful for understanding strategy behavior and turnover.
    """

    def __init__(self) -> None:
        super().__init__()
        self._name = "Holding Periods"

    @property
    def name(self) -> str:
        return self._name

    def calculate_from_positions(self, positions: list[Position]) -> dict[str, float]:
        """
        Calculate holding period statistics.

        Returns
        -------
        dict[str, float]
            Dictionary with avg_hours, min_hours, max_hours, median_hours.
        """
        holding_periods = []

        for position in positions:
            if not position.is_closed:
                continue

            # Calculate holding period in hours
            if position.ts_closed and position.ts_opened:
                duration_ns = position.ts_closed - position.ts_opened
                duration_hours = duration_ns / (1e9 * 3600)  # ns to hours
                holding_periods.append(duration_hours)

        if not holding_periods:
            return {
                "avg_hours": 0.0,
                "min_hours": 0.0,
                "max_hours": 0.0,
                "median_hours": 0.0,
            }

        periods = np.array(holding_periods)
        return {
            "avg_hours": float(np.mean(periods)),
            "min_hours": float(np.min(periods)),
            "max_hours": float(np.max(periods)),
            "median_hours": float(np.median(periods)),
        }


class DrawdownStatistic(PortfolioStatistic):
    """
    Calculate drawdown metrics from cumulative PnL.

    Measures the peak-to-trough decline in account value.
    """

    def __init__(self) -> None:
        super().__init__()
        self._name = "Drawdown Analysis"

    @property
    def name(self) -> str:
        return self._name

    def calculate_from_positions(self, positions: list[Position]) -> dict[str, float]:
        """
        Calculate drawdown metrics.

        Returns
        -------
        dict[str, float]
            Dictionary with max_drawdown, avg_drawdown, max_drawdown_duration_hours.
        """
        if not positions:
            return {
                "max_drawdown": 0.0,
                "avg_drawdown": 0.0,
                "max_drawdown_duration_hours": 0.0,
            }

        # Build cumulative PnL series
        cumulative_pnl = 0.0
        pnl_series = [0.0]
        timestamps = [0]

        for position in positions:
            if position.is_closed and position.realized_pnl is not None:
                cumulative_pnl += float(position.realized_pnl)
                pnl_series.append(cumulative_pnl)
                if position.ts_closed:
                    timestamps.append(position.ts_closed)

        if len(pnl_series) < 2:
            return {
                "max_drawdown": 0.0,
                "avg_drawdown": 0.0,
                "max_drawdown_duration_hours": 0.0,
            }

        # Calculate drawdowns
        pnl_array = np.array(pnl_series)
        running_max = np.maximum.accumulate(pnl_array)
        drawdowns = running_max - pnl_array

        max_drawdown = float(np.max(drawdowns))
        avg_drawdown = float(np.mean(drawdowns[drawdowns > 0])) if np.any(drawdowns > 0) else 0.0

        # Calculate max drawdown duration
        max_dd_duration_hours = 0.0
        in_drawdown = False
        dd_start_idx = 0

        for i, dd in enumerate(drawdowns):
            if dd > 0 and not in_drawdown:
                in_drawdown = True
                dd_start_idx = i
            elif dd == 0 and in_drawdown:
                in_drawdown = False
                if len(timestamps) > i and len(timestamps) > dd_start_idx:
                    duration_ns = timestamps[i] - timestamps[dd_start_idx]
                    duration_hours = duration_ns / (1e9 * 3600)
                    max_dd_duration_hours = max(max_dd_duration_hours, duration_hours)

        return {
            "max_drawdown": max_drawdown,
            "avg_drawdown": avg_drawdown,
            "max_drawdown_duration_hours": max_dd_duration_hours,
        }


class ProfitFactorStatistic(PortfolioStatistic):
    """
    Calculate profit factor (gross profit / gross loss).

    A profit factor > 1 indicates a profitable strategy.
    """

    def __init__(self) -> None:
        super().__init__()
        self._name = "Profit Factor"

    @property
    def name(self) -> str:
        return self._name

    def calculate_from_positions(self, positions: list[Position]) -> dict[str, float]:
        """
        Calculate profit factor and related metrics.

        Returns
        -------
        dict[str, float]
            Dictionary with profit_factor, gross_profit, gross_loss, win_rate.
        """
        gross_profit = 0.0
        gross_loss = 0.0
        wins = 0
        losses = 0

        for position in positions:
            if not position.is_closed or position.realized_pnl is None:
                continue

            pnl = float(position.realized_pnl)
            if pnl > 0:
                gross_profit += pnl
                wins += 1
            elif pnl < 0:
                gross_loss += abs(pnl)
                losses += 1

        total_trades = wins + losses

        if gross_loss > 0:
            profit_factor = gross_profit / gross_loss
        elif gross_profit > 0:
            profit_factor = float("inf")
        else:
            profit_factor = 0.0

        win_rate = wins / total_trades if total_trades > 0 else 0.0

        return {
            "profit_factor": profit_factor,
            "gross_profit": gross_profit,
            "gross_loss": gross_loss,
            "win_rate": win_rate,
            "total_trades": total_trades,
        }


class ExpectancyStatistic(PortfolioStatistic):
    """
    Calculate trade expectancy (average expected profit per trade).

    Expectancy = (Win% * Avg Win) - (Loss% * Avg Loss)
    """

    def __init__(self) -> None:
        super().__init__()
        self._name = "Trade Expectancy"

    @property
    def name(self) -> str:
        return self._name

    def calculate_from_positions(self, positions: list[Position]) -> dict[str, float]:
        """
        Calculate expectancy metrics.

        Returns
        -------
        dict[str, float]
            Dictionary with expectancy, avg_win, avg_loss, win_rate.
        """
        wins = []
        losses = []

        for position in positions:
            if not position.is_closed or position.realized_pnl is None:
                continue

            pnl = float(position.realized_pnl)
            if pnl > 0:
                wins.append(pnl)
            elif pnl < 0:
                losses.append(abs(pnl))

        total_trades = len(wins) + len(losses)

        if total_trades == 0:
            return {
                "expectancy": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "win_rate": 0.0,
            }

        win_rate = len(wins) / total_trades
        loss_rate = len(losses) / total_trades

        avg_win = np.mean(wins) if wins else 0.0
        avg_loss = np.mean(losses) if losses else 0.0

        expectancy = (win_rate * avg_win) - (loss_rate * avg_loss)

        return {
            "expectancy": float(expectancy),
            "avg_win": float(avg_win),
            "avg_loss": float(avg_loss),
            "win_rate": win_rate,
        }
