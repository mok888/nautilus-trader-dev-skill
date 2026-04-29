# NautilusTrader Developer Guide Full Sync Design

## Context

This repository is an AI-agent skill pack for NautilusTrader development. It
contains workflow skills, domain skills, local developer-guide references, and
review/testing guidance used by agents when building NautilusTrader systems.

The current repository is aligned with parts of NautilusTrader v1.224.0, but a
fresh audit against the official developer guide and reference repositories
found broader drift than the adapter guide alone. The drift includes missing
developer-guide reference pages, stale internal reference paths, older tooling
setup language, weak v1/v2 live-runtime distinction, incomplete latest testing
policy, adapter contract drift, and inconsistent skill inventory metadata.

Reference sources for this design:

- Official developer guide: <https://nautilustrader.io/docs/latest/developer_guide/>
- Official adapter guide: <https://nautilustrader.io/docs/latest/developer_guide/adapters/>
- Official source repository: <https://github.com/nautechsystems/nautilus_trader>
- Prior skill reference repository: <https://github.com/Martingale42/nautilus-dev>

## Goal

Bring `nautilus-trader-dev-skill` back into trustworthy alignment with the
current NautilusTrader developer guide and reference repositories, without
making unverified skill claims ahead of source truth.

The result should make agent behavior more production-safe for NautilusTrader
development by refreshing local reference truth first, then deriving canonical
contracts, then updating the skills that consume those contracts, and finally
adding lightweight drift checks.

## Non-goals

This design does not include:

- changes to NautilusTrader itself;
- implementation of a new venue adapter;
- new trading strategy development;
- replacement of the skill-pack architecture;
- speculative claims where official rendered documentation and source files are
  inconsistent, such as the observed `divan` versus `iai` benchmarking drift,
  until the source of truth is confirmed.

## Findings to address

The audit identified these high-value gaps:

1. The official developer guide includes pages that are not reflected cleanly in
   the local `references/developer_guide` tree, including design principles,
   data testing spec, execution testing spec, and test datasets.
2. Several skills refer to stale `references/guides/*` paths while the observed
   local mirror is under `references/developer_guide/*`.
3. Environment setup guidance still emphasizes `pre-commit` where latest
   official setup uses `make install-tools`, `tools.toml`, and `prek install`.
4. Live-runtime guidance does not clearly separate legacy `TradingNode` paths
   from the preferred `nautilus_trader.live.LiveNode` path for new Rust-backed
   PyO3 adapter work.
5. Local testing guidance is thinner than the latest official testing policy,
   especially around the mechanism ladder, projection rule, DST readiness,
   v1/v2 suite split, and PyO3 abort isolation.
6. Adapter guidance and DEX templates have drifted from current command/request
   signatures, reconciliation method expectations, credential conventions,
   standard instrument cache methods, connect lifecycle gates, and Rust module
   layout.
7. Message immutability appears in the official design principles but is not
   treated as a named cross-cutting invariant across local architecture,
   implementation, and review skills.
8. `skills/AGENTS.md` claims a smaller skill inventory than the actual local
   repository exposes.
9. There is no repeatable drift check that warns when local guide mirrors,
   skill references, or critical wording patterns fall behind the official
   guide.

## Proposed architecture

The sync should be implemented as four layers.

### 1. Reference layer

Refresh the local developer-guide mirror so it matches the official guide
structure closely enough for skills to cite it reliably.

Deliverables:

- add or refresh:
  - `references/developer_guide/design_principles.md`;
  - `references/developer_guide/spec_data_testing.md`;
  - `references/developer_guide/spec_exec_testing.md`;
  - `references/developer_guide/test_datasets.md`;
- update `references/developer_guide/index.md`;
- inventory and repair stale `references/guides/*` references;
- add a lightweight source metadata convention for mirrored guide files.

Each mirrored guide page should identify, where known:

- source URL;
- source repository path or branch;
- sync date;
- target NautilusTrader version or branch;
- confidence notes when rendered docs and raw source appear inconsistent.

### 2. Contract layer

Create concise canonical references that summarize operational rules shared by
multiple skills. Skills should cite these contracts instead of duplicating
drift-prone rule blocks.

Candidate files:

- `references/developer_guide/contracts/environment_tooling.md`;
- `references/developer_guide/contracts/testing_policy.md`;
- `references/developer_guide/contracts/adapter_contract.md`;
- `references/developer_guide/contracts/live_runtime_contract.md`;
- `references/developer_guide/contracts/design_principles.md`.

Each contract should:

- state the rule in agent-actionable terms;
- cite the refreshed guide source;
- separate required behavior from version-sensitive or uncertain behavior;
- remain short enough to be embedded or summarized in skills.

### 3. Skill layer

Update affected skills to consume the contracts and remove contradictory or
stale guidance.

Primary targets:

- `skills/nt-dev/SKILL.md`;
- `skills/nt-testing/SKILL.md`;
- `skills/nt-adapters/SKILL.md`;
- `skills/nt-dex-adapter/SKILL.md`;
- `skills/nt-live/SKILL.md`;
- `skills/nt-strategy-builder/SKILL.md`;
- `skills/nt-review/SKILL.md`;
- `skills/nt-architect/SKILL.md`;
- `skills/nt-implement/SKILL.md`;
- `skills/AGENTS.md` and top-level README/AGENTS inventory metadata where
  needed.

