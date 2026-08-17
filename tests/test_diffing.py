"""Unified-diff parsing tests for automatic graph target discovery."""

import pytest

from seismic.diffing import parse_unified_diff


def test_extracts_modified_added_and_deleted_line_ranges() -> None:
    changes = parse_unified_diff(
        """diff --git a/src/app.py b/src/app.py
--- a/src/app.py
+++ b/src/app.py
@@ -4,2 +4,3 @@
-old
+new
diff --git a/src/removed.py b/src/removed.py
--- a/src/removed.py
+++ /dev/null
@@ -8,2 +0,0 @@
-gone
"""
    )

    assert [(change.path, change.ranges) for change in changes] == [
        ("src/app.py", ((4, 6),)),
        ("src/removed.py", ((8, 9),)),
    ]


def test_merges_adjacent_ranges_and_rejects_path_escape() -> None:
    changes = parse_unified_diff(
        """diff --git a/src/app.py b/src/app.py
--- a/src/app.py
+++ b/src/app.py
@@ -2 +2 @@
-a
+b
@@ -3 +3 @@
-c
+d
"""
    )

    assert changes[0].ranges == ((2, 3),)
    with pytest.raises(ValueError, match="stay inside"):
        parse_unified_diff("--- a/good.py\n+++ b/../secret.py\n@@ -1 +1 @@\n")
