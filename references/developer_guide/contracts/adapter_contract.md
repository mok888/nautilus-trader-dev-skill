# Adapter Contract

Sources:

- `references/developer_guide/adapters.md`
- `references/developer_guide/spec_data_testing.md`
- `references/developer_guide/spec_exec_testing.md`

## Required guidance

- Keep Rust-core and Python-integration boundaries explicit.
- Use `nautilus_network::http::HttpClient` for Rust HTTP client examples unless
  official source evidence requires another client.
- Use `get_runtime().spawn()` for Python-runtime-sensitive async Rust paths; do
  not teach `tokio::spawn()` as the default from Python-driven adapter code.
- Align Python adapter methods with current command/request object signatures.
- Treat `InstrumentProvider.load_all_async()` as the required load method for
  current v1.224-era guidance; override targeted load methods only for venue
  semantics or efficiency.
- Require order status reports, fill reports, position status reports, and mass
  status generation where the official execution client contract requires them.

## Review rule

An adapter is not ready when it only has provider/data/exec class shells. It must
prove command handling, subscriptions, reconciliation, account state, and factory
wiring for the claimed venue scope.
