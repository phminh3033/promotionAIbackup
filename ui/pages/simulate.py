"""Simulate: cùng simulate_scenarios / rules / ROI, trình bày thành thẻ kịch bản."""
from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from services.workflow import ensure_scores, run_simulation, scenario_views
from src.promotion.mechanics import MECHANIC_LABELS_VI
from ui.charts import grouped_bars, show_chart
from ui.components import DASH, EMPTY, badge, chart_card, grid, kicker, scenario_card, show
from ui.formatters import integer, pct, roi_label, signed_pct
from ui.shell import continue_button, render_shell

RISK_KIND = {"Thấp": "ok", "Trung bình": "warn", "Cao": "bad"}


def render() -> None:
    render_shell("Simulate", "So sánh các phương án promotion và ước tính tác động.", stage=4)
    from src.utils.state import has_data

    if not has_data():
        _empty_simulation()
        return
    controls, board = st.columns([0.85, 1.7], gap="medium")
    with controls:
        scope, scope_value, promo_days, gift_cost = _controls()
        if st.button("Chạy mô phỏng", type="primary", key="run_sim", width="stretch"):
            if scope_value is None:
                st.error("Hãy chọn sản phẩm hoặc danh mục.")
            else:
                with st.spinner("Đang mô phỏng các cơ chế khuyến mãi..."):
                    ok, message = run_simulation(scope, scope_value, promo_days, gift_cost)
                (st.success if ok else st.error)(message)
    table = ensure_scores()
    meta = st.session_state.get("last_scenario_meta")
    with board:
        if table is None or meta is None:
            _scenario_placeholders()
        elif meta.get("scope_value") != scope_value:
            st.info("Bộ kết quả đang lưu thuộc lựa chọn khác. Chạy lại mô phỏng cho lựa chọn hiện tại.")
        else:
            st.caption("Mô phỏng dựa trên historical response hoặc giả định elasticity, dùng để so sánh tương đối giữa các kịch bản.")
            _cards(table, meta)
    if table is not None and meta and meta.get("scope_value") == scope_value:
        _chart(table, meta)
        with st.expander("Bảng đủ mọi kịch bản đã tính"):
            st.dataframe(_display_table(table), width="stretch", hide_index=True)
    left, right = st.columns([1, 1])
    with right:
        continue_button("Tiếp tục đến bước 5: Decide", "decide", key="sim_next")


def _empty_simulation() -> None:
    controls, board = st.columns([0.85, 1.7], gap="medium")
    with controls:
        show(scenario_card("Thiết lập mô phỏng", "", [
            f"Thời gian chiến dịch: {DASH}",
            f"Danh mục sản phẩm: {EMPTY}",
            f"Ngân sách tối đa: {DASH}",
            f"Giảm giá tối đa: {DASH}",
            f"Biên lợi nhuận tối thiểu: {DASH}",
        ]))
    with board:
        _scenario_placeholders()
    _left, right = st.columns([1, 1])
    with right:
        continue_button("Tiếp tục đến bước 5: Decide", "decide", key="sim_next_empty")


def _scenario_placeholders() -> None:
    show(grid([
        scenario_card(name, "", [
            f"Revenue lift {DASH}",
            f"Profit impact {DASH}",
            f"ROI {DASH}",
            f"Nhu cầu hàng {DASH}",
            EMPTY,
        ])
        for name in ("Phương án A", "Phương án B", "Phương án C")
    ]))
    show(chart_card("So sánh các phương án"))


def _controls():
    with st.container(border=True):
        show(kicker("Thiết lập mô phỏng"))
        return _control_fields()


