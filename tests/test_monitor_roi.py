"""ROI thực tế trên Monitor — fallback chi phí + công thức incremental GP."""
from __future__ import annotations

from types import SimpleNamespace

import pandas as pd

from src.monitoring.campaign_monitor import compute_actual_roi, resolve_promo_cost
from ui.pages.monitor import _roi_from_record


def test_compute_actual_roi_basic():
    # 2 ngày GP=100, no_promo=40/ngày → incremental=120; cost=60 → ROI=2.0
    roi = compute_actual_roi([100, 100], no_promo_gp_per_day=40, promo_cost=60)
    assert roi is not None
    assert abs(roi - 2.0) < 1e-9


def test_compute_actual_roi_skips_missing_gp_days():
    roi = compute_actual_roi([100, None, float("nan"), 50], no_promo_gp_per_day=10, promo_cost=50)
    # days=2, incremental=(150 - 20)=130, roi=130/50=2.6
    assert roi is not None
    assert abs(roi - 2.6) < 1e-9


def test_compute_actual_roi_requires_cost_and_baseline():
    assert compute_actual_roi([100], no_promo_gp_per_day=10, promo_cost=0) is None
    assert compute_actual_roi([100], no_promo_gp_per_day=None, promo_cost=50) is None
    assert compute_actual_roi([], no_promo_gp_per_day=10, promo_cost=50) is None


def test_resolve_promo_cost_prefers_actual_then_expected_then_budget():
    assert resolve_promo_cost(actual_cost=10, expected_promo_cost=20, budget=30) == 10
    assert resolve_promo_cost(actual_cost=0, expected_promo_cost=20, budget=30) == 20
    assert resolve_promo_cost(actual_cost=None, expected_promo_cost=None, budget=30) == 30
    assert resolve_promo_cost(actual_cost=0, expected_promo_cost=0, budget=0) is None


def test_resolve_promo_cost_derives_from_forecast_roi():
    # incremental = 80 - 10*5 = 30; roi=-0.5 → cost = 30/-0.5 = -60 → ignored (≤0)
    # incremental = 200 - 10*5 = 150; roi=0.5 → cost = 300
    forecast = {
        "expected_roi_range": [0.4, 0.6],
        "expected_gp_range": [180, 220],
        "no_promo_gp_per_day": 10,
        "promo_days": 5,
    }
    cost = resolve_promo_cost(forecast=forecast)
    assert cost is not None
    assert abs(cost - 300.0) < 1e-6


def test_roi_from_record_uses_budget_when_cost_missing():
    record = SimpleNamespace(
        roi_actual=None,
        forecast={
            "no_promo_gp_per_day": 40.0,
            "budget": 60.0,
            "expected_promo_cost": None,
        },
        actual={"daily_rows": [{"gp": 100}, {"gp": 100}], "promo_cost_actual": 0},
    )
    compared = pd.DataFrame({"gp": [100.0, 100.0]})
    roi = _roi_from_record(record, compared)
    assert roi is not None
    assert abs(roi - 2.0) < 1e-9
