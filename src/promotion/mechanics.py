"""Cơ chế khuyến mãi (Promotion Mechanics) và giả định elasticity mặc định (mục XIV, XVI).

QUAN TRỌNG (mục XVI yêu cầu gốc): Nếu dataset KHÔNG có lịch sử khuyến mãi (promotion_type,
discount...), hệ thống dùng bảng giả định elasticity mặc định dưới đây — được gắn nhãn
[ASSUMPTION] rõ ràng, KHÔNG được trình bày như một con số chắc chắn. Nếu dataset CÓ lịch sử
khuyến mãi đủ dữ liệu, hệ thống ưu tiên tính uplift từ so sánh trước/sau lịch sử thật
(historical response), vẫn không phải causal suy diễn đầy đủ (cần thiết kế treatment/control
mới đạt causal — xem docs/nghien_cuu_nen_tang.md mục XVII/1.1).

[LITERATURE định tính]: BOGO/B1G1 tạo uplift sản lượng cao hơn discount cùng "giá trị khuyến
mãi" nhưng biên lợi nhuận/đơn vị thấp hơn nhiều (Li, Khouja, Pan, Zhou - Management Science 2022);
khách hàng bị hạn chế tài chính phản ứng tốt hơn với BOGO-free so với khuyến mãi giới hạn thời
gian ngắn (Ulqinaku & Sarial-Abi, Italian Journal of Marketing 2025). Xem mục 1.3 trong
docs/nghien_cuu_nen_tang.md.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

MECHANIC_LABELS_VI = {
    "no_promo": "Không khuyến mãi",
    "discount_percent": "Giảm giá theo %",
    "discount_fixed": "Giảm giá số tiền cố định",
    "bogo": "Mua 1 Tặng 1 (B1G1)",
    "buy_x_get_y": "Mua X Tặng Y",
    "bundle": "Combo / Bundle",
    "gift": "Tặng quà kèm theo",
    "member_price": "Giá thành viên (Member Price)",
    "coupon": "Coupon giảm giá",
    "buy_more_save_more": "Mua nhiều giảm nhiều",
}

# Cách tính kinh tế học của từng cơ chế được quy về 1 trong 4 "khuôn" tính toán:
#   percent_discount: giảm % trên giá bán
#   fixed_discount: giảm số tiền cố định / đơn vị
#   free_ratio: tỷ lệ đơn vị được tặng miễn phí trên tổng số đơn vị giao cho khách
#   gift_cost: tặng thêm quà có giá trị nhất định / đơn vị bán, giá bán không đổi
MECHANIC_CALC_KIND = {
    "no_promo": "percent_discount",
    "discount_percent": "percent_discount",
    "discount_fixed": "fixed_discount",
    "bogo": "free_ratio",
    "buy_x_get_y": "free_ratio",
    "bundle": "percent_discount",
    "gift": "gift_cost",
    "member_price": "percent_discount",
    "coupon": "percent_discount",
    "buy_more_save_more": "percent_discount",
}


@dataclass
class BaselineMetrics:
    avg_daily_units: float
    avg_price: float
    unit_cost: float
    promo_days: int
    avg_daily_customers: float | None = None
    repeat_rate: float | None = None


@dataclass
class MechanicResult:
    mechanic: str
    label: str
    param_value: float
    total_units: float
    total_revenue: float
    total_cogs: float
    promotion_cost: float
    gross_profit: float
    margin_pct: float
    estimated_customers: float
    uplift_pct: float
    uplift_source: str  # "historical" hoặc "assumption"


def default_unit_uplift(mechanic: str, depth: float) -> float:
    """[ASSUMPTION cho MVP]: hệ số uplift sản lượng mặc định khi không có dữ liệu lịch sử."""
    depth = max(0.0, min(depth, 0.9))
    if mechanic == "no_promo":
        return 0.0
    if mechanic in ("discount_percent", "discount_fixed", "coupon", "member_price", "buy_more_save_more"):
        return min(0.55, depth * 2.3)
    if mechanic in ("bogo", "buy_x_get_y"):
        return min(0.75, 0.35 + depth * 1.5)
    if mechanic == "bundle":
        return min(0.5, 0.25 + depth * 1.2)
    if mechanic == "gift":
        return min(0.35, 0.10 + depth * 0.8)
    return depth


def estimate_historical_uplift(df: pd.DataFrame, min_promo_days: int = 5) -> dict[str, dict]:
    """Ước lượng uplift từ lịch sử thật (pre/post theo weekday), nếu dataset đủ dữ liệu.

    Đây KHÔNG phải causal inference (không kiểm soát confounder), chỉ là so sánh
    trung bình ngày có khuyến mãi so với ngày không khuyến mãi cùng thứ trong tuần —
    đúng tinh thần "historical response" được yêu cầu ở mục XVI, không tuyên bố causal.

    QUAN TRỌNG: việc so sánh (promo vs baseline) được thực hiện RIÊNG CHO TỪNG product_id
    rồi mới gộp lại theo promotion_type. Nếu so sánh trực tiếp trên toàn bộ dataset (nhiều SKU
    cùng lúc), một ngày khuyến mãi chỉ áp dụng cho 1-2 SKU sẽ bị so sánh nhầm với tổng doanh số
    TOÀN CÔNG TY (baseline không lọc theo SKU) — luôn cho ra uplift âm rất lớn một cách sai lệch.
    """
    if "promotion_type" not in df.columns or df["promotion_type"].isna().all():
        return {}

    df = df.copy()
    df["day"] = df["date"].dt.normalize()
    df["weekday"] = df["day"].dt.weekday

    per_product_daily = df.groupby(
        ["product_id", "day", "weekday", "promotion_type"], as_index=False, dropna=False
    ).agg(units=("quantity", "sum"))

    baseline = per_product_daily[per_product_daily["promotion_type"].isna()]
    baseline_avg = (
        baseline.groupby(["product_id", "weekday"])["units"].mean().rename("baseline_units").reset_index()
    )

    promo_rows = per_product_daily[per_product_daily["promotion_type"].notna()].merge(
        baseline_avg, on=["product_id", "weekday"], how="left"
    )
    promo_rows = promo_rows.dropna(subset=["baseline_units"])
    promo_rows = promo_rows[promo_rows["baseline_units"] > 0]
    promo_rows["ratio"] = promo_rows["units"] / promo_rows["baseline_units"] - 1
    # [BUSINESS RULE]: chặn outlier cực đoan (ví dụ SKU gần như không bán ngày thường) để
    # không làm méo trung bình.
    promo_rows["ratio"] = promo_rows["ratio"].clip(lower=-0.95, upper=5.0)

    result: dict[str, dict] = {}
    for promo_type, group in promo_rows.groupby("promotion_type"):
        if len(group) < min_promo_days:
            continue
        result[promo_type] = {
            "uplift_pct": float(group["ratio"].mean()),
            "n_days_observed": int(len(group)),
        }
    return result


def compute_mechanic_result(
    mechanic: str,
    param_value: float,
    baseline: BaselineMetrics,
    uplift_pct: float,
    uplift_source: str,
    gift_cost_per_unit: float = 0.0,
) -> MechanicResult:
    total_units = baseline.avg_daily_units * baseline.promo_days * (1 + uplift_pct)
    kind = MECHANIC_CALC_KIND[mechanic]
    price = baseline.avg_price
    unit_cost = baseline.unit_cost

    # QUAN TRỌNG: "promo_cost" (chi phí khuyến mãi) ở đây là một chỉ số BÁO CÁO — giá trị
    # doanh nghiệp "cho đi" so với việc bán cùng sản lượng ở giá gốc — chỉ dùng làm mẫu số ROI
    # (mục XVIII). Với 3 cơ chế percent_discount/fixed_discount/free_ratio, khoản này ĐÃ được
    # phản ánh trong "revenue" (vì revenue tính trên giá đã giảm / số đơn vị đã trả tiền), nên
    # KHÔNG được trừ thêm lần nữa khi tính gross_profit — nếu không sẽ trừ trùng 2 lần và làm
    # mọi khuyến mãi trông lỗ giả tạo bất kể margin thực tế. Với "gift_cost", chi phí quà tặng
    # là một khoản chi tiền mặt THẬT chưa hề nằm trong revenue/cogs, nên vẫn phải trừ trực tiếp.
    if kind == "percent_discount":
        depth = param_value
        revenue = total_units * price * (1 - depth)
        cogs = total_units * unit_cost
        promo_cost = total_units * price * depth
        cash_extra_cost = 0.0
    elif kind == "fixed_discount":
        depth_amount = param_value
        eff_price = max(0.0, price - depth_amount)
        revenue = total_units * eff_price
        cogs = total_units * unit_cost
        promo_cost = total_units * depth_amount
        cash_extra_cost = 0.0
    elif kind == "free_ratio":
        free_ratio = param_value
        paid_units = total_units * (1 - free_ratio)
        revenue = paid_units * price
        cogs = total_units * unit_cost
        promo_cost = total_units * free_ratio * price
        cash_extra_cost = 0.0
    elif kind == "gift_cost":
        revenue = total_units * price
        cogs = total_units * unit_cost
        promo_cost = total_units * gift_cost_per_unit
        cash_extra_cost = promo_cost
    else:
        raise ValueError(f"Không nhận diện được cơ chế: {mechanic}")

    gross_profit = revenue - cogs - cash_extra_cost
    margin_pct = (gross_profit / revenue) if revenue > 0 else 0.0

    customer_uplift_factor = 1 + uplift_pct * 0.6  # [ASSUMPTION]: không phải toàn bộ uplift đơn vị đến từ khách mới
    estimated_customers = (
        (baseline.avg_daily_customers or 0) * baseline.promo_days * customer_uplift_factor
    )

    return MechanicResult(
        mechanic=mechanic,
        label=MECHANIC_LABELS_VI.get(mechanic, mechanic),
        param_value=param_value,
        total_units=round(total_units, 1),
        total_revenue=round(revenue, 0),
        total_cogs=round(cogs, 0),
        promotion_cost=round(promo_cost, 0),
        gross_profit=round(gross_profit, 0),
        margin_pct=round(margin_pct, 4),
        estimated_customers=round(estimated_customers, 1),
        uplift_pct=round(uplift_pct, 4),
        uplift_source=uplift_source,
    )
