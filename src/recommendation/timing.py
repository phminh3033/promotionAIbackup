"""Đề xuất thời điểm chạy khuyến mãi (mục XX) và ánh xạ sự kiện kinh doanh -> mục tiêu (mục XXI).

[BUSINESS RULE tự thiết kế]: toàn bộ logic trong file này là heuristic tự thiết kế cho MVP,
không phải kết luận trực tiếp từ một paper cụ thể (dù định hướng chung "khuyến mãi nên đặt
đúng lúc nhu cầu/traffic tự nhiên cao" nhất quán với logic promotion timing trong literature
về promotion response).
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

WEEKDAY_NAMES_VI = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]

# [BUSINESS RULE]: các sự kiện kinh doanh phổ biến và mục tiêu khuyến nghị tương ứng
EVENT_TO_OBJECTIVE = {
    "Đối thủ mở cửa hàng gần đây": ("TRAFFIC", "Cần giữ chân khách hàng hiện tại và thu hút khách trước khi họ chuyển sang đối thủ mới."),
    "Đối thủ giảm giá": ("TRAFFIC", "Cần duy trì lượng khách ghé cửa hàng để không mất thị phần ngắn hạn."),
    "Tết Nguyên Đán": ("REVENUE", "Nhu cầu mua sắm tăng mạnh trước Tết — nên tối đa hoá doanh thu/dòng tiền."),
    "Lễ 30/4 - 1/5": ("REVENUE", "Kỳ nghỉ lễ dài thường kéo theo nhu cầu mua sắm/tiêu dùng tăng."),
    "Back to School (khai giảng)": ("REVENUE", "Nhu cầu theo mùa vụ khai giảng tăng, phù hợp đẩy doanh thu nhóm sản phẩm liên quan."),
    "Khai trương / mới mở cửa hàng": ("TRAFFIC", "Ưu tiên tạo traffic ban đầu và nhận diện thương hiệu hơn là tối đa lợi nhuận ngay."),
    "Mùa cao điểm ngành hàng": ("PROFIT", "Nhu cầu tự nhiên đã cao, không cần giảm giá sâu — nên tối ưu lợi nhuận."),
    "Cần xả hàng tồn kho": ("CLEARANCE", "Ưu tiên giải phóng tồn kho, chấp nhận margin thấp hơn để thu hồi vốn."),
}


def suggest_objective_from_event(event_name: str) -> tuple[str, str] | None:
    return EVENT_TO_OBJECTIVE.get(event_name)


@dataclass
class TimingRecommendation:
    best_weekdays: list[str]
    best_weekdays_reason: str
    seasonal_note: str | None
    payday_note: str
    suggested_window_text: str


def analyze_best_timing(daily: pd.DataFrame, date_col: str = "day", value_col: str = "revenue") -> TimingRecommendation:
    daily = daily.copy()
    daily["weekday"] = daily[date_col].dt.weekday
    weekday_avg = daily.groupby("weekday")[value_col].mean().sort_values(ascending=False)
    top_weekdays_idx = weekday_avg.index[:2].tolist()
    top_weekdays_names = [WEEKDAY_NAMES_VI[i] for i in top_weekdays_idx]

    overall_avg = daily[value_col].mean()
    top_avg = weekday_avg.iloc[:2].mean()
    uplift_vs_avg = (top_avg / overall_avg - 1) if overall_avg > 0 else 0
    reason = (
        f"{', '.join(top_weekdays_names)} có doanh số trung bình cao hơn {uplift_vs_avg:.0%} so với ngày thường trong dữ liệu lịch sử."
    )

    seasonal_note = None
    n_days = (daily[date_col].max() - daily[date_col].min()).days
    if n_days >= 350:
        monthly_avg = daily.groupby(daily[date_col].dt.month)[value_col].mean()
        peak_month = int(monthly_avg.idxmax())
        seasonal_note = (
            f"Theo dữ liệu lịch sử hơn 1 năm, tháng {peak_month} có doanh số trung bình cao nhất trong năm — "
            "cân nhắc ưu tiên ngân sách khuyến mãi vào giai đoạn này."
        )

    payday_note = (
        "Nhiều người tiêu dùng Việt Nam nhận lương vào đầu tháng hoặc giữa tháng — "
        "chạy khuyến mãi quanh các mốc 1-5 và 14-18 hàng tháng thường ghi nhận sức mua tốt hơn."
    )

    next_date = pd.Timestamp.today().normalize() + pd.Timedelta(days=1)
    while next_date.weekday() not in top_weekdays_idx:
        next_date += pd.Timedelta(days=1)
    window_end = next_date + pd.Timedelta(days=1)
    suggested_window_text = f"{next_date.strftime('%d/%m')} – {window_end.strftime('%d/%m')}"

    return TimingRecommendation(
        best_weekdays=top_weekdays_names,
        best_weekdays_reason=reason,
        seasonal_note=seasonal_note,
        payday_note=payday_note,
        suggested_window_text=suggested_window_text,
    )
