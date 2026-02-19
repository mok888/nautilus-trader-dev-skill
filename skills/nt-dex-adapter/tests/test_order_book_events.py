"""
DEX Adapter Tests: AMM Order Book and Quote Synthesis

Verifies:
- AMM constant-product price calculations
- QuoteTick synthesis from pool reserves
- Order book level generation (bid/ask price curve)
- Slippage model correctness
"""

import pytest

import sys
import importlib.util
from pathlib import Path

_templates = Path(__file__).parent.parent / "templates"

def _load_module(name: str):
    spec = importlib.util.spec_from_file_location(name, _templates / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

_ob_mod = _load_module("dex_order_book_builder")

amm_spot_price = _ob_mod.amm_spot_price
amm_execution_price = _ob_mod.amm_execution_price
calculate_amm_price_levels = _ob_mod.calculate_amm_price_levels


class TestAMMSpotPrice:
    """Verify constant-product AMM spot price formula."""

    def test_basic_spot_price(self):
        """reserve1/reserve0 gives spot price."""
        reserve0 = 1000.0   # 1000 WETH
        reserve1 = 3_000_000.0  # 3,000,000 USDC
        price = amm_spot_price(reserve0, reserve1)
        assert abs(price - 3000.0) < 0.001  # ~$3000/ETH

    def test_spot_price_zero_reserve_raises(self):
        with pytest.raises(ValueError, match="reserve0 is zero"):
            amm_spot_price(0, 1_000_000)

    def test_spot_price_is_inverse_of_flipped_reserves(self):
        """Price of A in B == 1 / Price of B in A."""
        r0, r1 = 100.0, 300_000.0
        price_a_in_b = amm_spot_price(r0, r1)      # WETH price in USDC
        price_b_in_a = amm_spot_price(r1, r0)      # USDC price in WETH
        assert abs(price_a_in_b * price_b_in_a - 1.0) < 1e-9


class TestAMMExecutionPrice:
    """Verify that execution price includes slippage from AMM formula."""

    @pytest.fixture
    def pool(self):
        """Standard test pool: 1000 ETH, $3M USDC."""
        return {"reserve0": 1000.0, "reserve1": 3_000_000.0, "fee_rate": 0.003}

    def test_small_buy_near_spot(self, pool):
        """Small buy should be close to spot price."""
        spot = amm_spot_price(pool["reserve0"], pool["reserve1"])
        exec_price = amm_execution_price(
            pool["reserve0"], pool["reserve1"],
            amount_in=1.0,  # Buy 1 WETH worth of USDC
            fee_rate=pool["fee_rate"],
            is_buy=True,
        )
        # Should be within 0.5% of spot for a tiny trade
        assert abs(exec_price - spot) / spot < 0.005

    def test_large_buy_has_more_slippage(self, pool):
        """Larger trade has more slippage than smaller trade."""
        small_price = amm_execution_price(
            pool["reserve0"], pool["reserve1"],
            amount_in=100.0,   # Pay 100 USDC
            fee_rate=pool["fee_rate"],
            is_buy=True,
        )
        large_price = amm_execution_price(
            pool["reserve0"], pool["reserve1"],
            amount_in=100_000.0,  # Pay 100k USDC
            fee_rate=pool["fee_rate"],
            is_buy=True,
        )
        # Larger trade → higher price paid (more slippage on buy)
        assert large_price > small_price

    def test_sell_price_below_spot(self, pool):
        """Selling token0 should give a price below spot (bid < ask)."""
        spot = amm_spot_price(pool["reserve0"], pool["reserve1"])
        sell_price = amm_execution_price(
            pool["reserve0"], pool["reserve1"],
            amount_in=1.0,
            fee_rate=pool["fee_rate"],
            is_buy=False,
        )
        assert sell_price < spot

    def test_buy_price_above_spot(self, pool):
        """Buying token0 should cost more than spot (ask > spot)."""
        spot = amm_spot_price(pool["reserve0"], pool["reserve1"])
        buy_price = amm_execution_price(
            pool["reserve0"], pool["reserve1"],
            amount_in=100.0,
            fee_rate=pool["fee_rate"],
            is_buy=True,
        )
        assert buy_price > spot


class TestAMMPriceLevels:
    """Verify synthetic order book level generation from pool reserves."""

    def test_returns_bid_and_ask_levels(self):
        bids, asks = calculate_amm_price_levels(
            reserve0=1000.0,
            reserve1=3_000_000.0,
            fee_rate=0.003,
            num_levels=5,
        )
        assert len(bids) > 0
        assert len(asks) > 0

    def test_num_levels_respected(self):
        bids, asks = calculate_amm_price_levels(
            reserve0=1000.0,
            reserve1=3_000_000.0,
            fee_rate=0.003,
            num_levels=3,
        )
        assert len(bids) <= 3
        assert len(asks) <= 3

    def test_bid_prices_below_ask_prices(self):
        """Best bid must be less than best ask (no crossed book)."""
        bids, asks = calculate_amm_price_levels(
            reserve0=1000.0,
            reserve1=3_000_000.0,
            fee_rate=0.003,
            num_levels=5,
        )
        if bids and asks:
            best_bid = max(p for p, _ in bids)
            best_ask = min(p for p, _ in asks)
            assert best_bid < best_ask

    def test_empty_pool_returns_empty_levels(self):
        """Empty pool (reserve0=0) returns empty levels."""
        bids, asks = calculate_amm_price_levels(
            reserve0=0.0,
            reserve1=3_000_000.0,
            fee_rate=0.003,
        )
        assert bids == []
        assert asks == []

    def test_higher_fee_widens_spread(self):
        """Higher fee pool should have wider bid/ask spread."""
        bids_low, asks_low = calculate_amm_price_levels(
            reserve0=1000.0, reserve1=3_000_000.0, fee_rate=0.0005
        )
        bids_high, asks_high = calculate_amm_price_levels(
            reserve0=1000.0, reserve1=3_000_000.0, fee_rate=0.01
        )

        if bids_low and asks_low and bids_high and asks_high:
            spread_low = min(p for p, _ in asks_low) - max(p for p, _ in bids_low)
            spread_high = min(p for p, _ in asks_high) - max(p for p, _ in bids_high)
            assert spread_high > spread_low
