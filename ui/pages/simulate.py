"""Simulate: cùng simulate_scenarios / rules / ROI — chỉ đổi lớp trình bày theo template."""
from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from services.workflow import ensure_scores, run_simulation, scenario_views
from src.promotion.mechanics import MECHANIC_LABELS_VI
from ui.charts import grouped_bars, show_chart
from ui.components import (
    DASH,
    EMPTY,
    badge,
    chart_workspace_header,
    esc,
    scenario_metric_row,
    show,
    simulation_empty_state,
    simulation_scenario_card,
    simulation_setup_header,
)
from ui.formatters import compact_vnd, integer, pct, roi_label, signed_pct
from ui.shell import continue_button, render_shell

RISK_KIND = {"Thấp": "ok", "Trung bình": "warn", "Cao": "bad"}
LETTER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

MECHANIC_ICON = {
    "bundle": "boxes",
    "discount_percent": "percent",
    "discount_fixed": "percent",
    "member_price": "users",
    "bogo": "gift",
    "buy_x_get_y": "gift",
    "gift": "gift",
    "coupon": "ticket",
    "buy_more_save_more": "trend",
    "no_promo": "circle-x",
}


def render() -> None:
    render_shell("Simulate", "So sánh các phương án promotion và ước tính tác động.", stage=4)
    from src.utils.state import has_data

    if not has_data():
        _empty_simulation()
        return

    setup, board = st.columns([0.95, 2.4], gap="medium")
    with setup:
        scope, scope_value, promo_days, gift_cost = _setup_panel()
        if st.button("Chạy mô phỏng →", type="primary", key="run_sim", width="stretch"):
            if scope_value is None:
                st.error("Hãy chọn sản phẩm hoặc danh mục.")
            else:
                with st.spinner("Đang mô phỏng các cơ chế khuyến mãi..."):
                    ok, message = run_simulation(scope, scope_value, promo_days, gift_cost)
                (st.success if ok else st.error)(message)

    table = ensure_scores()
    meta = st.session_state.get("last_scenario_meta")
    profile = st.session_state["business_profile"]
    views = []
    ready = False
    with board:
        if table is None or meta is None:
            show(
                simulation_empty_state(
                    "Chưa có kết quả mô phỏng",
                    "Thiết lập các tham số bên trái và chạy mô phỏng để so sánh các phương án khuyến mãi.",
                )
            )
        elif meta.get("scope_value") != scope_value:
            st.info("Bộ kết quả đang lưu thuộc lựa chọn khác. Chạy lại mô phỏng cho lựa chọn hiện tại.")
            show(
                simulation_empty_state(
                    "Kết quả không khớp phạm vi",
                    "Phạm vi sản phẩm/danh mục đã đổi — hãy chạy lại mô phỏng.",
                )
            )
        else:
            ready = True
            st.caption(
                "Mô phỏng dựa trên historical response hoặc giả định elasticity, "
                "dùng để so sánh tương đối giữa các kịch bản."
            )
            views = _display_views(table, profile, meta)
            _scenario_board(views)

    if ready and views:
        _comparison(views)
        with st.expander("Bảng đủ mọi kịch bản đã tính"):
            st.dataframe(_display_table(table), width="stretch", hide_index=True)

    _actions(ready=ready, views=views)

def _empty_simulation() -> None:
    setup, board = st.columns([0.95, 2.4], gap="medium")
    with setup, st.container(border=True):
        show(
            simulation_setup_header(
                "Thiết lập mô phỏng",
                "Điều chỉnh các tham số để so sánh hiệu quả giữa các phương án khuyến mãi.",
            )
        )
        st.caption(f"Thời gian chiến dịch: {DASH}")
        st.caption(f"Danh mục sản phẩm: {EMPTY}")
        st.caption(f"Ngân sách tối đa: {DASH}")
        st.caption(f"Giảm giá tối đa: {DASH}")
        st.caption(f"Biên lợi nhuận tối thiểu: {DASH}")
        st.button("Chạy mô phỏng →", type="primary", key="run_sim_empty", width="stretch", disabled=True)
    with board:
        show(
            simulation_empty_state(
                "Chưa có kết quả mô phỏng",
                "Tải dữ liệu và thiết lập tham số để chạy mô phỏng.",
            )
        )
    _actions(ready=False, views=[], empty_key=True)


