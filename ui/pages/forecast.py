"""Forecast: cùng pipeline select_and_forecast, chỉ đổi lớp hiển thị."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from services.workflow import run_forecast
from ui.charts import time_series
from ui.components import DASH, EMPTY, badge, chart_placeholder
from ui.formatters import integer, pct, signed_pct
from ui.shell import continue_button, render_shell

METRICS = [
    ("Dự báo nhu cầu", "Sản lượng bán", "quantity"),
    ("Dự báo doanh thu", "Doanh thu", "revenue"),
    ("Dự báo traffic", "Số giao dịch", "n_transactions"),
]


def render() -> None:
    render_shell("Forecast", "Dự báo nhu cầu, doanh thu và traffic từ dữ liệu lịch sử.", stage=2)
    from src.utils.state import has_data

    if not has_data():
        _empty_forecast()
        return
    df = st.session_state["clean_df"]
    caps = st.session_state["capabilities"]
    scope, scope_value, horizon = _controls(df, caps)
    tab_demand, tab_revenue, tab_traffic = st.tabs([item[0] for item in METRICS])
    with tab_demand:
        _panel(scope, scope_value, horizon, "Sản lượng bán", "quantity", "Đơn vị")
    with tab_revenue:
        _panel(scope, scope_value, horizon, "Doanh thu", "revenue", "Doanh thu")
    with tab_traffic:
        if caps.has_transaction:
            _panel(scope, scope_value, horizon, "Số giao dịch", "n_transactions", "Giao dịch")
        elif caps.has_customer:
            _panel(scope, scope_value, horizon, "Số khách hàng", "n_customers", "Khách hàng")
        else:
            st.info("Cần mã giao dịch hoặc mã khách hàng để dự báo traffic. Hệ thống không ước lượng traffic khi thiếu cột này.")
    left, right = st.columns([1, 1])
    with right:
        continue_button("Tiếp tục đến bước 3: Prepare", "prepare", key="fc_next")


def _empty_forecast() -> None:
    tab_demand, tab_revenue, tab_traffic = st.tabs([item[0] for item in METRICS])
    for tab, title in ((tab_demand, "Dự báo nhu cầu"), (tab_revenue, "Dự báo doanh thu"), (tab_traffic, "Dự báo traffic")):
        with tab:
            chart, summary = st.columns([1.7, 0.9])
            with chart:
                st.markdown(
                    f'<div class="pp-card"><div class="pp-kicker">{title}</div>{chart_placeholder()}</div>',
                    unsafe_allow_html=True,
                )
            with summary:
                st.markdown(
                    f"""
<div class="pp-card">
  <div class="pp-kicker">Kết quả dự báo</div>
  <div class="pp-metric-mini"><div class="l">Tổng kỳ dự báo</div><div class="v">{DASH}</div></div>
  <div class="pp-metric-mini" style="margin-top:8px"><div class="l">So với nhịp lịch sử gần</div><div class="v">{DASH}</div></div>
  <div class="pp-metric-mini" style="margin-top:8px"><div class="l">Khoảng tin cậy</div><div class="v">{DASH}</div></div>
  <p class="pp-muted" style="margin-top:8px">{EMPTY}</p>
