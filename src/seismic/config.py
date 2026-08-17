"""Validated runtime configuration for Seismic."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_URI = "neo4j://127.0.0.1:7687"


class SeismicConfigError(ValueError):
    """Raised when environment configuration is unsafe or malformed."""


@dataclass(frozen=True, slots=True)
class SeismicConfig:
    """Connection, repository-safety, and traversal limits."""

    uri: str = DEFAULT_URI
    username: str = "neo4j"
    token: str | None = None
    database: str = "default"
    allowed_roots: tuple[Path, ...] = ()
    max_files: int = 20_000
    max_file_bytes: int = 1_000_000
    max_artifacts: int = 100_000
    max_relationships: int = 500_000
    max_hops: int = 8
    max_results: int = 200

    @classmethod
    def from_env(cls) -> SeismicConfig:
        """Load Seismic settings while keeping repository access explicit."""

        raw_roots = os.getenv("SEISMIC_ALLOWED_ROOTS", "")
        roots = tuple(
            Path(value).expanduser().resolve()
            for value in raw_roots.split(os.pathsep)
            if value.strip()
        )
        return cls(
            uri=os.getenv("SEISMIC_URI", DEFAULT_URI),
            username=os.getenv("SEISMIC_USERNAME", "neo4j"),
            token=os.getenv("SEISMIC_TOKEN") or os.getenv("SEISMIC_PASSWORD"),
            database=os.getenv("SEISMIC_DATABASE", "default"),
            allowed_roots=roots,
            max_files=_bounded_env("SEISMIC_MAX_FILES", 20_000, 1, 200_000),
            max_file_bytes=_bounded_env("SEISMIC_MAX_FILE_BYTES", 1_000_000, 1_024, 20_000_000),
            max_artifacts=_bounded_env("SEISMIC_MAX_ARTIFACTS", 100_000, 1, 1_000_000),
            max_relationships=_bounded_env("SEISMIC_MAX_RELATIONSHIPS", 500_000, 1, 5_000_000),
            max_hops=_bounded_env("SEISMIC_MAX_HOPS", 8, 1, 32),
            max_results=_bounded_env("SEISMIC_MAX_RESULTS", 200, 1, 5_000),
        )

    def validate_repo_path(self, repo_path: str) -> Path:
        """Resolve a repository path and reject paths outside configured roots."""

        candidate = Path(repo_path).expanduser().resolve(strict=True)
        if not candidate.is_dir():
            raise SeismicConfigError(f"repository path is not a directory: {candidate}")
        if not (candidate / ".git").exists():
            raise SeismicConfigError(f"repository path is not a Git checkout: {candidate}")
        if not self.allowed_roots:
            raise SeismicConfigError(
                "SEISMIC_ALLOWED_ROOTS is empty; configure at least one safe repository root"
            )
        if not any(
            candidate == root or candidate.is_relative_to(root) for root in self.allowed_roots
        ):
            raise SeismicConfigError(
                f"repository path {candidate} is outside SEISMIC_ALLOWED_ROOTS"
            )
        return candidate


def _bounded_env(name: str, default: int, minimum: int, maximum: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise SeismicConfigError(f"{name} must be an integer") from exc
    if not minimum <= value <= maximum:
        raise SeismicConfigError(f"{name} must be between {minimum} and {maximum}")
    return value
