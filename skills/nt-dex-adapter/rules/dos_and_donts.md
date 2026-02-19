# DEX Adapter — DO and DON'Ts

Curated DEX-specific rules. For general NautilusTrader adapter rules, see `nt-review/SKILL.md`.

---

## ✅ DOs

### Instrument Discovery

**DO** implement both `load_all_async()` and `load_ids_async()` on your `InstrumentProvider`.
```python
async def load_all_async(self) -> None:
    """Fetch all pools/markets from on-chain registry."""
    pools = await self._client.fetch_all_pools()
    for pool in pools:
        instrument = self._parse_pool(pool)
        self._instruments[instrument.id] = instrument

async def load_ids_async(self, instrument_ids: list[InstrumentId]) -> None:
    """Load specific pools by ID (for targeted reconnects)."""
    for iid in instrument_ids:
        pool = await self._client.fetch_pool(iid.symbol.value)
        self._instruments[iid] = self._parse_pool(pool)
```

**DO** normalise instrument IDs to `{SYMBOL}.{VENUE}` format, e.g. `WETH-USDC.UNISWAP_V3`.

**DO** map on-chain fee tier into `maker_fee` and `taker_fee` on the instrument.
```python
# Uniswap V3: 3000 fee tier = 0.3%
maker_fee = Decimal(str(pool.fee / 1_000_000))
taker_fee = maker_fee
```

**DO** write instruments to catalog before writing any market data.
```python
catalog.write_data([instrument])  # Always first
catalog.write_data(trade_ticks)
```

---

### Tooling
- **DO** use `uv` for managing the adapter dev environment (see `docs/uv_guide.md`).
- **DO** use `msgspec` for high-performance internal data passing if bypassing the message bus.

### Market Data

**DO** synthesise `QuoteTick` from AMM pool reserves using the constantproduct formula.
```python
# For Uniswap V2-style: x * y = k
# price = reserve_quote / reserve_base
ask_price = reserve_quote / reserve_base  # token0/token1 in quote units
bid_price = ask_price * (1 - fee_rate)    # Effective bid includes fee
```

See `templates/dex_order_book_builder.py` for a full implementation.

**DO** drive chain polling from a dedicated polling Actor using `self.clock.set_timer()`, NOT from inside `on_bar` or `on_quote_tick`.
```python
class DEXPollingActor(Actor):
    def on_start(self) -> None:
        self.clock.set_timer(
            name="poll_chain",
            interval=pd.Timedelta(seconds=self.config.poll_interval_secs),
            callback=self._poll_chain,
        )

    def _poll_chain(self, event) -> None:
        # Async call goes to Rust client via get_runtime().block_on()
        data = self._client.fetch_pool_state(self.pool_address)
        self.publish_data(DEXPoolState, data)
```

**DO** emit `OrderBookDelta` events for on-chain CLOB DEX updates.

**DO** convert on-chain swap events to `TradeTick` objects.
```python
trade_tick = TradeTick(
    instrument_id=instrument_id,
    price=Price.from_str(str(execution_price)),
    size=Quantity.from_str(str(amount_in)),
    aggressor_side=AggressorSide.BUYER,
    trade_id=TradeId(tx_hash),
    ts_event=block_timestamp_ns,
    ts_init=self.clock.timestamp_ns(),
)
self._handle_trade_tick(trade_tick)
```

---

### Order Execution

**DO** sign transactions inside the Rust HTTP client, never in Python handler code.
```python
# Rust client signs and broadcasts; Python layer only submits parameters
result = await self._client.submit_swap(
    pool=pool_address,
    amount_in=quantity,
    min_amount_out=min_out,  # Derived from slippage tolerance
)
```

**DO** check transaction receipt status and emit the correct Nautilus event.
```python
receipt = await self._client.get_tx_receipt(tx_hash)
if receipt.status == 0:  # Reverted on-chain
    self.generate_order_rejected(
        order=order,
        reason=f"Transaction reverted: {tx_hash}",
        ts_event=self.clock.timestamp_ns(),
    )
else:
    self.generate_order_filled(
        order=order,
        venue_order_id=VenueOrderId(tx_hash),
        venue_position_id=None,
        trade_id=TradeId(tx_hash),
        position_side=PositionSide.FLAT,
        last_qty=actual_amount_out,
        last_px=actual_execution_price,
        quote_currency=instrument.quote_currency,
        commission=gas_cost_in_quote,
        liquidity_side=LiquiditySide.TAKER,
        ts_event=block_timestamp_ns,
        ts_init=self.clock.timestamp_ns(),
    )
```

