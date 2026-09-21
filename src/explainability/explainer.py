"""Explainable AI: chuyển các con số kỹ thuật thành câu giải thích tiếng Việt dễ hiểu (mục XXIII).

Nguyên tắc: mọi recommendation phải trả lời được "Tại sao?" bằng ngôn ngữ kinh doanh,
không dùng thuật ngữ kỹ thuật khó hiểu với SME (không nói "WAPE 8.2%", mà nói "độ tin cậy Tốt").
"""
from __future__ import annotations


def explain_trend(pct_change: float) -> str:
    if pct_change > 0.05:
        return f"Doanh thu có xu hướng tăng {pct_change:.0%} so với giai đoạn trước."
    if pct_change < -0.05:
        return f"Doanh thu có xu hướng giảm {abs(pct_change):.0%} so với giai đoạn trước — cần hành động để đảo chiều."
    return "Doanh thu khá ổn định so với giai đoạn trước, chưa có biến động rõ rệt."


def explain_repeat_rate(repeat_rate: float) -> str:
    if repeat_rate >= 0.35:
        return f"{repeat_rate:.0%} khách hàng mua lặp lại — nhóm này phản ứng tốt với ưu đãi khuyến khích mua thêm (BOGO, mua nhiều giảm nhiều)."
    if repeat_rate >= 0.15:
        return f"{repeat_rate:.0%} khách hàng mua lặp lại — ở mức trung bình, có thể cải thiện bằng chương trình thành viên."
    return f"Chỉ {repeat_rate:.0%} khách hàng quay lại mua — nên ưu tiên chương trình giữ chân khách hơn là giảm giá đại trà."


def explain_inventory_status(days_of_inventory: float, lead_time_days: float) -> str:
    if days_of_inventory == float("inf"):
        return "Sản phẩm hiện không bán ra nên chưa có áp lực tồn kho."
    if days_of_inventory > 3 * lead_time_days:
        return f"Tồn kho hiện đủ dùng {days_of_inventory:.0f} ngày, cao hơn nhiều so với thời gian chờ nhập hàng ({lead_time_days:.0f} ngày) — nên đẩy hàng ra."
    if days_of_inventory < lead_time_days:
        return f"Tồn kho chỉ đủ dùng {days_of_inventory:.0f} ngày, ngắn hơn thời gian chờ nhập hàng — rủi ro hết hàng nếu đẩy mạnh khuyến mãi."
    return f"Tồn kho ở mức hợp lý ({days_of_inventory:.0f} ngày dùng được)."


def explain_basket_lift(partner_product: str, lift: float, confidence: float) -> str:
    return (
        f"Sản phẩm này thường được mua cùng {partner_product} (xác suất {confidence:.0%}, "
        f"cao gấp {lift:.1f} lần bình thường) — ghép combo giúp tăng giá trị đơn hàng."
    )


def explain_margin_after_promotion(margin_after: float, min_margin: float) -> str:
    if margin_after >= min_margin + 0.05:
        return f"Margin sau khuyến mãi vẫn đạt {margin_after:.0%}, cao hơn ngưỡng tối thiểu {min_margin:.0%} doanh nghiệp đặt ra."
    if margin_after >= min_margin:
        return f"Margin sau khuyến mãi ở sát ngưỡng tối thiểu ({margin_after:.0%} so với {min_margin:.0%}) — cần theo dõi sát."
    return f"Margin sau khuyến mãi ({margin_after:.0%}) thấp hơn ngưỡng tối thiểu ({min_margin:.0%}) — không khuyến nghị."


def explain_customer_value_share(share: float) -> str:
    return f"{share:.0%} doanh thu đến từ nhóm Khách giá trị cao — nhóm này nhạy cảm với trải nghiệm/ưu đãi hơn là mức giá."


def explain_uplift_source(source: str) -> str:
    if source.startswith("historical"):
        return f"Uplift ước tính dựa trên dữ liệu lịch sử thật của doanh nghiệp ({source})."
    return (
        "Uplift ước tính dựa trên giả định elasticity mặc định (chưa có đủ lịch sử khuyến mãi thật) — "
        "nên xem là ước tính tham khảo để so sánh giữa các kịch bản, không phải cam kết chính xác tuyệt đối."
    )
