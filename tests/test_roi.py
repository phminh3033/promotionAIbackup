from src.promotion.mechanics import BaselineMetrics, compute_mechanic_result
from src.promotion.simulator import build_simulation_scenarios, simulate_scenarios
from src.roi.calculator import compute_roi_breakdown

BASELINE = BaselineMetrics(avg_daily_units=10, avg_price=100_000, unit_cost=60_000, promo_days=1, avg_daily_customers=5)

# Kịch bản test tường minh — không phụ thuộc DEFAULT cứng trong source.
_TEST_SCENARIOS = build_simulation_scenarios(
    allowed_mechanics=["discount_percent", "gift", "bogo"],
    max_discount_overrides={"discount_percent": 0.10},
    max_discount_pct=0.10,
    avg_price=BASELINE.avg_price,
)


def test_gross_profit_not_double_counted_for_percent_discount():
    """Regression test cho lỗi trừ trùng chi phí khuyến mãi khỏi lợi nhuận gộp.

    Với uplift=0 (không tăng sản lượng), giảm giá 10% chỉ nên làm lợi nhuận gộp giảm
    ĐÚNG BẰNG khoản giảm giá trên doanh thu (10% x giá x số lượng), KHÔNG bị trừ 2 lần.
    """
    result = compute_mechanic_result("discount_percent", 0.10, BASELINE, uplift_pct=0.0, uplift_source="test")
    total_units = BASELINE.avg_daily_units * BASELINE.promo_days
    expected_revenue = total_units * BASELINE.avg_price * 0.90
    expected_cogs = total_units * BASELINE.unit_cost
    expected_gp = expected_revenue - expected_cogs

    assert result.total_revenue == expected_revenue
    assert abs(result.gross_profit - expected_gp) < 1


def test_gift_cost_is_subtracted_once():
    result = compute_mechanic_result(
        "gift", 0.0, BASELINE, uplift_pct=0.0, uplift_source="test", gift_cost_per_unit=5_000
    )
    total_units = BASELINE.avg_daily_units * BASELINE.promo_days
    expected_gp = total_units * BASELINE.avg_price - total_units * BASELINE.unit_cost - total_units * 5_000
    assert abs(result.gross_profit - expected_gp) < 1


def test_roi_formula_consistent_with_incremental_gp():
    """ROI phải bằng incremental_gp / promotion_cost (không trừ promotion_cost thêm lần nữa)."""
    sim = simulate_scenarios(BASELINE, historical_uplifts={}, scenarios=_TEST_SCENARIOS)
    table = compute_roi_breakdown(sim.table, BASELINE)
    for _, row in table.iterrows():
        if row["chi_phi_khuyen_mai"] > 0:
            expected_roi = row["loi_nhuan_gop_tang_them"] / row["chi_phi_khuyen_mai"]
            assert abs(row["roi"] - expected_roi) < 1e-9


def test_no_promo_scenario_has_zero_cost_and_nan_roi():
    sim = simulate_scenarios(BASELINE, historical_uplifts={}, scenarios=_TEST_SCENARIOS)
    no_promo = sim.table[sim.table["mechanic"] == "no_promo"].iloc[0]
    assert no_promo["chi_phi_khuyen_mai"] == 0
    assert no_promo["roi"] is None or no_promo["roi"] != no_promo["roi"]  # None hoặc NaN


def test_higher_margin_product_has_better_roi_for_same_discount():
    high_margin = BaselineMetrics(avg_daily_units=10, avg_price=100_000, unit_cost=30_000, promo_days=5, avg_daily_customers=5)
    low_margin = BaselineMetrics(avg_daily_units=10, avg_price=100_000, unit_cost=85_000, promo_days=5, avg_daily_customers=5)

    r_high = compute_mechanic_result("discount_percent", 0.10, high_margin, uplift_pct=0.2, uplift_source="test")
    r_low = compute_mechanic_result("discount_percent", 0.10, low_margin, uplift_pct=0.2, uplift_source="test")

    assert r_high.margin_pct > r_low.margin_pct


def test_build_scenarios_one_per_mechanic_from_profile_not_hardcoded_af():
    scenarios = build_simulation_scenarios(
        allowed_mechanics=["discount_percent", "bundle", "gift"],
        max_discount_overrides={"discount_percent": 0.18, "bundle": 0.12},
        max_discount_pct=0.18,
        avg_price=100_000,
    )
    mechs = [s["mechanic"] for s in scenarios]
    assert mechs[0] == "no_promo"
    assert mechs.count("discount_percent") == 1
    assert "bundle" in mechs and "gift" in mechs
    # Không còn cặp 5% + 10% cứng trong source.
    assert not any("5%" in s["scenario"] and s["mechanic"] == "discount_percent" for s in scenarios)
    disc = next(s for s in scenarios if s["mechanic"] == "discount_percent")
    assert abs(disc["param"] - 0.18) < 1e-9
