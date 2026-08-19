"""Small Git provenance helpers for checked-in benchmark evidence."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

BENCHMARK_SOURCE_PATHS = ("src", "benchmarks", "tests", "pyproject.toml", "uv.lock")


def git_provenance(project_root: Path, *, prefix: str) -> dict[str, str]:
    """Describe the commit and benchmark execution surface used by a run."""

    commit = _git(project_root, "rev-parse", "HEAD")
    branch = _git(project_root, "rev-parse", "--abbrev-ref", "HEAD")
    source_patch = _source_patch(project_root)
    return {
        f"{prefix}_commit": commit or "unavailable",
        f"{prefix}_branch": branch or "unavailable",
        f"{prefix}_benchmark_source_dirty": str(bool(source_patch)).lower(),
        f"{prefix}_benchmark_source_patch_sha256": hashlib.sha256(source_patch).hexdigest(),
    }


def _source_patch(project_root: Path) -> bytes:
    patch = bytearray(
        _git_bytes(
            project_root,
            "diff",
            "--binary",
            "HEAD",
            "--",
            *BENCHMARK_SOURCE_PATHS,
            ":(exclude)benchmarks/results/**",
        )
    )
    untracked = _git_bytes(
        project_root,
        "ls-files",
        "-z",
        "--others",
        "--exclude-standard",
        "--",
        *BENCHMARK_SOURCE_PATHS,
    )
    for raw_relative in sorted(value for value in untracked.split(b"\0") if value):
        relative = raw_relative.decode("utf-8", errors="surrogateescape")
        if relative.startswith("benchmarks/results/"):
            continue
        path = project_root / relative
        if not path.is_file():
            continue
        patch.extend(b"\0UNTRACKED\0")
        patch.extend(raw_relative)
        patch.extend(b"\0")
        patch.extend(hashlib.sha256(path.read_bytes()).digest())
    return bytes(patch)


def _git(project_root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip() if completed.returncode == 0 else ""


def _git_bytes(project_root: Path, *arguments: str) -> bytes:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=project_root,
        check=False,
        capture_output=True,
    )
    return completed.stdout if completed.returncode == 0 else b""