**DO** implement `generate_account_state()` after every balance-changing transaction.
```python
async def _update_account_state(self) -> None:
    balances = await self._client.fetch_wallet_balances()
    self.generate_account_state(
        balances=[AccountBalance(
            total=Money(balances["USDT"], USDT),
            locked=Money(0, USDT),
            free=Money(balances["USDT"], USDT),
        )],
        margins=[],
        reported=True,
        ts_event=self.clock.timestamp_ns(),
    )
```

**DO** implement `generate_order_status_report()` for reconciliation.
```python
async def generate_order_status_report(
    self,
    instrument_id: InstrumentId,
    client_order_id: ClientOrderId | None = None,
    venue_order_id: VenueOrderId | None = None,
) -> OrderStatusReport | None:
    # Query on-chain tx status
    ...
```

**DO** expose a `sandbox_mode: bool` config flag for testnet / local fork.
```python
class MyDEXExecClientConfig(LiveExecClientConfig, frozen=True):
    rpc_url: str
    private_key: SecretStr
    sandbox_mode: bool = False  # True → use testnet/local fork
    max_slippage_bps: int = 50
    gas_limit: int = 300_000
```

---

### Rust Core Patterns (DEX-specific)

**DO** use `get_runtime().spawn()` for all async tasks in adapter code.
```rust
use nautilus_common::live::get_runtime;

get_runtime().spawn(async move {
    let receipt = client.submit_tx(signed_tx).await;
    // Handle receipt
});
```

**DO** use `AHashMap` for hot-path instrument/price caches; use standard `HashMap` for RPC client config.

**DO** put a `SAFETY:` comment on every `unsafe` block.

**DO** use `SecretStr` / environment variable injection for private keys, never hardcode.

---

## ❌ DON'Ts

### Market Data

**DON'T** poll the RPC node from inside `on_bar` or `on_quote_tick` — these are synchronous handlers.
```python
# ❌ WRONG – blocks the event loop thread
def on_bar(self, bar: Bar) -> None:
    pool_state = requests.get(self.rpc_url + "/pool").json()  # BLOCKS!
```

**DON'T** use AMM spot price as the execution fill price without modelling slippage.
```python
# ❌ WRONG – ignores k=xy slippage
fill_price = reserve_quote / reserve_base  # Spot price, not actual fill

# ✅ CORRECT – apply constant product formula for order size
price_impact = amount_in / (reserve_base + amount_in)
fill_price = reserve_quote * price_impact / amount_in
```

**DON'T** skip implementing `_subscribe_order_book_deltas` if your DEX has on-chain CLOB state.

---

### Order Execution

**DON'T** store private keys as plain `str` in config.
```python
# ❌ WRONG — key leaks in logs, repr, state dumps
class Config(LiveExecClientConfig):
    private_key: str

# ✅ CORRECT
from pydantic import SecretStr
class Config(LiveExecClientConfig):
    private_key: SecretStr
```

**DON'T** ignore transaction revert errors.
> A submitted tx that reaches the chain but reverts must emit `OrderRejected`, NOT be silently dropped.

**DON'T** assume gas estimates are exact — always add a 20% buffer.
```python
estimated_gas = await self._client.estimate_gas(tx)
safe_gas_limit = int(estimated_gas * 1.2)
```

**DON'T** skip `generate_account_state()` after orders execute.
> Without it, the portfolio state becomes stale and reconciliation fails.

---

### Rust Conventions

**DON'T** use `tokio::spawn()` in adapter code (not in tests).
```rust
// ❌ WRONG — panics from Python threads
tokio::spawn(async move { ... });

// ✅ CORRECT
get_runtime().spawn(async move { ... });
```

**DON'T** use `Arc<PyObject>` — causes reference cycles.
```rust
// ❌ WRONG
handler: Option<Arc<PyObject>>,

// ✅ CORRECT
handler: Option<PyObject>,
// with manual Clone using clone_py_object()
```

**DON'T** use `HashMap` / `HashSet` in hot paths — use `AHashMap` / `AHashSet`.

**DON'T** use `.unwrap()` in production (non-test) Rust code — propagate errors with `?`.

**DON'T** write box-style banner comments in Rust.
```rust
// ❌ WRONG
// ====================
// Section header
// ====================
```

---

### Testing

**DON'T** write tests that require a live RPC connection.
> All adapter tests must run offline. Use mock RPC responses or recorded fixtures.

**DON'T** skip the `test_dex_compliance.py` structural test before shipping the adapter.
