# Adapters

## Introduction

This developer guide provides specifications and instructions on how to develop an integration adapter for the NautilusTrader platform. Adapters provide connectivity to trading venues and data providers—translating raw venue APIs into Nautilus's unified interface and normalized domain model.

## Structure of an adapter

NautilusTrader adapters follow a layered architecture pattern with:

- **Rust core** for networking clients and performance-critical operations.
- **Python layer** for integrating Rust clients into the platform's data and execution engines.

Good references for standardized patterns are currently:

- OKX
- BitMEX
- Bybit

### Rust core (`crates/adapters/your_adapter/`)

The Rust layer handles:

- **HTTP client**: Raw API communication, request signing, rate limiting.
- **WebSocket client**: Low-latency streaming connections, message parsing.
- **Parsing**: Fast conversion of venue data to Nautilus domain models.
- **Python bindings**: PyO3 exports to make Rust functionality available to Python.

Typical Rust structure:

```text
crates/adapters/your_adapter/
├── src/
│   ├── common/              # Shared types and utilities
│   │   ├── consts.rs        # Venue constants / broker IDs
│   │   ├── credential.rs    # API key storage and signing helpers
│   │   ├── enums.rs         # Venue enums mirrored in REST/WS payloads
│   │   ├── models.rs        # Shared model types
│   │   ├── parse.rs         # Shared parsing helpers
│   │   ├── urls.rs          # Environment & product aware base-url resolvers
│   │   └── testing.rs       # Fixtures reused across unit tests
│   ├── data/                # Data client (Rust-native, optional)
│   │   └── mod.rs           # Data client implementation
│   ├── execution/           # Execution client (Rust-native, optional)
│   │   └── mod.rs           # Execution client implementation
│   ├── http/                # HTTP client implementation
│   │   ├── client.rs        # HTTP client with authentication
│   │   ├── error.rs         # HTTP-specific error types
│   │   ├── models.rs        # Structs for REST payloads
│   │   ├── parse.rs         # Response parsing functions
│   │   └── query.rs         # Request and query builders
│   ├── websocket/           # WebSocket implementation
│   │   ├── client.rs        # WebSocket client
│   │   ├── enums.rs         # WebSocket-specific enums
│   │   ├── error.rs         # WebSocket-specific error types
│   │   ├── handler.rs       # Message handler / feed handler
│   │   ├── messages.rs      # Structs for stream payloads
│   │   └── parse.rs         # Message parsing functions
│   ├── python/              # PyO3 Python bindings
│   │   ├── enums.rs         # Python-exposed enums
│   │   ├── http.rs          # Python HTTP client bindings
│   │   ├── urls.rs          # Python URL helpers
│   │   ├── websocket.rs     # Python WebSocket client bindings
│   │   └── mod.rs           # Module exports
│   ├── config.rs            # Configuration structures
│   ├── error.rs             # Adapter-level error types
│   ├── factories.rs         # Factory functions (optional)
│   └── lib.rs               # Library entry point
├── tests/                   # Integration tests with mock servers
│   ├── data.rs              # Data client integration tests
│   ├── execution.rs         # Execution client integration tests
│   ├── http.rs              # HTTP client integration tests
│   └── websocket.rs         # WebSocket client integration tests
└── test_data/               # Canonical venue payloads
```

### Python layer (`nautilus_trader/adapters/your_adapter`)

The Python layer provides the integration interface through these components:

1. **Instrument Provider**: Supplies instrument definitions via `InstrumentProvider`.
2. **Data Client**: Handles market data feeds and historical data requests via `LiveDataClient` and `LiveMarketDataClient`.
3. **Execution Client**: Manages order execution via `LiveExecutionClient`.
4. **Factories**: Converts venue-specific data to Nautilus domain models.
5. **Configuration**: User-facing configuration classes for client settings.

Typical Python structure:

```text
nautilus_trader/adapters/your_adapter/
├── config.py     # Configuration classes
├── constants.py  # Adapter constants
├── data.py       # LiveDataClient/LiveMarketDataClient
├── execution.py  # LiveExecutionClient
├── factories.py  # Instrument factories
├── providers.py  # InstrumentProvider
└── __init__.py   # Package initialization
```

## Adapter implementation sequence

This section outlines the recommended order for implementing an adapter. The sequence follows a dependency-driven approach where each phase builds upon the previous ones. Adapters use a Rust-first architecture—implement the Rust core before any Python layer.

### Phase 1: Rust core infrastructure

Build the low-level networking and parsing foundation.

