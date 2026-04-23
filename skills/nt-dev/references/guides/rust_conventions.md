# Rust

> **Summary**: This is a condensed reference of the NautilusTrader Rust development conventions. The full official guide is 47KB with detailed examples for every topic. Key sections are summarized below.

## Cargo manifest conventions

- In `[dependencies]`, list internal crates (`nautilus-*`) first in alphabetical order, insert a blank line, then external required dependencies alphabetically, followed by another blank line and the optional dependencies (those with `optional = true`) in alphabetical order.
- Add `"python"` to every `extension-module` feature list, keeping it adjacent to `"pyo3/extension-module"`.
- Always include a blank line before `[dev-dependencies]` and `[build-dependencies]` sections.
- Use snake_case filenames for `bin/` sources and kebab-case for `[[bin]] name` entries.

## Versioning guidance

- Use workspace inheritance for shared dependencies: `serde = { workspace = true }`
- Only pin versions directly for crate-specific dependencies
- Keep related dependencies aligned: `capnp`/`capnpc` (exact), `arrow`/`parquet` (major.minor)
- Adapter-only dependencies belong in the workspace `Cargo.toml` "Adapter dependencies" section

## Feature flag conventions

- Prefer additive feature flags — enabling must not break existing functionality
- Common patterns: `high-precision`, `default = []`, `python`, `extension-module`, `ffi`, `stubs`
- Document every feature in crate-level documentation

## Build configurations

Aligned targets share feature set `ffi,python,high-precision,defi` with `nextest` profile:
- `cargo-test` and `cargo-clippy` reuse artifacts between linting and testing
- Python extension building uses different features (`extension-module`) — rebuilds are expected

## Module organization

- Keep modules focused on single responsibility
- Use `mod.rs` as module root when defining submodules
- Prefer flat hierarchies over deep nesting
- Re-export commonly used items from crate root

## Code style and conventions

### File header requirements
All Rust files must include the standardized copyright header (automated enforcement via `check_copyright_year.sh`).

### Code formatting
- One blank line between functions and above doc comments
- Prefer inline format strings: `anyhow::bail!("Failed: {n}")` not positional args

### Type qualification
- **anyhow**: Always fully qualify (`anyhow::bail!`, `anyhow::Result<T>`)
- **Nautilus domain types**: Use directly after importing
- **tokio**: Generally fully qualify (`tokio::spawn`, `tokio::time::timeout`)

### Logging
- Fully qualify: `log::debug!`, `log::info!`, `log::warn!`
- Start messages with capitalised word, omit terminal periods

### Error handling
- Primary: `anyhow::Result<T>` for fallible functions
- Custom: `thiserror` for domain-specific errors
- Propagation: `?` operator
- Early returns: `anyhow::bail!` preferred over `return Err(anyhow::anyhow!(...))`
- Context: lowercase `.context()` messages

### Async patterns
- `get_runtime().spawn()` in adapters (not `tokio::spawn()`) — Python FFI compatibility
- `#[tokio::test]` OK in tests (creates own runtime)
- Wrap network awaits with `tokio::time::timeout`

### Attribute patterns
Consistent ordering: `#[repr(C)]` → `#[derive(...)]` → `#[cfg_attr(feature = "python", pyo3::pyclass(...))]` → stub gen attribute

### Type stub annotations (pyo3-stub-gen)
| PyO3 construct | Stub annotation |
|---|---|
| `#[pyclass]` | `pyo3_stub_gen::derive::gen_stub_pyclass` |
| enum `#[pyclass]` | `pyo3_stub_gen::derive::gen_stub_pyclass_enum` |
| `#[pymethods]` | `pyo3_stub_gen::derive::gen_stub_pymethods` |
| `#[pyfunction]` | `pyo3_stub_gen::derive::gen_stub_pyfunction` |

## Python bindings (PyO3)

- `#[pyclass]` naming: snake_case Rust → PascalCase Python
- Enums: `rename_all = "SCREAMING_SNAKE_CASE"`
- Properties vs methods: `#[getter]` for cheap, side-effect-free reads; method for actions/allocations

## Testing conventions

- Use `#[rstest]` for parameterized tests
- Property-based testing with `proptest`
- Test naming: descriptive scenario names
- Use `unwrap`/`expect` freely in tests

## Rust-Python memory management

- Use `clone_py_object()` for Python object cloning (handles reference cycles)
- Remove `#[derive(Clone)]` from callback-holding structs
- Accept `PyObject` in function signatures for Python callbacks
- Avoid `Arc::new()` when creating Python callbacks

## Unsafe Rust

### Safety policy
- Unsafe code must have a `// SAFETY:` comment explaining why the operation is valid
- Categories: FFI boundary, platform intrinsics, performance-critical optimizations

### Thread-local registries
- Actor registry vs component registry
- `ActorRef` usage: look up by ID each time, drop guard before scope ends, never hold across `.await`

## Cap'n Proto serialization

- Install via `./scripts/install-capnp.sh` or from source
- Schema files in `crates/nautilus-serialization/schema/`
- Generated code committed to repo
- Test with `make cargo-test EXTRA_FEATURES="capnp"`

---

*This summary covers the key conventions. For detailed examples, attribute patterns, constructor patterns, hash collection conventions, unsafe Rust guidelines, and more, refer to the full Rust developer guide in the NautilusTrader repository.*
