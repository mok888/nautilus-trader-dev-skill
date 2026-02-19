"""
DEX Adapter Template: Order Book Builder

Reconstructs a synthetic L2 order book from AMM pool state.

For AMM pools (Uniswap V2/V3, Curve, Balancer):
- There is no discrete order book — liquidity is continuous
- We synthesise price levels by simulating different trade sizes
- The resulting L2 snapshot approximates the effective price curve

For on-chain CLOB DEX (dYdX v4, Hyperliquid):
- Real order book exists on-chain
- Map order events to OrderBookDelta objects directly

This helper is called by the data client to generate OrderBookDelta snapshots.
"""

from decimal import Decimal

from nautilus_trader.model.data import OrderBookDelta, OrderBookDeltas
from nautilus_trader.model.enums import BookAction, OrderSide as BookSide
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.objects import Price, Quantity


# =============================================================================
# AMM Price Level Calculator
# =============================================================================

def calculate_amm_price_levels(
    reserve0: float,
    reserve1: float,
    fee_rate: float,
    num_levels: int = 10,
    size_step: float = 0.1,
) -> tuple[list[tuple[float, float]], list[tuple[float, float]]]:
    """
    Derive synthetic bid/ask price levels from AMM pool reserves.

    Uses the constant product formula (x * y = k) to calculate the effective
    execution price for each simulated trade size.

    This approximates the AMM's price curve as a discrete order book.

    Parameters
    ----------
    reserve0 : float
        Pool reserve of token0 (decimal-adjusted, e.g. WETH).
    reserve1 : float
        Pool reserve of token1 (decimal-adjusted, e.g. USDC).
    fee_rate : float
        Pool fee rate (e.g. 0.003 for 0.3%).
    num_levels : int
        Number of price levels to generate per side.
    size_step : float
        Step size between levels (fraction of reserve0).

    Returns
    -------
    tuple[list[tuple[float, float]], list[tuple[float, float]]]
        (bid_levels, ask_levels) where each level is (price, size).

        bid_levels: prices at which the pool will buy token0 (sells from pool).
        ask_levels: prices at which the pool will sell token0 (buys from pool).
    """
    if reserve0 <= 0 or reserve1 <= 0:
        return [], []

    k = reserve0 * reserve1  # Constant product

    bid_levels = []
    ask_levels = []

    for i in range(1, num_levels + 1):
        trade_size = reserve0 * size_step * i

        # ── Ask levels: cost to BUY trade_size of token0 ──────────────────────
        # After swap: pool has (reserve0 - trade_size) token0
        # To maintain k: new_reserve1 = k / (reserve0 - trade_size)
        # Amount in = new_reserve1 - reserve1 (how much token1 you pay)
        if reserve0 - trade_size <= 0:
            break

        new_reserve1_ask = k / (reserve0 - trade_size)
        amount_in_token1 = new_reserve1_ask - reserve1
        amount_in_with_fee = amount_in_token1 / (1 - fee_rate)

        if trade_size > 0:
            ask_price = amount_in_with_fee / trade_size
            ask_levels.append((ask_price, trade_size))

        # ── Bid levels: revenue from SELLING trade_size of token0 ─────────────
        # After swap: pool has (reserve0 + trade_size * (1-fee)) token0
        amount_in_adjusted = trade_size * (1 - fee_rate)
        new_reserve1_bid = k / (reserve0 + amount_in_adjusted)
        amount_out_token1 = reserve1 - new_reserve1_bid

        if trade_size > 0:
            bid_price = amount_out_token1 / trade_size
            bid_levels.append((bid_price, trade_size))

    return bid_levels, ask_levels


# =============================================================================
# OrderBookDelta Builder
# =============================================================================

