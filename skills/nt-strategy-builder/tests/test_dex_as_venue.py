"""
Strategy Builder Tests: DEX as Venue

Integration smoke test: wire a DEX venue into BacktestEngine and
verify the engine runs with DEX-normalised instrument and data types.

This test does NOT require a live chain connection.
All data is constructed in-memory using Nautilus test kit helpers.
"""

import pytest
from decimal import Decimal

from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.models import FillModel
from nautilus_trader.model.currencies import USDT
from nautilus_trader.model.data import QuoteTick
from nautilus_trader.model.enums import AccountType, OmsType
from nautilus_trader.model.identifiers import InstrumentId, Symbol, Venue
from nautilus_trader.model.instruments import CurrencyPair
from nautilus_trader.model.objects import Money, Price, Quantity


# ─── DEX INSTRUMENT BUILDER ────────────────────────────────────────────────────

def build_dex_instrument(pool_name: str, venue_name: str) -> CurrencyPair:
    """
    Build a synthetic Nautilus instrument representing an AMM pool.
    Mirrors the output of a DEX adapter's InstrumentProvider.
    """
    return CurrencyPair(
        instrument_id=InstrumentId(Symbol(pool_name), Venue(venue_name)),
        raw_symbol=Symbol(pool_name),
        base_currency=None,
        quote_currency=USDT,
        price_precision=6,
        size_precision=8,
        price_increment=Price.from_str("0.000001"),
        size_increment=Quantity.from_str("0.00000001"),
        lot_size=None,
        max_quantity=None,
        min_quantity=Quantity.from_str("0.001"),
        max_notional=None,
        min_notional=None,
        max_price=None,
        min_price=None,
        margin_init=Decimal("0"),
        margin_maint=Decimal("0"),
        maker_fee=Decimal("0.003"),
        taker_fee=Decimal("0.003"),
        ts_event=0,
        ts_init=0,
    )


class TestDEXasBacktestVenue:
    """Verify a DEX adapter output integrates with BacktestEngine."""

    def test_dex_instrument_adds_to_engine(self):
        """BacktestEngine accepts a DEX pool as an instrument."""
        instrument = build_dex_instrument("WETH-USDC", "UNISWAP_V3")
        engine = BacktestEngine()
        engine.add_venue(
            venue=Venue("UNISWAP_V3"),
            oms_type=OmsType.NETTING,
            account_type=AccountType.CASH,
            base_currency=USDT,
            starting_balances=[Money(10_000, USDT)],
        )
        engine.add_instrument(instrument)
        engine.run()
        engine.dispose()

    def test_dex_fill_model_parameters(self):
        """DEX fill model has higher slippage than CeFi model."""
        dex_model = FillModel(
            prob_fill_on_limit=0.25,
            prob_fill_on_stop=1.0,
            prob_slippage=0.70,
            random_seed=42,
        )
        cefi_model = FillModel(
            prob_fill_on_limit=0.5,
            prob_fill_on_stop=1.0,
            prob_slippage=0.2,
            random_seed=42,
        )
        # DEX should have higher slippage ratio
        assert dex_model.prob_slippage > cefi_model.prob_slippage
        assert dex_model.prob_fill_on_limit < cefi_model.prob_fill_on_limit

    def test_engine_with_dex_venue_runs_empty(self):
        """Engine with a DEX venue runs to completion with no data (empty run)."""
        instrument = build_dex_instrument("WETH-USDC", "UNISWAP_V3")
        engine = BacktestEngine()
        engine.add_venue(
            venue=Venue("UNISWAP_V3"),
            oms_type=OmsType.NETTING,
            account_type=AccountType.CASH,
            base_currency=USDT,
            starting_balances=[Money(10_000, USDT)],
            fill_model=FillModel(
                prob_fill_on_limit=0.25,
                prob_fill_on_stop=1.0,
                prob_slippage=0.70,
                random_seed=42,
            ),
        )
        engine.add_instrument(instrument)
        engine.run()  # No data → runs immediately

        report = engine.trader.generate_positions_report()
        assert report is not None  # Report should exist even with no trades
        engine.dispose()

    def test_dex_and_cefi_venues_coexist(self):
        """Engine accepts both a DEX venue and a CeFi venue simultaneously."""
        from nautilus_trader.test_kit.providers import TestInstrumentProvider

        dex_instrument = build_dex_instrument("WETH-USDC", "UNISWAP_V3")
        cefi_instrument = TestInstrumentProvider.btcusdt_binance()

        engine = BacktestEngine()

        engine.add_venue(
            venue=Venue("UNISWAP_V3"),
            oms_type=OmsType.NETTING,
            account_type=AccountType.CASH,
            base_currency=USDT,
            starting_balances=[Money(10_000, USDT)],
        )
        engine.add_venue(
            venue=Venue("BINANCE"),
            oms_type=OmsType.NETTING,
            account_type=AccountType.CASH,
            base_currency=USDT,
            starting_balances=[Money(10_000, USDT)],
        )
        engine.add_instrument(dex_instrument)
        engine.add_instrument(cefi_instrument)
        engine.run()
        engine.dispose()
