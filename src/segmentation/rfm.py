"""Tính RFM (Recency, Frequency, Monetary) cho từng khách hàng (mục XII yêu cầu gốc).

[LITERATURE]: RFM là phương pháp phổ biến, dễ diễn giải cho SME — xem
docs/nghien_cuu_nen_tang.md mục 1.4 (Christy et al. 2021; MDPI Sustainability 2022).
"""
from __future__ import annotations

import pandas as pd


def compute_rfm(df: pd.DataFrame) -> pd.DataFrame:
    """Tính RFM theo customer_id. Yêu cầu df có cột: customer_id, date, revenue.

    Recency: số ngày kể từ lần mua gần nhất tới ngày cuối cùng có dữ liệu.
    Frequency: số giao dịch (hoặc số ngày mua nếu không có transaction_id) duy nhất.
    Monetary: tổng doanh thu.
    """
    if "customer_id" not in df.columns:
        raise ValueError("Dữ liệu không có cột customer_id, không thể tính RFM.")

    reference_date = df["date"].max() + pd.Timedelta(days=1)

    freq_col = "transaction_id" if "transaction_id" in df.columns else "date"

    rfm = df.groupby("customer_id").agg(
        recency=("date", lambda s: (reference_date - s.max()).days),
        frequency=(freq_col, "nunique"),
        monetary=("revenue", "sum"),
        first_purchase=("date", "min"),
        last_purchase=("date", "max"),
    ).reset_index()

    rfm["monetary"] = rfm["monetary"].round(0)
    return rfm
