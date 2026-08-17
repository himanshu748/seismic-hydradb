"""Small bounded unified-diff parser for automatic change-target discovery."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import PurePosixPath

MAX_DIFF_BYTES = 250_000
MAX_DIFF_FILES = 100
MAX_DIFF_HUNKS = 1_000
_HUNK = re.compile(
    r"^@@ -(?P<old>\d+)(?:,(?P<old_count>\d+))? "
    r"\+(?P<new>\d+)(?:,(?P<new_count>\d+))? @@"
)


@dataclass(frozen=True, slots=True)
class ChangedFile:
    """One safe repository path plus line ranges touched by a patch."""

    path: str
    ranges: tuple[tuple[int, int], ...]


def parse_unified_diff(value: str) -> list[ChangedFile]:
    """Extract bounded file and line ranges without applying or trusting the patch."""

    if not isinstance(value, str):
        raise ValueError("diff must be a string")
    if not value.strip():
        raise ValueError("diff must not be empty")
    if len(value.encode("utf-8")) > MAX_DIFF_BYTES:
        raise ValueError(f"diff must be at most {MAX_DIFF_BYTES} bytes")

    old_path = ""
    current_path = ""
    ranges: dict[str, list[tuple[int, int]]] = {}
    hunk_count = 0
    for line in value.splitlines():
        if line.startswith("--- "):
            old_path = _patch_path(line[4:])
            continue
        if line.startswith("+++ "):
            new_path = _patch_path(line[4:])
            current_path = new_path or old_path
            if current_path and current_path not in ranges:
                if len(ranges) >= MAX_DIFF_FILES:
                    raise ValueError(f"diff may contain at most {MAX_DIFF_FILES} files")
                ranges[current_path] = []
            continue
        match = _HUNK.match(line)
        if match is None or not current_path:
            continue
        hunk_count += 1
        if hunk_count > MAX_DIFF_HUNKS:
            raise ValueError(f"diff may contain at most {MAX_DIFF_HUNKS} hunks")
        old_start = int(match.group("old"))
        old_count = int(match.group("old_count") or "1")
        new_start = int(match.group("new"))
        new_count = int(match.group("new_count") or "1")
        if new_count > 0:
            ranges[current_path].append((new_start, new_start + new_count - 1))
        elif old_count > 0:
            ranges[current_path].append((old_start, old_start + old_count - 1))

    return [
        ChangedFile(path=path, ranges=tuple(_merge_ranges(file_ranges)))
        for path, file_ranges in ranges.items()
    ]


def _patch_path(raw: str) -> str:
    value = raw.split("\t", 1)[0].strip()
    if value == "/dev/null":
        return ""
    if value.startswith('"'):
        try:
            decoded = ast.literal_eval(value)
        except (SyntaxError, ValueError) as exc:
            raise ValueError("diff contains an invalid quoted path") from exc
        if not isinstance(decoded, str):
            raise ValueError("diff contains an invalid path")
        value = decoded
    if value.startswith(("a/", "b/")):
        value = value[2:]
    path = PurePosixPath(value)
    if path.is_absolute() or not value or ".." in path.parts:
        raise ValueError("diff paths must stay inside the repository")
    return path.as_posix()


def _merge_ranges(values: list[tuple[int, int]]) -> list[tuple[int, int]]:
    merged: list[tuple[int, int]] = []
    for start, end in sorted(values):
        if not merged or start > merged[-1][1] + 1:
            merged.append((start, end))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
    return merged
