# ExecTesterConfig API Reference

Extracted from the Execution Testing Spec. Both Python (`nautilus_trader.test_kit.strategies.tester_exec`)
and Rust (`nautilus_testkit::testers`) provide the `ExecTester`.

## Python: ExecTesterConfig

```python
from nautilus_trader.test_kit.strategies.tester_exec import ExecTester, ExecTesterConfig
```

## Rust: ExecTesterConfig

```rust
use nautilus_testkit::testers::{ExecTester, ExecTesterConfig};
```

## Constructor

### Python

```python
ExecTesterConfig(
    instrument_id=instrument_id,   # InstrumentId, required
    order_qty=Decimal("0.01"),     # Decimal, required
    ...
)
```

### Rust

```rust
ExecTesterConfig::new(strategy_id, instrument_id, client_id, order_qty)
    .with_enable_limit_buys(true)
    // ... builder methods
```

Where `order_qty` is `Quantity` or `Decimal`.

## Parameters

| Parameter                                       | Type              | Default         | Affects groups |
|-------------------------------------------------|-------------------|-----------------|----------------|
| `instrument_id`                                 | InstrumentId      | *required*      | All            |
| `order_qty`                                     | Decimal           | *required*      | All            |
| `order_display_qty`                             | Decimal?          | None            | 2, 7           |
| `order_expire_time_delta_mins`                  | PositiveInt?      | None            | 2              |
| `order_params`                                  | dict?             | None            | 7, 10          |
| `client_id`                                     | ClientId?         | None            | All            |
| `subscribe_quotes`                              | bool              | True            | —              |
| `subscribe_trades`                              | bool              | True            | —              |
| `subscribe_book`                                | bool              | False           | —              |
| `book_type`                                     | BookType          | L2_MBP          | —              |
| `book_depth`                                    | PositiveInt?      | None            | —              |
| `book_interval_ms`                              | PositiveInt       | 1000            | —              |
| `book_levels_to_print`                          | PositiveInt       | 10              | —              |
| `open_position_on_start_qty`                    | Decimal?          | None            | 1, 9           |
| `open_position_time_in_force`                   | TimeInForce       | GTC             | 1              |
| `enable_limit_buys`                             | bool              | True            | 2, 4, 5, 6     |
| `enable_limit_sells`                            | bool              | True            | 2, 4, 5, 6     |
| `enable_stop_buys`                              | bool              | False           | 3, 4           |
| `enable_stop_sells`                             | bool              | False           | 3, 4           |
| `limit_time_in_force`                           | TimeInForce?      | None            | 2, 6           |
| `tob_offset_ticks`                              | PositiveInt       | 500             | 2, 4           |
| `stop_order_type`                               | OrderType         | STOP_MARKET     | 3              |
| `stop_offset_ticks`                             | PositiveInt       | 100             | 3              |
| `stop_limit_offset_ticks`                       | PositiveInt?      | None            | 3              |
| `stop_time_in_force`                            | TimeInForce?      | None            | 3              |
| `stop_trigger_type`                             | TriggerType?      | None            | 3              |
| `enable_brackets`                               | bool              | False           | 6              |
| `bracket_entry_order_type`                      | OrderType         | LIMIT           | 6              |
| `bracket_offset_ticks`                          | PositiveInt       | 500             | 6              |
| `modify_orders_to_maintain_tob_offset`          | bool              | False           | 4              |
| `modify_stop_orders_to_maintain_offset`         | bool              | False           | 4              |
| `cancel_replace_orders_to_maintain_tob_offset`  | bool              | False           | 4              |
| `cancel_replace_stop_orders_to_maintain_offset` | bool              | False           | 4              |
| `use_post_only`                                 | bool              | False           | 2, 6, 7, 8     |
| `use_quote_quantity`                            | bool              | False           | 1, 7           |
| `emulation_trigger`                             | TriggerType?      | None            | 2, 3           |
| `cancel_orders_on_stop`                         | bool              | True            | 5, 9           |
| `close_positions_on_stop`                       | bool              | True            | 9              |
| `close_positions_time_in_force`                 | TimeInForce?      | None            | 9              |
| `reduce_only_on_stop`                           | bool              | True            | 7, 9           |
| `use_individual_cancels_on_stop`                | bool              | False           | 5              |
| `use_batch_cancel_on_stop`                      | bool              | False           | 5              |
| `dry_run`                                       | bool              | False           | —              |
| `log_data`                                      | bool              | True            | —              |
| `test_reject_post_only`                         | bool              | False           | 8              |
| `test_reject_reduce_only`                       | bool              | False           | 8              |
| `can_unsubscribe`                               | bool              | True            | 9              |

