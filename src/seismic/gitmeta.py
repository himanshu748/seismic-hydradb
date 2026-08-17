"""Bounded Git history and CODEOWNERS extraction for repository artifacts."""

from __future__ import annotations

import fnmatch
import subprocess
from dataclasses import dataclass
from pathlib import Path


class GitMetadataError(RuntimeError):
    """Raised when required Git metadata cannot be read safely."""


@dataclass(frozen=True, slots=True)
class LastTouch:
    """The latest known author and commit timestamp for one repository path."""

    author: str = ""
    timestamp: str = ""


@dataclass(frozen=True, slots=True)
class OwnerMatch:
    """CODEOWNERS-derived ownership evidence for one path."""

    owner: str = ""
    source: str = ""


def git_head(repo: Path) -> str:
    """Return the current Git commit SHA."""

    return _git(repo, "rev-parse", "HEAD").strip()


def is_dirty(repo: Path) -> bool:
    """Return whether tracked or untracked worktree content differs from HEAD."""

    return bool(_git(repo, "status", "--porcelain=v1", "--untracked-files=all").strip())


def collect_last_touch(
    repo: Path, paths: set[str], max_commits: int = 1_000
) -> dict[str, LastTouch]:
    """Collect latest-touch metadata in one bounded Git history subprocess."""

    if not paths:
        return {}
    output = _git(
        repo,
        "log",
        f"--max-count={max_commits}",
        "--format=@@SEISMIC@@%an%x1f%ct",
        "--name-only",
        "--no-renames",
        "--",
    )
    result: dict[str, LastTouch] = {}
    author = ""
    timestamp = ""
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if line.startswith("@@SEISMIC@@"):
            payload = line.removeprefix("@@SEISMIC@@")
            author, _, timestamp = payload.partition("\x1f")
            continue
        if not line or line not in paths or line in result:
            continue
        result[line] = LastTouch(author=author, timestamp=timestamp)
        if len(result) == len(paths):
            break
    return result


def load_codeowners(repo: Path) -> tuple[Path | None, list[tuple[str, str]]]:
    """Load CODEOWNERS rules in declaration order; the final matching rule wins."""

    candidates = (
        repo / ".github" / "CODEOWNERS",
        repo / "CODEOWNERS",
        repo / "docs" / "CODEOWNERS",
    )
    source = next((path for path in candidates if path.is_file()), None)
    if source is None:
        return None, []
    rules: list[tuple[str, str]] = []
    for raw_line in source.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        pattern = parts[0].lstrip("/")
        if pattern.endswith("/"):
            pattern += "*"
        rules.append((pattern, " ".join(parts[1:])))
    return source, rules


def match_owner(
    relative_path: str, source: Path | None, rules: list[tuple[str, str]]
) -> OwnerMatch:
    """Apply CODEOWNERS' last-match-wins rule to one repository-relative path."""

    owner = ""
    for pattern, candidate in rules:
        if fnmatch.fnmatch(relative_path, pattern) or fnmatch.fnmatch(
            relative_path, f"**/{pattern}"
        ):
            owner = candidate
    return OwnerMatch(owner=owner, source="codeowners" if owner and source else "")


def _git(repo: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise GitMetadataError(
            f"Git command failed in {repo}: git {' '.join(args)}: {exc}"
        ) from exc
    return result.stdout
