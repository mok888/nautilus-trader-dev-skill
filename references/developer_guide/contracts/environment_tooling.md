# Environment Tooling Contract

Sources:

- `references/developer_guide/environment_setup.md`
- Official developer guide environment setup page

## Required guidance

- Use `uv` for Python environment and command execution in this skill repo.
- For NautilusTrader core setup, prefer the official latest setup path:
  `make install-tools`, pinned tools from `tools.toml`, and `prek install`.
- Preserve command names that are still official make targets, even when they
  include the phrase `pre-commit`.

## Review rule

Unqualified setup instructions that say only `pre-commit install` are stale. Use
`prek install` or explain that a legacy repository still requires pre-commit.
