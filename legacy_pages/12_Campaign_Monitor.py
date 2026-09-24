"""Trang Campaign Monitor (mục XXIX spec PromotionPilot AI): so sánh Actual vs Forecast."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.learning.campaign_log import CampaignRecord, list_campaign_records, save_campaign_record
from src.monitoring.campaign_monitor import build_daily_baseline, compare_actual_vs_forecast, cumulative_variance
from src.utils.state import init_session_state

init_session_state()

st.title("📈 Campaign Monitor — Actual vs Forecast")

records = list_campaign_records()
if not records:
    st.warning(
        "⚠️ Chưa có campaign nào được khởi tạo. Vào trang **Execution Plan**, bấm "
        "**Khởi tạo Campaign này** trước."
    )
    st.stop()

record_ids = [r.campaign_id for r in records]
default_idx = record_ids.index(st.session_state["active_campaign_id"]) if st.session_state.get("active_campaign_id") in record_ids else 0
selected_id = st.selectbox(
    "Chọn campaign",
    record_ids,
    index=default_idx,
    format_func=lambda cid: f"{cid} — {next(r.promotion_label for r in records if r.campaign_id == cid)}",
)
record: CampaignRecord = next(r for r in records if r.campaign_id == selected_id)
st.session_state["active_campaign_id"] = selected_id

with st.container(border=True):
    c1, c2, c3 = st.columns(3)
    c1.metric("Sản phẩm/Danh mục", record.product_focus)
    c2.metric("Chương trình", record.promotion_label)
    c3.metric("Ngày khởi chạy", record.forecast.get("campaign_start", "N/A"))

st.subheader("1️⃣ Nhập dữ liệu thực tế (Actual)")
st.write("Nhập số liệu thực tế theo từng ngày kể từ khi khởi chạy (vd Day 1-3 như spec yêu cầu).")

default_actual = pd.DataFrame(
    record.actual.get("daily_rows", [])
    or [{"date": record.forecast.get("campaign_start", ""), "revenue": None, "gp": None, "customers": None, "units": None, "inventory_onhand": None}]
)
if "date" in default_actual.columns:
    try:
        default_actual["date"] = pd.to_datetime(default_actual["date"])
    except Exception:  # noqa: BLE001
        pass

edited = st.data_editor(
    default_actual,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "date": st.column_config.DateColumn("Ngày", required=True),
        "revenue": st.column_config.NumberColumn("Doanh thu thực tế (VNĐ)"),
        "gp": st.column_config.NumberColumn("Lợi nhuận gộp thực tế (VNĐ)"),
        "customers": st.column_config.NumberColumn("Số khách hàng thực tế"),
        "units": st.column_config.NumberColumn("Sản lượng thực tế"),
        "inventory_onhand": st.column_config.NumberColumn("Tồn kho hiện tại"),
    },
)

promo_cost_actual = st.number_input(
    "Chi phí khuyến mãi thực tế đã chi (VNĐ) — để tính ROI thực tế", min_value=0, value=0, step=100_000
)


def json_safe_records(df: pd.DataFrame) -> list[dict]:
    out = df.copy()
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    return out.where(pd.notna(out), None).to_dict("records")


if st.button("💾 Lưu dữ liệu thực tế & Tính toán", type="primary"):
    df = edited.dropna(subset=["date"]).copy()
    df["date"] = pd.to_datetime(df["date"])
    for col in ["revenue", "gp", "customers", "units"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    baseline = build_daily_baseline(
        expected_revenue_range=tuple(record.forecast["expected_revenue_range"]),
        expected_gp_range=tuple(record.forecast["expected_gp_range"]),
        expected_customers_range=tuple(record.forecast["expected_customers_range"]),
        expected_demand_range=tuple(record.forecast["expected_demand_range"]),
        promo_days=record.forecast.get("promo_days") or 7,
    )
    compared = compare_actual_vs_forecast(df, baseline)

    variance = {
        "revenue": cumulative_variance(compared, "revenue"),
        "gp": cumulative_variance(compared, "gp"),
        "customers": cumulative_variance(compared, "customers"),
        "units": cumulative_variance(compared, "units"),
    }

    roi_actual = None
    no_promo_gp_per_day = record.forecast.get("no_promo_gp_per_day")
    if promo_cost_actual > 0 and no_promo_gp_per_day is not None and "gp" in df.columns and df["gp"].notna().any():
        total_actual_gp = df["gp"].sum()
        total_baseline_no_promo_gp = no_promo_gp_per_day * len(df)
        incremental_gp_actual = total_actual_gp - total_baseline_no_promo_gp
        roi_actual = incremental_gp_actual / promo_cost_actual

    record.actual = {"daily_rows": json_safe_records(df), "promo_cost_actual": promo_cost_actual}
    record.variance = variance
    record.roi_actual = roi_actual
    save_campaign_record(record)
    st.session_state["campaign_actual_data"] = compared
    st.success("Đã lưu dữ liệu thực tế. Xem biểu đồ so sánh bên dưới và sang trang **Alerts** để xem cảnh báo.")
    st.rerun()


if record.actual.get("daily_rows"):
    st.divider()
    st.subheader("2️⃣ So sánh Actual vs Forecast")

    baseline = build_daily_baseline(
        expected_revenue_range=tuple(record.forecast["expected_revenue_range"]),
        expected_gp_range=tuple(record.forecast["expected_gp_range"]),
        expected_customers_range=tuple(record.forecast["expected_customers_range"]),
        expected_demand_range=tuple(record.forecast["expected_demand_range"]),
        promo_days=record.forecast.get("promo_days") or 7,
    )
    actual_df = pd.DataFrame(record.actual["daily_rows"])
    actual_df["date"] = pd.to_datetime(actual_df["date"])
    for col in ["revenue", "gp", "customers", "units"]:
        if col in actual_df.columns:
            actual_df[col] = pd.to_numeric(actual_df[col], errors="coerce")
    compared = compare_actual_vs_forecast(actual_df, baseline)

    m1, m2, m3, m4 = st.columns(4)
    rev_var = record.variance.get("revenue")
    gp_var = record.variance.get("gp")
    cust_var = record.variance.get("customers")
    m1.metric("Doanh thu vs Dự báo", f"{rev_var:+.0%}" if rev_var is not None else "N/A")
    m2.metric("Lợi nhuận gộp vs Dự báo", f"{gp_var:+.0%}" if gp_var is not None else "N/A")
    m3.metric("Khách hàng vs Dự báo", f"{cust_var:+.0%}" if cust_var is not None else "N/A")
    m4.metric("ROI thực tế", f"{record.roi_actual:.0%}" if record.roi_actual is not None else "N/A")

    if "revenue" in compared.columns:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=compared["date"], y=compared["revenue"], name="Thực tế", line=dict(color="#2E7D32")))
        fig.add_trace(go.Scatter(x=compared["date"], y=compared["revenue_forecast"], name="Dự báo (baseline/ngày)", line=dict(color="#9E9E9E", dash="dash")))
        fig.update_layout(title="Doanh thu: Thực tế vs Dự báo", height=380)
        st.plotly_chart(fig, use_container_width=True)

    st.dataframe(compared, use_container_width=True)
    st.session_state["campaign_actual_data"] = compared

    st.caption("👉 Sang trang **Alerts** để xem cảnh báo tự động và đề xuất Continue/Adjust/Stop/Scale.")