</div>
""",
                    unsafe_allow_html=True,
                )
    st.markdown(
        f'<div class="pp-card" style="margin-top:12px"><div class="pp-kicker">Insight từ mô hình</div><p class="pp-muted">{EMPTY}</p></div>',
        unsafe_allow_html=True,
    )
    _col, right = st.columns([1, 1])
    with right:
        continue_button("Tiếp tục đến bước 3: Prepare", "prepare", key="fc_next_empty")


def _controls(df, caps):
    c1, c2, c3 = st.columns(3)
    with c1:
        scope = st.selectbox("Phạm vi", ["Toàn công ty", "Theo Danh mục", "Theo SKU"], key="fc_scope")
    scope_value = None
    with c2:
        if scope == "Theo Danh mục":
            if not caps.has_category:
                st.warning("Dữ liệu không có danh mục.")
            else:
                scope_value = st.selectbox("Danh mục", sorted(df["category"].dropna().unique()), key="fc_cat")
        elif scope == "Theo SKU":
            top = df.groupby("product_id")["revenue"].sum().sort_values(ascending=False).index.tolist()
            scope_value = st.selectbox("Sản phẩm", top, key="fc_sku")
        else:
            st.caption("Phạm vi toàn bộ dữ liệu đã tải.")
    with c3:
        horizon = st.selectbox("Số ngày dự báo", [7, 14, 30], index=1, key="fc_horizon")
    return scope, scope_value, int(horizon)


def _panel(scope, scope_value, horizon, label, metric, y_title) -> None:
    if scope != "Toàn công ty" and scope_value is None:
        return
    cache_key = f"{scope}|{scope_value}|{metric}|{horizon}"
    if st.button(f"Chạy {label.lower()}", type="primary", key=f"run_{metric}_{scope}_{horizon}"):
        try:
            with st.spinner("Đang backtest và chọn mô hình..."):
                run_forecast(scope, scope_value, metric, label, horizon)
        except ValueError as exc:
            st.error(str(exc))
            return
    result = st.session_state.get("forecast_cache", {}).get(cache_key)
    history = st.session_state.get("forecast_history", {}).get(cache_key)
    if result is None or history is None:
        st.info("Chọn phạm vi rồi bấm chạy dự báo. Kết quả được lưu trong phiên và dùng lại ở các màn sau.")
        return
    chart, summary = st.columns([1.7, 0.9])
    with chart:
        fig = time_series(
            history.index,
            history.values,
            result.dates,
            result.yhat,
            result.yhat_lower,
            result.yhat_upper,
            y_title=y_title,
            title=label,
        )
        st.plotly_chart(fig, use_container_width=True)
    with summary:
        expected = float(pd.Series(result.yhat).sum())
        hist_sum = float(pd.Series(history.values).sum()) or None
        growth = (expected / (hist_sum / max(len(history), 1) * len(result.yhat)) - 1) if hist_sum else None
        low, high = float(pd.Series(result.yhat_lower).sum()), float(pd.Series(result.yhat_upper).sum())
        st.markdown(
            f"""
<div class="pp-card">
  <div class="pp-kicker">Kết quả dự báo</div>
  <div class="pp-metric-mini"><div class="l">Tổng kỳ dự báo</div><div class="v">{integer(expected)}</div></div>
  <div class="pp-metric-mini" style="margin-top:8px"><div class="l">So với nhịp lịch sử gần</div><div class="v">{signed_pct(growth) if growth is not None else "—"}</div></div>
  <div class="pp-metric-mini" style="margin-top:8px"><div class="l">Khoảng tin cậy (~80%)</div><div class="v" style="font-size:14px">{integer(low)} – {integer(high)}</div></div>
  <div style="margin-top:8px">{badge(result.confidence, "ok" if result.confidence == "Cao" else "warn")} <span class="pp-muted">WAPE {pct(result.wape, 1) if pd.notna(result.wape) else "—"} · {result.model_name}</span></div>
</div>
""",
            unsafe_allow_html=True,
        )
    st.markdown(
        f'<div class="pp-card" style="margin-top:12px"><div class="pp-kicker">Insight từ mô hình</div><p class="pp-muted">{result.explanation}</p></div>',
        unsafe_allow_html=True,
    )
    if not result.all_model_scores.empty:
        with st.expander("Bảng backtest các mô hình đã thử"):
            scores = result.all_model_scores.copy()
            if "WAPE" in scores.columns:
                scores["WAPE"] = scores["WAPE"].map(lambda value: f"{value:.1%}" if pd.notna(value) else "—")
            st.dataframe(scores, use_container_width=True, hide_index=True)
    if not result.data_sufficient:
        st.warning("Chuỗi chưa đủ dài để backtest chắc chắn. Hãy xem dự báo này là tham khảo sơ bộ.")
