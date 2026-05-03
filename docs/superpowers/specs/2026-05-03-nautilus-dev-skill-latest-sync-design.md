# NautilusTrader dev-skill latest-sync design

## Goal

Update the NautilusTrader development skills repository so its operator-facing
guidance, local skill contracts, and static sync checks reflect the current
NautilusTrader developer-guide evidence instead of the older v1.224 snapshot.

The update should close the validation findings from the repo audit without
blindly rewriting valid Python `TradingNode` examples. The target state is a
clear boundary:

- Python live-trading examples may still use `TradingNode` when that matches the
  official Python live connectivity docs.
- Rust v2 / Rust-backed live-node guidance should prefer `LiveNode`.
- Existing integration-specific `TradingNode` examples should be labeled as
  Python live or integration-specific examples, not presented as the universal
  default for all new Rust-backed work.

## Scope

### Top-level project guidance

Update `README.md` and `AGENTS.md` so the repository no longer claims a stale
single-version validation target. The text should describe current alignment as
latest developer-guide sync with version-sensitive notes carried forward where
still useful.

High-visibility summaries should say `LiveNode` / `TradingNode` boundary rather
than only `TradingNode`.

### Developer workflow skill (`nt-dev`)

Update `skills/nt-dev/SKILL.md` to include current developer-guide guidance:

- Cap'n Proto version source is `tools.toml`, installed through
  `./scripts/install-capnp.sh`, with repo tooling reading versions through the
  pinned tools flow.
- Linux `LD_LIBRARY_PATH` setup derives the library directory with
  `sysconfig.get_config_var("LIBDIR")` from `$PYO3_PYTHON`.
- PyO3 property-versus-method guidance: cheap, side-effect-free values may be
  `#[getter]`; actions, allocations, I/O, mutations, and argument-taking APIs
  should remain methods.
- `pyo3-stub-gen` annotations are required for Python-exposed Rust types,
  methods, and functions.
- PyO3 `eq_int` enums must not rely on the generated `hash` pyclass attribute;
  they should provide a manual `__hash__` returning the discriminant.
- DST-observable iteration should use `IndexMap` / `IndexSet`; lookup-only hot
  paths may still use `AHashMap` / `AHashSet`; concurrent writes require a real
  concurrency primitive such as `DashMap`.
- Async Rust guidance should mention cancellation-safety notes and the adapter
  runtime bridge (`get_runtime().spawn()` / `get_runtime().block_on()`) where
  Python threads are involved.

### Testing skill (`nt-testing`)

Update `skills/nt-testing/SKILL.md` to promote official test commands:

- `make pytest` for v1 legacy Python tests.
- `make pytest-v2` for Rust-backed PyO3 Python tests.
- `make cargo-test` or `cargo nextest run --workspace --features
  "python,ffi,high-precision,defi" --cargo-profile nextest` for Rust tests.

Direct `pytest tests/ -v` and `cargo test --workspace` may appear only as
legacy or targeted troubleshooting examples, not as primary commands.

Add DST readiness guidance for async/runtime modules:

- time/task/runtime/signal primitives route through deterministic seams;
- wall-clock reads go through the project time seam;
- ordering-sensitive maps use `IndexMap` / `IndexSet`;
- control-plane `tokio::select!` uses `biased`;
- ambient `Instant::now`, `SystemTime::now`, `tokio::signal::ctrl_c`,
  `std::thread::spawn`, and `tokio::task::spawn_blocking` do not escape seams;
- replay-sensitive IDs are pure functions of their inputs.

Update dataset metadata guidance to require the official fields:

- `file`
- `sha256`
- `size_bytes`
- `original_url`
- `licence`
- `added_at`

For user-fetched datasets, document restricted redistribution metadata such as
distribution, fetch method/reference, auth, transform version, redistribution,
and public mirror status.

### Live-runtime wording

Update `skills/nt-live/SKILL.md`, `skills/nt-strategy-builder/SKILL.md`, and
`skills/nt-review/SKILL.md` to clarify the live-runtime boundary:

- Python live connectivity may use `TradingNode`.
- Rust v2 / Rust-backed live-node guidance should use `LiveNode`.
- Integration-specific `TradingNode` examples must be labeled or contextualized.

Do not perform a mechanical global replacement of `TradingNode`.

### Broader references and templates

Because the user approved updating all recommended fixes, apply the boundary
wording to high-impact references and templates that currently present
`TradingNode` as the default without context, especially:

- `references/concepts/live.md`
- `skills/nt-learn/curriculum/07-live-trading.md`
- integration references under `references/integrations/` where a section starts
  by recommending a live `TradingNode`
- strategy-builder templates that demonstrate Python live nodes

These updates should be labels and context notes unless the example is actually
being converted to a Rust `LiveNode` example.

### Sync checker and tests

Extend `tools/check_dev_guide_sync.py` with targeted string checks matching the
repo's existing simple static-check style:

- reject stale `capnp-version` guidance in checked markdown;
- require `sysconfig.get_config_var("LIBDIR")` in `skills/nt-dev/SKILL.md` when
  `LD_LIBRARY_PATH` appears;
- reject primary stale `cargo test --workspace` and `pytest tests/ -v` commands
  in `skills/nt-testing/SKILL.md`;
- require DST readiness language in `skills/nt-testing/SKILL.md`;
- require official dataset metadata fields in `skills/nt-testing/SKILL.md`;
- require explicit live-runtime boundary language in `skills/nt-live/SKILL.md`,
  `skills/nt-strategy-builder/SKILL.md`, and `skills/nt-review/SKILL.md`.

Update `tests/test_dev_guide_sync.py` with RED/GREEN coverage for each new check.
Keep tests deterministic and in the same `tmp_path` style used by the existing
suite.

## Non-goals

- Do not claim the local reference summaries are full copies of official docs if
  they remain compact action contracts.
- Do not replace every `TradingNode` occurrence with `LiveNode`.
- Do not modify Nautilus-Daedalus; this design is for
  `/home/mok/projects/nautilus-trader-dev-skill`.
- Do not introduce network-dependent tests.

## Verification

Required verification after implementation:

```bash
uv run python tools/check_dev_guide_sync.py
uv run --with pytest pytest tests/test_dev_guide_sync.py -q
```

If strategy-builder templates or tests are changed, also run:

```bash
uv run pytest skills/nt-strategy-builder/tests/ -q
```

## Commit strategy

Use semantic commits. Prefer several bounded commits instead of one large patch:

1. Top-level metadata and live-runtime wording.
2. `nt-dev` and `nt-testing` content updates.
3. Sync checker and tests.
4. Broader reference/template labeling if changed separately.

Each implementation commit should include its directly related tests or checker
updates where applicable.
