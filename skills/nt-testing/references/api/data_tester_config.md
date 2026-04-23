# DataTesterConfig API Reference

Extracted from the Data Testing Spec. Both Python (`nautilus_trader.test_kit.strategies.tester_data`)
and Rust (`nautilus_testkit::testers`) provide the `DataTester`.

## Python: DataTesterConfig

```python
from nautilus_trader.test_kit.strategies.tester_data import DataTester, DataTesterConfig
```

## Rust: DataTesterConfig

```rust
use nautilus_testkit::testers::{DataTester, DataTesterConfig};
```

## Constructor

### Python

```python
DataTesterConfig(
    instrument_ids=[instrument_id],   # list[InstrumentId], required
    ...
)
```

### Rust

```rust
DataTesterConfig::new(client_id, vec![instrument_id])  // client_id: ClientId, instrument_ids: Vec<InstrumentId>
    .with_subscribe_quotes(true)
    // ... builder methods
```

## Parameters

| Parameter                    | Type              | Default         | Affects groups |
|------------------------------|-------------------|-----------------|----------------|
| `instrument_ids`             | list[InstrumentId]| *required*      | All            |
| `client_id`                  | ClientId?         | None            | All            |
| `bar_types`                  | list[BarType]?    | None            | 5              |
| `subscribe_book_deltas`      | bool              | False           | 2              |
| `subscribe_book_depth`       | bool              | False           | 2              |
| `subscribe_book_at_interval` | bool              | False           | 2              |
| `subscribe_quotes`           | bool              | False           | 3              |
| `subscribe_trades`           | bool              | False           | 4              |
| `subscribe_mark_prices`      | bool              | False           | 6              |
| `subscribe_index_prices`     | bool              | False           | 6              |
| `subscribe_funding_rates`    | bool              | False           | 6              |
| `subscribe_bars`             | bool              | False           | 5              |
| `subscribe_instrument`       | bool              | False           | 1              |
| `subscribe_instrument_status`| bool              | False           | 7              |
| `subscribe_instrument_close` | bool              | False           | 7              |
| `subscribe_option_greeks`    | bool              | False           | 8              |
| `subscribe_params`           | dict?             | None            | 9              |
| `can_unsubscribe`            | bool              | True            | 9              |
| `request_instruments`        | bool              | False           | 1              |
| `request_book_snapshot`      | bool              | False           | 2              |
| `request_book_deltas`        | bool              | False           | 2              |
| `request_quotes`             | bool              | False           | 3              |
| `request_trades`             | bool              | False           | 4              |
| `request_bars`               | bool              | False           | 5              |
| `request_funding_rates`      | bool              | False           | 6              |
| `request_params`             | dict?             | None            | 9              |
| `requests_start_delta`       | Timedelta?        | 1 hour          | 3, 4, 5        |
| `book_type`                  | BookType          | L2_MBP          | 2              |
| `book_depth`                 | PositiveInt?      | None            | 2              |
| `book_interval_ms`           | PositiveInt       | 1000            | 2              |
| `book_levels_to_print`       | PositiveInt       | 10              | 2              |
| `manage_book`                | bool              | False           | 2              |
| `use_pyo3_book`              | bool              | False           | 2              |
| `log_data`                   | bool              | True            | All            |

Note: Rust `DataTesterConfig::new` sets `manage_book=true`, while Python defaults it to `False`.

## Rust Builder Methods

Each `with_*` method corresponds to a Python config parameter:

| Rust builder method                   | Python param equivalent                |
|---------------------------------------|----------------------------------------|
| `.with_request_instruments(bool)`     | `request_instruments`                  |
| `.with_subscribe_instrument(bool)`    | `subscribe_instrument`                 |
| `.with_subscribe_book_deltas(bool)`   | `subscribe_book_deltas`                |
| `.with_subscribe_book_at_interval(bool)` | `subscribe_book_at_interval`        |
| `.with_subscribe_book_depth(bool)`    | `subscribe_book_depth`                 |
| `.with_request_book_snapshot(bool)`   | `request_book_snapshot`                |
| `.with_request_book_deltas(bool)`     | `request_book_deltas`                  |
| `.with_subscribe_quotes(bool)`        | `subscribe_quotes`                     |
| `.with_request_quotes(bool)`          | `request_quotes`                       |
| `.with_subscribe_trades(bool)`        | `subscribe_trades`                     |
| `.with_request_trades(bool)`          | `request_trades`                       |
| `.with_bar_types(Vec<BarType>)`       | `bar_types`                            |
| `.with_subscribe_bars(bool)`          | `subscribe_bars`                       |
| `.with_request_bars(bool)`            | `request_bars`                         |
| `.with_subscribe_mark_prices(bool)`   | `subscribe_mark_prices`                |
| `.with_subscribe_index_prices(bool)`  | `subscribe_index_prices`               |
| `.with_subscribe_funding_rates(bool)` | `subscribe_funding_rates`              |
| `.with_request_funding_rates(bool)`   | `request_funding_rates`                |
| `.with_subscribe_instrument_status(bool)` | `subscribe_instrument_status`      |
| `.with_subscribe_instrument_close(bool)` | `subscribe_instrument_close`        |
| `.with_subscribe_option_greeks(bool)` | `subscribe_option_greeks`              |
| `.with_manage_book(bool)`             | `manage_book`                          |
| `.with_book_type(BookType)`           | `book_type`                            |
| `.with_book_depth(Option<NonZeroUsize>)` | `book_depth`                         |
| `.with_book_interval_ms(NonZeroUsize)` | `book_interval_ms`                    |
| `.with_can_unsubscribe(bool)`         | `can_unsubscribe`                      |

## Test Groups

| Group | Name                | Test IDs    | Description                                    |
|-------|---------------------|-------------|------------------------------------------------|
| 1     | Instruments         | TC-D01–D03  | Request, subscribe, load instruments            |
| 2     | Order book          | TC-D10–D15  | Book deltas, snapshots, depth, managed book     |
| 3     | Quotes              | TC-D20–D21  | Quote tick subscribe, historical quotes         |
| 4     | Trades              | TC-D30–D31  | Trade tick subscribe, historical trades         |
| 5     | Bars                | TC-D40–D41  | Bar subscribe, historical bars                  |
| 6     | Derivatives data    | TC-D50–D53  | Mark/index prices, funding rates                |
| 7     | Instrument status   | TC-D60–D61  | Status and close events                         |
| 8     | Option greeks       | TC-D62–D63  | Option greeks and chain                         |
| 9     | Lifecycle           | TC-D70–D72  | Unsubscribe, custom params                      |

An adapter that passes groups 1–4 is considered **baseline data compliant**.

## Node Setup

### Python

```python
from nautilus_trader.live.node import TradingNode
from nautilus_trader.test_kit.strategies.tester_data import DataTester, DataTesterConfig

node = TradingNode(config=config_node)
tester = DataTester(config=config_tester)
node.trader.add_actor(tester)
# Register adapter factories, build, and run
```

Reference: `examples/live/{adapter}/{adapter}_data_tester.py`

### Rust

```rust
use nautilus_testkit::testers::{DataTester, DataTesterConfig};

let tester_config = DataTesterConfig::new(client_id, vec![instrument_id])
    .with_subscribe_quotes(true);
let tester = DataTester::new(tester_config);
node.add_actor(tester)?;
node.run().await?;
```

Reference: `crates/adapters/{adapter}/examples/node_data_tester.rs`
