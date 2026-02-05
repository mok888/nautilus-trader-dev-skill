# Risk Management

NautilusTrader provides a dedicated `RiskEngine` to validate orders pre-trade and enforce operational limits.

## Risk Engine

The `RiskEngine` sits between the Strategy and the Execution Client. It validates every order submission and modification.

### Configuration

```python
from nautilus_trader.config import RiskEngineConfig

config = RiskEngineConfig(
    # Operational Limits
    max_order_submit_rate="50/00:00:01",   # 50 orders per second
    max_order_modify_rate="20/00:00:01",   # 20 modifications per second
    
    # Global Switch
    bypass=False,  # Set to True to disable ALL checks (Dangerous!)
)
```

### Automatic Checks

Unless bypassed, the Risk Engine always checks:
1. **Precision**: Price/Quantity matches instrument step size.
2. **Limits**: Quantity is within min/max instrument limits.
3. **Notional**: Value is within min/max notional limits (if supported).
4. **Reduce Only**: Ensures reduce-only orders do not open positions.

### Instrument Limits

To set specific notional limits per instrument (requires custom setup):

```python
risk_engine.set_max_notional_per_order(instrument_id, Money(100_000, USD))
```

## Exchange-Specific Risks

### Bybit Spot Margin
For Bybit Unified Trading Accounts, leverage is not automatic. You explicitly opt-in per order:

- **Auto-Borrow**: Requires `auto_repay_spot_borrows=True` in client config.
- **Order Param**: Must send `is_leverage=True` in order command params.

Without these, orders exceeding spot balance will be rejected.
