"""Campaign Monitor: so sánh Actual vs Forecast trong lúc chạy chương trình (mục XXIX spec).

[BUSINESS RULE]: baseline dự báo theo ngày được suy ra đơn giản bằng cách CHIA ĐỀU tổng dự báo cả
kỳ khuyến mãi cho số ngày (uniform daily baseline) — MVP chưa có forecast dạng phân phối theo từng
ngày cho scenario khuyến mãi cụ thể. Đây là giới hạn đã biết, ghi trong docs/backlog_tinh_nang.md.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class DailyBaseline:
    revenue_per_day: float
    gp_per_day: float
    customers_per_day: float
    units_per_day: float


def build_daily_baseline(
    expected_revenue_range: tuple[float, float],
    expected_gp_range: tuple[float, float],
    expected_customers_range: tuple[float, float],
    expected_demand_range: tuple[float, float],
    promo_days: int,
) -> DailyBaseline:
    mid_revenue = sum(expected_revenue_range) / 2
    mid_gp = sum(expected_gp_range) / 2
    mid_customers = sum(expected_customers_range) / 2
    mid_units = sum(expected_demand_range) / 2
    n = max(promo_days, 1)
    return DailyBaseline(
        revenue_per_day=mid_revenue / n,
        gp_per_day=mid_gp / n,
        customers_per_day=mid_customers / n,
        units_per_day=mid_units / n,
    )


def compare_actual_vs_forecast(actual_daily: pd.DataFrame, baseline: DailyBaseline) -> pd.DataFrame:
    """actual_daily cần có cột 'date' và tối thiểu 1 trong các cột: revenue, gp, customers, units.

    Trả về bảng so sánh từng ngày + % chênh lệch so với baseline (âm = thấp hơn dự báo).
    """
    df = actual_daily.copy()
    df = df.sort_values("date").reset_index(drop=True)
    df["day_index"] = range(1, len(df) + 1)

    metric_baseline = {
        "revenue": baseline.revenue_per_day,
        "gp": baseline.gp_per_day,
        "customers": baseline.customers_per_day,
        "units": baseline.units_per_day,
    }
    for metric, base_val in metric_baseline.items():
        if metric in df.columns:
            df[f"{metric}_forecast"] = base_val
            df[f"{metric}_variance_pct"] = np.where(
                base_val > 0, (df[metric] - base_val) / base_val, np.nan
            )
    return df


def cumulative_variance(compared_df: pd.DataFrame, metric: str) -> float | None:
    """% chênh lệch LUỸ KẾ (không phải trung bình từng ngày) — cộng dồn actual và forecast riêng
    rồi mới so sánh, tránh bị lệch bởi ngày có forecast baseline nhỏ."""
    actual_col, forecast_col = metric, f"{metric}_forecast"
    if actual_col not in compared_df.columns or forecast_col not in compared_df.columns:
        return None
    total_actual = compared_df[actual_col].sum()
    total_forecast = compared_df[forecast_col].sum()
    if total_forecast <= 0:
        return None
    return (total_actual - total_forecast) / total_forecast
