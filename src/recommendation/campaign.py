"""Campaign Generator (mục XXV yêu cầu gốc): sinh kế hoạch campaign + content rule-based.

Mặc định dùng template rule-based bằng tiếng Việt (không cần internet/API key) — đúng nguyên
tắc mục XIV: "LLM chỉ được dùng để giải thích/viết nội dung/tóm tắt", KHÔNG quyết định promotion.
Nếu người dùng tự cấu hình LLM_ENABLED=true và API key trong .env, có thể mở rộng gọi LLM để
viết content sinh động hơn — nhưng chỉ gửi dữ liệu tổng hợp (aggregated), không gửi transaction
chi tiết (mục XXX Data Privacy). MVP này chỉ triển khai nhánh rule-based, để hook LLM ở dạng
optional function chưa kích hoạt mặc định.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from src.recommendation.engine import RecommendationCard


@dataclass
class CampaignPlan:
    name: str
    objective: str
    target: str
    product: str
    offer: str
    timing: str
    inventory_plan: str
    staffing_plan: str
    kpi: list[str]
    fb_copy: str
    zalo_copy: str
    sms_copy: str


def _format_vnd(value: float) -> str:
    return f"{value:,.0f}đ".replace(",", ".")


def generate_campaign_plan(
    card: RecommendationCard,
    business_name: str,
    service_capacity_per_staff_per_hour: float | None = None,
) -> CampaignPlan:
    name = f"Chương trình {card.promotion_label} – {card.product_focus} ({card.timing_text})"

    kpi = [
        f"Doanh thu mục tiêu: {_format_vnd(card.expected_revenue_range[0])} – {_format_vnd(card.expected_revenue_range[1])}",
        f"Lợi nhuận gộp mục tiêu: {_format_vnd(card.expected_gp_range[0])} – {_format_vnd(card.expected_gp_range[1])}",
        f"Sản lượng bán mục tiêu: {card.expected_demand_range[0]:.0f} – {card.expected_demand_range[1]:.0f} sản phẩm",
        f"Số khách hàng phục vụ dự kiến: {card.expected_customers_range[0]:.0f} – {card.expected_customers_range[1]:.0f}",
    ]
    if card.expected_roi_range:
        kpi.append(f"ROI mục tiêu: {card.expected_roi_range[0]:.0%} – {card.expected_roi_range[1]:.0%}")

    inventory_plan = (
        f"Chuẩn bị tối thiểu {card.recommended_stock:.0f} sản phẩm cho {card.product_focus} trước ngày bắt đầu "
        f"chương trình để đáp ứng nhu cầu dự kiến {card.expected_demand_range[0]:.0f}-{card.expected_demand_range[1]:.0f} sản phẩm."
    )

    if service_capacity_per_staff_per_hour:
        avg_customers = (card.expected_customers_range[0] + card.expected_customers_range[1]) / 2
        est_hours_per_day = 10  # [BUSINESS RULE] giả định khung giờ mở bán trung bình/ngày
        capacity_needed = avg_customers / max(1, est_hours_per_day)
        staff_needed = max(1, round(capacity_needed / service_capacity_per_staff_per_hour))
        staffing_plan = (
            f"Ước tính cần khoảng {staff_needed} nhân viên phục vụ/giờ trong khung giờ cao điểm "
            f"(năng lực {service_capacity_per_staff_per_hour:.0f} khách/nhân viên/giờ)."
        )
    else:
        staffing_plan = "Chưa đủ dữ liệu năng lực phục vụ — vui lòng nhập ở phần Cấu hình để tính số nhân viên cần thiết."

    fb_copy = (
        f"🎉 {business_name} ưu đãi đặc biệt: {card.promotion_label} cho {card.product_focus}!\n"
        f"⏰ Áp dụng: {card.timing_text}\n"
        f"👉 {card.timing_reason}\n"
        f"Số lượng có hạn — nhanh tay đặt hàng ngay hôm nay!"
    )

    zalo_copy = (
        f"[{business_name}] {card.promotion_label} – {card.product_focus}\n"
        f"Thời gian: {card.timing_text}\n"
        f"Ưu tiên dành cho: {card.target_segment}\n"
        f"Inbox Zalo để được tư vấn & giữ ưu đãi ngay!"
    )

    sms_copy = (
        f"{business_name}: {card.promotion_label} {card.product_focus} - Ap dung {card.timing_text}. "
        f"Ghe cua hang ngay hom nay!"
    )

    return CampaignPlan(
        name=name,
        objective=card.objective_vi,
        target=card.target_segment,
        product=card.product_focus,
        offer=card.promotion_label,
        timing=card.timing_text,
        inventory_plan=inventory_plan,
        staffing_plan=staffing_plan,
        kpi=kpi,
        fb_copy=fb_copy,
        zalo_copy=zalo_copy,
        sms_copy=sms_copy,
    )


def is_llm_enabled() -> bool:
    """Kiểm tra cấu hình .env — mặc định False, không tự động gọi LLM nếu người dùng chưa bật."""
    return os.getenv("LLM_ENABLED", "false").strip().lower() == "true" and bool(
        os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    )
