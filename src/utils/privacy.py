"""Tiện ích riêng tư dữ liệu (mục XXXIX spec PromotionPilot AI).

Cho phép doanh nghiệp ẩn/mã hoá Mã khách hàng trước khi hiển thị/xuất báo cáo — dữ liệu gốc trong
DataFrame làm việc KHÔNG bị đổi (chỉ áp dụng cho bản hiển thị/export), để các phép tính RFM/basket
vẫn dùng đúng customer_id gốc để nhóm giao dịch chính xác.
"""
from __future__ import annotations

import hashlib

import pandas as pd


def hash_customer_id(customer_id: str, salt: str = "promotionpilot") -> str:
    if pd.isna(customer_id) or str(customer_id).strip() == "":
        return ""
    digest = hashlib.sha256(f"{salt}:{customer_id}".encode("utf-8")).hexdigest()
    return f"KH_{digest[:10].upper()}"


def mask_dataframe_customer_id(df: pd.DataFrame, column: str = "customer_id", enabled: bool = True) -> pd.DataFrame:
    """Trả về bản SAO của df với cột customer_id đã hash — dùng khi hiển thị bảng chi tiết/export
    cho người xem không cần biết danh tính khách hàng thật (vd chia sẻ báo cáo ra ngoài)."""
    if not enabled or column not in df.columns:
        return df
    masked = df.copy()
    masked[column] = masked[column].map(lambda v: hash_customer_id(v))
    return masked
