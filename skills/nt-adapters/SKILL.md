---
name: nt-adapters
description: "Use when working with exchange or data provider adapters, HTTP/WebSocket clients, instrument providers, or venue integration in NautilusTrader."
---

# nt-adapters

## What This Skill Covers

NautilusTrader **adapter domain** — exchange/data provider integrations following a layered architecture with Rust core for networking and Python layer for platform integration.

**Python modules**: `adapters/*` (16 adapters), `adapters/_template/`
**Rust crates**: All 16 `adapters/*` crates, `nautilus_network`, `nautilus_cryptography`

**Supported adapters**: Binance, Bybit, OKX, Kraken, Deribit, dYdX, Hyperliquid, BitMEX, Interactive Brokers, Databento, Tardis, Betfair, Polymarket, Architect (AX), Blockchain, Shioaji

## When To Use

- Configuring an existing adapter for live trading
- Building a new exchange or data provider adapter
- Customizing instrument providers
- Working with HTTP/WebSocket client patterns
- Understanding adapter testing specifications
- Venue-specific data parsing or execution logic

## When NOT To Use

- **Live node system config** → use `nt-live`
- **Strategy logic** → use `nt-trading`
- **Data persistence** → use `nt-data`
- **Domain model types** → use `nt-model`
- **Testing spec details** → use `nt-testing` (DataTesterConfig/ExecTesterConfig)

## Adapter Architecture

Adapters follow a layered architecture:

- **Rust core** — networking clients, parsing, rate limiting, request signing
- **Python layer** — integration with platform's data and execution engines

### Rust Core Structure

```
crates/adapters/your_adapter/
├── src/
│   ├── common/              # Shared types and utilities
│   │   ├── consts.rs        # Venue constants / broker IDs
│   │   ├── credential.rs    # API key storage and signing helpers
│   │   ├── enums.rs         # Venue enums mirrored in REST/WS payloads
│   │   ├── error.rs         # Adapter-level error aggregation
│   │   ├── models.rs        # Shared model types
│   │   ├── parse.rs         # Shared parsing helpers
│   │   ├── retry.rs         # Retry classification
│   │   ├── urls.rs          # Environment & product aware base-url resolvers
│   │   └── testing.rs       # Fixtures reused across unit tests
│   ├── http/                # HTTP client implementation
│   │   ├── client.rs        # HTTP client with authentication
│   │   ├── error.rs         # HTTP-specific error types
│   │   ├── models.rs        # Structs for REST payloads
│   │   ├── parse.rs         # Response parsing functions
│   │   └── query.rs         # Request and query builders
│   ├── websocket/           # WebSocket implementation
│   │   ├── client.rs        # WebSocket client
│   │   ├── dispatch.rs      # Execution event dispatch and order routing
│   │   ├── enums.rs         # WebSocket-specific enums
│   │   ├── error.rs         # WebSocket-specific error types
│   │   ├── messages.rs      # Streaming payload types
│   │   └── parse.rs         # Stream message parsing
│   ├── python/              # PyO3 bindings
│   │   ├── mod.rs           # Module exports
│   │   └── ...              # Per-component bindings
│   ├── config.rs            # Adapter configuration (Python-facing)
│   ├── factories.rs         # Client factories
│   └── lib.rs               # Crate root
├── tests/                   # Integration tests
└── Cargo.toml
```

### Python Layer Structure

```
nautilus_trader/adapters/your_adapter/
├── __init__.py
├── config.py                # DataClientConfig, ExecClientConfig, InstrumentProviderConfig
├── factories.py             # DataClientFactory, ExecClientFactory
├── providers.py             # InstrumentProvider
├── data.py                  # DataClient / MarketDataClient
├── execution.py             # ExecutionClient
└── http/                    # HTTP client wrapper (if needed)
```

## Adapter Implementation Sequence

Follow this dependency-driven order. Each phase builds on the previous one. **Implement the Rust core before any Python layer.**

### Phase 1: Rust Core Infrastructure

| Step | Component | Description |
|------|-----------|-------------|
| 1.1 | HTTP error types | Define HTTP-specific error enum with retryable/non-retryable variants |
| 1.2 | HTTP client | Implement credentials, request signing, rate limiting, retry logic |
| 1.3 | HTTP API models | Define request/response structs for REST endpoints |
| 1.4 | HTTP parsing | Convert venue responses to Nautilus domain models |
| 1.5 | WebSocket error types | Define WebSocket-specific error enum |
| 1.6 | WebSocket client | Connection lifecycle, authentication, heartbeat, reconnection |
| 1.7 | WebSocket messages | Define streaming payload types |
| 1.8 | WebSocket parsing | Convert stream messages to Nautilus domain models |
| 1.9 | Python bindings | Expose Rust functionality via PyO3 |

**Milestone**: Rust crate compiles, unit tests pass, HTTP/WebSocket clients can authenticate and stream/request raw data.

### Phase 2: Instrument Definitions

