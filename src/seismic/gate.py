"""Deterministic change policy built only from Seismic's graph evidence."""

from __future__ import annotations

from collections.abc import Iterable

from seismic.models import ChangeGate, GateDecision, ImpactResult

POLICY_VERSION = "seismic-change-gate-v1"
BLOCK_RISK_SCORE = 75.0


def build_change_gate(
    *,
    targets: list[str],
    results: list[ImpactResult],
    unresolved_targets: list[str],
    evidence_complete: bool = True,
) -> ChangeGate:
    """Convert supported paths into a conservative action for a coding agent."""

    max_risk_score = max((result["risk_score"] for result in results), default=0.0)
    incident_pairs = sum(result["incident_pair_count"] for result in results)
    required_tests = _unique(
        result["logical_key"] for result in results if result["kind"] == "test"
    )
    affected_entrypoints = _unique(
        result["logical_key"] for result in results if result["kind"] == "entrypoint"
    )
    verification_commands = [f"pytest {test}" for test in required_tests]
    affected_owners = _unique(result["owner"] for result in results if result["owner"])

    decision: GateDecision
    if incident_pairs or max_risk_score >= BLOCK_RISK_SCORE:
        decision = "block"
    elif unresolved_targets or not targets or results or not evidence_complete:
        decision = "review"
    else:
        decision = "safe"

    reasons: list[str] = []
    if incident_pairs:
        reasons.append(
            f"{incident_pairs} prior trigger-impact incident pair"
            f"{'s' if incident_pairs != 1 else ''} match this change."
        )
    if max_risk_score >= BLOCK_RISK_SCORE:
        reasons.append(
            f"The highest supported risk score is {max_risk_score:.2f}, at or above the "
            f"{BLOCK_RISK_SCORE:.0f} block threshold."
        )
    if results:
        reasons.append(
            f"HydraDB supports {len(results)} downstream impact path"
            f"{'s' if len(results) != 1 else ''}."
        )
    if unresolved_targets:
        reasons.append(
            f"{len(unresolved_targets)} change target"
            f"{'s could' if len(unresolved_targets) != 1 else ' could'} not be resolved."
        )
    if not targets:
        reasons.append("No indexed symbol could be resolved from the supplied change.")
    if not evidence_complete:
        reasons.append(
            "The active snapshot contains unresolved parser evidence, so Seismic cannot "
            "issue a safe decision."
        )
    if decision == "safe":
        reasons.append("No downstream dependency path is supported within the requested bound.")

    headlines = {
        "safe": "No supported downstream impact",
        "review": "Review graph evidence before editing",
        "block": "Stop and investigate before editing",
    }
    if decision == "block":
        summary = (
            "The graph contains high-risk or prior-incident evidence. Resolve it before the "
            "agent changes code."
        )
    elif decision == "review":
        summary = (
            "Inspect the exact paths, cover the listed tests and review affected entrypoints "
            "before changing code."
            if results
            else "The available graph cannot justify a safe decision for this change."
        )
    else:
        summary = (
            "The target resolved, but HydraDB found no supported downstream path within the "
            "requested traversal bound."
        )

    return {
        "policy": POLICY_VERSION,
        "decision": decision,
        "headline": headlines[decision],
        "summary": summary,
        "max_risk_score": round(max_risk_score, 2),
        "impacted_artifacts": len(results),
        "required_tests": required_tests,
        "verification_commands": verification_commands,
        "affected_entrypoints": affected_entrypoints,
        "affected_owners": affected_owners,
        "reasons": reasons,
    }


def _unique(values: Iterable[object]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        item = str(value)
        if item and item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered
