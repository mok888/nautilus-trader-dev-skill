"""
Strategy Builder Tests: Backtest Patterns

Verifies that backtest configuration patterns from templates
construct, run, and dispose correctly using NautilusTrader's test kit.
"""

import pytest
from decimal import Decimal

from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.models import FillModel
from nautilus_trader.model.currencies import USDT, BTC
from nautilus_trader.model.enums import AccountType, OmsType
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.model.objects import Money
from nautilus_trader.test_kit.providers import TestInstrumentProvider


class TestBacktestVenueConfig:
    """Verify venue configuration patterns build without error."""

    def test_cash_venue_builds(self):
        """A CASH account venue builds and accepts starting balances."""
        engine = BacktestEngine()
        engine.add_venue(
            venue=Venue("SIM"),
            oms_type=OmsType.NETTING,
            account_type=AccountType.CASH,
            base_currency=USDT,
            starting_balances=[Money(10_000, USDT)],
        )
        assert engine is not None
        engine.dispose()

    def test_margin_venue_with_leverage(self):
        """A MARGIN account venue accepts default_leverage."""
        engine = BacktestEngine()
        engine.add_venue(
            venue=Venue("SIM"),
            oms_type=OmsType.NETTING,
            account_type=AccountType.MARGIN,
            base_currency=USDT,
            starting_balances=[Money(10_000, USDT)],
            default_leverage=Decimal("10"),
        )
        assert engine is not None
        engine.dispose()

    def test_dex_cash_venue_builds(self):
        """A DEX venue (no margin) builds the same way as CeFi CASH."""
        engine = BacktestEngine()
        engine.add_venue(
            venue=Venue("UNISWAP_V3"),
            oms_type=OmsType.NETTING,
            account_type=AccountType.CASH,
            base_currency=USDT,
            starting_balances=[Money(10_000, USDT)],
        )
        assert engine is not None
        engine.dispose()

    def test_multi_currency_starting_balances(self):
        """Multiple starting currencies are accepted."""
        engine = BacktestEngine()
        engine.add_venue(
            venue=Venue("SIM"),
            oms_type=OmsType.NETTING,
            account_type=AccountType.CASH,
            base_currency=None,
            starting_balances=[
                Money(10_000, USDT),
                Money(1, BTC),
            ],
        )
        assert engine is not None
        engine.dispose()


class TestFillModelPatterns:
    """Verify fill model construction and parameter bounds."""

    def test_cefi_fill_model_builds(self):
        model = FillModel(
            prob_fill_on_limit=0.5,
            prob_fill_on_stop=1.0,
            prob_slippage=0.2,
            random_seed=42,
        )
        assert model is not None

    def test_dex_fill_model_builds(self):
        """DEX-realistic fill model with higher slippage probability."""
        model = FillModel(
            prob_fill_on_limit=0.25,
            prob_fill_on_stop=1.0,
            prob_slippage=0.70,
            random_seed=42,
        )
        assert model is not None

    def test_fill_model_is_reproducible(self):
        """Same random_seed produces identical results."""
        model_a = FillModel(prob_fill_on_limit=0.5, prob_fill_on_stop=1.0, prob_slippage=0.2, random_seed=1)
        model_b = FillModel(prob_fill_on_limit=0.5, prob_fill_on_stop=1.0, prob_slippage=0.2, random_seed=1)

        results_a = [model_a.is_limit_filled() for _ in range(20)]
        results_b = [model_b.is_limit_filled() for _ in range(20)]
        assert results_a == results_b

    @pytest.mark.parametrize("prob", [0.0, 0.5, 1.0])
    def test_fill_model_accepts_boundary_probabilities(self, prob):
        model = FillModel(
            prob_fill_on_limit=prob,
            prob_fill_on_stop=1.0,
            prob_slippage=prob,
            random_seed=0,
        )
        assert model is not None


class TestBacktestEngineWithInstrument:
    """Verify engine accepts instruments and runs without data."""

    def test_engine_add_instrument(self):
        instrument = TestInstrumentProvider.btcusdt_binance()
        engine = BacktestEngine()
        engine.add_venue(
            venue=Venue("BINANCE"),
            oms_type=OmsType.NETTING,
            account_type=AccountType.CASH,
            base_currency=USDT,
            starting_balances=[Money(10_000, USDT)],
        )
        engine.add_instrument(instrument)
        engine.run()  # No data → runs immediately
        engine.dispose()

    def test_engine_generates_account_report(self):
        instrument = TestInstrumentProvider.btcusdt_binance()
        engine = BacktestEngine()
        venue = Venue("BINANCE")
        engine.add_venue(
            venue=venue,
            oms_type=OmsType.NETTING,
            account_type=AccountType.CASH,
            base_currency=USDT,
            starting_balances=[Money(10_000, USDT)],
        )
        engine.add_instrument(instrument)
        engine.run()

        report = engine.trader.generate_account_report(venue)
        assert report is not None
        engine.dispose()