def build_order_book_snapshot(
    instrument_id: InstrumentId,
    reserve0: float,
    reserve1: float,
    fee_rate: float,
    ts_event: int,
    ts_init: int,
    num_levels: int = 5,
    size_step: float = 0.05,
) -> OrderBookDeltas:
    """
    Build an OrderBookDeltas snapshot from AMM pool reserves.

    Creates a synthetic L2 snapshot representing the AMM's effective price curve.
    Each call should be preceded by a CLEAR delta if replacing a previous snapshot.

    Parameters
    ----------
    instrument_id : InstrumentId
        The pool's instrument identifier.
    reserve0 : float
        Token0 reserve (decimal-adjusted).
    reserve1 : float
        Token1 reserve (decimal-adjusted).
    fee_rate : float
        Pool fee rate (0.003 = 0.3%).
    ts_event : int
        Event timestamp in Unix nanoseconds.
    ts_init : int
        Init timestamp in Unix nanoseconds.
    num_levels : int
        Number of price levels per side.
    size_step : float
        Step size as fraction of reserve0.

    Returns
    -------
    OrderBookDeltas
        A sequence of OrderBookDelta events representing the current snapshot.
    """
    bid_levels, ask_levels = calculate_amm_price_levels(
        reserve0=reserve0,
        reserve1=reserve1,
        fee_rate=fee_rate,
        num_levels=num_levels,
        size_step=size_step,
    )

    deltas = []
    sequence = 0

    # Clear existing book first
    clear_delta = OrderBookDelta.clear(
        instrument_id=instrument_id,
        sequence=sequence,
        ts_event=ts_event,
        ts_init=ts_init,
    )
    deltas.append(clear_delta)
    sequence += 1

    # Add bid levels (sorted descending by price — best bid first)
    for price, size in sorted(bid_levels, key=lambda x: -x[0]):
        delta = OrderBookDelta(
            instrument_id=instrument_id,
            action=BookAction.ADD,
            order=None,  # TODO: BookOrder(BookSide.BUY, Price.from_str(f"{price:.6f}"), Quantity.from_str(f"{size:.8f}"), 0)
            flags=0,
            sequence=sequence,
            ts_event=ts_event,
            ts_init=ts_init,
        )
        deltas.append(delta)
        sequence += 1

    # Add ask levels (sorted ascending by price — best ask first)
    for price, size in sorted(ask_levels, key=lambda x: x[0]):
        delta = OrderBookDelta(
            instrument_id=instrument_id,
            action=BookAction.ADD,
            order=None,  # TODO: BookOrder(BookSide.SELL, Price.from_str(f"{price:.6f}"), Quantity.from_str(f"{size:.8f}"), 0)
            flags=0,
            sequence=sequence,
            ts_event=ts_event,
            ts_init=ts_init,
        )
        deltas.append(delta)
        sequence += 1

    return OrderBookDeltas(instrument_id=instrument_id, deltas=deltas)


# =============================================================================
# Mid-Price Helper
# =============================================================================

def amm_spot_price(reserve0: float, reserve1: float) -> float:
    """
    Calculate AMM spot price (no fee, no slippage).

    This is the instantaneous price at the current pool state.
    For execution price with slippage, use calculate_amm_price_levels().

    Parameters
    ----------
    reserve0 : float
        Token0 reserve (decimal-adjusted).
    reserve1 : float
        Token1 reserve (decimal-adjusted).

    Returns
    -------
    float
        Spot price of token0 in terms of token1.
    """
    if reserve0 == 0:
        raise ValueError("reserve0 is zero — cannot calculate price from empty pool")
    return reserve1 / reserve0


def amm_execution_price(
    reserve0: float,
    reserve1: float,
    amount_in: float,
    fee_rate: float = 0.003,
    is_buy: bool = True,
) -> float:
    """
    Calculate actual execution price for a specific order size using AMM formula.

    This models real slippage and should be used for backtest fill price
    calculations and pre-trade analysis.

    Parameters
    ----------
    reserve0 : float
        Token0 reserve (decimal-adjusted).
    reserve1 : float
        Token1 reserve (decimal-adjusted).
    amount_in : float
        Amount being swapped (in token0 for sell, token1 for buy).
    fee_rate : float
        Pool fee rate (0.003 = 0.3%).
    is_buy : bool
        True if buying token0 with token1.

    Returns
    -------
    float
        Effective execution price (token1 per token0).
    """
    k = reserve0 * reserve1

    if is_buy:
        # Paying token1 to receive token0
        amount_in_adjusted = amount_in * (1 - fee_rate)
        new_reserve1 = reserve1 + amount_in_adjusted
        new_reserve0 = k / new_reserve1
        amount_out = reserve0 - new_reserve0
        return amount_in / amount_out if amount_out > 0 else float("inf")
    else:
        # Paying token0 to receive token1
        amount_in_adjusted = amount_in * (1 - fee_rate)
        new_reserve0 = reserve0 + amount_in_adjusted
        new_reserve1 = k / new_reserve0
        amount_out = reserve1 - new_reserve1
        return amount_out / amount_in if amount_in > 0 else 0.0
