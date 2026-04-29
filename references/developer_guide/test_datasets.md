---
source_url: https://nautilustrader.io/docs/latest/developer_guide/test_datasets/
source_repo: nautechsystems/nautilus_trader/docs/developer_guide/test_datasets.md
sync_date: 2026-04-29
target: latest developer guide
confidence: high
---

# Test Datasets

Test datasets should make adapter and system tests reproducible without hiding
network, license, or freshness assumptions.

## Dataset standards

- Keep fixture data small enough for repository tests unless the dataset is
  explicitly documented as external.
- Document source, license, generation command, and refresh date for fetched or
  generated datasets.
- Skip tests with clear reasons when external datasets are intentionally absent.
- Prefer deterministic local fixtures for unit tests and reserve large datasets
  for integration or acceptance runs.

## Agent checklist

- Do not fetch large datasets implicitly during normal unit tests.
- Add metadata beside generated fixtures.
- Keep dataset-dependent tests serializable when shared caches or file paths are
  involved.
