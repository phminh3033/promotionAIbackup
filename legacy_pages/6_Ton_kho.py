"""Trang Tồn kho & Đề xuất nhập hàng (mục XI yêu cầu gốc)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import plotly.express as px
import streamlit as st

from src.inventory.planning import plan_inventory_for_all_skus
from src.utils.state import init_session_state, require_data_warning

init_session_state()

st.title("📦 Tồn kho & Đề xuất nhập hàng")

if require_data_warning():
    st.stop()

df = st.session_state["clean_df"]
caps = st.session_state["capabilities"]
profile = st.session_state["business_profile"]

RECENT_DAYS = 30
cutoff = df["date"].max() - pd.Timedelta(days=RECENT_DAYS)
recent_df = df[df["date"] >= cutoff]
avg_demand = (
    recent_df.groupby("product_id")["quantity"].sum().reset_index().rename(columns={"quantity": "total_qty"})
)
avg_demand["avg_daily_demand"] = avg_demand["total_qty"] / RECENT_DAYS
st.caption(f"Nhu cầu bình quân/ngày được tính từ {RECENT_DAYS} ngày gần nhất trong dữ liệu (đến {df['date'].max().date()}).")

if not caps.has_inventory:
    st.warning(
        "⛔ Dữ liệu không có cột **Tồn kho** nên hệ thống chỉ hiển thị được nhu cầu dự kiến, "
        "chưa thể tính số lượng cần nhập. Vui lòng bổ sung cột Tồn kho ở lần tải dữ liệu sau."
    )
    st.dataframe(
        avg_demand[["product_id", "avg_daily_demand"]].sort_values("avg_daily_demand", ascending=False),
        use_container_width=True,
    )
    st.stop()

col1, col2 = st.columns(2)
with col1:
    lead_time = st.number_input("Lead Time (số ngày chờ hàng về)", min_value=1, value=profile.lead_time_days)
with col2:
    safety_days = st.number_input("Safety Stock (số ngày dự phòng)", min_value=0, value=profile.safety_stock_days)

latest_inventory = (
    df.sort_values("date").groupby("product_id")["inventory"].last().reset_index()
)

if st.button("📋 Tính đề xuất nhập hàng", type="primary"):
    plan = plan_inventory_for_all_skus(
        demand_by_sku=avg_demand[["product_id", "avg_daily_demand"]],
        inventory_by_sku=latest_inventory,
        lead_time_days=lead_time,
        safety_stock_days=safety_days,
    )
    st.session_state["inventory_plan"] = plan

plan = st.session_state.get("inventory_plan")
if plan is not None:
    st.divider()
    risk_vi = {"LOW": "Thấp", "MEDIUM": "Trung bình", "HIGH": "Cao"}
    plan_display = plan.copy()
    plan_display["stockout_risk_vi"] = plan_display["stockout_risk"].map(risk_vi)
    plan_display["overstock_risk_vi"] = plan_display["overstock_risk"].map(risk_vi)

    c1, c2, c3 = st.columns(3)
    c1.metric("Số SKU cần đặt hàng", int((plan_display["recommended_order_qty"] > 0).sum()))
    c2.metric("Số SKU rủi ro hết hàng Cao", int((plan_display["stockout_risk"] == "HIGH").sum()))
    c3.metric("Số SKU rủi ro tồn dư Cao", int((plan_display["overstock_risk"] == "HIGH").sum()))

    tab1, tab2, tab3 = st.tabs(["📋 Cần đặt hàng", "⚠️ Rủi ro hết hàng", "📈 Rủi ro tồn dư"])
    with tab1:
        need_order = plan_display[plan_display["recommended_order_qty"] > 0].sort_values(
            "recommended_order_qty", ascending=False
        )
        st.dataframe(
            need_order[
                ["product_id", "avg_daily_demand", "current_inventory", "recommended_order_qty", "days_of_inventory", "stockout_risk_vi"]
            ].rename(
                columns={
                    "product_id": "Sản phẩm",
                    "avg_daily_demand": "Nhu cầu TB/ngày",
                    "current_inventory": "Tồn kho hiện tại",
                    "recommended_order_qty": "Đề xuất nhập",
                    "days_of_inventory": "Số ngày tồn kho còn dùng",
                    "stockout_risk_vi": "Rủi ro hết hàng",
                }
            ),
            use_container_width=True,
        )
    with tab2:
        st.dataframe(
            plan_display[plan_display["stockout_risk"] == "HIGH"][["product_id", "days_of_inventory", "recommended_order_qty", "explanation"]],
            use_container_width=True,
        )
    with tab3:
        st.dataframe(
            plan_display[plan_display["overstock_risk"] == "HIGH"][["product_id", "days_of_inventory", "current_inventory", "explanation"]],
            use_container_width=True,
        )

    st.subheader("Chi tiết từng sản phẩm")
    selected_sku = st.selectbox("Chọn sản phẩm để xem giải thích", plan_display["product_id"].tolist())
    row = plan_display[plan_display["product_id"] == selected_sku].iloc[0]
    st.info(row["explanation"])

    fig = px.bar(
        plan_display.sort_values("recommended_order_qty", ascending=False).head(20),
        x="product_id",
        y="recommended_order_qty",
        title="Top 20 SKU cần nhập nhiều nhất",
        labels={"product_id": "Sản phẩm", "recommended_order_qty": "Số lượng đề xuất nhập"},
    )
    st.plotly_chart(fig, use_container_width=True)
