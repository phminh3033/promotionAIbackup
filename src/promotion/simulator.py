"""Promotion Simulator: mô-đun trung tâm so sánh nhiều kịch bản khuyến mãi (mục XVI yêu cầu gốc)."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.promotion.mechanics import (
    MECHANIC_CALC_KIND,
    MECHANIC_LABELS_VI,
    BaselineMetrics,
    compute_mechanic_result,
    default_unit_uplift,
)

DISCLAIMER_VI = (
    "Đây là mô phỏng dựa trên historical response / elasticity assumption, "
    "chưa phải causal uplift đã được chứng minh. Kết quả nên dùng để SO SÁNH tương đối "
    "giữa các kịch bản, không nên xem là con số cam kết chính xác tuyệt đối."
)


@dataclass
class ScenarioSimulationResult:
    table: pd.DataFrame
    disclaimer: str
    baseline: BaselineMetrics


def build_simulation_scenarios(
    *,
    allowed_mechanics: list[str] | None,
    historical_uplifts: dict[str, dict] | None = None,
    max_discount_overrides: dict[str, float] | None = None,
    max_discount_pct: float = 0.3,
    avg_price: float = 0.0,
) -> list[dict]:
    """Ghép kịch bản từ hồ sơ + lịch sử + ngưỡng depth — không dùng danh sách A–F cứng trong source.

    - Baseline `no_promo` luôn có để so sánh tương đối.
    - Mỗi cơ chế trong `allowed_mechanics` (và/hoặc có historical uplift) → đúng 1 kịch bản.
    - Độ sâu giảm giá lấy từ `max_discount_overrides` (rule/ML depth) hoặc `max_discount_pct` hồ sơ.
    """
    historical_uplifts = historical_uplifts or {}
    max_discount_overrides = max_discount_overrides or {}
    allowed = [m for m in (allowed_mechanics or []) if m and m != "no_promo" and m in MECHANIC_CALC_KIND]

    pool: list[str] = []
    for mech in allowed:
        if mech not in pool:
            pool.append(mech)
    # Cơ chế từng quan sát trong dữ liệu (nếu vẫn được phép, hoặc khi chưa cấu hình allowed).
    for mech in historical_uplifts:
        if mech == "no_promo" or mech not in MECHANIC_CALC_KIND:
            continue
        if allowed and mech not in allowed:
            continue
        if mech not in pool:
            pool.append(mech)

    scenarios: list[dict] = [
        {"scenario": MECHANIC_LABELS_VI["no_promo"], "mechanic": "no_promo", "param": 0.0},
    ]
    for mech in pool:
        param = _param_for_mechanic(mech, max_discount_overrides, max_discount_pct, avg_price)
        scenarios.append(
            {
                "scenario": _scenario_label(mech, param),
                "mechanic": mech,
                "param": param,
            }
        )
    return scenarios


def _param_for_mechanic(
    mechanic: str,
    overrides: dict[str, float],
    max_discount_pct: float,
    avg_price: float,
) -> float:
    """Tham số mô phỏng theo loại cơ chế — depth từ rule engine khi có."""
    pct_depth = float(overrides.get(mechanic, overrides.get("discount_percent", max_discount_pct)))
    pct_depth = max(0.0, min(0.9, pct_depth))
    if mechanic in ("discount_percent", "bundle", "coupon", "member_price", "buy_more_save_more"):
        return pct_depth
    if mechanic == "discount_fixed":
        # [ASSUMPTION]: quy đổi % depth tối đa → số tiền / đơn vị theo giá baseline.
        return max(0.0, float(avg_price) * pct_depth)
    if mechanic in ("bogo", "buy_x_get_y"):
        # Định nghĩa B1G1: 50% đơn vị miễn phí — không phải “kịch bản mẫu” cứng A–F.
        return 0.5
    if mechanic == "gift":
        return 0.0
    return pct_depth


def _scenario_label(mechanic: str, param: float) -> str:
    base = MECHANIC_LABELS_VI.get(mechanic, mechanic)
    if mechanic in ("discount_percent", "bundle", "coupon", "member_price", "buy_more_save_more") and param > 0:
        return f"{base} ({param:.0%})"
    if mechanic == "discount_fixed" and param > 0:
        return f"{base} (−{param:,.0f} đ)"
    return base


def simulate_scenarios(
    baseline: BaselineMetrics,
    historical_uplifts: dict[str, dict] | None = None,
    scenarios: list[dict] | None = None,
    gift_cost_per_unit: float = 0.0,
    max_discount_overrides: dict[str, float] | None = None,
    *,
    allowed_mechanics: list[str] | None = None,
    max_discount_pct: float = 0.3,
) -> ScenarioSimulationResult:
    """Chạy toàn bộ kịch bản khuyến mãi cho một baseline (1 SKU, 1 category, hoặc toàn công ty)."""
    historical_uplifts = historical_uplifts or {}
    max_discount_overrides = max_discount_overrides or {}
    if scenarios is None:
        scenarios = build_simulation_scenarios(
            allowed_mechanics=allowed_mechanics,
            historical_uplifts=historical_uplifts,
            max_discount_overrides=max_discount_overrides,
            max_discount_pct=max_discount_pct,
            avg_price=float(baseline.avg_price),
        )

    rows = []
    for sc in scenarios:
        mechanic = sc["mechanic"]
        param = sc["param"]
        if mechanic in max_discount_overrides:
            param = min(param, max_discount_overrides[mechanic]) if param > 0 else param

        if mechanic in historical_uplifts:
            uplift_pct = historical_uplifts[mechanic]["uplift_pct"]
            uplift_source = f"historical ({historical_uplifts[mechanic]['n_days_observed']} ngày quan sát)"
        else:
            uplift_pct = default_unit_uplift(mechanic, param)
            uplift_source = "assumption"

        result = compute_mechanic_result(
            mechanic=mechanic,
            param_value=param,
            baseline=baseline,
            uplift_pct=uplift_pct,
            uplift_source=uplift_source,
            gift_cost_per_unit=gift_cost_per_unit,
        )

        no_promo_baseline_units = baseline.avg_daily_units * baseline.promo_days
        no_promo_revenue = no_promo_baseline_units * baseline.avg_price
        no_promo_cogs = no_promo_baseline_units * baseline.unit_cost
        no_promo_gp = no_promo_revenue - no_promo_cogs

        incremental_revenue = result.total_revenue - no_promo_revenue
        incremental_gp = result.gross_profit - no_promo_gp
        # incremental_gp đã là lợi nhuận tăng thêm THỰC (net), tương đương về mặt đại số với
        # (incremental_GP tính theo margin gốc - chi phí khuyến mãi) — xem giải thích ở mechanics.py.
        # Vì vậy ROI = incremental_gp / promotion_cost, KHÔNG trừ promotion_cost thêm lần nữa.
        roi = incremental_gp / result.promotion_cost if result.promotion_cost > 0 else None

        rows.append(
            {
                "scenario": sc["scenario"],
                "mechanic": mechanic,
                "tham_so": param,
                "uplift_gia_dinh": result.uplift_pct,
                "nguon_uplift": result.uplift_source,
                "san_luong": result.total_units,
                "doanh_thu": result.total_revenue,
                "loi_nhuan_gop": result.gross_profit,
                "margin": result.margin_pct,
                "khach_hang_uoc_tinh": result.estimated_customers,
                "chi_phi_khuyen_mai": result.promotion_cost,
                "doanh_thu_tang_them": incremental_revenue,
                "loi_nhuan_gop_tang_them": incremental_gp,
                "roi": roi,
            }
        )

    table = pd.DataFrame(rows)
    return ScenarioSimulationResult(table=table, disclaimer=DISCLAIMER_VI, baseline=baseline)
