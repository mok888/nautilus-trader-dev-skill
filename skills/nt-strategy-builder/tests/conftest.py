"""
Strategy Builder Tests: Conftest

Shared fixtures for unit and integration tests.
"""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock, AsyncMock

from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.models import FillModel
from nautilus_trader.model.currencies import USDT, BTC, ETH
from nautilus_trader.model.enums import AccountType, AssetClass, OmsType
from nautilus_trader.model.identifiers import InstrumentId, Symbol, Venue
from nautilus_trader.model.instruments import CurrencyPair
from nautilus_trader.model.objects import Money, Price, Quantity
from nautilus_trader.test_kit.providers import TestInstrumentProvider
from nautilus_trader.test_kit.stubs.identifiers import TestIdStubs


# ─── INSTRUMENT FIXTURES ───────────────────────────────────────────────────────


@pytest.fixture
def btcusdt_binance():
    """Standard BTC/USDT instrument on Binance."""
    return TestInstrumentProvider.btcusdt_binance()


@pytest.fixture
def eth_usdc_uniswap():
    """
    Synthetic DEX instrument (WETH/USDC on Uniswap V3).
    Uses CurrencyPair as the closest standard Nautilus instrument type for AMM pools.
    """
    return CurrencyPair(
        instrument_id=InstrumentId(Symbol("WETH-USDC"), Venue("UNISWAP_V3")),
        raw_symbol=Symbol("WETH-USDC"),
        base_currency=ETH,
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
        maker_fee=Decimal("0.003"),  # Uniswap 0.3% pool
        taker_fee=Decimal("0.003"),
        ts_event=0,
        ts_init=0,
    )


# ─── FILL MODEL FIXTURES ───────────────────────────────────────────────────────


@pytest.fixture
def cefi_fill_model():
    """Realistic CeFi fill model."""
    return FillModel(
        prob_fill_on_limit=0.5,
        prob_slippage=0.2,
        random_seed=42,
    )


@pytest.fixture
def dex_fill_model():
    """Realistic DEX fill model with higher slippage."""
    return FillModel(
        prob_fill_on_limit=0.25,
        prob_slippage=0.70,
        random_seed=42,
    )


# ─── BACKTEST ENGINE FIXTURES ──────────────────────────────────────────────────


@pytest.fixture
def cefi_engine(btcusdt_binance, cefi_fill_model):
    """BacktestEngine pre-configured with a standard CeFi venue."""
    engine = BacktestEngine()
    engine.add_venue(
        venue=Venue("BINANCE"),
        oms_type=OmsType.NETTING,
        account_type=AccountType.CASH,
        base_currency=USDT,
        starting_balances=[Money(10_000, USDT)],
        fill_model=cefi_fill_model,
    )
    engine.add_instrument(btcusdt_binance)
    yield engine
    engine.dispose()


@pytest.fixture
def dex_engine(eth_usdc_uniswap, dex_fill_model):
    """BacktestEngine pre-configured with a DEX venue."""
    engine = BacktestEngine()
    engine.add_venue(
        venue=Venue("UNISWAP_V3"),
        oms_type=OmsType.NETTING,
        account_type=AccountType.CASH,
        base_currency=USDT,
        starting_balances=[Money(10_000, USDT)],
        fill_model=dex_fill_model,
    )
    engine.add_instrument(eth_usdc_uniswap)
    yield engine
    engine.dispose()
