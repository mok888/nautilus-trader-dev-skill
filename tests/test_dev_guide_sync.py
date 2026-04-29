from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.check_dev_guide_sync import CheckResult
from tools.check_dev_guide_sync import run_checks


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_reports_missing_required_guide_files(tmp_path: Path) -> None:
    write(tmp_path / "references/developer_guide/index.md", "# Developer Guide\n")

    result = run_checks(tmp_path)

    assert result.ok is False
    assert "missing required guide file: references/developer_guide/design_principles.md" in result.errors
    assert "missing required guide file: references/developer_guide/spec_data_testing.md" in result.errors
    assert "missing required guide file: references/developer_guide/spec_exec_testing.md" in result.errors
    assert "missing required guide file: references/developer_guide/test_datasets.md" in result.errors


def test_reports_missing_source_metadata(tmp_path: Path) -> None:
    for relative in [
        "references/developer_guide/design_principles.md",
        "references/developer_guide/spec_data_testing.md",
        "references/developer_guide/spec_exec_testing.md",
        "references/developer_guide/test_datasets.md",
    ]:
        write(tmp_path / relative, "# Guide\n\nNo metadata here.\n")

    result = run_checks(tmp_path)

    assert result.ok is False
    assert any("missing source metadata" in error for error in result.errors)


def test_reports_stale_references_guides_path(tmp_path: Path) -> None:
    write(
        tmp_path / "skills/nt-testing/SKILL.md",
        "Read references/guides/spec_data_testing.md before testing.\n",
    )

    result = run_checks(tmp_path)

    assert result.ok is False
    assert "stale references/guides path in skills/nt-testing/SKILL.md" in result.errors


def test_reports_unqualified_pre_commit_install(tmp_path: Path) -> None:
    write(tmp_path / "skills/nt-dev/SKILL.md", "Run pre-commit install during setup.\n")

    result = run_checks(tmp_path)

    assert result.ok is False
    assert "unqualified pre-commit install in skills/nt-dev/SKILL.md" in result.errors


def test_reports_missing_required_invariants(tmp_path: Path) -> None:
    write(tmp_path / "skills/nt-live/SKILL.md", "# Live\n")
    write(tmp_path / "skills/nt-testing/SKILL.md", "# Testing\n")
    write(tmp_path / "skills/nt-adapters/SKILL.md", "# Adapters\n")
    write(tmp_path / "skills/nt-architect/SKILL.md", "# Architect\n")

    result = run_checks(tmp_path)

    assert result.ok is False
    assert "missing invariant 'LiveNode' in skills/nt-live/SKILL.md" in result.errors
    assert "missing invariant 'DataTester' in skills/nt-testing/SKILL.md" in result.errors
    assert "missing invariant 'ExecTester' in skills/nt-testing/SKILL.md" in result.errors
    assert "missing invariant 'nautilus_network::http::HttpClient' in skills/nt-adapters/SKILL.md" in result.errors
    assert "missing invariant 'message immutability' in skills/nt-architect/SKILL.md" in result.errors


def test_success_when_required_files_metadata_paths_and_invariants_exist(tmp_path: Path) -> None:
    metadata = """---
source_url: https://nautilustrader.io/docs/latest/developer_guide/design_principles/
source_repo: nautechsystems/nautilus_trader/docs/developer_guide/design_principles.md
sync_date: 2026-04-29
target: latest developer guide
confidence: high
---
"""
    for name in [
        "design_principles.md",
        "spec_data_testing.md",
        "spec_exec_testing.md",
        "test_datasets.md",
    ]:
        write(tmp_path / "references/developer_guide" / name, metadata + f"# {name}\n")

    write(tmp_path / "skills/nt-live/SKILL.md", "Prefer LiveNode; label TradingNode legacy.\n")
    write(tmp_path / "skills/nt-testing/SKILL.md", "Use DataTester and ExecTester evidence.\n")
    write(tmp_path / "skills/nt-adapters/SKILL.md", "Use nautilus_network::http::HttpClient and get_runtime().spawn().\n")
    write(tmp_path / "skills/nt-architect/SKILL.md", "Preserve message immutability in designs.\n")

    result = run_checks(tmp_path)

    assert result == CheckResult(ok=True, errors=[])