| Step | Component | Description |
|------|-----------|-------------|
| 1.1 | HTTP error types | Define HTTP-specific error enum with retryable/non-retryable variants (`http/error.rs`). |
| 1.2 | HTTP client | Implement credentials, request signing, rate limiting, and retry logic. |
| 1.3 | HTTP API models | Define request/response structs for REST endpoints (`http/models.rs`, `http/query.rs`). |
| 1.4 | HTTP parsing | Convert venue responses to Nautilus domain models (`http/parse.rs`, `common/parse.rs`). |
| 1.5 | WebSocket error types | Define WebSocket-specific error enum (`websocket/error.rs`). |
| 1.6 | WebSocket client | Implement connection lifecycle, authentication, heartbeat, and reconnection. |
| 1.7 | WebSocket messages | Define streaming payload types (`websocket/messages.rs`). |
| 1.8 | WebSocket parsing | Convert stream messages to Nautilus domain models (`websocket/parse.rs`). |
| 1.9 | Python bindings | Expose Rust functionality via PyO3 (`python/mod.rs`). |

**Milestone**: Rust crate compiles, unit tests pass, HTTP/WebSocket clients can authenticate and stream/request raw data.

### Phase 2: Instrument definitions

Instruments are the foundation—both data and execution clients depend on them.

| Step | Component | Description |
|------|-----------|-------------|
| 2.1 | Instrument parsing | Parse venue instrument definitions into Nautilus types (spot, perpetual, future, option). |
| 2.2 | Instrument provider | Implement `InstrumentProvider` to load, filter, and cache instruments. |
| 2.3 | Symbol mapping | Handle venue-specific symbol formats and Nautilus `InstrumentId` conversion. |

**Milestone**: `InstrumentProvider.load_all_async()` returns valid Nautilus instruments.

### Phase 3: Market data

Build data subscriptions and historical data requests.

| Step | Component | Description |
|------|-----------|-------------|
| 3.1 | Public WebSocket streams | Subscribe to order books, trades, tickers, and other public channels. |
| 3.2 | Historical data requests | Fetch historical bars, trades, and order book snapshots via HTTP. |
| 3.3 | Data client (Python) | Implement `LiveDataClient` or `LiveMarketDataClient` wiring Rust clients to the data engine. |

**Milestone**: Data client connects, subscribes to instruments, and emits market data to the platform.

### Phase 4: Order execution

Build order management and account state.

| Step | Component | Description |
|------|-----------|-------------|
| 4.1 | Private WebSocket streams | Subscribe to order updates, fills, positions, and account balance changes. |
| 4.2 | Basic order submission | Implement market and limit orders via HTTP or WebSocket. |
| 4.3 | Order modification/cancel | Implement order amendment and cancellation. |
| 4.4 | Execution client (Python) | Implement `LiveExecutionClient` wiring Rust clients to the execution engine. |
| 4.5 | Execution reconciliation | Generate order, fill, and position status reports for startup reconciliation. |

**Milestone**: Execution client submits orders, receives fills, and reconciles state on connect.

### Phase 5: Advanced features

Extend coverage based on venue capabilities.

| Step | Component | Description |
|------|-----------|-------------|
| 5.1 | Advanced order types | Conditional orders, stop-loss, take-profit, trailing stops, iceberg, etc. |
| 5.2 | Batch operations | Batch order submission, batch cancellation, mass cancel. |
| 5.3 | Venue-specific features | Options chains, funding rates, liquidations, or other venue-specific data. |

### Phase 6: Configuration and factories

Wire everything together for production usage.

| Step | Component | Description |
|------|-----------|-------------|
| 6.1 | Configuration classes | Create `LiveDataClientConfig` and `LiveExecClientConfig` subclasses. |
| 6.2 | Factory functions | Implement factory functions to instantiate clients from configuration. |
| 6.3 | Environment variables | Support credential resolution from environment variables. |

### Phase 7: Testing and documentation

Validate the integration and document usage.

| Step | Component | Description |
|------|-----------|-------------|
| 7.1 | Rust unit tests | Test parsers, signing helpers, and business logic in `#[cfg(test)]` blocks. |
| 7.2 | Rust integration tests | Test HTTP/WebSocket clients against mock Axum servers in `tests/`. |
| 7.3 | Python integration tests | Test data/execution clients in `tests/integration_tests/adapters/<adapter>/`. |
| 7.4 | Example scripts | Provide runnable examples demonstrating data subscription and order execution. |

## Rust adapter patterns

### Common code (`common/`)

