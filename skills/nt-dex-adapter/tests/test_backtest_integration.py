"""
DEX Adapter Tests: BacktestEngine Integration

Smoke test: wire a DEX adapter-style instrument into BacktestEngine and
verify the engine initialises, runs, and disposes without errors.

This mirrors the integration path described in dex_venue_input.py but
tests only the instrument and venue layer — execution logic is tested
separately in test_dex_compliance.py.

No live chain connection required — all data is in-memory.
"""

import pytest
from decimal import Decimal

import sys
import importlib.util
from pathlib import Path

from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.models import FillModel
from nautilus_trader.model.currencies import USDT
from nautilus_trader.model.data import QuoteTick
from nautilus_trader.model.enums import AccountType, OmsType
from nautilus_trader.model.identifiers import InstrumentId, Symbol, Venue
from nautilus_trader.model.instruments import CurrencyPair
from nautilus_trader.model.objects import Money, Price, Quantity

_templates = Path(__file__).parent.parent / "templates"


def _load_module(name: str):
    spec = importlib.util.spec_from_file_location(name, _templates / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_config_mod = _load_module("dex_config")
_provider_mod = _load_module("dex_instrument_provider")
_ob_mod = _load_module("dex_order_book_builder")

MyDEXInstrumentProviderConfig = _config_mod.MyDEXInstrumentProviderConfig
MyDEXInstrumentProvider = _provider_mod.MyDEXInstrumentProvider
amm_spot_price = _ob_mod.amm_spot_price


@pytest.fixture
def dex_instrument():
    """Synthetic DEX instrument from sandbox provider."""
    config = MyDEXInstrumentProviderConfig(sandbox_mode=True)
    provider = MyDEXInstrumentProvider(config=config)
    provider._load_sandbox_instruments()
    instruments = provider.get_all()
    return next(iter(instruments.values()))


@pytest.fixture
def dex_fill_model():
    return FillModel(
        prob_fill_on_limit=0.25,
        prob_slippage=0.70,
        random_seed=42,
    )


class TestDEXBacktestEngineIntegration:
    """Integration smoke tests for DEX adapter + BacktestEngine."""

    def test_engine_accepts_dex_instrument(self, dex_instrument, dex_fill_model):
        """BacktestEngine accepts a DEX instrument without error."""
        base = dex_instrument.base_currency
        quote = dex_instrument.quote_currency
        engine = BacktestEngine()
        engine.add_venue(
            venue=dex_instrument.id.venue,
            oms_type=OmsType.NETTING,
            account_type=AccountType.CASH,
            base_currency=None,
            starting_balances=[Money(10_000, quote), Money(10, base)],
            fill_model=dex_fill_model,
        )
        engine.add_instrument(dex_instrument)
        engine.run()
        engine.dispose()

    def test_engine_generates_account_report(self, dex_instrument, dex_fill_model):
        base = dex_instrument.base_currency
        quote = dex_instrument.quote_currency
        engine = BacktestEngine()
        venue = dex_instrument.id.venue
        engine.add_venue(
            venue=venue,
            oms_type=OmsType.NETTING,
            account_type=AccountType.CASH,
            base_currency=None,
            starting_balances=[Money(10_000, quote), Money(10, base)],
        )
        engine.add_instrument(dex_instrument)
        engine.run()

        report = engine.trader.generate_account_report(venue)
        assert report is not None
        engine.dispose()

    def test_sandbox_provider_instrument_is_valid(self, dex_instrument):
        """Sandbox provider creates instruments with valid precision/fee fields."""
        assert dex_instrument.price_precision > 0
        assert dex_instrument.size_precision > 0
        assert dex_instrument.maker_fee > Decimal("0")
        assert dex_instrument.min_quantity > Quantity.from_str("0")

    def test_amm_price_rounds_to_instrument_precision(self, dex_instrument):
        """Verify AMM price can be expressed at instrument's price precision."""
        reserve0, reserve1 = 1000.0, 3_000_000.0
        spot = amm_spot_price(reserve0, reserve1)

        # Price should be expressible at the configured precision
        price_str = f"{spot:.{dex_instrument.price_precision}f}"
        price = Price.from_str(price_str)
        assert float(price) > 0

    def test_dex_venue_with_zero_balance_initialises(self, dex_instrument):
        """Engine tolerates DEX venue starting with zero additional token balance."""
        base = dex_instrument.base_currency
        quote = dex_instrument.quote_currency
        engine = BacktestEngine()
        engine.add_venue(
            venue=dex_instrument.id.venue,
            oms_type=OmsType.NETTING,
            account_type=AccountType.CASH,
            base_currency=None,
            starting_balances=[Money(10_000, quote), Money(0, base)],
        )
        engine.add_instrument(dex_instrument)
        engine.run()
        engine.dispose()
