---
source_url: https://nautilustrader.io/docs/latest/developer_guide/spec_data_testing/
source_repo: nautechsystems/nautilus_trader/docs/developer_guide/spec_data_testing.md
sync_date: 2026-04-29
target: latest developer guide
confidence: high
---

# Data Testing Spec

The Data Testing Spec defines acceptance evidence for market-data adapters and
data clients. Agent work should not treat method presence as sufficient for data
adapter readiness.

## Required evidence themes

- Subscription and unsubscription behavior for supported data types.
- Correct conversion from venue payloads into Nautilus data objects.
- Instrument cache interaction before live subscriptions depend on instruments.
- Condition-based async waits instead of fixed sleeps in tests.
- Realistic fixtures for venue payloads, including malformed or partial payloads
  where the adapter claims to handle them.

## Agent checklist

- Use DataTester or the official data tester pattern when the adapter surface is
  compatible with it.
- Require concrete data-type coverage instead of generic adapter smoke tests.
- Pair data-client behavior changes with tests that prove the emitted Nautilus
  object fields, timestamps, and identifiers.