def _setup_panel():
    with st.container(border=True):
        show(
            simulation_setup_header(
                "Thiết lập mô phỏng",
                "Điều chỉnh các tham số để so sánh hiệu quả giữa các phương án khuyến mãi.",
            )
        )
        return _control_fields()


def _control_fields():
    df = st.session_state["clean_df"]
    caps = st.session_state["capabilities"]
    profile = st.session_state["business_profile"]

    scope = st.radio("Phạm vi", ["Một SKU cụ thể", "Một Danh mục"], key="sim_scope")
    scope_value = None
    if scope == "Một Danh mục":
        if caps.has_category:
            scope_value = st.selectbox(
                "Danh mục sản phẩm",
                sorted(df["category"].dropna().unique()),
                key="sim_cat",
            )
        else:
            st.warning("Không có cột danh mục trong dữ liệu.")
    else:
        top = df.groupby("product_id")["revenue"].sum().sort_values(ascending=False).index.tolist()
        scope_value = st.selectbox("Sản phẩm", top, key="sim_sku")

    period = st.date_input(
        "Thời gian chiến dịch",
        value=(date.today(), date.today() + timedelta(days=6)),
        key="sim_period",
    )
    if isinstance(period, (list, tuple)) and len(period) == 2:
        start, end = period[0], period[1]
    else:
        start = period if isinstance(period, date) else date.today()
        end = start + timedelta(days=6)
    promo_days = max(1, min(30, (end - start).days + 1))
    st.caption(f"{start.strftime('%d/%m/%Y')} – {end.strftime('%d/%m/%Y')} · {promo_days} ngày đưa vào mô hình.")

    budget = st.number_input(
        "Ngân sách tối đa (đ)",
        min_value=0.0,
        value=float(profile.promotion_budget),
        step=1_000_000.0,
        key="sim_budget",
    )
    profile.promotion_budget = float(budget)

    max_discount = st.number_input(
        "Giảm giá tối đa",
        min_value=0.0,
        max_value=0.9,
        value=float(profile.max_discount_pct),
        step=0.01,
        format="%.2f",
        key="sim_max_disc",
        help="Giới hạn cứng theo hồ sơ kinh doanh / business rules.",
    )
    min_margin = st.number_input(
        "Biên lợi nhuận tối thiểu",
        min_value=0.0,
        max_value=0.9,
        value=float(profile.min_margin_pct),
        step=0.01,
        format="%.2f",
        key="sim_min_margin",
        help="Ngưỡng margin tối thiểu từ Prepare / hồ sơ.",
    )
    profile.max_discount_pct = float(max_discount)
    profile.min_margin_pct = float(min_margin)

    gift_cost = st.number_input(
        "Giá trị quà tặng / đơn vị (đ)",
        min_value=0,
        value=5000,
        step=1000,
        key="sim_gift",
    )
    st.caption(
        f"Ngân sách hồ sơ: {compact_vnd(profile.promotion_budget)}. "
        "Vượt ngân sách được gắn cờ, không tự loại kịch bản."
    )
    return scope, scope_value, promo_days, float(gift_cost)


def _display_views(table: pd.DataFrame, profile, meta) -> list[dict]:
    """UI adapter — không đổi scenario_views / scoring."""
    views = [row for row in scenario_views(table, profile, meta) if row["mechanic"] != "no_promo"]
    feasible = [v for v in views if not v["rejected"]]
    rejected = [v for v in views if v["rejected"]]
    # Ưu tiên kịch bản hợp lệ; vẫn generic theo số lượng backend trả.
    ordered = feasible + rejected
    # Gắn letter + recommended (điểm mục tiêu cao nhất trong nhóm hợp lệ)
    best_mech = feasible[0]["mechanic"] if feasible else None
    out = []
    for idx, view in enumerate(ordered[:6]):
        item = dict(view)
        item["letter"] = LETTER[idx] if idx < len(LETTER) else str(idx + 1)
        item["recommended"] = bool(best_mech and view["mechanic"] == best_mech and not view["rejected"])
        item["icon"] = MECHANIC_ICON.get(view["mechanic"], "flask")
        item["subtitle"] = MECHANIC_LABELS_VI.get(view["mechanic"], view["label"])
        out.append(item)
    return out


