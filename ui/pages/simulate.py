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
from ui.formatters import compact_vnd, format_int_commas, integer, parse_int_commas, roi_label, signed_pct
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
    # Trước shell: nếu vừa vào lại từ Decide/trang khác → khớp widget với kết quả mô phỏng đã lưu.
    prev_page = st.session_state.get("_pp_active_page")
    if prev_page != "simulate":
        _align_controls_from_last_simulation()

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
                # Chỉ đọc ô text → số; không ghi lại *_fmt (widget đã instantiate).
                _pull_sim_money_from_fmt()
                gift_cost = float(st.session_state.get("sim_gift") or 0)
                st.session_state["business_profile"].promotion_budget = float(
                    st.session_state.get("sim_budget") or 0
                )
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
            # Fallback: vẫn hiện kết quả đã lưu nếu meta còn — tránh mất board khi widget lệch tạm thời.
            st.info(
                f"Đang hiện kết quả mô phỏng cho «{meta.get('scope_value')}». "
                "Phạm vi bên trái khác kết quả — chạy lại mô phỏng nếu muốn cập nhật."
            )
            ready = True
            views = _display_views(table, profile, meta)
            _scenario_board(views)
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

    _actions(ready=ready, views=views)


def _align_controls_from_last_simulation() -> None:
    """Khôi phục tham số Simulate + giữ selected_mechanic khi quay lại từ Decide/trang khác.

    Widget Streamlit có thể mất/khác mặc định sau switch_page → lệch scope_value so với
    last_scenario_meta và làm board trông như «mất» kết quả. Hàm này khớp lại UI với meta
    đã lưu khi bấm «Chạy mô phỏng» (kể cả ngày bắt đầu/kết thúc và ngân sách thật).
    """
    from src.promotion.sim_setup import budget_from_meta, campaign_window_from_meta

    drafts = dict(st.session_state.get("ui_control_drafts") or {})
    for key, value in drafts.items():
        if str(key).startswith("sim_") and key not in st.session_state:
            st.session_state[key] = value
    if not st.session_state.get("selected_mechanic") and drafts.get("selected_mechanic"):
        st.session_state["selected_mechanic"] = drafts["selected_mechanic"]

    meta = st.session_state.get("last_scenario_meta")
    if not isinstance(meta, dict) or not meta.get("scope_value"):
        return
    if st.session_state.get("last_scenario_table") is None:
        return

    scope = meta.get("scope") or "Một SKU cụ thể"
    st.session_state["sim_scope"] = scope
    if scope == "Một Danh mục":
        st.session_state["sim_cat"] = meta["scope_value"]
    else:
        st.session_state["sim_sku"] = meta["scope_value"]

    start, end, _days = campaign_window_from_meta(meta)
    st.session_state["sim_period"] = (start, end)

    profile = st.session_state.get("business_profile")
    fallback_budget = float(getattr(profile, "promotion_budget", 0) or 0) if profile is not None else 0.0
    budget = budget_from_meta(meta, fallback=fallback_budget)
    st.session_state["sim_budget"] = float(budget)
    st.session_state["sim_budget_fmt"] = format_int_commas(int(round(budget))) if budget else ""

    if meta.get("max_discount_pct") is not None:
        st.session_state["sim_max_disc"] = float(meta["max_discount_pct"])
    if meta.get("min_margin_pct") is not None:
        st.session_state["sim_min_margin"] = float(meta["min_margin_pct"])

    gift = meta.get("gift_cost_per_unit")
    if gift is not None:
        gift_i = max(0, int(round(float(gift))))
        st.session_state["sim_gift"] = gift_i
        st.session_state["sim_gift_fmt"] = format_int_commas(gift_i) if gift_i else ""

    # selected_mechanic giữ nguyên trong session — không đụng ở đây.

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
        format="DD/MM/YYYY",
    )
    if isinstance(period, (list, tuple)) and len(period) == 2:
        start, end = period[0], period[1]
    else:
        start = period if isinstance(period, date) else date.today()
        end = start + timedelta(days=6)
    promo_days = max(1, min(30, (end - start).days + 1))
    st.caption(f"{start.strftime('%d/%m/%Y')} – {end.strftime('%d/%m/%Y')} · {promo_days} ngày đưa vào mô hình.")

    _ensure_sim_money_widgets(profile)
    st.text_input(
        "Ngân sách tối đa (đ)",
        key="sim_budget_fmt",
        on_change=_sync_sim_budget,
        help="Nhập số nguyên; hệ thống tự thêm dấu phẩy phân tách hàng nghìn.",
    )
    budget = float(st.session_state.get("sim_budget") or 0)
    profile.promotion_budget = budget

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

    st.text_input(
        "Giá trị quà tặng / đơn vị (đ)",
        key="sim_gift_fmt",
        on_change=_sync_sim_gift,
        help="Nhập số nguyên; hệ thống tự thêm dấu phẩy phân tách hàng nghìn.",
    )
    gift_cost = float(st.session_state.get("sim_gift") or 0)
    st.caption(
        f"Ngân sách hồ sơ: {compact_vnd(profile.promotion_budget)}. "
        "Vượt ngân sách được gắn cờ, không tự loại kịch bản."
    )
    return scope, scope_value, promo_days, gift_cost


