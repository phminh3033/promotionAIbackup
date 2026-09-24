"""Trang Dự báo (mục IX, X yêu cầu gốc): Auto Model Selection + Forecast Output."""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.features.engineering import aggregate_daily
from src.forecasting.selector import select_and_forecast
from src.utils.state import init_session_state, require_data_warning

init_session_state()

st.title("📈 Dự báo Nhu cầu & Doanh thu")

if require_data_warning():
    st.stop()

df = st.session_state["clean_df"]
caps = st.session_state["capabilities"]

st.write(
    "Hệ thống sẽ tự động thử nhiều mô hình dự báo (Naive, Moving Average, Exponential Smoothing, "
    "Holt-Winters, Random Forest, Gradient Boosting...), kiểm tra bằng backtesting, và chọn mô hình "
    "có sai số thấp nhất — **không dùng một mô hình cố định cho mọi trường hợp**."
)

metric_options = {"Doanh thu": "revenue", "Sản lượng bán": "quantity"}
if caps.has_transaction:
    metric_options["Số giao dịch"] = "n_transactions"
if caps.has_customer:
    metric_options["Số khách hàng"] = "n_customers"

col1, col2, col3 = st.columns(3)
with col1:
    scope = st.radio("Phạm vi dự báo", ["Toàn công ty", "Theo Danh mục", "Theo SKU"], horizontal=False)
with col2:
    metric_label = st.selectbox("Chỉ số cần dự báo", list(metric_options.keys()))
    metric_col = metric_options[metric_label]
with col3:
    horizon = st.selectbox("Số ngày dự báo", [7, 14, 30], index=1)

scope_value = None
if scope == "Theo Danh mục":
    if not caps.has_category:
        st.warning("Dữ liệu không có cột Danh mục.")
        st.stop()
    scope_value = st.selectbox("Chọn danh mục", sorted(df["category"].dropna().unique()))
elif scope == "Theo SKU":
    top_skus = df.groupby("product_id")["revenue"].sum().sort_values(ascending=False).index.tolist()
    scope_value = st.selectbox("Chọn sản phẩm (sắp xếp theo doanh thu)", top_skus)

cache_key = f"{scope}|{scope_value}|{metric_col}|{horizon}"

if st.button("🚀 Chạy dự báo", type="primary"):
    status = st.status("Đang xử lý dự báo...", expanded=True)
    status.write("🔄 Đang tổng hợp dữ liệu theo ngày...")

    if scope == "Toàn công ty":
        scoped_df = df
    elif scope == "Theo Danh mục":
        scoped_df = df[df["category"] == scope_value]
    else:
        scoped_df = df[df["product_id"] == scope_value]

    daily = aggregate_daily(scoped_df)
    if metric_col not in daily.columns:
        status.update(label="Thiếu dữ liệu cho chỉ số đã chọn.", state="error")
        st.stop()

    y = daily.set_index("day")[metric_col]
    time.sleep(0.2)
    status.write("🧠 Đang thử nhiều mô hình dự báo & chạy backtesting...")
    result = select_and_forecast(y, horizon=horizon, series_name=metric_label)
    time.sleep(0.2)
    status.write(f"🏆 Đã chọn mô hình: **{result.model_name}**")
    status.update(label="Hoàn tất dự báo!", state="complete")

    st.session_state["forecast_cache"][cache_key] = result

result = st.session_state["forecast_cache"].get(cache_key)

if result is not None:
    st.divider()
    conf_color = {"Cao": "green", "Trung bình": "orange", "Thấp": "red"}[result.confidence]
    c1, c2, c3 = st.columns(3)
    c1.metric("Mô hình được chọn", result.model_name)
    c2.metric("Sai số backtest (WAPE)", f"{result.wape:.1%}" if pd.notna(result.wape) else "N/A")
    c3.markdown(f"**Độ tin cậy:** :{conf_color}[{result.confidence}]")

    st.info(result.explanation)
    if not result.data_sufficient:
        st.warning(
            "Dữ liệu chưa đủ dài để backtest đáng tin cậy — nên xem kết quả dự báo này là tham khảo sơ bộ."
        )

    fig = go.Figure()
    history_tail = y.tail(60) if scope else y
    fig.add_trace(go.Scatter(x=history_tail.index, y=history_tail.values, name="Lịch sử", line=dict(color="#4C78A8")))
    fig.add_trace(
        go.Scatter(
            x=result.dates + result.dates[::-1],
            y=list(result.yhat_upper) + list(result.yhat_lower[::-1]),
            fill="toself",
            fillcolor="rgba(244,162,97,0.25)",
            line=dict(color="rgba(255,255,255,0)"),
            name="Khoảng tin cậy (~80%)",
        )
    )
    fig.add_trace(go.Scatter(x=result.dates, y=result.yhat, name="Dự báo", line=dict(color="#F4A261", dash="dash")))
    fig.update_layout(
        title=f"Dự báo {metric_label.lower()} — {horizon} ngày tới",
        xaxis_title="Ngày",
        yaxis_title=metric_label,
        height=450,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("So sánh các mô hình đã thử (Backtesting)")
    if not result.all_model_scores.empty:
        display_scores = result.all_model_scores.copy()
        display_scores["WAPE"] = display_scores["WAPE"].map(lambda v: f"{v:.1%}")
        if "MAPE" in display_scores.columns:
            display_scores["MAPE"] = display_scores["MAPE"].map(lambda v: f"{v:.1%}" if pd.notna(v) else "N/A (actual gần 0)")
        st.dataframe(display_scores, use_container_width=True)
    else:
        st.write("Không có đủ dữ liệu để so sánh nhiều model.")

    st.subheader("Bảng dự báo chi tiết")
    forecast_table = pd.DataFrame(
        {
            "Ngày": [d.date() for d in result.dates],
            "Dự báo": result.yhat.round(0),
            "Cận dưới": result.yhat_lower.round(0),
            "Cận trên": result.yhat_upper.round(0),
        }
    )
    st.dataframe(forecast_table, use_container_width=True)
else:
    st.info("Chọn phạm vi/chỉ số/số ngày rồi bấm **Chạy dự báo**.")