def _scenario_board(views: list[dict]) -> None:
    if not views:
        st.warning("Không có kịch bản khuyến mãi hợp lệ.")
        return
    selected = st.session_state.get("selected_mechanic")
    cols = st.columns(min(3, len(views)), gap="medium")
    for col, view in zip(cols, views[:3]):
        with col:
            _one_card(view, selected)
    if len(views) > 3:
        cols2 = st.columns(min(3, len(views) - 3), gap="medium")
        for col, view in zip(cols2, views[3:]):
            with col:
                _one_card(view, selected)


def _one_card(view: dict, selected) -> None:
    is_selected = selected == view["mechanic"]
    conf_html = _confidence_html(view["confidence"])
    risk_html = f'<span class="{RISK_KIND.get(view["risk"], "muted")}">{esc(view["risk"])}</span>'
    rev = signed_pct(view["revenue_lift"]) if view["revenue_lift"] is not None else DASH
    profit = signed_pct(view["profit_lift"]) if view["profit_lift"] is not None else DASH
    roi = roi_label(view["roi"]) if view["roi"] is not None else DASH
    # Inventory need = sản lượng kịch bản (đơn vị), kèm gap nếu có tồn kho — không fake %.
    units = integer(view["units"])
    if view["inventory_gap"] is None:
        inv_html = f"{esc(units)} đơn vị"
    else:
        gap = float(view["inventory_gap"])
        inv_html = (
            f"{esc(units)} đơn vị"
            if gap <= 0
            else f'{esc(units)} · <span class="down">thiếu {esc(integer(gap))}</span>'
        )

    metrics = "".join(
        [
            scenario_metric_row("trend", "Revenue lift", f'<span class="up">{esc(rev)}</span>' if rev.startswith("+") else esc(rev)),
            scenario_metric_row("dollar", "Profit impact", f'<span class="up">{esc(profit)}</span>' if str(profit).startswith("+") else esc(profit)),
            scenario_metric_row("chart", "ROI", esc(roi)),
            scenario_metric_row("package", "Inventory need", inv_html),
            scenario_metric_row("alert-triangle", "Risk level", risk_html),
            scenario_metric_row("shield-check", "Confidence", conf_html),
        ]
    )
    show(
        simulation_scenario_card(
            letter=view["letter"],
            title=view["label"],
            subtitle=view["scenario"],
            description=_short_desc(view),
            metrics_html=metrics,
            icon_name=view["icon"],
            selected=is_selected,
            recommended=view.get("recommended", False),
            rejected=view["rejected"],
        )
    )
    if view["rejected"]:
        st.caption("Business rules đã loại kịch bản này.")
        st.button("Không thể chọn", key=f"pick_{view['mechanic']}", width="stretch", disabled=True)
    elif is_selected:
        if st.button("Đã chọn ✓", key=f"pick_{view['mechanic']}", width="stretch", type="primary"):
            pass
    else:
        if st.button("Chọn →", key=f"pick_{view['mechanic']}", width="stretch"):
            st.session_state["selected_mechanic"] = view["mechanic"]
            st.rerun()
    with st.expander("Xem chi tiết →", expanded=False):
        st.write(
            {
                "Cơ chế": view["mechanic"],
                "Doanh thu": view["revenue"],
                "Lợi nhuận gộp": view["profit"],
                "ROI": view["roi"],
                "Sản lượng": view["units"],
                "Revenue lift": view["revenue_lift"],
                "Profit lift": view["profit_lift"],
                "Rủi ro": view["risk"],
                "Bị loại": view["rejected"],
            }
        )


def _short_desc(view: dict) -> str:
    if view["rejected"]:
        return "Kịch bản vi phạm ràng buộc kinh doanh hiện tại."
    if view.get("recommended"):
        return "Điểm mục tiêu cao nhất trong các phương án hợp lệ sau mô phỏng."
    return "Ước tính tác động tương đối so với phương án không khuyến mãi."


