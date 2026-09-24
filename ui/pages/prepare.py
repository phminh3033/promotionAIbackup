"""Prepare: tồn kho, ngân sách, margin — dùng inventory planner hiện có."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from services.workflow import recent_demand, run_inventory, stock_status
from ui.components import DASH, EMPTY, badge, banner, bullets, card, data_table, esc, kicker, kpi_grid, muted, placeholder_table, show, stat_card
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
        show(kpi_grid([
            stat_card("Tồn kho", DASH, EMPTY),
            stat_card("Ngân sách", DASH, EMPTY),
            stat_card("Biên lợi nhuận", DASH, EMPTY),
            stat_card("Năng lực vận hành", DASH, EMPTY),
        ]))
        show(placeholder_table(["Sản phẩm", "Danh mục", "Tồn kho hiện tại", "Nhu cầu dự báo", "Chênh lệch", "Trạng thái"]))
        show(card(kicker("Vấn đề cần xử lý") + muted(EMPTY), style="margin-top:12px"))
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
        st.dataframe(demand.sort_values("avg_daily_demand", ascending=False), width="stretch", hide_index=True)
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
    show(kpi_grid([
        stat_card("Tồn kho", ready, ready_note),
        stat_card("Ngân sách", vnd(profile.promotion_budget), "Ngân sách khuyến mãi trong hồ sơ", compact=True),
        stat_card("Biên lợi nhuận", margin_txt, f"Thực tế nếu có giá vốn, không thì margin mục tiêu {pct(profile.target_margin_pct, 0)}"),
        stat_card("Năng lực vận hành", ops, gap_note or "Dựa trên số SKU rủi ro hết hàng cao.", compact=True),
    ]))


def _table(plan: pd.DataFrame) -> None:
    frame = plan.copy()
    frame["Trạng thái"] = frame.apply(stock_status, axis=1)
    frame["Nhu cầu lead time"] = frame["expected_demand_leadtime"]
    frame["Chênh lệch"] = frame["recommended_order_qty"]
    query = st.text_input("Tìm sản phẩm", key="prep_search")
    if query:
        frame = frame[frame["product_id"].astype(str).str.contains(query, case=False, na=False)]
    rows = []
    for _, row in frame.sort_values("recommended_order_qty", ascending=False).head(40).iterrows():
        status = row["Trạng thái"]
        category = row["category"] if "category" in frame.columns and pd.notna(row.get("category")) else "—"
        rows.append([
            esc(row["product_id"]),
            esc(category),
            esc(integer(row["current_inventory"])),
            esc(integer(row["Nhu cầu lead time"])),
            esc(integer(row["Chênh lệch"])),
            badge(status, STATUS_KIND[status]),
        ])
    show(data_table(
        ["Sản phẩm", "Danh mục", "Tồn kho hiện tại", "Nhu cầu lead time", "Cần nhập", "Trạng thái"],
        rows,
        title="Sản phẩm trọng tâm",
        raw=True,
    ))


def _issues(plan: pd.DataFrame, profile) -> None:
    issues = plan[plan["stockout_risk"] == "HIGH"].sort_values("recommended_order_qty", ascending=False).head(3)
    if issues.empty:
        show(banner("Không có SKU nào ở mức rủi ro hết hàng cao với tham số hiện tại.", "good"))
        return
    items = [
        f"{row.product_id}: cần nhập thêm {integer(row.recommended_order_qty)} để phủ lead time và safety stock."
        for row in issues.itertuples()
    ]
    table = st.session_state.get("last_scenario_table")
    if table is not None and "chi_phi_khuyen_mai" in table.columns:
        cost = float(table["chi_phi_khuyen_mai"].max())
        if profile.promotion_budget and cost > profile.promotion_budget:
            items.append("Chi phí khuyến mãi của một kịch bản đã mô phỏng vượt ngân sách hồ sơ.")
    show(card(kicker("Vấn đề cần xử lý") + bullets(items), style="margin-top:12px"))
