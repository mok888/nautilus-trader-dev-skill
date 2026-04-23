# Stage 12: Adapter Development

## Goal

Build a complete adapter for a new exchange or data provider, following NautilusTrader's official adapter specification.

## Prerequisites

- Stage 11 completed (can write all types of tests)
- Deep understanding of Rust async programming
- Familiarity with WebSocket and HTTP client patterns
- Understanding of the NT domain model (nt-model)

## Concepts

### Adapter Architecture

Adapters follow a layered architecture:
- **Rust core** — HTTP/WebSocket clients, parsing, rate limiting
- **Python layer** — integration with NT data and execution engines

### Implementation Sequence (7 Phases)

| Phase | Focus | Key Files |
|-------|-------|-----------|
| 1 | Rust core infrastructure | HTTP client, WebSocket client, error types, parsing |
| 2 | Instrument definitions | Instrument parsing, provider, symbol mapping |
| 3 | Market data | Subscriptions, historical data, order book management |
| 4 | Order execution | Order submission, management, fill handling |
| 5 | Advanced features | Account management, position tracking |
| 6 | Configuration & factories | Config types, factory registration |
| 7 | Testing & documentation | DataTesterConfig, ExecTesterConfig, docs |

### Directory Structure

```
crates/adapters/your_adapter/
├── src/
│   ├── common/       # Shared types, credential, enums, parsing
│   ├── http/         # HTTP client, models, parsing, query
│   ├── websocket/    # WS client, messages, parsing, dispatch
│   ├── python/       # PyO3 bindings
│   ├── config.rs     # Adapter configuration
│   ├── factories.rs  # Client factories
│   └── lib.rs        # Crate root
├── tests/            # Integration tests
└── Cargo.toml
```

### Key Patterns

**Message routing**: `raw → msg → out` naming convention
- `raw`: Raw bytes from WebSocket
- `msg`: Parsed venue-specific message
- `out`: Nautilus domain model

**HTTP client**:
```rust
pub struct HttpClient {
    client: reqwest::Client,
    credential: Credential,
    rate_limit: RateLimit,
}
```

**WebSocket client**:
```rust
pub struct WebSocketClient {
    url: Url,
    credential: Credential,
    subscription_state: Shared<SubscriptionState>,
}
```

**Config pattern**: `{Venue}DataClientConfig`, `{Venue}ExecClientConfig`, `{Venue}InstrumentProviderConfig`

### Testing Your Adapter

Use the official testing specs:

```python
# Data testing
DataTesterConfig(client_id, instrument_ids).with_subscribe_trades()
DataTesterConfig(client_id, instrument_ids).with_subscribe_book_deltas(book_type=BookType.L2_MBP)

# Execution testing
ExecTesterConfig(strategy_id, instrument_id, client_id, order_qty).with_enable_limit_buys()
ExecTesterConfig(strategy_id, instrument_id, client_id, order_qty).with_test_reject_post_only()
```

## Exercises

1. **Study an existing adapter**: Read through `crates/adapters/binance/` and trace the data flow
2. **Implement Phase 1**: Create HTTP error types, client, and basic parsing for a test venue
3. **Add instruments**: Implement `InstrumentProvider` for your test venue
4. **Data subscriptions**: Add WebSocket subscription for trade ticks
5. **Write tests**: Create DataTesterConfig tests for your adapter
6. **Documentation**: Add Rust doc comments to all public types

## Checkpoint

You can:
- Build a new adapter following the 7-phase implementation sequence
- Structure Rust code following NT conventions
- Wire adapter into LiveNode via factory pattern
- Write DataTesterConfig and ExecTesterConfig validation
- Document adapter code following NT standards

## Key Skills

- `nt-adapters` — full adapter architecture and patterns
- `nt-testing` — adapter testing specs
- `nt-dev` — coding standards, Rust conventions

## Next

You are now a NautilusTrader developer! 🎉

Continue contributing by:
- Adding features to existing adapters
- Improving test coverage
- Contributing to core Rust or Python modules
- Writing documentation and examples
