"""Prepare: tồn kho, ngân sách, margin — dùng inventory planner hiện có."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from services.workflow import recent_demand, run_inventory, stock_status
from ui.components import DASH, EMPTY, badge
from ui.formatters import integer, pct, vnd
from ui.shell import continue_button, render_shell

STATUS_KIND = {"Đủ hàng": "ok", "Sắp thiếu": "warn", "Thiếu hàng": "bad"}


def render() -> None:
    render_shell(
        "Prepare",
        "Đánh giá tồn kho, ngân sách, margin và năng lực vận hành trước khi mô phỏng.",
        stage=3,
    )
    from src.utils.state import has_data

    if not has_data():
        st.markdown(
            f"""
<div class="pp-kpi-grid">
  <div class="pp-card"><div class="pp-kicker">Tồn kho</div><div class="pp-value">{DASH}</div><div class="pp-muted">{EMPTY}</div></div>
  <div class="pp-card"><div class="pp-kicker">Ngân sách</div><div class="pp-value">{DASH}</div><div class="pp-muted">{EMPTY}</div></div>
  <div class="pp-card"><div class="pp-kicker">Biên lợi nhuận</div><div class="pp-value">{DASH}</div><div class="pp-muted">{EMPTY}</div></div>
  <div class="pp-card"><div class="pp-kicker">Năng lực vận hành</div><div class="pp-value">{DASH}</div><div class="pp-muted">{EMPTY}</div></div>
</div>
""",
            unsafe_allow_html=True,
        )
        from ui.components import placeholder_table

        st.markdown(placeholder_table(["Sản phẩm", "Danh mục", "Tồn kho hiện tại", "Nhu cầu dự báo", "Chênh lệch", "Trạng thái"]), unsafe_allow_html=True)
        st.markdown(f'<div class="pp-card" style="margin-top:12px"><div class="pp-kicker">Vấn đề cần xử lý</div><p class="pp-muted">{EMPTY}</p></div>', unsafe_allow_html=True)
        _left, right = st.columns([1, 1])
        with right:
            continue_button("Tiếp tục sang Simulate", "simulate", key="prep_next_empty")
        return
    profile = st.session_state["business_profile"]
    caps = st.session_state["capabilities"]
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        lead = st.number_input("Lead time (ngày)", min_value=1, value=int(profile.lead_time_days), key="prep_lead")
    with c2:
        safety = st.number_input("Safety stock (ngày)", min_value=0, value=int(profile.safety_stock_days), key="prep_safety")
    with c3:
        budget = st.number_input("Ngân sách khuyến mãi (đ)", min_value=0.0, value=float(profile.promotion_budget), step=1_000_000.0, key="prep_budget")
    with c4:
        min_margin = st.number_input("Margin tối thiểu", min_value=0.0, max_value=0.9, value=float(profile.min_margin_pct), step=0.01, format="%.2f", key="prep_margin")
    profile.promotion_budget = float(budget)
    profile.min_margin_pct = float(min_margin)
    if not caps.has_inventory:
        st.warning("Chưa có cột tồn kho. Hệ thống chỉ hiện nhu cầu gần đây, không tính số lượng cần nhập.")
        demand = recent_demand(st.session_state["clean_df"])
        st.dataframe(demand.sort_values("avg_daily_demand", ascending=False), use_container_width=True, hide_index=True)
    elif st.button("Tính mức sẵn sàng tồn kho", type="primary", key="run_inv"):
        with st.spinner("Đang lập kế hoạch tồn kho..."):
            run_inventory(int(lead), int(safety))
    plan = st.session_state.get("inventory_plan")
    _kpis(plan, profile, caps)
    if plan is not None:
        _table(plan)
        _issues(plan, profile)
    left, right = st.columns([1, 1])
    with right:
        continue_button("Tiếp tục sang Simulate", "simulate", key="prep_next")


def _kpis(plan, profile, caps) -> None:
    if plan is None or plan.empty:
        ready = "Chưa tính"
        ready_note = "Bấm tính mức sẵn sàng khi đã có tồn kho."
        gap_note = ""
    else:
        enough = int((plan["stockout_risk"] == "LOW").sum())
        ready_pct = enough / len(plan)
        ready = pct(ready_pct, 0)
        ready_note = f"{enough}/{len(plan)} SKU đủ hàng theo lead time và safety stock đã chọn."
        gap_note = ready_note
    margin_txt = pct(profile.target_margin_pct, 0)
    if caps.has_cost or caps.has_gross_profit:
        df = st.session_state["clean_df"]
        revenue = float(df["revenue"].sum())
        if "gross_profit" in df.columns and revenue:
            margin_txt = pct(float(df["gross_profit"].sum()) / revenue, 1)
    ops = "Sẵn sàng" if plan is not None and not plan.empty and int((plan["stockout_risk"] == "HIGH").sum()) == 0 else "Cần rà soát"
    st.markdown(
        f"""
