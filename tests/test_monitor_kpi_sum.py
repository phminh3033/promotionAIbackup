"""KPI Monitor — cộng số liệu thực tế bỏ NaN."""
from __future__ import annotations

import math

import pandas as pd

from ui.pages.monitor import _records_without_nan, _sum_field, _sum_series


def test_sum_field_skips_nan_and_none():
    rows = [
        {"revenue": 25_300_024.0, "customers": 120, "gp": 2_450_233.0},
        {"revenue": float("nan"), "customers": 50, "gp": None},
        {"revenue": 10_000_000.0, "customers": None, "gp": 500_000.0},
    ]
    assert _sum_field(rows, "revenue") == 35_300_024.0
    assert _sum_field(rows, "customers") == 170.0
    assert _sum_field(rows, "gp") == 2_950_233.0


def test_sum_field_all_missing_returns_none():
    rows = [{"revenue": None}, {"revenue": float("nan")}]
    assert _sum_field(rows, "revenue") is None


def test_sum_series_skipna():
    series = pd.Series([1.0, float("nan"), 3.0])
    assert _sum_series(series) == 4.0
    assert _sum_series(pd.Series([float("nan"), float("nan")])) is None


def test_records_without_nan_replaces_nan_with_none():
    frame = pd.DataFrame(
        {
            "date": ["2026-09-26", "2026-09-27"],
            "revenue": [25_300_024.0, float("nan")],
            "customers": [120.0, 50.0],
        }
    )
    rows = _records_without_nan(frame)
    assert rows[0]["revenue"] == 25_300_024.0
    assert rows[1]["revenue"] is None
    assert rows[1]["customers"] == 50.0
    # Không còn nan để làm hỏng sum
    total = _sum_field(rows, "revenue")
    assert total == 25_300_024.0
    assert math.isfinite(total)
