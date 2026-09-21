"""Business Objective Engine (mục VIII yêu cầu gốc): 4 mục tiêu kinh doanh với hàm mục tiêu khác nhau.

[BUSINESS RULE tự thiết kế]: trọng số trong từng hàm mục tiêu là quy tắc tự đặt cho MVP để
đảm bảo mỗi mục tiêu cho ra thứ hạng kịch bản khác nhau một cách hợp lý về mặt kinh doanh —
không phải kết quả tối ưu hoá học được từ dữ liệu (chưa đủ dữ liệu causal để làm điều đó).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

OBJECTIVES = ["TRAFFIC", "REVENUE", "PROFIT", "CLEARANCE", "BRANDING"]

OBJECTIVE_LABELS_VI = {
    "TRAFFIC": "Kéo Traffic (số khách / số giao dịch)",
    "REVENUE": "Tăng Doanh thu / Dòng tiền",
    "PROFIT": "Tăng Lợi nhuận",
    "CLEARANCE": "Giải phóng Tồn kho",
    "BRANDING": "Xây dựng thương hiệu (Branding)",
}

OBJECTIVE_PRIORITY_METRICS_VI = {
    "TRAFFIC": ["Số giao dịch/khách hàng ước tính", "Số khách mới", "Traffic uplift"],
    "REVENUE": ["Tổng doanh thu", "Sản lượng bán", "Giá trị đơn hàng trung bình"],
    "PROFIT": ["Lợi nhuận gộp tăng thêm", "ROI", "Margin"],
    "CLEARANCE": ["Sản lượng bán (sell-through)", "Mức giảm tồn kho", "Dòng tiền giải phóng"],
    "BRANDING": ["Độ phủ khách hàng tiếp cận (proxy)", "Số khách dùng thử", "Sản lượng lan toả"],
}


def _minmax_normalize(s: pd.Series) -> pd.Series:
    s = s.astype(float)
    if s.max() == s.min():
        return pd.Series(0.5, index=s.index)
    return (s - s.min()) / (s.max() - s.min())


def score_scenarios(table: pd.DataFrame, objective: str, current_inventory: float | None = None) -> pd.DataFrame:
    """Thêm cột 'diem_muc_tieu' (objective score, 0-1) vào bảng kịch bản theo mục tiêu đã chọn."""
    table = table.copy()
    n_customers_norm = _minmax_normalize(table["khach_hang_uoc_tinh"])
    revenue_norm = _minmax_normalize(table["doanh_thu"])
    units_norm = _minmax_normalize(table["san_luong"])
    gp_norm = _minmax_normalize(table["loi_nhuan_gop"])
    roi_series = table["roi"].fillna(0)
    roi_norm = _minmax_normalize(roi_series)
    margin_norm = _minmax_normalize(table["margin"])

    if objective == "TRAFFIC":
        score = 0.65 * n_customers_norm + 0.25 * units_norm + 0.10 * revenue_norm
    elif objective == "REVENUE":
        score = 0.55 * revenue_norm + 0.30 * units_norm + 0.15 * n_customers_norm
    elif objective == "PROFIT":
        score = 0.5 * gp_norm + 0.35 * roi_norm + 0.15 * margin_norm
    elif objective == "CLEARANCE":
        sell_through_norm = units_norm
        if current_inventory and current_inventory > 0:
            sell_through_ratio = (table["san_luong"] / current_inventory).clip(upper=1.5)
            sell_through_norm = _minmax_normalize(sell_through_ratio)
        score = 0.6 * sell_through_norm + 0.2 * units_norm + 0.2 * (1 - margin_norm)
    elif objective == "BRANDING":
        # [BUSINESS RULE / proxy]: chưa có dữ liệu reach/impression thật (mạng xã hội, in-store
        # traffic đếm bằng camera...), dùng số khách hàng ước tính làm proxy cho "độ phủ" —
        # ưu tiên mạnh hơn TRAFFIC (0.65/0.25/0.10) vì branding chấp nhận đánh đổi lợi nhuận/ROI
        # ngắn hạn nhiều hơn để tối đa số người tiếp cận/dùng thử.
        score = 0.8 * n_customers_norm + 0.2 * units_norm
    else:
        raise ValueError(f"Mục tiêu không hợp lệ: {objective}")

    table["diem_muc_tieu"] = score.round(4)
    return table.sort_values("diem_muc_tieu", ascending=False).reset_index(drop=True)


def pick_best_scenario(
    table: pd.DataFrame,
    objective: str,
    min_margin_pct: float,
    exclude_no_promo: bool = True,
) -> pd.Series | None:
    scored = score_scenarios(table, objective)
    candidates = scored[scored["margin"] >= min_margin_pct]
    if exclude_no_promo:
        candidates = candidates[candidates["mechanic"] != "no_promo"]
    if candidates.empty:
        candidates = scored[scored["mechanic"] != "no_promo"] if exclude_no_promo else scored
    if candidates.empty:
        return None
    return candidates.iloc[0]
