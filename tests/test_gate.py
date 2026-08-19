"""Fast tests for the conservative agent-facing change gate."""

from __future__ import annotations

from seismic.gate import build_change_gate
from seismic.models import ImpactResult


def test_gate_returns_review_with_tests_entrypoints_and_owners() -> None:
    results = [
        _impact("tests/test_checkout.py::test_total", "test", 61.0, owner="quality"),
        _impact("pyproject.toml::script::sample", "entrypoint", 48.0, owner="platform"),
    ]

    gate = build_change_gate(
        targets=["src/sample_app/pricing.py::calculate"],
        results=results,
        unresolved_targets=[],
    )

    assert gate["decision"] == "review"
    assert gate["required_tests"] == ["tests/test_checkout.py::test_total"]
    assert gate["verification_commands"] == ["pytest tests/test_checkout.py::test_total"]
    assert gate["affected_entrypoints"] == ["pyproject.toml::script::sample"]
    assert gate["affected_owners"] == ["quality", "platform"]
    assert gate["max_risk_score"] == 61.0


def test_gate_blocks_high_risk_or_prior_incident_evidence() -> None:
    high_risk = build_change_gate(
        targets=["src/a.py::run"],
        results=[_impact("src/api.py::handler", "function", 75.0)],
        unresolved_targets=[],
    )
    prior_incident = build_change_gate(
        targets=["src/a.py::run"],
        results=[_impact("src/api.py::handler", "function", 42.0, incident_pairs=1)],
        unresolved_targets=[],
    )

    assert high_risk["decision"] == "block"
    assert prior_incident["decision"] == "block"
    assert "prior trigger-impact incident pair" in prior_incident["reasons"][0]


def test_gate_is_safe_only_when_a_target_resolves_without_supported_impact() -> None:
    safe = build_change_gate(
        targets=["src/leaf.py::format"],
        results=[],
        unresolved_targets=[],
    )
    unresolved = build_change_gate(
        targets=["src/missing.py::run"],
        results=[],
        unresolved_targets=["src/missing.py::run"],
    )
    empty_diff = build_change_gate(targets=[], results=[], unresolved_targets=[])

    assert safe["decision"] == "safe"
    assert unresolved["decision"] == "review"
    assert empty_diff["decision"] == "review"


def test_gate_withholds_safe_when_snapshot_evidence_is_incomplete() -> None:
    gate = build_change_gate(
        targets=["src/leaf.py::format"],
        results=[],
        unresolved_targets=[],
        evidence_complete=False,
    )

    assert gate["decision"] == "review"
    assert "cannot issue a safe decision" in gate["reasons"][-1]


def _impact(
    logical_key: str,
    kind: str,
    risk_score: float,
    *,
    owner: str = "",
    incident_pairs: int = 0,
) -> ImpactResult:
    return {
        "target": "src/a.py::run",
        "artifact_key": f"snapshot::{logical_key}",
        "logical_key": logical_key,
        "kind": kind,
        "path": logical_key.split("::", 1)[0],
        "qualified_name": logical_key.rsplit("::", 1)[-1],
        "hop_distance": 1,
        "risk_score": risk_score,
        "score_components": {},
        "resolution_confidence": 1.0,
        "owner": owner,
        "owner_source": "CODEOWNERS" if owner else "",
        "last_author": "",
        "last_modified": "",
        "incident_count": incident_pairs,
        "incident_pair_count": incident_pairs,
        "reason": "Supported by one graph hop.",
        "nodes": [],
        "hops": [],
    }
