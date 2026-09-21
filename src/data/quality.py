"""Kiểm tra chất lượng dữ liệu sau khi mapping (mục VI yêu cầu gốc).

[BUSINESS RULE tự thiết kế cho MVP]: Điểm số Data Quality Score (0-100) và các ngưỡng
phân loại (Tốt/Khá/Thấp) là quy tắc tự đặt cho MVP, không phải kết quả nghiên cứu khoa học.
Mục tiêu là đưa ra tín hiệu dễ hiểu cho SME, không phải một chỉ số học thuật.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass
class DataQualityReport:
    n_rows: int
    n_transactions: int | None
    n_skus: int
    n_customers: int | None
    date_min: pd.Timestamp | None
    date_max: pd.Timestamp | None
    n_days_span: int
    n_missing_dates: int
    missing_values: dict[str, int]
    n_duplicate_rows: int
    n_negative_quantity: int
    n_negative_revenue: int
    n_zero_sales_rows: int
    n_invalid_rows_dropped: int
    score: int
    score_label: str
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def run_quality_check(df: pd.DataFrame) -> tuple[pd.DataFrame, DataQualityReport]:
    """Chạy kiểm tra chất lượng, trả về (df đã làm sạch cơ bản, báo cáo).

    Không raise exception - luôn trả về báo cáo kèm cảnh báo tiếng Việt.
    """
    warnings: list[str] = []
    notes: list[str] = []
    n_rows_original = len(df)

    missing_values = {col: int(df[col].isna().sum()) for col in df.columns if df[col].isna().any()}

    n_duplicate_rows = int(df.duplicated().sum())

    n_negative_quantity = int((df["quantity"] < 0).sum()) if "quantity" in df.columns else 0
    n_negative_revenue = int((df["revenue"] < 0).sum()) if "revenue" in df.columns else 0
    n_zero_sales_rows = int(((df.get("quantity", pd.Series(dtype=float)) == 0)).sum())

    invalid_mask = df["date"].isna() | df["product_id"].isna() | df["product_id"].eq("nan")
    if "quantity" in df.columns:
        invalid_mask = invalid_mask | df["quantity"].isna()
    if "revenue" in df.columns:
        invalid_mask = invalid_mask | df["revenue"].isna()

    n_invalid_rows_dropped = int(invalid_mask.sum())
    clean_df = df.loc[~invalid_mask].copy()
    clean_df = clean_df.drop_duplicates()

    if clean_df.empty:
        report = DataQualityReport(
            n_rows=n_rows_original,
            n_transactions=None,
            n_skus=0,
            n_customers=None,
            date_min=None,
            date_max=None,
            n_days_span=0,
            n_missing_dates=0,
            missing_values=missing_values,
            n_duplicate_rows=n_duplicate_rows,
            n_negative_quantity=n_negative_quantity,
            n_negative_revenue=n_negative_revenue,
            n_zero_sales_rows=n_zero_sales_rows,
            n_invalid_rows_dropped=n_invalid_rows_dropped,
            score=0,
            score_label="Không thể phân tích",
            warnings=["Sau khi loại bỏ dòng lỗi, không còn dữ liệu hợp lệ nào. Vui lòng kiểm tra lại file gốc."],
            notes=notes,
        )
        return clean_df, report

    date_min = clean_df["date"].min()
    date_max = clean_df["date"].max()
    n_days_span = int((date_max - date_min).days) + 1

    all_days = pd.date_range(date_min.normalize(), date_max.normalize(), freq="D")
    days_with_sales = set(clean_df["date"].dt.normalize().unique())
    n_missing_dates = int(len([d for d in all_days if d not in days_with_sales]))

    n_skus = int(clean_df["product_id"].nunique())
    n_transactions = int(clean_df["transaction_id"].nunique()) if "transaction_id" in clean_df.columns else None
    n_customers = int(clean_df["customer_id"].nunique()) if "customer_id" in clean_df.columns else None

    # --- Chấm điểm Data Quality Score (BUSINESS RULE) ---
    score = 100.0

    invalid_ratio = n_invalid_rows_dropped / max(n_rows_original, 1)
    score -= min(30, invalid_ratio * 100 * 1.5)
    if invalid_ratio > 0.05:
        warnings.append(
            f"Có {n_invalid_rows_dropped:,} dòng ({invalid_ratio:.1%}) bị loại vì thiếu ngày/sản phẩm/số lượng/doanh thu."
        )

    dup_ratio = n_duplicate_rows / max(n_rows_original, 1)
    score -= min(15, dup_ratio * 100)
    if dup_ratio > 0.02:
        warnings.append(f"Phát hiện {n_duplicate_rows:,} dòng trùng lặp hoàn toàn.")

    missing_date_ratio = n_missing_dates / max(n_days_span, 1)
    score -= min(15, missing_date_ratio * 30)
    if missing_date_ratio > 0.2:
        warnings.append(
            f"Có {n_missing_dates}/{n_days_span} ngày không có giao dịch nào — có thể do cửa hàng đóng cửa hoặc thiếu dữ liệu."
        )

    if n_days_span < 60:
        score -= 20
        notes.append(
            f"Dữ liệu chỉ trải dài {n_days_span} ngày, chưa đủ để nhận diện mùa vụ theo năm; dự báo dài hạn sẽ có độ tin cậy thấp hơn."
        )
    elif n_days_span < 180:
        score -= 8
        notes.append(
            f"Dữ liệu có {n_days_span} ngày — đủ để thấy chu kỳ theo tuần/tháng nhưng chưa đủ 1 năm để thấy rõ mùa vụ theo năm."
        )

    neg_ratio = (n_negative_quantity + n_negative_revenue) / max(len(clean_df), 1)
    score -= min(10, neg_ratio * 100)
    if n_negative_quantity or n_negative_revenue:
        notes.append(
            f"Có {n_negative_quantity:,} dòng số lượng âm và {n_negative_revenue:,} dòng doanh thu âm — có thể là đơn trả hàng, hệ thống đã giữ lại để không làm méo tổng doanh thu, nhưng loại khỏi phần huấn luyện dự báo."
        )

    zero_ratio = n_zero_sales_rows / max(len(clean_df), 1)
    if zero_ratio > 0.3:
        notes.append(f"{zero_ratio:.0%} dòng có số lượng bán = 0 — dữ liệu có tính chất intermittent demand.")

    score = max(0, min(100, round(score)))
    if score >= 85:
        label = "Tốt"
    elif score >= 65:
        label = "Khá — có thể phân tích, một số dự báo có độ tin cậy trung bình"
    elif score >= 40:
        label = "Thấp — có thể phân tích cơ bản nhưng độ tin cậy dự báo thấp"
    else:
        label = "Rất thấp — khuyến nghị bổ sung/làm sạch dữ liệu trước khi dùng để ra quyết định"

    report = DataQualityReport(
        n_rows=n_rows_original,
        n_transactions=n_transactions,
        n_skus=n_skus,
        n_customers=n_customers,
        date_min=date_min,
        date_max=date_max,
        n_days_span=n_days_span,
        n_missing_dates=n_missing_dates,
        missing_values=missing_values,
        n_duplicate_rows=n_duplicate_rows,
        n_negative_quantity=n_negative_quantity,
        n_negative_revenue=n_negative_revenue,
        n_zero_sales_rows=n_zero_sales_rows,
        n_invalid_rows_dropped=n_invalid_rows_dropped,
        score=int(score),
        score_label=label,
        warnings=warnings,
        notes=notes,
    )

    clean_df = clean_df[(clean_df["quantity"].fillna(0) >= 0) & (clean_df["revenue"].fillna(0) >= 0)]

    return clean_df, report
