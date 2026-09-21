"""AI Recommendation Engine: tổng hợp toàn bộ tín hiệu thành 1 Recommendation Card (mục XXII, XXIII).

Nguyên tắc (mục XIV, XXXVI): Recommendation PHẢI phụ thuộc dữ liệu thật của doanh nghiệp
(baseline, forecast, inventory, rules, objective) — không hard-code, không dùng LLM để quyết định.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from src.optimization.objective import OBJECTIVE_LABELS_VI
from src.promotion.mechanics import BaselineMetrics, MECHANIC_LABELS_VI
from src.recommendation.timing import TimingRecommendation

# [BUSINESS RULE]: dải bất định (uncertainty band) hiển thị quanh điểm ước tính trung tâm,
# rộng hơn khi uplift đến từ giả định (assumption) thay vì lịch sử thật (historical).
BAND_WIDTH_BY_SOURCE = {"assumption": 0.18, "historical": 0.10}
CONFIDENCE_PCT_BY_LABEL = {"Cao": (78, 90), "Trung bình": (60, 77), "Thấp": (40, 59)}


@dataclass
class RecommendationCard:
    objective_vi: str
    product_focus: str
    target_segment: str
    promotion_label: str
    timing_text: str
    timing_reason: str
    expected_customers_range: tuple[float, float]
    expected_demand_range: tuple[float, float]
    recommended_stock: float
    expected_revenue_range: tuple[float, float]
    expected_gp_range: tuple[float, float]
    expected_roi_range: tuple[float, float] | None
    risk_label: str
    confidence_pct_range: tuple[int, int]
    why_bullets: list[str] = field(default_factory=list)
    data_caveats: list[str] = field(default_factory=list)


def _band(value: float, source: str, round_to_int: bool = True) -> tuple[float, float]:
    width = BAND_WIDTH_BY_SOURCE.get(source, 0.18)
    a, b = value * (1 - width), value * (1 + width)
    # Với value âm, value*(1-width) > value*(1+width) — luôn sắp lại (nhỏ, lớn) để tránh
    # hiển thị khoảng đảo ngược kiểu "-100%–-200%".
    lo, hi = (a, b) if a <= b else (b, a)
    if round_to_int:
        # Chỉ làm tròn số nguyên cho các đại lượng đếm được (khách hàng, sản lượng, tiền VNĐ).
        # KHÔNG áp dụng cho tỷ lệ (ROI) — round() không có ndigits sẽ làm tròn về đơn vị "1.0"
        # (tức 100 điểm %), quá thô khi hiển thị dạng phần trăm.
        return (round(lo), round(hi))
    return (lo, hi)


def _assess_risk(uplift_source: str, margin_after: float, min_margin: float, stockout_risk: str | None) -> str:
    risk_points = 0
    if uplift_source == "assumption":
        risk_points += 1
    if margin_after < min_margin + 0.03:
        risk_points += 1
    if stockout_risk == "HIGH":
        risk_points += 2
    elif stockout_risk == "MEDIUM":
        risk_points += 1

    if risk_points >= 3:
        return "Cao"
    if risk_points >= 1:
        return "Trung bình"
    return "Thấp"


def build_recommendation_card(
    objective: str,
    chosen_scenario: pd.Series,
    baseline: BaselineMetrics,
    business_profile,
    product_focus: str,
    target_segment: str,
    timing: TimingRecommendation,
    recommended_stock: float,
    confidence_label_forecast: str,
    why_bullets: list[str],
    stockout_risk: str | None = None,
    data_caveats: list[str] | None = None,
) -> RecommendationCard:
    source = chosen_scenario.get("nguon_uplift", "assumption")
    source_key = "historical" if str(source).startswith("historical") else "assumption"

    customers_range = _band(chosen_scenario["khach_hang_uoc_tinh"], source_key)
    demand_range = _band(chosen_scenario["san_luong"], source_key)
    revenue_range = _band(chosen_scenario["doanh_thu"], source_key)
    gp_range = _band(chosen_scenario["loi_nhuan_gop"], source_key)
    roi_val = chosen_scenario.get("roi")
    roi_range = _band(roi_val, source_key, round_to_int=False) if pd.notna(roi_val) else None

    risk_label = _assess_risk(
        source_key,
        chosen_scenario["margin"],
        business_profile.min_margin_pct,
        stockout_risk,
    )

    conf_band = CONFIDENCE_PCT_BY_LABEL.get(confidence_label_forecast, (40, 59))
    if source_key == "assumption":
        conf_band = (max(30, conf_band[0] - 10), max(45, conf_band[1] - 10))

    mechanic_label = MECHANIC_LABELS_VI.get(chosen_scenario["mechanic"], chosen_scenario["mechanic"])
    param = chosen_scenario["tham_so"]
    if chosen_scenario["mechanic"] in ("discount_percent", "bundle", "coupon", "member_price", "buy_more_save_more"):
        promotion_label = f"{mechanic_label} {param:.0%}" if param else mechanic_label
    else:
        promotion_label = mechanic_label

    return RecommendationCard(
        objective_vi=OBJECTIVE_LABELS_VI.get(objective, objective),
        product_focus=product_focus,
        target_segment=target_segment,
        promotion_label=promotion_label,
        timing_text=timing.suggested_window_text,
        timing_reason=timing.best_weekdays_reason,
        expected_customers_range=customers_range,
        expected_demand_range=demand_range,
        recommended_stock=recommended_stock,
        expected_revenue_range=revenue_range,
        expected_gp_range=gp_range,
        expected_roi_range=roi_range,
        risk_label=risk_label,
        confidence_pct_range=conf_band,
        why_bullets=why_bullets,
        data_caveats=data_caveats or [],
    )