## Rust Builder Methods

Key builder methods on `ExecTesterConfig`:

| Rust builder method                           | Python param equivalent                     |
|-----------------------------------------------|---------------------------------------------|
| `.with_open_position_on_start(Option<Decimal>)` | `open_position_on_start_qty`              |
| `.with_enable_limit_buys(bool)`               | `enable_limit_buys`                         |
| `.with_enable_limit_sells(bool)`              | `enable_limit_sells`                        |
| `.with_enable_stop_buys(bool)`                | `enable_stop_buys`                          |
| `.with_enable_stop_sells(bool)`               | `enable_stop_sells`                         |
| `.with_stop_order_type(OrderType)`            | `stop_order_type`                           |
| `.with_enable_brackets(bool)`                 | `enable_brackets`                           |
| `.with_bracket_entry_order_type(OrderType)`   | `bracket_entry_order_type`                  |
| `.with_bracket_offset_ticks(usize)`           | `bracket_offset_ticks`                      |
| `.with_use_post_only(bool)`                   | `use_post_only`                             |
| `.with_use_quote_quantity(bool)`              | `use_quote_quantity`                        |
| `.with_cancel_orders_on_stop(bool)`           | `cancel_orders_on_stop`                     |
| `.with_close_positions_on_stop(bool)`         | `close_positions_on_stop`                   |
| `.with_use_batch_cancel_on_stop(bool)`        | `use_batch_cancel_on_stop`                  |

Some fields are set directly on the struct instead of builder methods:

```rust
let mut config = ExecTesterConfig::new(...);
config.open_position_time_in_force = TimeInForce::Ioc;
config.order_expire_time_delta_mins = Some(60);
config.stop_limit_offset_ticks = Some(50);
config.modify_orders_to_maintain_tob_offset = true;
config.cancel_replace_orders_to_maintain_tob_offset = true;
config.modify_stop_orders_to_maintain_offset = true;
config.cancel_replace_stop_orders_to_maintain_offset = true;
config.use_individual_cancels_on_stop = true;
```

## Test Groups

| Group | Name                     | Test IDs    | Description                                         |
|-------|--------------------------|-------------|-----------------------------------------------------|
| 1     | Market orders            | TC-E01–E06  | Buy, sell, IOC, FOK, quote qty, close on stop       |
| 2     | Limit orders             | TC-E10–E19  | GTC, pair, IOC, FOK, GTD, DAY                       |
| 3     | Stop & conditional       | TC-E20–E27  | StopMarket, StopLimit, MIT, LIT                     |
| 4     | Order modification       | TC-E30–E36  | Modify, cancel-replace, modify rejected             |
| 5     | Order cancellation       | TC-E40–E44  | Single, cancel all, individual, batch, already-canceled |
| 6     | Bracket orders           | TC-E50–E53  | Bracket buy/sell, entry fill, post-only entry       |
| 7     | Post-only & reduce-only  | TC-E60–E63  | Post-only limits, reduce-only, display qty          |
| 8     | Rejection tests          | TC-E70–E76  | Post-only reject, reduce-only reject, duplicate ID  |
| 9     | Lifecycle & cleanup      | TC-E80–E86  | Cancel on stop, close on stop, unsubscribe, reconcile |
| 10    | Options                  | TC-E90–E101 | Option orders, alternative pricing, reconcile        |

An adapter that passes groups 1–5 is considered **baseline execution compliant**.

## Node Setup

### Python

```python
from nautilus_trader.live.node import TradingNode
from nautilus_trader.test_kit.strategies.tester_exec import ExecTester, ExecTesterConfig

node = TradingNode(config=config_node)
strategy = ExecTester(config=config_tester)
node.trader.add_strategy(strategy)
# Register adapter factories, build, and run
```

Reference: `examples/live/{adapter}/{adapter}_exec_tester.py`

### Rust

```rust
use nautilus_testkit::testers::{ExecTester, ExecTesterConfig};

let tester_config = ExecTesterConfig::new(strategy_id, instrument_id, client_id, dec!(0.001));
let tester = ExecTester::new(tester_config);
node.add_strategy(tester)?;
node.run().await?;
```

Reference: `crates/adapters/{adapter}/examples/node_exec_tester.rs`

## Prerequisites

- Demo/testnet account with valid API credentials (preferred).
- Account funded with sufficient margin for the test instrument and quantities.
- Target instrument available and loadable via the instrument provider.
- Environment variables: `{VENUE}_API_KEY`, `{VENUE}_API_SECRET`.
- Risk engine bypassed: `LiveRiskEngineConfig(bypass=True)`.
- Reconciliation enabled to verify state consistency.
