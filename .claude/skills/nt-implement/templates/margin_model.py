# -------------------------------------------------------------------------------------------------
#  Copyright (C) 2015-2025 Nautech Systems Pty Ltd. All rights reserved.
#  https://nautechsystems.io
#
#  Licensed under the GNU Lesser General Public License Version 3.0 (the "License");
#  You may not use this file except in compliance with the License.
#  You may obtain a copy of the License at https://www.gnu.org/licenses/lgpl-3.0.en.html
# -------------------------------------------------------------------------------------------------
"""
Custom MarginModel template for backtesting margin accounts.

NautilusTrader provides two built-in models:
- StandardMarginModel: Fixed percentages, ignores leverage (traditional brokers)
- LeveragedMarginModel: Divides margin by leverage (crypto exchanges)

This template shows how to implement custom margin calculation logic.

Usage with BacktestVenueConfig:
    venue_config = BacktestVenueConfig(
        name="SIM",
        oms_type="NETTING",
        account_type="MARGIN",
        starting_balances=["1_000_000 USD"],
        margin_model=MarginModelConfig(
            model_type="my_package.margin_model:RiskAdjustedMarginModel",
            config={
                "risk_multiplier": 1.5,
                "use_leverage": False,
            },
        ),
    )

Usage programmatically:
    from nautilus_trader.backtest.config import MarginModelConfig, MarginModelFactory

    config = MarginModelConfig(
        model_type="my_package.margin_model:RiskAdjustedMarginModel",
        config={"risk_multiplier": 1.5},
    )
    model = MarginModelFactory.create(config)
    account.set_margin_model(model)
"""

from decimal import Decimal

from nautilus_trader.backtest.config import MarginModelConfig
from nautilus_trader.backtest.models import MarginModel
from nautilus_trader.model.enums import PositionSide
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.model.objects import Money
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity


class CustomMarginModel(MarginModel):
    """
    Custom margin model template.

    Receives configuration through MarginModelConfig.config dict.
    Override calculate_margin_init and calculate_margin_maint to implement
    custom margin logic.

    Configuration parameters (via MarginModelConfig.config):
    - Custom parameters defined by your implementation
    """

    def __init__(self, config: MarginModelConfig) -> None:
        """
        Initialize the margin model with configuration.

        Parameters
        ----------
        config : MarginModelConfig
            The margin model configuration containing custom parameters.
        """
        # Extract parameters from config.config dict
        self.custom_param = config.config.get("custom_param", 1.0)

    def calculate_margin_init(
        self,
        instrument: Instrument,
        quantity: Quantity,
        price: Price,
        leverage: Decimal,
        use_quote_for_inverse: bool = False,
    ) -> Money:
        """
        Calculate initial margin required for order submission.

        This is the collateral required to open a new position.

        Parameters
        ----------
        instrument : Instrument
            The instrument for the calculation.
        quantity : Quantity
            The order quantity.
        price : Price
            The order price (limit price or expected fill price).
        leverage : Decimal
            The account leverage setting.
        use_quote_for_inverse : bool, default False
            Use quote currency for inverse instrument calculations.

        Returns
        -------
        Money
            The initial margin requirement.
        """
        notional = instrument.notional_value(quantity, price, use_quote_for_inverse)
        margin = notional.as_decimal() * instrument.margin_init
        return Money(margin, instrument.quote_currency)

    def calculate_margin_maint(
        self,
        instrument: Instrument,
        side: PositionSide,
        quantity: Quantity,
        price: Price,
        leverage: Decimal,
        use_quote_for_inverse: bool = False,
    ) -> Money:
        """
        Calculate maintenance margin for open positions.

        This is the minimum collateral required to maintain an existing position.
        Falling below this triggers margin calls or liquidation.

        Parameters
        ----------
        instrument : Instrument
            The instrument for the calculation.
        side : PositionSide
            The position side (LONG or SHORT).
        quantity : Quantity
            The position quantity.
        price : Price
            The current market price.
        leverage : Decimal
            The account leverage setting.
        use_quote_for_inverse : bool, default False
            Use quote currency for inverse instrument calculations.

        Returns
        -------
        Money
            The maintenance margin requirement.
        """
        notional = instrument.notional_value(quantity, price, use_quote_for_inverse)
        margin = notional.as_decimal() * instrument.margin_maint
        return Money(margin, instrument.quote_currency)


