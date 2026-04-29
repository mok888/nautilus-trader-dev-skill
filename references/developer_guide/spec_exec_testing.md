---
source_url: https://nautilustrader.io/docs/latest/developer_guide/spec_exec_testing/
source_repo: nautechsystems/nautilus_trader/docs/developer_guide/spec_exec_testing.md
sync_date: 2026-04-29
target: latest developer guide
confidence: high
---

# Execution Testing Spec

The Execution Testing Spec defines acceptance evidence for execution adapters and
execution clients. Agent work should prove order submission, cancellation,
modification, reconciliation, and status-report behavior before claiming live
readiness.

## Required evidence themes

- Submit, cancel, cancel-all, modify, and query command handling.
- Order status reports, fill reports, position status reports, and mass status
  generation where required by the official adapter contract.
- Startup reconciliation and account-state emission before connected state is
  announced.
- Rejection, timeout, and venue error mapping into safe Nautilus behavior.

## Agent checklist

- Use ExecTester or the official execution tester pattern when available.
- Require reconciliation report coverage for production adapters.
- Do not mark execution adapters ready when only structural method presence is
  tested.