| Step | Component | Description |
|------|-----------|-------------|
| 2.1 | Instrument parsing | Parse venue instrument definitions into Nautilus types |
| 2.2 | Instrument provider | Implement `InstrumentProvider` to load, filter, and cache instruments |
| 2.3 | Symbol mapping | Handle venue-specific symbol formats and Nautilus `InstrumentId` conversion |

### Phase 3: Market Data

| Step | Component | Description |
|------|-----------|-------------|
| 3.1 | Data subscriptions | Subscribe to trade ticks, quote ticks, bars, order book updates |
| 3.2 | Historical data | Request historical bars, trades, quotes via REST |
| 3.3 | Order book management | Maintain L2/L3 order book from delta stream |

### Phase 4: Order Execution

| Step | Component | Description |
|------|-----------|-------------|
| 4.1 | Order submission | Submit market, limit, stop orders via REST/WebSocket |
| 4.2 | Order management | Cancel, modify, track order state |
| 4.3 | Fill handling | Process trade reports, update positions |

### Phase 5: Advanced Features

Account management, position tracking, funding rate handling, etc.

### Phase 6: Configuration & Factories

Wire everything into the platform via config types and factory patterns.

### Phase 7: Testing & Documentation

Data testing (DataTesterConfig), execution testing (ExecTesterConfig), documentation.

## Python Usage

### Configure Existing Adapter

```python
from nautilus_trader.adapters.binance.config import BinanceDataClientConfig, BinanceExecClientConfig

data_config = BinanceDataClientConfig(
    api_key="...",
    api_secret="...",
    account_type=BinanceAccountType.USDT_FUTURE,
)

exec_config = BinanceExecClientConfig(
    api_key="...",
    api_secret="...",
    account_type=BinanceAccountType.USDT_FUTURE,
)
```

### Use InstrumentProvider

```python
# Instrument discovery happens automatically when adapter connects
# Access instruments via cache:
instruments = self.cache.instruments(venue=Venue("BINANCE"))
instrument = self.cache.instrument(InstrumentId.from_str("ETHUSDT-PERP.BINANCE"))
```

### Adapter Configuration Pattern

Each adapter follows the same config pattern:
- `{Adapter}DataClientConfig` — data feed configuration
- `{Adapter}ExecClientConfig` — execution configuration
- `{Adapter}InstrumentProviderConfig` — instrument discovery settings

## Python Extension

### Customize Instrument Provider

```python
from nautilus_trader.adapters.binance.providers import BinanceInstrumentProvider

class MyInstrumentProvider(BinanceInstrumentProvider):
    async def load_all_async(self, filters=None):
        await super().load_all_async(filters)
        # Add custom instrument filtering/transformation
```

## Rust Usage

### Using Adapters with Rust LiveNode

```rust
use nautilus_live::node::LiveNode;
use nautilus_model::identifiers::Venue;

let node = LiveNode::builder()
    .add_adapter(MyAdapterConfig::default())
    .add_strategy(MyStrategy::new(config))
    .build()?;

node.run().await?;
```

### Adapter Factory Pattern (Rust)

Each adapter implements a factory trait that creates data and execution clients:

```rust
pub trait AdapterFactory {
    fn create_data_client(&self, config: &AdapterConfig) -> Result<Box<dyn DataClient>>;
    fn create_exec_client(&self, config: &AdapterConfig) -> Result<Box<dyn ExecClient>>;
}
```

### Available Rust Adapters

All 16 adapters have Rust implementations with varying feature completeness. Check `crates/adapters/` for available adapters.

### Environment Variables

```bash
# Per-adapter credentials follow this pattern
{VENUE}_API_KEY=xxx
{VENUE}_API_SECRET=xxx
{VENUE}_PASSPHRASE=xxx  # OKX, Bybit
```

## Rust Extension

### Build New Adapter in Rust

Follow the implementation sequence above. Key patterns:

**HTTP Client**:
```rust
pub struct HttpClient {
    client: reqwest::Client,
    credential: Credential,
    rate_limit: RateLimit,
}

impl HttpClient {
    pub async fn sign_request(&self, method: Method, path: &str, body: &str) -> Request { ... }
}
```

**WebSocket Client**:
```rust
pub struct WebSocketClient {
    url: Url,
    credential: Credential,
    subscription_state: Shared<SubscriptionState>,
}
```

**Message Routing**: Follow the `raw → msg → out` naming convention:
- `raw`: Raw bytes from WebSocket
- `msg`: Parsed venue-specific message
- `out`: Nautilus domain model

### Factory Implementation

```rust
// crates/adapters/your_adapter/src/factories.rs
pub fn register(config: YourAdapterConfig) -> AdapterRegistry {
    AdapterRegistry::new()
        .data_client(YourDataClientFactory::new(config.clone()))
        .exec_client(YourExecClientFactory::new(config))
}
```

### PyO3 Bindings (Optional)