Group venue constants, credential helpers, enums, and reusable parsers under `src/common`. Adapters such as OKX keep submodules like `consts`, `credential`, `enums`, and `urls` alongside a `testing` module for fixtures, providing a single place for cross-cutting pieces.

### Configurations (`config.rs`)

Expose typed config structs in `src/config.rs` so Python callers toggle venue-specific behaviour. Keep defaults minimal and delegate URL selection to helpers in `common::urls`.

### Error taxonomy (`error.rs`)

Centralise HTTP/WebSocket failure handling in an adapter-specific error enum. Separate retryable, non-retryable, and fatal variants while embedding the original transport error.

### Python exports (`python/mod.rs`)

Mirror the Rust surface area through PyO3 modules by re-exporting clients, enums, and helper functions.

### Python bindings (`python/`)

Expose Rust functionality to Python through PyO3. Mark venue-specific structs that need Python access with `#[pyclass]` and implement `#[pymethods]` blocks with `#[getter]` attributes for field access.

For async methods in the HTTP client, use `pyo3_async_runtimes::tokio::future_into_py` to convert Rust futures into Python awaitables.

Follow the pattern: prefixing Python-facing methods with `py_*` in Rust while using `#[pyo3(name = "method_name")]` to expose them without the prefix.

### Type qualification

Adapter-specific types (enums, structs) and Nautilus domain types should not be fully qualified. Import them at the module level and use short names. Only fully qualify types from `anyhow` and `tokio` to avoid ambiguity.

### String interning

Use `ustr::Ustr` for any non-unique strings the platform stores repeatedly (venues, symbols, instrument IDs) to minimise allocations and comparisons.

### Instrument cache standardization

All clients that cache instruments must implement three methods with standardized names: `cache_instruments()` (plural, bulk replace), `cache_instrument()` (singular, upsert), and `get_instrument()` (retrieve by symbol).

## HTTP client patterns

### Client structure

The architecture consists of two complementary clients:

1. **Raw client** (`MyRawHttpClient`) - Low-level API methods matching venue endpoints.
2. **Domain client** (`MyHttpClient`) - High-level methods using Nautilus domain types.

Use `nautilus_network::http::HttpClient` instead of `reqwest::Client` directly - this provides rate limiting, retry logic, and consistent error handling.

### Query parameter builders

Use the `derive_builder` crate with proper defaults and ergonomic Option handling.

### Request signing and authentication

Keep signing logic in a `Credential` struct under `common/credential.rs`. Store API keys using `Ustr` for efficient comparison, secrets in `Box<[u8]>` with `#[zeroize]`.

### Environment variable conventions

Adapters support loading API credentials from environment variables when not provided directly.

**Naming conventions:**

| Environment | API Key Variable | API Secret Variable |
|-------------|------------------|---------------------|
| Mainnet/Live | `{VENUE}_API_KEY` | `{VENUE}_API_SECRET` |
| Testnet | `{VENUE}_TESTNET_API_KEY` | `{VENUE}_TESTNET_API_SECRET` |
| Demo | `{VENUE}_DEMO_API_KEY` | `{VENUE}_DEMO_API_SECRET` |

## WebSocket client patterns

### Client structure

WebSocket adapters use a **two-layer architecture**:

- **Outer client** (`{Venue}WebSocketClient`): Orchestrates connection lifecycle, authentication, subscriptions.
- **Inner handler** (`{Venue}WsFeedHandler`): Runs in dedicated Tokio task as stateless I/O boundary.

### Authentication

Authentication state is managed through events. Handler processes `Login` response → returns `NautilusWsMessage::Authenticated` immediately.

### Subscription management

Use shared `SubscriptionState` pattern. Track user intent in client, server confirmations in handler.

### Reconnection logic

On reconnection, restore authentication and subscriptions:
1. Receive `NautilusWsMessage::Reconnected` from handler.
2. If authenticated: Re-authenticate and wait for confirmation.
3. Restore all tracked subscriptions via handler commands.

### Instrument cache architecture

WebSocket clients that cache instruments use a **dual-tier pattern** for performance:

- **Outer client**: `Arc<DashMap<Ustr, InstrumentAny>>` provides thread-safe cache for concurrent Python access.
- **Inner handler**: `AHashMap<Ustr, InstrumentAny>` provides local cache for single-threaded hot path during message parsing.
- **Command channel**: `tokio::sync::mpsc::unbounded_channel` synchronizes updates from outer to inner.

## Testing

See the [Testing](testing.md) section for detailed test organization guidelines.
