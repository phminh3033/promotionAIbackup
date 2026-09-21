"""Lập kế hoạch tồn kho & đề xuất số lượng nhập hàng (mục XI yêu cầu gốc).

Công thức theo yêu cầu gốc:
    Recommended Order Qty = Expected Demand + Safety Stock - Current Inventory - Incoming Inventory

[BUSINESS RULE tự thiết kế]: Safety Stock = nhu cầu bình quân/ngày x Safety Stock Days
(cách tiếp cận đơn giản, dễ hiểu cho SME, thay vì công thức thống kê z*sigma*sqrt(L)
phức tạp hơn — phù hợp với việc SME nhập liệu "Safety Stock Days" trực tiếp theo yêu cầu
gốc mục XI, thay vì yêu cầu tính service level phân phối chuẩn).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class InventoryRecommendation:
    product_id: str
    avg_daily_demand: float
    expected_demand_leadtime: float
    safety_stock: float
    current_inventory: float
    incoming_inventory: float
    recommended_order_qty: float
    days_of_inventory: float
    stockout_risk: str
    overstock_risk: str
    explanation: str


def plan_sku_inventory(
    product_id: str,
    avg_daily_demand: float,
    current_inventory: float,
    lead_time_days: float,
    safety_stock_days: float,
    incoming_inventory: float = 0.0,
) -> InventoryRecommendation:
    avg_daily_demand = max(0.0, float(avg_daily_demand))
    current_inventory = max(0.0, float(current_inventory))
    incoming_inventory = max(0.0, float(incoming_inventory))

    expected_demand_leadtime = avg_daily_demand * lead_time_days
    safety_stock = avg_daily_demand * safety_stock_days
    recommended_order_qty = max(
        0.0, expected_demand_leadtime + safety_stock - current_inventory - incoming_inventory
    )

    days_of_inventory = (current_inventory / avg_daily_demand) if avg_daily_demand > 0 else float("inf")

    stockout_threshold_high = lead_time_days
    stockout_threshold_medium = lead_time_days + safety_stock_days
    if days_of_inventory < stockout_threshold_high:
        stockout_risk = "HIGH"
    elif days_of_inventory < stockout_threshold_medium:
        stockout_risk = "MEDIUM"
    else:
        stockout_risk = "LOW"

    overstock_base = lead_time_days + safety_stock_days
    if days_of_inventory > 3 * overstock_base and overstock_base > 0:
        overstock_risk = "HIGH"
    elif days_of_inventory > 1.5 * overstock_base and overstock_base > 0:
        overstock_risk = "MEDIUM"
    else:
        overstock_risk = "LOW"

    risk_vi = {"HIGH": "Cao", "MEDIUM": "Trung bình", "LOW": "Thấp"}
    if avg_daily_demand == 0:
        explanation = f"Sản phẩm {product_id} không có nhu cầu bán ra gần đây, chưa cần nhập thêm."
    elif recommended_order_qty > 0:
        explanation = (
            f"Nhu cầu dự kiến trong {lead_time_days:.0f} ngày chờ hàng là {expected_demand_leadtime:.0f} sản phẩm, "
            f"cộng {safety_stock:.0f} sản phẩm dự phòng (an toàn {safety_stock_days:.0f} ngày). "
            f"Sau khi trừ tồn kho hiện có ({current_inventory:.0f}) và hàng đang về ({incoming_inventory:.0f}), "
            f"nên đặt thêm {recommended_order_qty:.0f} sản phẩm. "
            f"Rủi ro hết hàng: {risk_vi[stockout_risk]}."
        )
    else:
        explanation = (
            f"Tồn kho hiện tại ({current_inventory:.0f}) đã đủ đáp ứng nhu cầu dự kiến, chưa cần đặt thêm. "
            f"Rủi ro tồn dư: {risk_vi[overstock_risk]}."
        )

    return InventoryRecommendation(
        product_id=product_id,
        avg_daily_demand=round(avg_daily_demand, 2),
        expected_demand_leadtime=round(expected_demand_leadtime, 1),
        safety_stock=round(safety_stock, 1),
        current_inventory=current_inventory,
        incoming_inventory=incoming_inventory,
        recommended_order_qty=round(recommended_order_qty, 0),
        days_of_inventory=round(days_of_inventory, 1) if np.isfinite(days_of_inventory) else float("inf"),
        stockout_risk=stockout_risk,
        overstock_risk=overstock_risk,
        explanation=explanation,
    )


def plan_inventory_for_all_skus(
    demand_by_sku: pd.DataFrame,
    inventory_by_sku: pd.DataFrame,
    lead_time_days: float,
    safety_stock_days: float,
) -> pd.DataFrame:
    """demand_by_sku: cột [product_id, avg_daily_demand]. inventory_by_sku: cột [product_id, inventory, incoming_inventory?]."""
    merged = demand_by_sku.merge(inventory_by_sku, on="product_id", how="left")
    merged["inventory"] = merged["inventory"].fillna(0)
    if "incoming_inventory" not in merged.columns:
        merged["incoming_inventory"] = 0.0
    merged["incoming_inventory"] = merged["incoming_inventory"].fillna(0)

    records = []
    for _, row in merged.iterrows():
        rec = plan_sku_inventory(
            product_id=row["product_id"],
            avg_daily_demand=row["avg_daily_demand"],
            current_inventory=row["inventory"],
            lead_time_days=lead_time_days,
            safety_stock_days=safety_stock_days,
            incoming_inventory=row["incoming_inventory"],
        )
        records.append(rec.__dict__)

    return pd.DataFrame(records)