<div class="pp-kpi-grid">
  <div class="pp-card"><div class="pp-kicker">Tồn kho</div><div class="pp-value">{ready}</div><div class="pp-muted">{ready_note}</div></div>
  <div class="pp-card"><div class="pp-kicker">Ngân sách</div><div class="pp-value" style="font-size:22px">{vnd(profile.promotion_budget)}</div><div class="pp-muted">Ngân sách khuyến mãi trong hồ sơ</div></div>
  <div class="pp-card"><div class="pp-kicker">Biên lợi nhuận</div><div class="pp-value">{margin_txt}</div><div class="pp-muted">Thực tế nếu có giá vốn, không thì margin mục tiêu {pct(profile.target_margin_pct, 0)}</div></div>
  <div class="pp-card"><div class="pp-kicker">Năng lực vận hành</div><div class="pp-value" style="font-size:22px">{ops}</div><div class="pp-muted">{gap_note or "Dựa trên số SKU rủi ro hết hàng cao."}</div></div>
</div>
""",
        unsafe_allow_html=True,
    )


def _table(plan: pd.DataFrame) -> None:
    show = plan.copy()
    show["Trạng thái"] = show.apply(stock_status, axis=1)
    show["Nhu cầu lead time"] = show["expected_demand_leadtime"]
    show["Chênh lệch"] = show["recommended_order_qty"]
    query = st.text_input("Tìm sản phẩm", key="prep_search")
    if query:
        show = show[show["product_id"].astype(str).str.contains(query, case=False, na=False)]
    rows = []
    for _, row in show.sort_values("recommended_order_qty", ascending=False).head(40).iterrows():
        status = row["Trạng thái"]
        category = row["category"] if "category" in show.columns and pd.notna(row.get("category")) else "—"
        rows.append(
            "<tr>"
            f"<td>{row['product_id']}</td><td>{category}</td>"
            f"<td>{integer(row['current_inventory'])}</td><td>{integer(row['Nhu cầu lead time'])}</td>"
            f"<td>{integer(row['Chênh lệch'])}</td><td>{badge(status, STATUS_KIND[status])}</td>"
            "</tr>"
        )
    st.markdown(
        '<div class="pp-card" style="overflow-x:auto"><div class="pp-kicker">Sản phẩm trọng tâm</div>'
        '<table class="pp-table"><thead><tr><th>Sản phẩm</th><th>Danh mục</th><th>Tồn kho hiện tại</th>'
        f'<th>Nhu cầu lead time</th><th>Cần nhập</th><th>Trạng thái</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>',
        unsafe_allow_html=True,
    )


def _issues(plan: pd.DataFrame, profile) -> None:
    issues = plan[plan["stockout_risk"] == "HIGH"].sort_values("recommended_order_qty", ascending=False).head(3)
    if issues.empty:
        st.markdown('<div class="pp-banner good">Không có SKU nào ở mức rủi ro hết hàng cao với tham số hiện tại.</div>', unsafe_allow_html=True)
        return
    items = "".join(
        f"<li>{row.product_id}: cần nhập thêm {integer(row.recommended_order_qty)} để phủ lead time và safety stock.</li>"
        for row in issues.itertuples()
    )
    budget_note = ""
    table = st.session_state.get("last_scenario_table")
    if table is not None and "chi_phi_khuyen_mai" in table.columns:
        cost = float(table["chi_phi_khuyen_mai"].max())
        if profile.promotion_budget and cost > profile.promotion_budget:
            budget_note = "<li>Chi phí khuyến mãi của một kịch bản đã mô phỏng vượt ngân sách hồ sơ.</li>"
    st.markdown(
        f'<div class="pp-card" style="margin-top:12px"><div class="pp-kicker">Vấn đề cần xử lý</div><ul class="pp-list">{items}{budget_note}</ul></div>',
        unsafe_allow_html=True,
    )
