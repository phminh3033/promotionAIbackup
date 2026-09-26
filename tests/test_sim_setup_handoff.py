"""Handoff Simulate → Execute: snapshot thiết lập mô phỏng."""
from __future__ import annotations

from datetime import date

from src.promotion.sim_setup import (
    budget_from_meta,
    build_setup_snapshot,
    campaign_window_from_meta,
    scope_label_from_meta,
)


def test_build_setup_snapshot_persists_form_fields():
    snap = build_setup_snapshot(
        scope="Một Danh mục",
        scope_value="Thiết bị y tế",
        promo_days=7,
        gift_cost=5000.0,
        campaign_start=date(2026, 9, 26),
        campaign_end=date(2026, 10, 2),
        budget=20_000_000.0,
        max_discount_pct=0.30,
        min_margin_pct=0.15,
    )
    assert snap["scope"] == "Một Danh mục"
    assert snap["scope_value"] == "Thiết bị y tế"
    assert snap["campaign_start"] == "2026-09-26"
    assert snap["campaign_end"] == "2026-10-02"
    assert snap["promo_days"] == 7
    assert snap["budget"] == 20_000_000.0
    assert snap["gift_cost_per_unit"] == 5000.0
    assert snap["max_discount_pct"] == 0.30
    assert snap["min_margin_pct"] == 0.15


def test_campaign_window_prefers_saved_dates_not_today():
    meta = {
        "campaign_start": "2026-09-26",
        "campaign_end": "2026-10-02",
        "promo_days": 7,
    }
    start, end, days = campaign_window_from_meta(meta)
    assert start == date(2026, 9, 26)
    assert end == date(2026, 10, 2)
    assert days == 7


def test_budget_and_scope_label_for_execute():
    meta = build_setup_snapshot(
        scope="Một Danh mục",
        scope_value="Thiết bị y tế",
        promo_days=7,
        gift_cost=5000.0,
        campaign_start=date(2026, 9, 26),
        campaign_end=date(2026, 10, 2),
        budget=20_000_000.0,
        max_discount_pct=0.3,
        min_margin_pct=0.15,
    )
    assert budget_from_meta(meta, fallback=0) == 20_000_000.0
    assert scope_label_from_meta(meta) == "Theo Danh mục · Thiết bị y tế"
    assert scope_label_from_meta({"scope": "Một SKU cụ thể", "scope_value": "SP001"}) == "Theo SKU · SP001"
