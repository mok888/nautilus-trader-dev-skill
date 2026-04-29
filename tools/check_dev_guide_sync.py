from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


REQUIRED_GUIDE_FILES = [
    Path("references/developer_guide/design_principles.md"),
    Path("references/developer_guide/spec_data_testing.md"),
    Path("references/developer_guide/spec_exec_testing.md"),
    Path("references/developer_guide/test_datasets.md"),
]

METADATA_KEYS = ["source_url:", "source_repo:", "sync_date:", "target:", "confidence:"]

INVARIANT_TARGETS = {
    Path("skills/nt-live/SKILL.md"): ["LiveNode"],
    Path("skills/nt-testing/SKILL.md"): ["DataTester", "ExecTester"],
    Path("skills/nt-adapters/SKILL.md"): [
        "nautilus_network::http::HttpClient",
        "get_runtime().spawn()",
    ],
    Path("skills/nt-architect/SKILL.md"): ["message immutability"],
}


@dataclass(frozen=True)
class CheckResult:
    ok: bool
    errors: list[str]


def _iter_markdown_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.md") if ".git" not in path.parts)


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def run_checks(root: Path) -> CheckResult:
    errors: list[str] = []

    for relative in REQUIRED_GUIDE_FILES:
        absolute = root / relative
        if not absolute.exists():
            errors.append(f"missing required guide file: {relative.as_posix()}")
            continue
        text = _read(absolute)
        missing_keys = [key for key in METADATA_KEYS if key not in text]
        if missing_keys:
            errors.append(
                f"missing source metadata in {relative.as_posix()}: {', '.join(missing_keys)}"
            )

    for markdown_file in _iter_markdown_files(root):
        text = _read(markdown_file)
        relative = _relative(markdown_file, root)
        if "references/guides/" in text:
            errors.append(f"stale references/guides path in {relative}")
        if "pre-commit install" in text and "prek install" not in text:
            errors.append(f"unqualified pre-commit install in {relative}")

    for relative, required_terms in INVARIANT_TARGETS.items():
        absolute = root / relative
        if not absolute.exists():
            continue
        text = _read(absolute)
        for term in required_terms:
            if term not in text:
                errors.append(f"missing invariant '{term}' in {relative.as_posix()}")

    return CheckResult(ok=not errors, errors=errors)


def main() -> int:
    result = run_checks(Path.cwd())
    if result.ok:
        print("Developer guide sync checks passed.")
        return 0
    print("Developer guide sync checks failed:")
    for error in result.errors:
        print(f"- {error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