def _control_fields():
    df = st.session_state["clean_df"]
    caps = st.session_state["capabilities"]
    profile = st.session_state["business_profile"]
    scope = st.radio("Phạm vi", ["Một SKU cụ thể", "Một Danh mục"], key="sim_scope")
    scope_value = None
    if scope == "Một Danh mục":
        if caps.has_category:
            scope_value = st.selectbox("Danh mục", sorted(df["category"].dropna().unique()), key="sim_cat")
        else:
            st.warning("Không có cột danh mục.")
    else:
        top = df.groupby("product_id")["revenue"].sum().sort_values(ascending=False).index.tolist()
        scope_value = st.selectbox("Sản phẩm", top, key="sim_sku")
    start = st.date_input("Bắt đầu", value=date.today(), key="sim_start")
    end = st.date_input("Kết thúc", value=date.today() + timedelta(days=6), key="sim_end")
    promo_days = max(1, min(30, (end - start).days + 1))
    st.caption(f"Thời lượng đưa vào mô hình: {promo_days} ngày.")
    max_discount = st.number_input("Giảm giá tối đa", min_value=0.0, max_value=0.9, value=float(profile.max_discount_pct), step=0.01, format="%.2f", key="sim_max_disc")
    min_margin = st.number_input("Margin tối thiểu", min_value=0.0, max_value=0.9, value=float(profile.min_margin_pct), step=0.01, format="%.2f", key="sim_min_margin")
    profile.max_discount_pct = float(max_discount)
    profile.min_margin_pct = float(min_margin)
    gift_cost = st.number_input("Giá trị quà tặng / đơn vị (đ)", min_value=0, value=5000, step=1000, key="sim_gift")
    st.caption(f"Ngân sách hồ sơ: {profile.promotion_budget:,.0f} đ. Vượt ngân sách được gắn cờ, không tự loại kịch bản.")
    return scope, scope_value, promo_days, float(gift_cost)


def _cards(table, meta) -> None:
    profile = st.session_state["business_profile"]
    views = [row for row in scenario_views(table, profile, meta) if row["mechanic"] != "no_promo"]
    views = views[:3]
    if not views:
        st.warning("Không có kịch bản khuyến mãi hợp lệ.")
        return
    cols = st.columns(len(views))
    selected = st.session_state.get("selected_mechanic")
    for col, view in zip(cols, views):
        with col:
            conf = "Chưa có dự báo"
            if view["confidence"][0]:
                band = view["confidence"][1]
                conf = f"{view['confidence'][0]}" + (f" ({band[0]}–{band[1]}%)" if band else "")
            gap = "—" if view["inventory_gap"] is None else integer(view["inventory_gap"])
            show(scenario_card(
                view["scenario"],
                view["label"],
                [
                    f"Revenue lift {signed_pct(view['revenue_lift'])}",
                    f"Profit impact {signed_pct(view['profit_lift'])}",
                    f"ROI {roi_label(view['roi'])}",
                    f"Nhu cầu hàng {integer(view['units'])} · thiếu so với tồn {gap}",
                ],
                badges_html=badge(view["risk"], RISK_KIND.get(view["risk"], "muted")) + badge(conf, "purple"),
                selected=selected == view["mechanic"],
            ))
            if view["rejected"]:
                st.caption("Business rules đã loại kịch bản này.")
            elif st.button("Chọn", key=f"pick_{view['mechanic']}", width="stretch"):
                st.session_state["selected_mechanic"] = view["mechanic"]
                st.rerun()


def _chart(table, meta) -> None:
    profile = st.session_state["business_profile"]
    views = [row for row in scenario_views(table, profile, meta) if row["mechanic"] != "no_promo" and not row["rejected"]][:4]
    if len(views) < 2:
        return
    labels = [row["label"] for row in views]
    fig = grouped_bars(
        ["Doanh thu tăng", "Lợi nhuận tăng"],
        [(row["label"], [row["revenue_lift"] or 0, row["profit_lift"] or 0]) for row in views],
        "So với không khuyến mãi",
        "So sánh các phương án",
        as_percent=True,
    )
    show_chart(fig)
    units = grouped_bars(["Sản lượng"], [(row["label"], [row["units"]]) for row in views], "Đơn vị", "Nhu cầu hàng theo kịch bản")
    show_chart(units)
    del labels


def _display_table(table: pd.DataFrame) -> pd.DataFrame:
    show = table.copy()
    show["Kịch bản"] = show["mechanic"].map(lambda item: MECHANIC_LABELS_VI.get(item, item))
    show["Doanh thu"] = show["doanh_thu"].map(lambda value: f"{value:,.0f}")
    show["Lợi nhuận gộp"] = show["loi_nhuan_gop"].map(lambda value: f"{value:,.0f}")
    show["ROI"] = show["roi"].map(lambda value: roi_label(value))
    show["Margin"] = show["margin"].map(lambda value: pct(value, 0))
    show["Trạng thái"] = show["bi_tu_choi"].map(lambda value: "Bị loại" if value else "Hợp lệ")
    return show[["Kịch bản", "Trạng thái", "Doanh thu", "Lợi nhuận gộp", "ROI", "Margin", "diem_muc_tieu"]]
