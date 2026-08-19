"""Repository parser and direction-invariant tests."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from seismic.config import SeismicConfig, SeismicConfigError
from seismic.parser import RepositoryParser

FIXTURE = Path(__file__).parent / "fixtures" / "sample_repo"


def _git(*args: str, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def _fixture_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "sample-repo"
    shutil.copytree(FIXTURE, repo)
    (repo / ".gitignore").write_text("work/\n", encoding="utf-8")
    (repo / "work").mkdir()
    (repo / "work" / "ignored.py").write_text("def ignored(): ...\n", encoding="utf-8")
    _git("init", "-b", "main", cwd=repo)
    _git("config", "user.email", "seismic@example.test", cwd=repo)
    _git("config", "user.name", "Seismic Test", cwd=repo)
    _git("add", ".", cwd=repo)
    _git("commit", "-m", "fixture", cwd=repo)
    return repo


def test_parser_builds_reverse_traversable_python_graph(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    config = SeismicConfig(allowed_roots=(tmp_path.resolve(),))

    graph = RepositoryParser(config).parse(str(repo), explicit_repo_key="sample")

    artifacts = {artifact.logical_key: artifact for artifact in graph.artifacts}
    assert "work/ignored.py" not in artifacts
    pricing = artifacts["src/sample_app/pricing.py::calculate"]
    checkout = artifacts["src/sample_app/checkout.py::total"]
    service = artifacts["src/sample_app/service.py::handler"]
    test = artifacts["tests/test_checkout.py::test_total"]
    edges = {(edge.kind, edge.source_id, edge.target_id) for edge in graph.relationships}

    assert ("CALLS", checkout.id, pricing.id) in edges
    assert ("CALLS", service.id, checkout.id) in edges
    assert ("TESTS", test.id, checkout.id) in edges
    assert any(
        edge.kind == "STARTS_AT" and edge.target_id == artifacts["src/sample_app/cli.py::main"].id
        for edge in graph.relationships
    )
    assert any(
        artifact.kind == "package_version" and artifact.qualified_name == "httpx"
        for artifact in graph.artifacts
    )


def test_parser_reuses_snapshot_for_clean_commit_and_changes_dirty_snapshot(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    parser = RepositoryParser(SeismicConfig(allowed_roots=(tmp_path.resolve(),)))

    clean = parser.parse(str(repo), explicit_repo_key="sample")
    clean_again = parser.parse(str(repo), explicit_repo_key="sample")
    (repo / "src" / "sample_app" / "pricing.py").write_text(
        "def calculate(value):\n    return value\n"
    )
    dirty = parser.parse(str(repo), explicit_repo_key="sample")

    assert clean.snapshot_key == clean_again.snapshot_key
    assert dirty.snapshot_key != clean.snapshot_key
    assert "@worktree-" in dirty.snapshot_key


def test_dirty_manifest_changes_get_distinct_snapshot_keys(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    parser = RepositoryParser(SeismicConfig(allowed_roots=(tmp_path.resolve(),)))
    manifest = repo / "pyproject.toml"

    manifest.write_text(manifest.read_text().replace("httpx==0.28.1", "httpx==0.28.2"))
    first = parser.parse(str(repo), explicit_repo_key="sample")
    manifest.write_text(manifest.read_text().replace("httpx==0.28.2", "httpx==0.28.3"))
    second = parser.parse(str(repo), explicit_repo_key="sample")

    assert first.snapshot_key != second.snapshot_key
    assert any(artifact.logical_key == "pypi::httpx::0.28.2" for artifact in first.artifacts)
    assert any(artifact.logical_key == "pypi::httpx::0.28.3" for artifact in second.artifacts)


def test_dirty_codeowners_changes_get_distinct_snapshot_keys(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    parser = RepositoryParser(SeismicConfig(allowed_roots=(tmp_path.resolve(),)))
    codeowners = repo / "CODEOWNERS"

    codeowners.write_text("src/sample_app/pricing.py @pricing-one\n", encoding="utf-8")
    first = parser.parse(str(repo), explicit_repo_key="sample")
    codeowners.write_text("src/sample_app/pricing.py @pricing-two\n", encoding="utf-8")
    second = parser.parse(str(repo), explicit_repo_key="sample")

    first_pricing = next(
        artifact
        for artifact in first.artifacts
        if artifact.logical_key == "src/sample_app/pricing.py::calculate"
    )
    second_pricing = next(
        artifact
        for artifact in second.artifacts
        if artifact.logical_key == "src/sample_app/pricing.py::calculate"
    )
    assert first.snapshot_key != second.snapshot_key
    assert first_pricing.owner == "@pricing-one"
    assert second_pricing.owner == "@pricing-two"


def test_repository_path_must_be_inside_an_allowed_root(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    config = SeismicConfig(allowed_roots=((tmp_path / "different").resolve(),))

    with pytest.raises(SeismicConfigError, match="outside SEISMIC_ALLOWED_ROOTS"):
        RepositoryParser(config).parse(str(repo), explicit_repo_key="sample")