def _ensure_sim_money_widgets(profile) -> None:
    """Khởi tạo / migrate ô ngân sách & quà tặng sang dạng text có dấu phẩy."""
    if "sim_budget_fmt" not in st.session_state:
        raw = st.session_state.get("sim_budget", profile.promotion_budget)
        try:
            budget = max(0, int(round(float(raw or 0))))
        except (TypeError, ValueError):
            budget = max(0, int(round(float(profile.promotion_budget or 0))))
        st.session_state["sim_budget"] = float(budget)
        st.session_state["sim_budget_fmt"] = format_int_commas(budget) if budget else ""
    if "sim_gift_fmt" not in st.session_state:
        raw = st.session_state.get("sim_gift", 5000)
        try:
            gift = max(0, int(round(float(raw or 0))))
        except (TypeError, ValueError):
            gift = 5000
        st.session_state["sim_gift"] = gift
        st.session_state["sim_gift_fmt"] = format_int_commas(gift) if gift else ""


def _sync_sim_budget() -> None:
    """on_change của ô ngân sách — được phép ghi lại sim_budget_fmt (callback)."""
    raw = st.session_state.get("sim_budget_fmt")
    if not str(raw or "").strip():
        st.session_state["sim_budget"] = 0.0
        st.session_state["sim_budget_fmt"] = ""
        return
    value = parse_int_commas(raw, default=0, minimum=0)
    st.session_state["sim_budget"] = float(value)
    st.session_state["sim_budget_fmt"] = format_int_commas(value) if value else ""


def _sync_sim_gift() -> None:
    """on_change của ô quà tặng — được phép ghi lại sim_gift_fmt (callback)."""
    raw = st.session_state.get("sim_gift_fmt")
    if not str(raw or "").strip():
        st.session_state["sim_gift"] = 0
        st.session_state["sim_gift_fmt"] = ""
        return
    value = parse_int_commas(raw, default=0, minimum=0)
    st.session_state["sim_gift"] = value
    st.session_state["sim_gift_fmt"] = format_int_commas(value) if value else ""


def _pull_sim_money_from_fmt() -> None:
    """Đọc sim_*_fmt → sim_budget / sim_gift sau khi widget đã tạo (không ghi lại *_fmt)."""
    raw_budget = st.session_state.get("sim_budget_fmt")
    if str(raw_budget or "").strip():
        st.session_state["sim_budget"] = float(parse_int_commas(raw_budget, default=0, minimum=0))
    else:
        st.session_state["sim_budget"] = 0.0

    raw_gift = st.session_state.get("sim_gift_fmt")
    if str(raw_gift or "").strip():
        st.session_state["sim_gift"] = parse_int_commas(raw_gift, default=0, minimum=0)
    else:
        st.session_state["sim_gift"] = 0


def _display_views(table: pd.DataFrame, profile, meta) -> list[dict]:
    """UI adapter — không đổi scenario_views / scoring."""
    views = [row for row in scenario_views(table, profile, meta) if row["mechanic"] != "no_promo"]
    feasible = [v for v in views if not v["rejected"]]
    rejected = [v for v in views if v["rejected"]]
    # Ưu tiên kịch bản hợp lệ; vẫn generic theo số lượng backend trả.
    ordered = feasible + rejected
    best_mech = feasible[0]["mechanic"] if feasible else None
    out = []
    for idx, view in enumerate(ordered):
        item = dict(view)
        item["letter"] = LETTER[idx] if idx < len(LETTER) else str(idx + 1)
        item["card_idx"] = idx
        item["recommended"] = bool(best_mech and view["mechanic"] == best_mech and not view["rejected"])
        item["icon"] = MECHANIC_ICON.get(view["mechanic"], "flask")
        item["subtitle"] = MECHANIC_LABELS_VI.get(view["mechanic"], view["label"])
        out.append(item)
    return out


def _apply_sim_pick_from_query(valid_mechanics: set[str]) -> None:
    """Card click dùng ?sim_pick=mechanic — chỉ nhận đúng 1 phương án hợp lệ."""
    raw = st.query_params.get("sim_pick")
    if not raw:
        return
    pick = raw[0] if isinstance(raw, (list, tuple)) else str(raw)
    try:
        del st.query_params["sim_pick"]
    except Exception:
        st.query_params.pop("sim_pick", None)
    if pick in valid_mechanics:
        st.session_state["selected_mechanic"] = pick
        st.session_state["last_recommendation_card"] = None
        st.session_state.pop("last_campaign_plan", None)
        st.session_state.pop("last_execution_plan", None)
    st.rerun()


def _sim_pick_href(mechanic: str) -> str:
    """Giữ các query param hiện có (vd workspace id), chỉ ghi đè sim_pick."""
    from urllib.parse import urlencode

    params: dict[str, str] = {}
    for key in st.query_params:
        val = st.query_params.get(key)
        if val is None or key == "sim_pick":
            continue
        params[key] = val[0] if isinstance(val, (list, tuple)) else str(val)
    params["sim_pick"] = mechanic
    return "?" + urlencode(params)