def _confidence_html(confidence) -> str:
    label, band = confidence if confidence else (None, None)
    if not label:
        return esc("Chưa có dự báo")
    if band:
        mid = int(round((band[0] + band[1]) / 2))
        return f'<span class="ok">{esc(f"{mid}%")}</span> <span style="color:#94A3B8;font-weight:500">({esc(label)})</span>'
    return f'<span class="ok">{esc(str(label))}</span>'


def _comparison(views: list[dict]) -> None:
    """Chỉ chart các metric % cùng đơn vị; ROI (x) và inventory (đơn vị) tách riêng."""
    chartable = [v for v in views if not v["rejected"]][:4]
    if len(chartable) < 1:
        return
    with st.container(border=True):
        show(
            chart_workspace_header(
                "So sánh các phương án",
                "So sánh tác động dự kiến của các phương án khuyến mãi dựa trên kết quả mô phỏng.",
                "chart-column",
            )
        )
        if len(chartable) >= 2:
            fig = grouped_bars(
                ["Doanh thu tăng", "Lợi nhuận tăng"],
                [(v["label"], [v["revenue_lift"] or 0, v["profit_lift"] or 0]) for v in chartable],
                "So với không khuyến mãi",
                "",
                as_percent=True,
            )
            show_chart(fig)
        roi_items = []
        for v in chartable:
            roi_txt = roi_label(v["roi"]) if v["roi"] is not None else DASH
            inv_txt = f"{integer(v['units'])} đơn vị"
            roi_items.append(
                f'<div class="pp-sim-roi-item"><div class="l">{esc(v["label"])}</div>'
                f'<div class="v">ROI {esc(roi_txt)}</div>'
                f'<div class="u">Inventory need: {esc(inv_txt)}</div></div>'
            )
        show(f'<div class="pp-sim-roi-strip">{"".join(roi_items)}</div>')


def _display_table(table: pd.DataFrame) -> pd.DataFrame:
    show_df = table.copy()
    show_df["Kịch bản"] = show_df["mechanic"].map(lambda item: MECHANIC_LABELS_VI.get(item, item))
    show_df["Doanh thu"] = show_df["doanh_thu"].map(lambda value: f"{value:,.0f}")
    show_df["Lợi nhuận gộp"] = show_df["loi_nhuan_gop"].map(lambda value: f"{value:,.0f}")
    show_df["ROI"] = show_df["roi"].map(lambda value: roi_label(value))
    show_df["Margin"] = show_df["margin"].map(lambda value: pct(value, 0))
    show_df["Trạng thái"] = show_df["bi_tu_choi"].map(lambda value: "Bị loại" if value else "Hợp lệ")
    return show_df[["Kịch bản", "Trạng thái", "Doanh thu", "Lợi nhuận gộp", "ROI", "Margin", "diem_muc_tieu"]]


def _actions(*, ready: bool, views: list[dict], empty_key: bool = False) -> None:
    selected = st.session_state.get("selected_mechanic")
    selected_view = next((v for v in views if v["mechanic"] == selected), None)
    if selected_view and not selected_view["rejected"]:
        show(
            f'<p class="pp-sim-selected-note">Đã chọn: <b>Phương án {esc(selected_view["letter"])} — '
            f'{esc(selected_view["label"])}</b></p>'
        )
    elif ready and not selected:
        show('<p class="pp-sim-selected-note">Chưa chọn phương án — Decide sẽ dùng phương án mặc định theo điểm mục tiêu.</p>')

    left, spacer, right = st.columns([1, 1.4, 1.4])
    with right:
        key = "sim_next_empty" if empty_key else "sim_next"
        if ready:
            # Workflow hiện tại: Decide dùng default_choice nếu chưa chọn — cho phép tiếp tục.
            if selected_view and selected_view["rejected"]:
                st.button("Tiếp tục đến Bước 5: Decide →", type="primary", key=key, width="stretch", disabled=True)
                st.caption("Phương án đang chọn không khả thi — hãy chọn phương án khác.")
            else:
                continue_button("Tiếp tục đến Bước 5: Decide →", "decide", key=key)
        else:
            st.button("Tiếp tục đến Bước 5: Decide →", type="primary", key=key, width="stretch", disabled=True)
