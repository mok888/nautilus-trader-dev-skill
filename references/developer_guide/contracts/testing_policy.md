# Testing Policy Contract

Sources:

- `references/developer_guide/testing.md`
- `references/developer_guide/spec_data_testing.md`
- `references/developer_guide/spec_exec_testing.md`
- `references/developer_guide/test_datasets.md`

## Required guidance

- Choose the smallest test mechanism that proves the production behavior.
- Use DataTester evidence for data adapter behavior when the adapter surface is
  compatible with the official data tester pattern.
- Use ExecTester evidence for execution adapter behavior when the adapter surface
  is compatible with the official execution tester pattern.
- Isolate PyO3 panic/abort behavior in subprocess-style tests when a failure
  would abort the interpreter.
- Keep unit tests deterministic and avoid implicit network or dataset downloads.

## Review rule

Structural method presence is not enough for production readiness. Adapter and
live-runtime claims need behavior evidence, fixtures, or explicit unsupported
scope labels.
