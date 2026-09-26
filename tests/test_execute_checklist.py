"""Checklist readiness trên Execute — điều kiện launch."""
from __future__ import annotations

from ui.pages.execute import checklist_progress


def test_checklist_progress_partial():
    checks = {"a": True, "b": False, "c": True}
    done, total, pct = checklist_progress(checks, ["a", "b", "c"])
    assert done == 2
    assert total == 3
    assert pct == 67


def test_checklist_progress_all_checked_enables_launch_math():
    ids = [f"t{i}" for i in range(12)]
    checks = {tid: True for tid in ids}
    done, total, pct = checklist_progress(checks, ids)
    assert done == 12
    assert total == 12
    assert pct == 100


def test_checklist_progress_empty():
    assert checklist_progress({}, []) == (0, 0, 0)
