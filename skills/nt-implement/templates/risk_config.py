from nautilus_trader.config import RiskEngineConfig

def get_risk_config(
    bypass: bool = False,
    max_order_submit_rate: str = "50/00:00:01",
    max_order_modify_rate: str = "20/00:00:01",
) -> RiskEngineConfig:
    """
    Create a RiskEngineConfig with defined limits.

    Args:
        bypass: If True, skips all pre-trade checks (NOT RECOMMENDED for live).
        max_order_submit_rate: Rate limit for new orders (count/duration).
        max_order_modify_rate: Rate limit for modifications (count/duration).
    """
    return RiskEngineConfig(
        bypass=bypass,
        max_order_submit_rate=max_order_submit_rate,
        max_order_modify_rate=max_order_modify_rate,
        # Note: Pre-trade checks (precision, min/max qty, notional) 
        # are always active unless bypass=True.
    )
