# Serialization in NautilusTrader

NautilusTrader supports multiple serialization formats for high-performance data interchange.

## Comparison: msgspec vs Cap'n Proto

| Feature | `msgspec` | Cap'n Proto (`capnp`) |
|---------|-----------|-----------------------|
| **Speed** | Very Fast | Blazing (Zero-copy) |
| **Ease of Use** | High (Python-native) | Moderate (Requires Schema) |
| **Schema** | Optional (Structs) | Required (`.capnp`) |
| **Language Cross-op** | Good | Excellent |
| **When to use** | Standard trading data | Extreme performance / Rust core |

## Using `msgspec`

Default in Nautilus. Use for custom data objects:

```python
from msgspec import Struct

class MyModel(Struct):
    price: float
    qty: float
```

## Using Cap'n Proto

Requires enabling the `capnp` feature in the `nautilus-serialization` crate.

1. **Define Schema**: Create a `.capnp` file.
2. **Compile**: Use `capnpc` to generate code.
3. **Register**: Add to the message bus handlers.

Example schema: [capnp_schema.capnp](../skills/nt-implement/templates/capnp_schema.capnp).

## Performance Tip

Avoid using standard `pickle` or `json` (built-in) in hot paths, as they are significantly slower than `msgspec`.
