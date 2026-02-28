# NT-STRATEGY-BUILDER

BacktestEngine and TradingNode wiring for NautilusTrader.

## OVERVIEW

From idea → running system. Covers backtesting, paper trading, and live deployment with multi-venue support (CeFi + custom DEX adapters).

## TEMPLATES

| Template | Mode | Use When |
|----------|------|----------|
| `backtest_node.py` | Backtest | Historical data replay |
| `live_node.py` | Live | Production with real orders |
| `paper_node.py` | Paper | Live data, simulated execution |
| `dex_venue_input.py` | DEX | Wire custom DEX adapter |
| `multi_venue_strategy.py` | Multi-venue | 2+ venues simultaneously |

## DECISION TREE

```
Live market data?
├─ NO  → BacktestEngine + templates/backtest_node.py
└─ YES → TradingNode
         ├─ Real orders? → templates/live_node.py
         └─ Paper?       → templates/paper_node.py
```

## VENUE INPUTS

1. **CeFi Adapters** — Built-in (Binance, Bybit, OKX, etc.)
2. **DEX Adapter** — Built with nt-dex-adapter, wire via `dex_venue_input.py`
3. **Catalog Data** — ParquetDataCatalog for backtests
4. **Multi-Venue** — Multiple data_clients + exec_clients

## ADAPTER WIRING CONTRACT (2026)

- Enable live order flow only after adapter phases 1-4 are complete
- Require canonical factory signatures for data/exec wiring
- Verify reconciliation/report generation paths before production mode
- Block deploy when provider/data/exec contracts are incomplete

## SIMULATION MODELS

```python
# DEX-realistic
FillModel(prob_fill_on_limit=0.3, prob_slippage=0.7)

# CeFi-realistic
FillModel(prob_fill_on_limit=0.5, prob_slippage=0.2)
```

## CRITICAL DON'Ts

- ❌ Block in handlers (no HTTP, file I/O, `time.sleep()`)
- ❌ Assume `cache.instrument()` is non-None
- ❌ Use raw `float` for Price/Quantity
- ❌ Set `reconciliation=False` without justification
- ❌ Use `datetime.utcnow()` — use `self.clock.utc_now()`

## TESTING

```bash
uv run pytest skills/nt-strategy-builder/tests/ -v
```

## NEXT

- Build DEX adapter → `nt-dex-adapter`
- Review code → `nt-review`
