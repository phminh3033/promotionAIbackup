"""Alert Engine + AI Action (mục XXX, XXXI spec PromotionPilot AI).

Toàn bộ cảnh báo và đề xuất Continue/Adjust/Stop/Scale đều dựa trên RULE + SỐ LIỆU THỰC TẾ đã
upload — không dùng LLM để tự suy luận quyết định (đúng nguyên tắc "LLM chỉ explain/summarize,
không tự recommend" xuyên suốt toàn bộ hệ thống — mục XXIV gốc, XI-B trong PromoPilot AI cũ).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

# [BUSINESS RULE] ngưỡng cảnh báo mặc định — doanh nghiệp có thể ghi đè qua Business Constraints
REVENUE_WARNING_THRESHOLD = 0.80  # doanh thu thực tế < 80% dự báo -> Warning
INVENTORY_STOCKOUT_DAYS = 2  # còn dưới 2 ngày tồn kho -> Stockout Alert
TRAFFIC_STAFFING_THRESHOLD = 0.30  # traffic thực tế cao hơn dự báo > 30% -> Staffing Alert
OVERSTOCK_THRESHOLD = 1.50  # tồn kho hiện tại > 150% mức dự báo cần dùng -> Overstock Alert


@dataclass
class Alert:
    level: str  # "info" | "warning" | "critical"
    code: str
    message: str


def evaluate_alerts(
    cumulative_revenue_variance: float | None,
    current_margin_pct: float | None,
    min_margin_pct: float,
    days_of_inventory: float | None,
    cumulative_customers_variance: float | None,
    inventory_vs_forecast_ratio: float | None,
    actual_roi: float | None,
    min_roi_pct: float,
) -> list[Alert]:
    """Áp dụng các luật cảnh báo từ mục XXX. Bất kỳ input nào là None sẽ được bỏ qua (thiếu dữ liệu
    thì không cảnh báo giả — tránh false alarm)."""
    alerts: list[Alert] = []

    if cumulative_revenue_variance is not None and cumulative_revenue_variance < (REVENUE_WARNING_THRESHOLD - 1):
        alerts.append(
            Alert(
                "warning",
                "REVENUE_BELOW_FORECAST",
                f"Doanh thu thực tế đang thấp hơn dự báo {abs(cumulative_revenue_variance):.0%} "
                f"(dưới ngưỡng {1 - REVENUE_WARNING_THRESHOLD:.0%} cho phép).",
            )
        )

    if current_margin_pct is not None and current_margin_pct < min_margin_pct:
        alerts.append(
            Alert(
                "critical",
                "MARGIN_BELOW_MINIMUM",
                f"Margin thực tế ({current_margin_pct:.0%}) đã xuống dưới ngưỡng tối thiểu "
                f"({min_margin_pct:.0%}) doanh nghiệp đặt ra.",
            )
        )

    if days_of_inventory is not None and days_of_inventory < INVENTORY_STOCKOUT_DAYS:
        alerts.append(
            Alert(
                "critical",
                "STOCKOUT_RISK",
                f"Tồn kho chỉ còn đủ dùng {days_of_inventory:.1f} ngày — rủi ro hết hàng cận kề.",
            )
        )

    if cumulative_customers_variance is not None and cumulative_customers_variance > TRAFFIC_STAFFING_THRESHOLD:
        alerts.append(
            Alert(
                "warning",
                "STAFFING_ALERT",
                f"Lượng khách thực tế cao hơn dự báo {cumulative_customers_variance:.0%} — cân nhắc "
                "tăng cường nhân sự phục vụ để không ảnh hưởng trải nghiệm khách hàng.",
            )
        )

    if inventory_vs_forecast_ratio is not None and inventory_vs_forecast_ratio > OVERSTOCK_THRESHOLD:
        alerts.append(
            Alert(
                "warning",
                "OVERSTOCK_ALERT",
                f"Tồn kho hiện tại cao hơn {inventory_vs_forecast_ratio:.0%} so với mức cần dùng dự "
                "kiến — cân nhắc đẩy mạnh tiêu thụ hoặc điều chuyển hàng.",
            )
        )

    if actual_roi is not None and actual_roi < min_roi_pct:
        alerts.append(
            Alert(
                "warning",
                "ROI_BELOW_MINIMUM",
                f"ROI thực tế ({actual_roi:.0%}) đang thấp hơn ngưỡng tối thiểu ({min_roi_pct:.0%}) "
                "— nên xem xét lại hiệu quả chương trình.",
            )
        )

    if not alerts:
        alerts.append(Alert("info", "ON_TRACK", "Chưa phát hiện dấu hiệu bất thường — chương trình đang bám sát kế hoạch."))

    return alerts


@dataclass
class AiActionResult:
    action: str  # "CONTINUE" | "ADJUST" | "STOP" | "SCALE"
    action_vi: str
    reasons: list[str] = field(default_factory=list)


ACTION_LABELS_VI = {
    "CONTINUE": "Tiếp tục (Continue)",
    "ADJUST": "Điều chỉnh (Adjust)",
    "STOP": "Dừng chương trình (Stop)",
    "SCALE": "Mở rộng quy mô (Scale)",
}


def decide_action(
    alerts: list[Alert],
    cumulative_revenue_variance: float | None,
    cumulative_customers_variance: float | None,
    actual_roi: float | None,
    min_roi_pct: float,
) -> AiActionResult:
    """Quyết định Continue/Adjust/Stop/Scale dựa trên số lượng/mức độ alert + hiệu suất thực tế.

    [BUSINESS RULE]: thứ tự ưu tiên quyết định — có alert CRITICAL nào cũng đủ để không đề xuất
    SCALE; nhiều alert WARNING cùng lúc thì nghiêng về STOP/ADJUST thay vì CONTINUE.
    """
    critical_alerts = [a for a in alerts if a.level == "critical"]
    warning_alerts = [a for a in alerts if a.level == "warning"]

    reasons: list[str] = []

    if len(critical_alerts) >= 2 or (
        len(critical_alerts) >= 1 and actual_roi is not None and actual_roi < min_roi_pct - 0.30
    ):
        reasons.append("Có nhiều dấu hiệu nghiêm trọng cùng lúc (margin/tồn kho) và hiệu quả tài chính kém xa mục tiêu.")
        for a in critical_alerts:
            reasons.append(a.message)
        return AiActionResult("STOP", ACTION_LABELS_VI["STOP"], reasons)

    if critical_alerts:
        reasons.append("Có dấu hiệu nghiêm trọng cần xử lý trước khi tiếp tục như kế hoạch ban đầu.")
        for a in critical_alerts:
            reasons.append(a.message)
        return AiActionResult("ADJUST", ACTION_LABELS_VI["ADJUST"], reasons)

    strong_positive = (
        cumulative_revenue_variance is not None
        and cumulative_revenue_variance > 0.15
        and (actual_roi is None or actual_roi >= min_roi_pct)
        and not warning_alerts
    )
    if strong_positive:
        roi_note = f"và ROI vẫn đạt mục tiêu ({actual_roi:.0%})" if actual_roi is not None else "(chưa đủ dữ liệu lợi nhuận gộp thực tế để tính ROI, nhưng doanh thu và các chỉ số khác đều tích cực)"
        reasons.append(f"Doanh thu thực tế cao hơn dự báo {cumulative_revenue_variance:.0%} {roi_note}.")
        if cumulative_customers_variance is not None and cumulative_customers_variance > 0.15:
            reasons.append(f"Lượng khách cũng tăng {cumulative_customers_variance:.0%} — nhu cầu thật sự, không phải biến động ngẫu nhiên.")
        reasons.append("Có thể cân nhắc mở rộng quy mô (thêm SKU, thêm cửa hàng, hoặc kéo dài thời gian).")
        return AiActionResult("SCALE", ACTION_LABELS_VI["SCALE"], reasons)

    if warning_alerts:
        reasons.append("Có một số dấu hiệu cần theo dõi/điều chỉnh, nhưng chưa đến mức nghiêm trọng.")
        for a in warning_alerts:
            reasons.append(a.message)
        return AiActionResult("ADJUST", ACTION_LABELS_VI["ADJUST"], reasons)

    reasons.append("Các chỉ số đang bám sát dự báo, chưa có dấu hiệu bất thường.")
    return AiActionResult("CONTINUE", ACTION_LABELS_VI["CONTINUE"], reasons)
