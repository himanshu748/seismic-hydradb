"""Run Seismic's self-authored graph retrieval evaluation against TF-IDF."""

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from benchmarks.provenance import git_provenance
from benchmarks.similarity_baseline import SimilarityIndex
from seismic.config import SeismicConfig
from seismic.db import HydraDB
from seismic.models import RepositoryGraph
from seismic.parser import RepositoryParser
from seismic.tools import SeismicService

PROJECT_ROOT = Path(__file__).parents[1]
DEFAULT_TASKS = Path(__file__).with_name("tasks.json")
DEFAULT_OUTPUT = Path(__file__).parent / "results" / "track02-evaluation.json"


def main() -> None:
    """Index configured repositories, evaluate retrieval and write raw JSON evidence."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", type=Path, default=DEFAULT_TASKS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    result = run_evaluation(arguments.tasks)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))


def run_evaluation(tasks_path: Path) -> dict[str, Any]:
    """Execute every annotated task with graph, TF-IDF and graph-first hybrid ranking."""

    definition = json.loads(tasks_path.read_text(encoding="utf-8"))
    repo_paths = {
        repo_id: (PROJECT_ROOT / relative).resolve()
        for repo_id, relative in definition["repositories"].items()
    }
    environment = SeismicConfig.from_env()
    config = SeismicConfig(
        uri=environment.uri,
        username=environment.username,
        token=environment.token,
        database=environment.database,
        allowed_roots=tuple(sorted(repo_paths.values())),
    )
    parser = RepositoryParser(config)
    graphs: dict[str, RepositoryGraph] = {}
    baselines: dict[str, SimilarityIndex] = {}
    indexed: dict[str, dict[str, object]] = {}
    with HydraDB(config) as db:
        db.verify_connection()
        db.setup_schema()
        service = SeismicService(db, config)
        for repo_id, path in repo_paths.items():
            graphs[repo_id] = parser.parse(str(path), explicit_repo_key=repo_id)
            baselines[repo_id] = SimilarityIndex(graphs[repo_id])
            indexed[repo_id] = dict(service.index_repository(str(path), repo_id=repo_id))

        details: list[dict[str, Any]] = []
        graph_latencies: list[float] = []
        baseline_latencies: list[float] = []
        for task in definition["tasks"]:
            expected = list(task["expected"])
            limit = max(1, len(expected))
            started = time.perf_counter()
            graph_report = service.analyze_change(
                task["repo_id"],
                [task["target"]],
                max_hops=int(task["max_hops"]),
                limit=limit,
            )
            graph_latency = (time.perf_counter() - started) * 1_000
            started = time.perf_counter()
            baseline_ranked = baselines[task["repo_id"]].rank(task["target"], limit)
            baseline_latency = (time.perf_counter() - started) * 1_000
            graph_keys = [str(item["logical_key"]) for item in graph_report["results"]]
            baseline_keys = [item.logical_key for item in baseline_ranked]
            hybrid_keys = _unique(graph_keys + baseline_keys)[:limit]
            should_abstain = bool(task.get("should_abstain", False))
            graph_latencies.append(graph_latency)
            baseline_latencies.append(baseline_latency)
            details.append(
                {
                    "id": task["id"],
                    "repo_id": task["repo_id"],
                    "target": task["target"],
                    "expected": expected,
                    "limit": limit,
                    "should_abstain": should_abstain,
                    "graph": {
                        "retrieved": graph_keys,
                        **_metrics(expected, graph_keys, limit),
                        "abstention_correct": should_abstain and not graph_keys,
                        "exact_paths_valid": all(
                            _path_valid(task["target"], result)
                            for result in graph_report["results"]
                        ),
                        "latency_ms": round(graph_latency, 3),
                    },
                    "tfidf": {
                        "retrieved": baseline_keys,
                        "scores": [round(item.score, 6) for item in baseline_ranked],
                        **_metrics(expected, baseline_keys, limit),
                        "abstention_correct": should_abstain and not baseline_keys,
                        "latency_ms": round(baseline_latency, 3),
                    },
                    "hybrid": {
                        "retrieved": hybrid_keys,
                        **_metrics(expected, hybrid_keys, limit),
                        "abstention_correct": should_abstain and not hybrid_keys,
                    },
                    "warnings": graph_report["warnings"],
                    "unresolved_targets": graph_report["unresolved_targets"],
                }
            )

    valid = [detail for detail in details if not detail["should_abstain"]]
    abstention = [detail for detail in details if detail["should_abstain"]]
    return {
        "kind": "self-authored Track 02 evaluation",
        "generated_at": datetime.now(UTC).isoformat(),
        "commit": _git_commit(),
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "hydradb_uri": config.uri,
            "hydradb_commit": os.getenv("SEISMIC_HYDRADB_COMMIT", "unspecified"),
            **git_provenance(PROJECT_ROOT, prefix="seismic"),
        },
        "dataset": {
            "path": str(tasks_path.relative_to(PROJECT_ROOT)),
            "tasks": len(details),
            "supported_tasks": len(valid),
            "abstention_tasks": len(abstention),
            "repositories": indexed,
        },
        "summary": {
            "graph": _aggregate(valid, abstention, "graph", graph_latencies),
            "tfidf": _aggregate(valid, abstention, "tfidf", baseline_latencies),
            "hybrid": _aggregate(valid, abstention, "hybrid", []),
        },
        "tasks": details,
    }


def _metrics(expected: list[str], retrieved: list[str], limit: int) -> dict[str, float]:
    if not expected:
        return {"precision_at_k": 0.0, "recall_at_k": 0.0, "mrr": 0.0}
    expected_set = set(expected)
    hits = len(expected_set & set(retrieved[:limit]))
    first = next(
        (index for index, key in enumerate(retrieved[:limit], start=1) if key in expected_set),
        None,
    )
    return {
        "precision_at_k": round(hits / limit, 4),
        "recall_at_k": round(hits / len(expected_set), 4),
        "mrr": round(0.0 if first is None else 1.0 / first, 4),
    }


def _aggregate(
    valid: list[dict[str, Any]],
    abstention: list[dict[str, Any]],
    system: str,
    latencies: list[float],
) -> dict[str, float | int]:
    result: dict[str, float | int] = {
        "precision_at_k": round(
            statistics.fmean(item[system]["precision_at_k"] for item in valid), 4
        ),
        "recall_at_k": round(statistics.fmean(item[system]["recall_at_k"] for item in valid), 4),
        "mrr": round(statistics.fmean(item[system]["mrr"] for item in valid), 4),
        "abstention_correct": sum(bool(item[system]["abstention_correct"]) for item in abstention),
        "abstention_total": len(abstention),
    }
    if system == "graph":
        result["exact_path_tasks_valid"] = sum(
            bool(item[system]["exact_paths_valid"]) for item in valid
        )
        result["exact_path_tasks_total"] = len(valid)
    if latencies:
        result["latency_p50_ms"] = round(_percentile(latencies, 0.50), 3)
        result["latency_p95_ms"] = round(_percentile(latencies, 0.95), 3)
    return result


def _path_valid(target: str, result: dict[str, Any]) -> bool:
    nodes = result["nodes"]
    hops = result["hops"]
    return bool(
        nodes
        and nodes[0]["logical_key"] == target
        and nodes[-1]["logical_key"] == result["logical_key"]
        and len(hops) == result["hop_distance"]
        and len(nodes) == len(hops) + 1
    )


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _percentile(values: list[float], quantile: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower = int(position)
    upper = min(len(ordered) - 1, lower + 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _git_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "uncommitted"


if __name__ == "__main__":
    main()