def _layout_rows(n: int) -> list[int]:
    """Số card mỗi hàng — cân đối theo tổng số phương án."""
    if n <= 0:
        return []
    if n <= 3:
        return [n]
    if n == 4:
        return [2, 2]
    if n == 5:
        return [3, 2]
    if n == 6:
        return [3, 3]
    rows: list[int] = []
    left = n
    while left > 0:
        if left == 4:
            rows.extend([2, 2])
            break
        take = min(3, left)
        rows.append(take)
        left -= take
    return rows


def _scenario_board(views: list[dict]) -> None:
    if not views:
        st.warning("Không có kịch bản khuyến mãi từ hồ sơ / dữ liệu lịch sử. Kiểm tra cơ chế được phép trong Hồ sơ doanh nghiệp.")
        return

    selectable = {v["mechanic"] for v in views if not v["rejected"]}
    _apply_sim_pick_from_query(selectable)

    selected = st.session_state.get("selected_mechanic")
    # Nếu phương án cũ không còn trong kết quả mô phỏng hiện tại → bỏ chọn.
    if selected and selected not in {v["mechanic"] for v in views}:
        st.session_state["selected_mechanic"] = None
        selected = None
    if selected and selected not in selectable:
        st.session_state["selected_mechanic"] = None
        selected = None

    st.caption(
        f"{len(views)} phương án từ mô phỏng (hồ sơ + lịch sử + ngưỡng depth). "
        "Nhấn vào một card để chọn — chỉ phương án đó đi tiếp sang Decide."
    )

    rows = _layout_rows(len(views))
    cursor = 0
    row_cap = max(rows) if rows else 3
    for count in rows:
        chunk = views[cursor : cursor + count]
        cursor += count
        _render_card_row(chunk, selected, row_cap=row_cap)


def _render_card_row(chunk: list[dict], selected, *, row_cap: int) -> None:
    """Hàng card cùng chiều cao cột; hàng lẻ được căn giữa."""
    n = len(chunk)
    if n <= 0:
        return
    if n == row_cap:
        cols = st.columns(n, gap="medium")
        for col, view in zip(cols, chunk):
            with col:
                _one_card(view, selected)
        return
    # Căn giữa: spacer | cards | spacer
    layout = [1] + [2] * n + [1]
    cols = st.columns(layout, gap="medium")
    for i, view in enumerate(chunk):
        with cols[i + 1]:
            _one_card(view, selected)


def _one_card(view: dict, selected) -> None:
    is_selected = selected == view["mechanic"]
    conf_html = _confidence_html(view["confidence"])
    risk_html = f'<span class="{RISK_KIND.get(view["risk"], "muted")}">{esc(view["risk"])}</span>'
    rev = signed_pct(view["revenue_lift"]) if view["revenue_lift"] is not None else DASH
    profit = signed_pct(view["profit_lift"]) if view["profit_lift"] is not None else DASH
    roi = roi_label(view["roi"]) if view["roi"] is not None else DASH
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
    href = None if view["rejected"] else _sim_pick_href(view["mechanic"])
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
            href=href,
        )
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
    """Biểu đồ doanh thu/lợi nhuận cho mọi phương án hợp lệ sau mô phỏng."""
    chartable = [v for v in views if not v["rejected"]]
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
        fig = grouped_bars(
            ["Doanh thu tăng", "Lợi nhuận tăng"],
            [(v["label"], [v["revenue_lift"] or 0, v["profit_lift"] or 0]) for v in chartable],
            "So với không khuyến mãi",
            "",
            as_percent=True,
        )
        show_chart(fig)


def _actions(*, ready: bool, views: list[dict], empty_key: bool = False) -> None:
    selected = st.session_state.get("selected_mechanic")
    selected_view = next((v for v in views if v["mechanic"] == selected), None)
    if selected_view and not selected_view["rejected"]:
        show(
            f'<p class="pp-sim-selected-note">Đã chọn: <b>Phương án {esc(selected_view["letter"])} — '
            f'{esc(selected_view["label"])}</b> (duy nhất dùng cho Decide).</p>'
        )
    elif ready and not selected:
        show(
            '<p class="pp-sim-selected-note">Chưa chọn phương án — hãy nhấn vào một card trước khi sang Decide.</p>'
        )

    key = "sim_next_empty" if empty_key else "sim_next"
    label = "Tiếp tục đến Bước 5: Decide →"
    if ready and selected_view and not selected_view["rejected"]:
        continue_button(label, "decide", key=key)
    else:
        st.markdown('<div class="pp-continue-row" aria-hidden="true"></div>', unsafe_allow_html=True)
        st.button(label, type="primary", key=key, width="stretch", disabled=True)
        if ready and selected_view and selected_view["rejected"]:
            st.caption("Phương án đang chọn không khả thi — hãy chọn phương án khác.")
        elif ready and not selected:
            st.caption("Cần chọn đúng một phương án trên board trước khi tiếp tục.")
