# MetaTrader 5

MetaTrader 5 (MT5) is a popular multi-asset trading platform developed by MetaQuotes Software, widely used for forex, stocks, and futures trading. MT5 is offered by numerous brokers worldwide and provides access to thousands of financial instruments.

This integration supports live market data ingest and order execution for MT5 through a ZeroMQ bridge connection.

## Examples

You can find live example scripts [here](https://github.com/nautechsystems/nautilus_trader/tree/develop/examples/live/mt5/).

## Overview

This guide assumes a trader is setting up for both live market data feeds and trade execution.
The MT5 adapter includes multiple components, which can be used together or separately depending
on the use case.

- `Mt5Client`: Low-level ZeroMQ client for MT5 connectivity (Rust implementation with Python bindings).
- `MT5InstrumentProvider`: Instrument parsing and loading functionality.
- `MT5DataClient`: A market data feed manager.
- `MT5ExecutionClient`: An account management and trade execution gateway.
- `MT5LiveDataClientFactory`: Factory for MT5 data clients (used by the trading node builder).
- `MT5LiveExecClientFactory`: Factory for MT5 execution clients (used by the trading node builder).

:::note
Most users will define a configuration for a live trading node (as below),
and won't need to necessarily work with these lower level components directly.
:::

## Prerequisites

### MT5 Terminal Setup

1. **Install MetaTrader 5**: Download and install MT5 from your broker or from [MetaQuotes](https://www.metatrader5.com/).
2. **Enable Algo Trading**: In MT5, go to Tools → Options → Expert Advisors, and ensure "Allow algorithmic trading" is enabled.
3. **Install MT5-ZeroMQ Bridge**: Install the JsonAPI.mq5 Expert Advisor that provides the ZeroMQ bridge.

### Docker Setup (Recommended)

The easiest way to run the MT5-ZeroMQ bridge is using Docker:

```bash
# Clone the MT5-Docker repository
git clone https://github.com/Martingale42/MT5-Docker.git
cd MT5-Docker

# Configure your MT5 credentials in .env file
cp .env.example .env
# Edit .env with your broker details

# Start the Docker container
docker-compose up -d
```

The Docker container runs:
- MT5 Terminal with your broker connection
- JsonAPI.mq5 Expert Advisor providing ZeroMQ endpoints
- Automatically connects to your trading account

### ZeroMQ Ports

The MT5 adapter communicates via three ZeroMQ sockets:

| Socket        | Port | Type | Purpose                              |
|---------------|------|------|--------------------------------------|
| `live_port`   | 2203 | PULL | Live tick data streaming             |
| `stream_port` | 2204 | PULL | Order and position status updates    |
| `sys_port`    | 2201 | REQ  | Commands and queries (REQ/REP)       |

:::note
These ports must be accessible from your NautilusTrader instance. If running locally, ensure no firewall blocks them.
:::

## Installation

To install NautilusTrader with MT5 support:

```bash
uv pip install nautilus_trader
```

The MT5 adapter is built into NautilusTrader's Rust core and requires no additional dependencies.

## Product support

| Product Type              | Supported | Notes                                    |
|---------------------------|-----------|------------------------------------------|
| Forex (Currency Pairs)    | ✓         | Full support for major and exotic pairs  |
| CFDs (Stocks, Indices)    | ✓         | Supported via MT5 broker                 |
| Futures                   | ✓         | Supported via MT5 broker                 |
| Cryptocurrencies          | ✓         | If offered by broker                     |
| Options                   | -         | Not yet implemented                      |

:::note
Product availability depends on your MT5 broker's offerings. The adapter supports any instrument type
that MT5 can trade, but options trading is not currently implemented.
:::

## Data types

The MT5 integration provides the following market data types:

- `QuoteTick`: Bid/ask price updates (preferred for forex and CFDs).
- `TradeTick`: Last trade price updates (alternative representation).
- `Instrument`: Full instrument definitions including contract specifications.

All tick data is sourced from MT5's live price feed and converted to Nautilus domain types.

## Symbology

MT5 uses native broker symbols, which vary by broker. Common formats include:

- Forex: `EURUSD`, `GBPUSD`, `USDJPY`
- CFDs: `AAPL`, `SPX500`, `US30`
- Futures: `ES`, `NQ` (broker-specific)

The adapter uses symbols exactly as they appear in MT5, with the venue `MT5`.

Example instrument IDs:
- `EURUSD.MT5`
- `AAPL.MT5`
- `SPX500.MT5`

:::note
Symbol formats are broker-specific. Check your MT5 Market Watch to see available symbols.
:::

## Order capability

The following tables detail the order types, execution instructions, and time-in-force options supported by the MT5 adapter:

### Order types

| Order Type         | Supported | Notes                                           |
|--------------------|-----------|------------------------------------------------|
| `MARKET`           | ✓         | Immediate execution at current market price    |
| `LIMIT`            | ✓         | Pending order at specified price               |
| `STOP_MARKET`      | ✓         | Stop order triggered at specified price        |
| `STOP_LIMIT`       | ✓         | Stop order that becomes limit order when triggered |
| `MARKET_TO_LIMIT`  | -         | Not supported by MT5                           |
| `TRAILING_STOP`    | -         | Not yet implemented                            |

### Time in force

| TIF          | Supported | Notes                                    |
|--------------|-----------|------------------------------------------|
| `GTC`        | ✓         | Good Till Cancel (default)               |
| `DAY`        | ✓         | Valid until end of trading day           |
| `IOC`        | ✓         | Immediate Or Cancel                      |
| `FOK`        | ✓         | Fill Or Kill                             |

### Execution instructions

| Instruction   | Supported | Notes                                           |
|---------------|-----------|------------------------------------------------|
| `post_only`   | -         | Not supported by MT5 API                       |
| `reduce_only` | -         | Not supported by MT5 API                       |

### Position mode

MT5 uses **netting mode** by default, meaning:
- Only one position per instrument at a time
- Opposite orders reduce or close existing positions
- Net position quantity is tracked

:::note
Hedging mode (multiple positions per instrument) is available in MT5 but not yet supported by this adapter.
:::

## Configuration

### Basic configuration

Here's a minimal configuration for connecting to MT5:

```python
from nautilus_trader.adapters.mt5.config import MT5DataClientConfig
from nautilus_trader.adapters.mt5.config import MT5ExecClientConfig
from nautilus_trader.config import TradingNodeConfig

config = TradingNodeConfig(
    data_clients={
        "MT5": MT5DataClientConfig(
            host="localhost",
            live_port=2203,
            stream_port=2204,
            sys_port=2201,
        ),
    },
    exec_clients={
        "MT5": MT5ExecClientConfig(
            host="localhost",
            stream_port=2204,
            sys_port=2201,
            account_id="123456",  # Your MT5 account number
        ),
    },
)
```

### Configuration options

#### MT5DataClientConfig

| Parameter                         | Type          | Default       | Description                                          |
|-----------------------------------|---------------|---------------|------------------------------------------------------|
| `host`                            | str           | "localhost"   | ZeroMQ host address                                  |
| `live_port`                       | int           | 2203          | Port for live tick data                              |
| `stream_port`                     | int           | 2204          | Port for order/position updates                      |
| `sys_port`                        | int           | 2201          | Port for commands and queries                        |
| `account_id`                      | str \| None   | None          | MT5 account number (optional for data client)        |
| `update_instruments_interval_mins`| int \| None   | 60            | Interval to refresh instrument definitions (minutes) |

#### MT5ExecClientConfig

| Parameter      | Type        | Default     | Description                              |
|----------------|-------------|-------------|------------------------------------------|
| `host`         | str         | "localhost" | ZeroMQ host address                      |
| `stream_port`  | int         | 2204        | Port for order/position updates          |
| `sys_port`     | int         | 2201        | Port for commands and queries            |
| `account_id`   | str \| None | None        | MT5 account number (required)            |
| `max_retries`  | int \| None | 3           | Maximum retry attempts for failed orders |
| `retry_delay_secs` | int \| None | 1       | Delay between retries (seconds)          |

## Live trading example

Below is a complete example of setting up a live trading node with the MT5 adapter:

```python
from decimal import Decimal

from nautilus_trader.adapters.mt5.config import MT5DataClientConfig
from nautilus_trader.adapters.mt5.config import MT5ExecClientConfig
from nautilus_trader.config import InstrumentProviderConfig
from nautilus_trader.config import LoggingConfig
from nautilus_trader.config import TradingNodeConfig
from nautilus_trader.live.node import TradingNode
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.identifiers import TraderId


# Configure MT5 data client
data_config = MT5DataClientConfig(
    host="localhost",
    live_port=2203,
    stream_port=2204,
    sys_port=2201,
    instrument_provider=InstrumentProviderConfig(load_all=True),
)

# Configure MT5 execution client
exec_config = MT5ExecClientConfig(
    host="localhost",
    stream_port=2204,
    sys_port=2201,
    account_id="123456",  # Your MT5 account number
)

# Configure trading node
config = TradingNodeConfig(
    trader_id=TraderId("TESTER-001"),
    logging=LoggingConfig(log_level="INFO"),
    data_clients={
        "MT5": data_config,
    },
    exec_clients={
        "MT5": exec_config,
    },
    timeout_connection=30.0,
    timeout_reconciliation=10.0,
    timeout_portfolio=10.0,
    timeout_disconnection=10.0,
)

# Create and start trading node
node = TradingNode(config=config)
node.start()

# Subscribe to market data
eurusd = InstrumentId.from_str("EURUSD.MT5")
node.subscribe(
    data_type="QuoteTick",
    client_id="MT5",
    instrument_id=eurusd,
)

# Keep node running
try:
    node.run()  # Blocks until interrupted
finally:
    node.stop()
    node.dispose()
```

## Strategy integration

To trade on MT5 from a strategy:

```python
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.orders import MarketOrder
from nautilus_trader.trading.strategy import Strategy


class MT5Strategy(Strategy):
    def on_start(self):
        # Subscribe to EURUSD quotes
        self.instrument_id = InstrumentId.from_str("EURUSD.MT5")
        self.subscribe_quote_ticks(self.instrument_id)

    def on_quote_tick(self, tick):
        # Example: Buy when bid/ask spread is tight
        spread = tick.ask_price - tick.bid_price

        if spread < 0.0001:  # Tight spread
            # Submit market buy order
            order = self.order_factory.market(
                instrument_id=self.instrument_id,
                order_side=OrderSide.BUY,
                quantity=self.instrument.make_qty(0.01),  # 0.01 lots
            )
            self.submit_order(order)
```

## Troubleshooting

### Connection issues

**Problem**: `Timeout waiting for connection after 10.0s`

**Solutions**:
1. Verify MT5 Terminal is running and logged in
2. Check JsonAPI.mq5 Expert Advisor is active in MT5
3. Confirm ZeroMQ ports are not blocked by firewall
4. Check Docker container logs: `docker logs mt5-zeromq`

### No market data

**Problem**: Subscriptions succeed but no ticks received

**Solutions**:
1. Verify the symbol exists in Market Watch (right-click → Show All)
2. Check that the market is open for trading
3. Ensure your broker provides data for the instrument
4. Review MT5 Experts tab for JsonAPI.mq5 logs

### Order rejections

**Problem**: Orders rejected with error codes

**Common MT5 error codes**:
- `10006`: Request rejected (check trading permissions)
- `10018`: Market closed (outside trading hours)
- `10019`: Insufficient funds (check margin requirements)
- `10027`: Symbol not found (check symbol spelling)

**Solutions**:
1. Verify trading is enabled in MT5 settings
2. Check account balance and margin requirements
3. Confirm symbol is tradeable (not disabled)
4. Review broker-specific trading restrictions

### Instrument not found

**Problem**: `Cannot find instrument for SYMBOL.MT5`

**Solutions**:
1. Right-click Market Watch in MT5 → Show All
2. Add the symbol to Market Watch manually
3. Wait for instrument provider to refresh (default: 60 minutes)
4. Check symbol spelling matches MT5 exactly

## Architecture

The MT5 adapter uses a unique architecture optimized for low-latency trading:

### ZeroMQ Bridge

```
┌─────────────────┐
│  MT5 Terminal   │  MetaTrader 5 with your broker
│  (JsonAPI.mq5)  │
└────────┬────────┘
         │ ZeroMQ (3 sockets)
         │
┌────────▼─────────────────────────────┐
│  Mt5Client (Rust)                    │
│  - Dedicated OS thread for ZMQ       │
│  - Non-blocking message polling      │
│  - High-performance JSON parsing     │
└────────┬─────────────────────────────┘
         │ PyO3 (Python bindings)
         │
┌────────▼─────────────────────────────┐
│  Python Layer                        │
│  - MT5DataClient (market data)       │
│  - MT5ExecutionClient (orders)       │
└──────────────────────────────────────┘
```

### Threading model

The adapter uses a **dedicated thread pattern** for optimal performance:

1. **ZMQ Thread** (OS thread): Polls ZeroMQ sockets non-blocking, never blocks
2. **Tokio Runtime** (async): Processes parsed messages asynchronously
3. **Python Callbacks**: Receives data via PyO3 bridges

This design ensures:
- No GIL contention for data reception
- Zero-copy data transfer where possible
- Microsecond-level latency for tick processing

### Data flow

```
MT5 Terminal
    ↓ (ZeroMQ JSON)
Rust ZMQ Thread (dedicated OS thread)
    ↓ (parse to Nautilus types)
Tokio Channel (mpsc)
    ↓ (PyCapsule conversion)
Python Callback (_handle_msg)
    ↓
NautilusTrader Message Bus
    ↓
Strategy / Cache / Data Engine
```

## API Reference

For detailed API documentation, see the [MT5 API Reference](../api_reference/adapters/mt5.md).

## Limitations

Current limitations of the MT5 adapter:

1. **Position mode**: Only netting mode supported (no hedging mode)
2. **Historical data**: Bar data requests not yet implemented
3. **Options trading**: Not supported
4. **Trailing stops**: Not yet implemented
5. **Order modification**: Not yet implemented (cancel and replace required)

Contributions to address these limitations are welcome via pull requests.

## Further information

- [MetaTrader 5 Official Website](https://www.metatrader5.com/)
- [MQL5 Documentation](https://www.mql5.com/en/docs)
- [ZeroMQ Guide](https://zeromq.org/get-started/)
- [MT5-ZeroMQ Bridge Repository](https://github.com/your-repo/MT5-Docker)
