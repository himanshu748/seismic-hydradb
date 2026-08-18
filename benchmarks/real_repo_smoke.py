"""Run a graph-grounded Seismic smoke across real Git repositories."""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from seismic.config import SeismicConfig
from seismic.db import HydraDB
from seismic.models import RepositoryGraph
from seismic.parser import RepositoryParser
from seismic.tools import SeismicService

PROJECT_ROOT = Path(__file__).parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "benchmarks" / "results" / "real-repositories.json"


def main() -> None:
    """Index supplied repositories and verify every returned impact path."""

    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument(
        "--repo",
        action="append",
        required=True,
        metavar="NAME=PATH",
        help="A stable repository label and local Git checkout path.",
    )
    argument_parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = argument_parser.parse_args()
    repositories = dict(_parse_repository(value) for value in arguments.repo)
    result = run_smoke(repositories)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))


def run_smoke(repositories: dict[str, Path]) -> dict[str, Any]:
    """Return reproducible path-validity evidence for several real checkouts."""

    resolved = {name: path.expanduser().resolve() for name, path in repositories.items()}
    environment = SeismicConfig.from_env()
    config = SeismicConfig(
        uri=environment.uri,
        username=environment.username,
        token=environment.token,
        database=environment.database,
        allowed_roots=tuple(resolved.values()),
    )
    parser = RepositoryParser(config)
    details: list[dict[str, Any]] = []
    with HydraDB(config) as db:
        db.verify_connection()
        db.setup_schema()
        service = SeismicService(db, config)
        for name, path in resolved.items():
            repo_id = f"real-{name}"
            graph = parser.parse(str(path), explicit_repo_key=repo_id)
            indexed = service.index_repository(str(path), repo_id=repo_id)
            candidates = _candidate_targets(graph)
            selected = (
                service.analyze_change(repo_id, [candidates[0]], max_hops=4, limit=20)
                if candidates
                else None
            )
            results = selected["results"] if selected is not None else []
            valid_paths = all(_path_valid(result) for result in results)
            details.append(
                {
                    "repo_id": repo_id,
                    "commit_sha": graph.commit_sha,
                    "artifacts": indexed["artifacts"],
                    "relationships": indexed["relationships"],
                    "selection_strategy": "highest direct incoming dependency edge count",
                    "candidate_targets_considered": len(candidates),
                    "selected_target": None if selected is None else selected["targets"][0],
                    "gate_decision": None if selected is None else selected["gate"]["decision"],
                    "supported_impacts": len(results),
                    "exact_paths_valid": valid_paths,
                    "sample_impacts": [
                        {
                            "logical_key": result["logical_key"],
                            "kind": result["kind"],
                            "hop_distance": result["hop_distance"],
                        }
                        for result in results[:8]
                    ],
                    "warnings": graph.warnings,
                }
            )

    supported = [detail for detail in details if detail["supported_impacts"]]
    return {
        "kind": "real repository portability smoke",
        "generated_at": datetime.now(UTC).isoformat(),
        "seismic_commit": _seismic_commit(),
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "hydradb_uri": config.uri,
        },
        "summary": {
            "repositories_indexed": len(details),
            "repositories_with_supported_impacts": len(supported),
            "supported_impacts": sum(int(detail["supported_impacts"]) for detail in details),
            "all_returned_paths_valid": all(
                bool(detail["exact_paths_valid"]) for detail in details
            ),
        },
        "repositories": details,
    }


def _candidate_targets(graph: RepositoryGraph) -> list[str]:
    incoming = Counter(relationship.target_id for relationship in graph.relationships)
    candidates = [
        artifact
        for artifact in graph.artifacts
        if artifact.kind in {"function", "class"} and incoming[artifact.id] > 0
    ]
    candidates.sort(key=lambda artifact: (-incoming[artifact.id], artifact.logical_key))
    return [artifact.logical_key for artifact in candidates]


def _path_valid(result: dict[str, Any]) -> bool:
    nodes = result["nodes"]
    hops = result["hops"]
    if not (
        nodes
        and nodes[-1]["logical_key"] == result["logical_key"]
        and len(hops) == result["hop_distance"]
        and len(nodes) == len(hops) + 1
    ):
        return False
    return all(
        hop["source"] == nodes[index]["logical_key"]
        and hop["target"] == nodes[index + 1]["logical_key"]
        and bool(hop["type"])
        and 0.0 <= float(hop["confidence"]) <= 1.0
        for index, hop in enumerate(hops)
    )


def _parse_repository(value: str) -> tuple[str, Path]:
    name, separator, raw_path = value.partition("=")
    if not separator or not name.strip() or not raw_path.strip():
        raise argparse.ArgumentTypeError("--repo must use NAME=PATH")
    return name.strip(), Path(raw_path.strip())


def _seismic_commit() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


if __name__ == "__main__":
    main()