class RiskAdjustedMarginModel(MarginModel):
    """
    Margin model with configurable risk adjustments.

    Applies risk multipliers and volatility buffers to standard margin calculations.
    Useful for conservative risk management or volatile instruments.

    Configuration parameters:
    - risk_multiplier: float - Multiply margin requirements (default 1.0)
    - use_leverage: bool - Divide by leverage (default False)
    - volatility_buffer: float - Additional margin buffer (default 0.0)
    """

    def __init__(self, config: MarginModelConfig) -> None:
        """Initialize with configuration parameters."""
        self.risk_multiplier = Decimal(str(config.config.get("risk_multiplier", 1.0)))
        self.use_leverage = config.config.get("use_leverage", False)
        self.volatility_buffer = Decimal(str(config.config.get("volatility_buffer", 0.0)))

    def calculate_margin_init(
        self,
        instrument: Instrument,
        quantity: Quantity,
        price: Price,
        leverage: Decimal,
        use_quote_for_inverse: bool = False,
    ) -> Money:
        """Calculate initial margin with risk adjustments."""
        notional = instrument.notional_value(quantity, price, use_quote_for_inverse)

        if self.use_leverage and leverage > 0:
            adjusted_notional = notional.as_decimal() / leverage
        else:
            adjusted_notional = notional.as_decimal()

        # Base margin with risk multiplier
        margin = adjusted_notional * instrument.margin_init * self.risk_multiplier

        # Add volatility buffer
        margin += adjusted_notional * self.volatility_buffer

        return Money(margin, instrument.quote_currency)

    def calculate_margin_maint(
        self,
        instrument: Instrument,
        side: PositionSide,
        quantity: Quantity,
        price: Price,
        leverage: Decimal,
        use_quote_for_inverse: bool = False,
    ) -> Money:
        """Calculate maintenance margin with risk adjustments."""
        notional = instrument.notional_value(quantity, price, use_quote_for_inverse)

        if self.use_leverage and leverage > 0:
            adjusted_notional = notional.as_decimal() / leverage
        else:
            adjusted_notional = notional.as_decimal()

        margin = adjusted_notional * instrument.margin_maint * self.risk_multiplier

        return Money(margin, instrument.quote_currency)


class TieredMarginModel(MarginModel):
    """
    Margin model with tiered requirements based on position size.

    Larger positions require proportionally higher margin, simulating
    the tiered margin systems used by many exchanges for risk management.

    Configuration parameters:
    - tiers: list[dict] - List of {threshold, multiplier} dicts
    - base_margin: float - Base margin percentage (default uses instrument)
    """

    def __init__(self, config: MarginModelConfig) -> None:
        """Initialize with tier configuration."""
        self.tiers = config.config.get(
            "tiers",
            [
                {"threshold": 100_000, "multiplier": Decimal("1.0")},
                {"threshold": 500_000, "multiplier": Decimal("1.5")},
                {"threshold": 1_000_000, "multiplier": Decimal("2.0")},
            ],
        )
        # Sort tiers by threshold
        self.tiers = sorted(self.tiers, key=lambda t: t["threshold"])

    def _get_tier_multiplier(self, notional_value: Decimal) -> Decimal:
        """Get margin multiplier based on notional value tier."""
        multiplier = Decimal("1.0")
        for tier in self.tiers:
            if notional_value >= tier["threshold"]:
                multiplier = Decimal(str(tier["multiplier"]))
        return multiplier

    def calculate_margin_init(
        self,
        instrument: Instrument,
        quantity: Quantity,
        price: Price,
        leverage: Decimal,
        use_quote_for_inverse: bool = False,
    ) -> Money:
        """Calculate tiered initial margin."""
        notional = instrument.notional_value(quantity, price, use_quote_for_inverse)
        notional_value = notional.as_decimal()

        tier_multiplier = self._get_tier_multiplier(notional_value)
        margin = notional_value * instrument.margin_init * tier_multiplier

        return Money(margin, instrument.quote_currency)

    def calculate_margin_maint(
        self,
        instrument: Instrument,
        side: PositionSide,
        quantity: Quantity,
        price: Price,
        leverage: Decimal,
        use_quote_for_inverse: bool = False,
    ) -> Money:
        """Calculate tiered maintenance margin."""
        notional = instrument.notional_value(quantity, price, use_quote_for_inverse)
        notional_value = notional.as_decimal()

        tier_multiplier = self._get_tier_multiplier(notional_value)
        margin = notional_value * instrument.margin_maint * tier_multiplier

        return Money(margin, instrument.quote_currency)


class AsymmetricMarginModel(MarginModel):
    """
    Margin model with different requirements for long vs short positions.

    Some markets have asymmetric risk profiles where short positions
    require higher margin due to theoretically unlimited loss potential.

    Configuration parameters:
    - short_multiplier: float - Multiplier for short positions (default 1.5)
    """

    def __init__(self, config: MarginModelConfig) -> None:
        """Initialize with asymmetric configuration."""
        self.short_multiplier = Decimal(str(config.config.get("short_multiplier", 1.5)))

    def calculate_margin_init(
        self,
        instrument: Instrument,
        quantity: Quantity,
        price: Price,
        leverage: Decimal,
        use_quote_for_inverse: bool = False,
    ) -> Money:
        """Calculate initial margin (same for both sides at order time)."""
        notional = instrument.notional_value(quantity, price, use_quote_for_inverse)
        margin = notional.as_decimal() * instrument.margin_init
        return Money(margin, instrument.quote_currency)

    def calculate_margin_maint(
        self,
        instrument: Instrument,
        side: PositionSide,
        quantity: Quantity,
        price: Price,
        leverage: Decimal,
        use_quote_for_inverse: bool = False,
    ) -> Money:
        """Calculate maintenance margin with asymmetric adjustment for shorts."""
        notional = instrument.notional_value(quantity, price, use_quote_for_inverse)
        margin = notional.as_decimal() * instrument.margin_maint

        # Apply higher margin for short positions
        if side == PositionSide.SHORT:
            margin *= self.short_multiplier

        return Money(margin, instrument.quote_currency)