Expected skill corrections include:

- update setup guidance toward `make install-tools`, pinned tools, and
  `prek install`, while preserving official command names that still include
  `pre-commit` targets;
- make `LiveNode` the preferred path for new Rust-backed PyO3 adapter examples
  and clearly label legacy `TradingNode` guidance;
- encode DataTester and ExecTester policy, acceptance matrices, and evidence
  requirements;
- add PyO3 abort/subprocess testing cautions where relevant;
- align adapter and DEX examples with official command/request object
  signatures;
- require the full execution reconciliation method set where official adapter
  contracts require it;
- normalize `InstrumentProvider` guidance to the current defaults;
- replace stale low-level Rust HTTP/runtime examples with the official
  `nautilus_network::http::HttpClient` and Python-runtime-safe
  `get_runtime().spawn()` guidance;
- elevate message immutability into architecture, implementation, and review
  checklists.

### 4. Validation layer

Add lightweight static checks so future drift is visible before agents rely on
stale guidance.

Candidate checks:

- every skill reference path resolves or is intentionally marked external;
- required developer-guide mirror pages exist locally;
- mirrored guide pages include source metadata;
- stale `references/guides/*` paths are absent;
- stale setup language such as unqualified `pre-commit install` is flagged when
  `prek install` should be used;
- unqualified `TradingNode` recommendations are flagged in new live/PyO3 adapter
  contexts;
- adapter template method names and parameter type names mention current
  command/request objects;
- adapter compliance tests mention the full reconciliation method set;
- critical invariants such as message immutability, DataTester, ExecTester,
  `LiveNode`, `get_runtime().spawn()`, and `nautilus_network::http::HttpClient`
  remain discoverable in the relevant skill or contract files.

Validation commands should use `uv` where project tooling permits.

## Implementation phases

### Phase 1: Reference truth

Refresh missing and stale developer-guide references, update the guide index,
repair missing reference paths, and introduce source metadata.

Acceptance criteria:

- missing official guide pages identified by the audit exist locally;
- no skill points to an obviously missing local guide path;
- refreshed files identify their source and confidence;
- ambiguous rendered-vs-source conflicts are labeled instead of guessed.

### Phase 2: Canonical contracts

Introduce the shared contract documents and route cross-skill rules through
them.

Acceptance criteria:

- each contract cites refreshed guide sources;
- contracts distinguish required, recommended, legacy, and uncertain guidance;
- contracts are concise enough for skills to summarize without duplication.

### Phase 3: Skill alignment

Update high-risk skills and repository inventory metadata to consume the
contracts.

Acceptance criteria:

- `nt-dev`, `nt-testing`, `nt-adapters`, `nt-dex-adapter`, `nt-live`, and
  `nt-review` no longer conflict with the canonical contracts;
- architecture and implementation skills include message immutability and
  current testing/adapter/live-runtime invariants where relevant;
- README and AGENTS inventory descriptions match the actual skill set;
- adapter, live, and testing skills require concrete acceptance evidence rather
  than structural presence alone.

### Phase 4: Drift checks

Add static verification for reference paths, source metadata, required guide
pages, and known stale patterns.

Acceptance criteria:

- drift checks run through a documented `uv` command;
- broken local reference paths fail verification;
- missing required guide pages fail verification;
- known stale wording patterns are surfaced with actionable messages;
- checks are narrow enough not to block legitimate legacy examples that are
  clearly labeled.

## Testing and review strategy

Because this repository is mostly a skill and documentation repository,
verification should be static, path-based, and content-focused.

Recommended verification:

- run existing tests with `uv run pytest` if available;
- add focused tests for new drift-check scripts;
- run path existence checks for skill references;
- run content checks for critical invariants;
- manually compare refreshed guide files against the official URLs before
  committing implementation changes.

Review should verify that every new or changed skill claim is backed by either
local reference truth, official source evidence, or an explicit uncertainty
label.

## Risk handling

### Rendered docs versus raw source drift

When the rendered official docs and raw GitHub docs disagree, the implementation
must not silently choose one. The relevant reference or contract should mark the
conflict, cite both sources, and keep downstream skills conservative until the
target source of truth is confirmed.

### Contract overcentralization

Contract documents should not become large manuals. They should hold concise
rules and cite the detailed reference pages. Skills should include practical
summaries so agents can act without excessive indirection.

### Docs claims ahead of source truth

The implementation order deliberately updates references first, then contracts,
then skills, then validation. A skill should not claim new behavior until the
source reference or contract exists.

### Large noisy commits

Implementation should commit by phase and concern: reference sync, contract
docs, skill updates, and validation checks. This keeps review and rollback
bounded.

## Open confirmation items

- Confirm the target NautilusTrader source branch or release for this sync.
- Resolve the benchmarking source of truth for `divan` versus `iai` before
  editing benchmarking guidance.
- Confirm how much content, if any, should be ported from
  `Martingale42/nautilus-dev` production architecture references after the
  official-guide sync is complete.
