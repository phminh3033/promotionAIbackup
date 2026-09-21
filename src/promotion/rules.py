"""Business Rules Engine cho khuyến mãi (mục XV yêu cầu gốc).

Đây là [BUSINESS RULE] tự thiết kế, mã hoá lại trực tiếp các luật IF-THEN trong đề bài gốc.
Không dùng LLM để ra quyết định — quyết định luôn dựa trên dữ liệu + luật + model
(mục XIV: "Không để LLM tự quyết promotion").
"""
from __future__ import annotations

from dataclasses import dataclass, field

# Ngưỡng [BUSINESS RULE] mặc định, có thể ghi đè bằng Business Profile của từng doanh nghiệp
DEFAULT_HIGH_INVENTORY_DAYS = 45
DEFAULT_LOW_VELOCITY_DECLINE = -0.15  # doanh số 14 ngày gần nhất giảm > 15% so với 14 ngày trước đó
DEFAULT_HIGH_REPEAT_RATE = 0.35


@dataclass
class SkuRuleContext:
    product_id: str
    days_of_inventory: float
    sales_velocity_change_pct: float  # % thay đổi doanh số gần đây so với trước đó
    margin_pct: float  # margin hiện tại của SKU (0-1)
    has_basket_partner: bool
    basket_partner_id: str | None
    repeat_rate: float | None  # % khách mua lặp lại liên quan sản phẩm này (nếu có RFM)
    high_value_customer_share: float | None  # % doanh thu từ nhóm "Khách giá trị cao"
    lead_time_days: float


@dataclass
class RuleVerdict:
    mechanic: str
    verdict: str  # "recommended" | "neutral" | "caution" | "rejected"
    reasons: list[str] = field(default_factory=list)


def evaluate_sku_rules(ctx: SkuRuleContext, min_margin_pct: float, max_discount_pct: float) -> list[RuleVerdict]:
    verdicts: dict[str, RuleVerdict] = {
        m: RuleVerdict(mechanic=m, verdict="neutral", reasons=[])
        for m in [
            "discount_percent",
            "discount_fixed",
            "bogo",
            "buy_x_get_y",
            "bundle",
            "gift",
            "member_price",
            "coupon",
            "buy_more_save_more",
        ]
    }

    # Rule: tồn kho không đủ so với lead time -> từ chối toàn bộ khuyến mãi đẩy thêm nhu cầu
    if ctx.days_of_inventory < ctx.lead_time_days:
        for v in verdicts.values():
            v.verdict = "rejected"
            v.reasons.append(
                f"Tồn kho chỉ đủ dùng {ctx.days_of_inventory:.0f} ngày, ngắn hơn thời gian chờ nhập hàng "
                f"({ctx.lead_time_days:.0f} ngày) — nếu đẩy mạnh khuyến mãi có thể gây hết hàng giữa chương trình."
            )
        return list(verdicts.values())

    # Rule: tồn kho cao + doanh số chậm lại + margin đủ -> khuyến khích discount/bundle
    if ctx.days_of_inventory > DEFAULT_HIGH_INVENTORY_DAYS and ctx.sales_velocity_change_pct < DEFAULT_LOW_VELOCITY_DECLINE:
        if ctx.margin_pct >= min_margin_pct + 0.05:
            for m in ["discount_percent", "discount_fixed", "bundle"]:
                verdicts[m].verdict = "recommended"
                verdicts[m].reasons.append(
                    f"Tồn kho còn dùng được {ctx.days_of_inventory:.0f} ngày (cao) và doanh số gần đây giảm "
                    f"{abs(ctx.sales_velocity_change_pct):.0%} — nên đẩy hàng qua giảm giá/bundle vì margin vẫn đủ."
                )

    # Rule: sản phẩm thường được mua cùng sản phẩm khác -> đề xuất bundle
    if ctx.has_basket_partner:
        verdicts["bundle"].verdict = "recommended"
        verdicts["bundle"].reasons.append(
            f"Sản phẩm thường được mua cùng {ctx.basket_partner_id} — ghép bundle giúp tăng giá trị đơn hàng."
        )

    # Rule: tần suất mua lặp lại cao -> đề xuất BOGO / Buy More Save More
    if ctx.repeat_rate is not None and ctx.repeat_rate >= DEFAULT_HIGH_REPEAT_RATE:
        for m in ["bogo", "buy_x_get_y", "buy_more_save_more"]:
            verdicts[m].verdict = "recommended"
            verdicts[m].reasons.append(
                f"Tỷ lệ khách mua lặp lại cao ({ctx.repeat_rate:.0%}) — BOGO/Mua nhiều giảm nhiều phù hợp để tăng sản lượng."
            )

    # Rule: khách hàng giá trị cao chiếm tỷ trọng lớn -> member benefit / gift
    if ctx.high_value_customer_share is not None and ctx.high_value_customer_share >= 0.3:
        for m in ["member_price", "gift"]:
            verdicts[m].verdict = "recommended"
            verdicts[m].reasons.append(
                f"{ctx.high_value_customer_share:.0%} doanh thu đến từ nhóm Khách giá trị cao — "
                "ưu đãi thành viên/quà tặng giữ chân nhóm này hiệu quả hơn giảm giá đại trà."
            )

    # Rule: margin thấp -> tránh giảm giá sâu
    if ctx.margin_pct < min_margin_pct + 0.05:
        for m in ["discount_percent", "discount_fixed", "bogo", "buy_x_get_y", "buy_more_save_more"]:
            if verdicts[m].verdict != "rejected":
                verdicts[m].verdict = "caution"
                verdicts[m].reasons.append(
                    f"Margin hiện tại ({ctx.margin_pct:.0%}) gần ngưỡng tối thiểu ({min_margin_pct:.0%}) — "
                    "cân nhắc cơ chế ít ảnh hưởng giá bán hơn (bundle, gift, member price)."
                )

    return list(verdicts.values())


def max_allowed_depth(mechanic: str, unit_cost: float, price: float, min_margin_pct: float, max_discount_pct: float) -> float:
    """Tính mức giảm giá tối đa cho phép để vẫn đạt min margin và không vượt max_discount_pct.

    [BUSINESS RULE]: margin sau khuyến mãi = (price*(1-depth) - unit_cost) / (price*(1-depth)) >= min_margin_pct
    => depth <= 1 - unit_cost / (price * (1 - min_margin_pct))
    """
    if price <= 0:
        return 0.0
    if mechanic not in ("discount_percent", "discount_fixed", "bundle", "coupon", "member_price", "buy_more_save_more"):
        return max_discount_pct
    if min_margin_pct >= 1:
        return 0.0
    max_depth_for_margin = 1 - (unit_cost / (price * (1 - min_margin_pct))) if unit_cost > 0 else max_discount_pct
    return max(0.0, min(max_discount_pct, max_depth_for_margin))
