"""Promotion Simulator: mô-đun trung tâm so sánh nhiều kịch bản khuyến mãi (mục XVI yêu cầu gốc)."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.promotion.mechanics import BaselineMetrics, compute_mechanic_result, default_unit_uplift

DISCLAIMER_VI = (
    "Đây là mô phỏng dựa trên historical response / elasticity assumption, "
    "chưa phải causal uplift đã được chứng minh. Kết quả nên dùng để SO SÁNH tương đối "
    "giữa các kịch bản, không nên xem là con số cam kết chính xác tuyệt đối."
)

# Định nghĩa kịch bản mặc định (mục XVI): A-No Promo, B-Discount5%, C-Discount10%, D-BOGO, E-Bundle, F-Gift
DEFAULT_SCENARIOS: list[dict] = [
    {"scenario": "A. Không khuyến mãi", "mechanic": "no_promo", "param": 0.0},
    {"scenario": "B. Giảm giá 5%", "mechanic": "discount_percent", "param": 0.05},
    {"scenario": "C. Giảm giá 10%", "mechanic": "discount_percent", "param": 0.10},
    {"scenario": "D. Mua 1 Tặng 1 (BOGO)", "mechanic": "bogo", "param": 0.5},
    {"scenario": "E. Combo/Bundle -12%", "mechanic": "bundle", "param": 0.12},
    {"scenario": "F. Tặng quà kèm theo", "mechanic": "gift", "param": 0.0},
]


@dataclass
class ScenarioSimulationResult:
    table: pd.DataFrame
    disclaimer: str
    baseline: BaselineMetrics


def simulate_scenarios(
    baseline: BaselineMetrics,
    historical_uplifts: dict[str, dict] | None = None,
    scenarios: list[dict] | None = None,
    gift_cost_per_unit: float = 0.0,
    max_discount_overrides: dict[str, float] | None = None,
) -> ScenarioSimulationResult:
    """Chạy toàn bộ kịch bản khuyến mãi cho một baseline (1 SKU, 1 category, hoặc toàn công ty)."""
    scenarios = scenarios or DEFAULT_SCENARIOS
    historical_uplifts = historical_uplifts or {}
    max_discount_overrides = max_discount_overrides or {}

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