```rust
// crates/adapters/your_adapter/src/python/mod.rs
#[pymodule]
fn your_adapter(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<YourAdapterConfig>()?;
    m.add_function(wrap_pyfunction!(create_client, m)?)?;
    Ok(())
}
```

## Rust Adapter Patterns

### Common Code (`common/`)

The `common/` directory contains shared types used by both HTTP and WebSocket:

- `consts.rs` — Venue constants (broker IDs, default timeouts)
- `credential.rs` — API key storage, signing helpers
- `enums.rs` — Venue enums (order types, time-in-force, account types)
- `error.rs` — Adapter-level error aggregation
- `parse.rs` — Shared parsing helpers (timestamp conversion, string normalization)
- `retry.rs` — Retry classification (which errors are retryable)
- `urls.rs` — Environment-aware URL resolution (testnet vs mainnet)

### Symbol Normalization

```rust
// common/symbol.rs
pub fn normalize_symbol(raw: &str) -> String {
    // Convert venue-specific symbol format to Nautilus convention
    raw.replace("USDT", "-PERP")  // e.g., BTCUSDT → BTC-PERP
}
```

### Configuration Builder Pattern

```rust
// config.rs follows builder + default pattern
#[derive(Debug, Clone)]
pub struct YourAdapterConfig {
    pub api_key: Option<String>,
    pub api_secret: Option<String>,
    pub base_url: Option<String>,
    pub testnet: bool,
}

impl Default for YourAdapterConfig {
    fn default() -> Self { ... }
}
```

**Field type rules**:
- Required fields: `String` (no `Option`)
- Optional fields: `Option<String>`, default via `Default`
- Python constructors: Always `#[new]` with defaults

### HTTP Client Patterns

**Parser functions**: Each HTTP endpoint has a dedicated parser:
```rust
pub fn parse_instrument(response: &str) -> Result<Vec<InstrumentAny>> { ... }
pub fn parse_order_response(response: &str) -> Result<Order> { ... }
```

**Method naming**: `{verb}_{resource}` — e.g., `get_instruments`, `post_order`, `delete_order`

**Query builders**: Separate query parameter construction:
```rust
pub struct GetOrdersQuery {
    pub symbol: Option<String>,
    pub order_id: Option<u64>,
    pub limit: Option<u32>,
}
```

### WebSocket Client Patterns

**Connection state tracking**:
```rust
pub struct SubscriptionState {
    subscribed: HashSet<String>,
    pending: HashSet<String>,
}
```

**Message routing**: `WsDispatchState` maps incoming messages to handlers
**Backpressure**: Use bounded channels, drop stale messages
**Split architectures**: Separate WebSocket connections for data vs execution

### Task Management

```rust
// Use spawn_task for async work — never block_on
tokio::spawn(async move { ... });

// Graceful shutdown via CancellationToken
let token = CancellationToken::new();
tokio::spawn(async move {
    tokio::select! {
        _ = work() => {},
        _ = token.cancelled() => {},
    }
});
```

**Critical**: Never use `block_on` in trait method implementations.

## Key Conventions

### Adapter Testing

- Use DataTesterConfig for data flow validation (see `nt-testing`)
- Use ExecTesterConfig for execution lifecycle testing (see `nt-testing`)
- Rust unit tests in `#[cfg(test)] mod tests` within source files
- Integration tests in `tests/` directory

### Adapter Naming

- Crate: `nautilus-{venue}` (e.g., `nautilus-binance`)
- Config: `{Venue}Config`, `{Venue}DataClientConfig`, `{Venue}ExecClientConfig`
- Client: `{Venue}HttpClient`, `{Venue}WebSocketClient`
- Factory: `{Venue}DataClientFactory`, `{Venue}ExecClientFactory`

### Factory Pattern

All adapters use factory registration:
```python
# Python factories
config.adapters.live.add("BINANCE", BinanceLiveDataClientFactory, BinanceLiveExecClientFactory)
```

### Channel Naming

Follow `raw → msg → out` convention:
- `raw`: Raw bytes from network
- `msg`: Parsed venue-specific message type
- `out`: Nautilus domain model

### Type Qualification

Use fully qualified types in adapter code for clarity:
```rust
nautilus_model::identifiers::InstrumentId  // not just InstrumentId
```

### String Interning

For frequently repeated strings (symbols, venues), use string interning for performance.

### Testing Helpers

Every adapter provides `common/testing.rs` with fixture helpers:
```rust
pub fn test_instrument_id() -> InstrumentId { ... }
pub fn test_credential() -> Credential { ... }
```

### Documentation

Rust adapter code must include:
- `///` doc comments on all public types and functions
- `//!` module-level docs
- Examples in doc comments when non-trivial

## References

- `references/guides/official_adapter_spec.md` — Full official adapter development spec (118KB)
- `references/api/` — Per-adapter API documentation
- `references/examples/` — Per-adapter runnable examples
- `references/integrations/` — Per-adapter integration docs
