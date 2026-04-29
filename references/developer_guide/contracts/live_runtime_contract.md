# Live Runtime Contract

Sources:

- `references/concepts/live.md`
- Official developer guide testing and adapter pages

## Required guidance

- Prefer `nautilus_trader.live.LiveNode` for new Rust-backed PyO3 adapter and v2
  live-runtime examples.
- Treat `nautilus_trader.live.node.TradingNode` as legacy v1/Cython-oriented
  guidance unless the skill is documenting an existing integration that still
  uses it.
- Keep reconciliation enabled for production live execution unless a documented
  adapter limitation makes it impossible.
- Refresh account state and satisfy startup reconciliation before announcing a
  production live client as connected.

## Review rule

Unqualified “use TradingNode” guidance in new adapter work is stale. Either use
`LiveNode` or label the example as legacy/integration-specific.
