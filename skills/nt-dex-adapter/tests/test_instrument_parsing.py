"""
DEX Adapter Tests: Instrument Parsing

Verifies that the DEX instrument provider correctly converts on-chain pool
metadata into valid NautilusTrader instrument objects.

All tests run offline — no RPC connections required.
"""

import pytest
from decimal import Decimal

from nautilus_trader.model.identifiers import InstrumentId, Symbol, Venue
from nautilus_trader.model.instruments import CurrencyPair
from nautilus_trader.model.objects import Price, Quantity

import sys
import importlib.util
from pathlib import Path

# Load template modules without installing as a package
_templates = Path(__file__).parent.parent / "templates"


def _load_module(name: str):
    spec = importlib.util.spec_from_file_location(name, _templates / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# Load provider template
_config_mod = _load_module("dex_config")
_provider_mod = _load_module("dex_instrument_provider")

MyDEXInstrumentProviderConfig = _config_mod.MyDEXInstrumentProviderConfig
MyDEXInstrumentProvider = _provider_mod.MyDEXInstrumentProvider


# ─── FIXTURES ──────────────────────────────────────────────────────────────────

@pytest.fixture
def sandbox_provider():
    """Instrument provider in sandbox mode (no chain connection)."""
    config = MyDEXInstrumentProviderConfig(sandbox_mode=True)
    return MyDEXInstrumentProvider(config=config)


@pytest.fixture
def weth_usdc_metadata():
    """Minimal pool metadata matching Uniswap V3 WETH/USDC 0.3% pool."""
    return {
        "token0_symbol": "WETH",
        "token1_symbol": "USDC",
        "fee": 3000,           # 0.3%
        "min_trade_size": "0.001",
    }


@pytest.fixture
def wbtc_usdc_metadata():
    """WBTC/USDC pool metadata (0.05% fee tier)."""
    return {
        "token0_symbol": "WBTC",
        "token1_symbol": "USDC",
        "fee": 500,            # 0.05%
        "min_trade_size": "0.0001",
    }


# ─── INSTRUMENT PARSING TESTS ──────────────────────────────────────────────────

class TestInstrumentParsing:
    """Verify pool metadata → NautilusTrader instrument conversion."""

    def test_parse_produces_currency_pair(self, sandbox_provider, weth_usdc_metadata):
        instrument = sandbox_provider._parse_pool_to_instrument(weth_usdc_metadata)
        assert isinstance(instrument, CurrencyPair)

    def test_instrument_id_format(self, sandbox_provider, weth_usdc_metadata):
        """Instrument ID must follow {SYMBOL}.{VENUE} format."""
        instrument = sandbox_provider._parse_pool_to_instrument(weth_usdc_metadata)
        assert str(instrument.id) == "WETH-USDC.MYDEX"

    def test_instrument_id_venue(self, sandbox_provider, weth_usdc_metadata):
        instrument = sandbox_provider._parse_pool_to_instrument(weth_usdc_metadata)
        assert instrument.id.venue == Venue("MYDEX")

    def test_fee_tier_mapped_to_maker_fee(self, sandbox_provider):
        """0.3% fee tier (3000) maps to Decimal('0.003')."""
        metadata = {
            "token0_symbol": "WETH",
            "token1_symbol": "USDC",
            "fee": 3000,
            "min_trade_size": "0.001",
        }
        instrument = sandbox_provider._parse_pool_to_instrument(metadata)
        assert instrument.maker_fee == Decimal("0.003")
        assert instrument.taker_fee == Decimal("0.003")

    def test_fee_tier_01pct(self, sandbox_provider):
        """0.05% fee tier (500) maps to Decimal('0.0005')."""
        metadata = {
            "token0_symbol": "WBTC",
            "token1_symbol": "USDC",
            "fee": 500,
            "min_trade_size": "0.0001",
        }
        instrument = sandbox_provider._parse_pool_to_instrument(metadata)
        assert instrument.maker_fee == Decimal("0.0005")

    def test_min_quantity_respected(self, sandbox_provider):
        metadata = {
            "token0_symbol": "WETH",
            "token1_symbol": "USDC",
            "fee": 3000,
            "min_trade_size": "0.5",
        }
        instrument = sandbox_provider._parse_pool_to_instrument(metadata)
        assert instrument.min_quantity == Quantity.from_str("0.5")

    def test_instrument_has_zero_margin(self, sandbox_provider, weth_usdc_metadata):
        """DEX instruments have zero margin (CASH account type)."""
        instrument = sandbox_provider._parse_pool_to_instrument(weth_usdc_metadata)
        assert instrument.margin_init == Decimal("0")
        assert instrument.margin_maint == Decimal("0")

    def test_symbol_built_from_token_pair(self, sandbox_provider, wbtc_usdc_metadata):
        instrument = sandbox_provider._parse_pool_to_instrument(wbtc_usdc_metadata)
        assert instrument.raw_symbol == Symbol("WBTC-USDC")


class TestSandboxProvider:
    """Verify sandbox mode loads synthetic instruments without chain connection."""

    def test_sandbox_loads_instruments(self, sandbox_provider):
        sandbox_provider._load_sandbox_instruments()
        instruments = sandbox_provider.get_all()
        assert len(instruments) > 0

    def test_sandbox_instrument_is_findable(self, sandbox_provider):
        sandbox_provider._load_sandbox_instruments()
        iid = InstrumentId.from_str("WETH-USDC.MYDEX")
        instrument = sandbox_provider.find(iid)
        assert instrument is not None

    def test_get_all_returns_copy(self, sandbox_provider):
        """get_all() returns a copy, not a reference to the internal dict."""
        sandbox_provider._load_sandbox_instruments()
        all1 = sandbox_provider.get_all()
        all2 = sandbox_provider.get_all()
        assert all1 is not all2

    def test_find_returns_none_for_missing(self, sandbox_provider):
        iid = InstrumentId.from_str("UNKNOWN-TOKEN.MYDEX")
        result = sandbox_provider.find(iid)
        assert result is None
