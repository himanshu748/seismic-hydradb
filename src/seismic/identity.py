"""Collision-checked numeric identities compatible with HydraDB path procedures."""

from __future__ import annotations

import hashlib
import re

MAX_VERTEX_ID = (1 << 63) - 1
_SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


def stable_id(domain: str, key: str) -> int:
    """Return a deterministic positive 63-bit ID for a domain-separated key."""

    digest = hashlib.blake2b(f"seismic:{domain}:{key}".encode(), digest_size=8).digest()
    value = int.from_bytes(digest, "big") & MAX_VERTEX_ID
    return value or 1


def relationship_id(snapshot_key: str, kind: str, source_id: int, target_id: int) -> int:
    """Return a deterministic relationship ID for one snapshot edge."""

    return stable_id("relationship", f"{snapshot_key}:{kind}:{source_id}:{target_id}")


def repo_key(name: str, absolute_path: str) -> str:
    """Build a readable repository key that is stable for one absolute checkout."""

    slug = _SLUG_PATTERN.sub("-", name.casefold()).strip("-") or "repository"
    suffix = hashlib.blake2b(absolute_path.encode(), digest_size=4).hexdigest()
    return f"{slug}-{suffix}"
