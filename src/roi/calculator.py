"""Tính ROI và các chỉ số tài chính chi tiết cho từng kịch bản khuyến mãi (mục XVIII yêu cầu gốc).

ROI = (Incremental Gross Profit - Promotion Cost) / Promotion Cost
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.promotion.mechanics import BaselineMetrics


@dataclass
class RoiBreakdown:
    scenario: str
    incremental_revenue: float
    incremental_gross_profit: float
    promotion_cost: float
    roi: float | None
    margin_dilution_pct: float
    cash_required: float
    payback_days: float | None


def compute_roi_breakdown(
    scenario_table: pd.DataFrame,
    baseline: BaselineMetrics,
    baseline_scenario_name: str = "A. Không khuyến mãi",
) -> pd.DataFrame:
    """Bổ sung cột margin dilution, cash required, payback vào bảng kịch bản đã có sẵn ROI/incremental."""
    table = scenario_table.copy()
    base_row = table[table["scenario"] == baseline_scenario_name]
    base_margin = float(base_row["margin"].iloc[0]) if not base_row.empty else 0.0

    table["margin_dilution"] = base_margin - table["margin"]

    extra_units = table["san_luong"] - (base_row["san_luong"].iloc[0] if not base_row.empty else 0)
    table["cash_required"] = table["chi_phi_khuyen_mai"] + extra_units.clip(lower=0) * baseline.unit_cost

    daily_incremental_gp = table["loi_nhuan_gop_tang_them"] / max(baseline.promo_days, 1)
    table["payback_days"] = table.apply(
        lambda r: (
            r["chi_phi_khuyen_mai"] / (r["loi_nhuan_gop_tang_them"] / max(baseline.promo_days, 1))
            if r["chi_phi_khuyen_mai"] > 0 and r["loi_nhuan_gop_tang_them"] > 0
            else None
        ),
        axis=1,
    )

    return table


def format_roi_summary_vi(row: pd.Series) -> str:
    roi_txt = f"{row['roi']:.0%}" if pd.notna(row.get("roi")) else "không xác định (không phát sinh chi phí khuyến mãi)"
    payback_txt = f"{row['payback_days']:.0f} ngày" if pd.notna(row.get("payback_days")) else "chưa hoàn vốn trong giai đoạn mô phỏng"
    return (
        f"Doanh thu tăng thêm {row['doanh_thu_tang_them']:,.0f}đ, lợi nhuận gộp tăng thêm "
        f"{row['loi_nhuan_gop_tang_them']:,.0f}đ, chi phí khuyến mãi {row['chi_phi_khuyen_mai']:,.0f}đ. "
        f"ROI ước tính: {roi_txt}. Thời gian hoàn vốn: {payback_txt}."
    )
