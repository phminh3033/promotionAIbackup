"""Understand: mục tiêu, bối cảnh, khách hàng, giỏ hàng — gọi module src/ sẵn có."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from services.scientific_model_engine import ScientificModelEngine
from services.workflow import run_basket_analysis
from src.context.local_context import BUSINESS_EVENTS, CUSTOMER_CONTEXTS, STORE_CONTEXTS, LocalContext
from src.explainability.explainer import explain_trend
from src.external_signals import competitor, events, google_trends, social_listener, weather
from src.features.engineering import aggregate_daily
from src.optimization.objective import OBJECTIVE_LABELS_VI, OBJECTIVE_PRIORITY_METRICS_VI, OBJECTIVES
from src.recommendation.engine import CONFIDENCE_PCT_BY_LABEL
from src.recommendation.timing import analyze_best_timing
from ui.components import (
    DASH,
    EMPTY,
    badge,
    card,
    grid,
    info_banner,
    insight_input_card,
    kicker,
    model_insight_panel,
    muted,
    show,
)
from ui.pages import data_workspace
from ui.shell import continue_button, render_shell

ENGINE = ScientificModelEngine()

# Subtitle + mô tả cố định theo design system; status vẫn lấy từ session thật.
CARD_META = {
    "data": {
        "title": "Data readiness",
        "subtitle": "Kiểm tra và chuẩn bị dữ liệu",
        "description": "Đảm bảo dữ liệu bán hàng, sản phẩm, khách hàng đã sẵn sàng cho mô hình.",
        "icon": "database",
        "accent": "green",
    },
    "goal": {
        "title": "Business goal",
        "subtitle": "Mục tiêu kinh doanh",
        "description": "Xác định mục tiêu của chiến dịch như tăng doanh thu, thị phần hoặc lợi nhuận.",
        "icon": "target",
        "accent": "purple",
    },
    "local": {
        "title": "Local context",
        "subtitle": "Bối cảnh địa phương",
        "description": "Hiểu đặc thù địa phương như địa bàn, đối thủ, mùa vụ, sự kiện và hành vi mua sắm.",
        "icon": "map-pin",
        "accent": "pink",
    },
    "customer": {
        "title": "Customer insight",
        "subtitle": "Hiểu khách hàng",
        "description": "Phân tích hành vi, nhu cầu và phân khúc khách hàng tại từng khu vực.",
        "icon": "users",
        "accent": "blue",
    },
    "basket": {
        "title": "Product & Basket insight",
        "subtitle": "Hiệu suất sản phẩm",
        "description": "Phân tích hiệu suất sản phẩm, nhóm hàng và cơ hội cross-sell, basket.",
        "icon": "package",
        "accent": "orange",
    },
    "segments": {
        "title": "Main customer segments",
        "subtitle": "Phân khúc khách hàng chính",
        "description": "Xác định các phân khúc khách hàng quan trọng cần tập trung.",
        "icon": "users-round",
        "accent": "purple",
    },
    "groups": {
        "title": "Potential product groups",
        "subtitle": "Nhóm sản phẩm tiềm năng",
        "description": "Tìm ra nhóm sản phẩm có cơ hội tăng trưởng cao.",
        "icon": "boxes",
        "accent": "blue",
    },
    "signals": {
        "title": "Local market signals",
        "subtitle": "Tín hiệu thị trường",
        "description": "Phân tích xu hướng thị trường, đối thủ, sự kiện và các yếu tố tác động tại địa phương.",
        "icon": "activity",
        "accent": "pink",
    },
}


def render() -> None:
    render_shell(
        "Understand the market",
        "Hiểu rõ thị trường, khách hàng và cơ hội tăng trưởng của bạn",
        stage=1,
    )
    show(
        info_banner(
            "Cần 3–5 đầu vào trước khi chạy dự báo",
            "Hãy hoàn thành các phần dưới đây để giúp mô hình hiểu rõ thị trường, khách hàng và mục tiêu của bạn.",
        )
    )
    _cards()
    _insight()
    _bottom_actions()


def _status_cards() -> list[dict]:
    caps = st.session_state.get("capabilities")
    report = st.session_state.get("quality_report")
    local_ctx = st.session_state["local_context"]
    seg = st.session_state.get("segmentation_result")
    basket = st.session_state.get("basket_result")
    order = list(CARD_META.keys())
    if caps is None:
        return [
            {
                "id": key,
                **CARD_META[key],
                "state": EMPTY,
                "ok": False,
                "action": "Phân tích ngay →" if key == "groups" else "Xem chi tiết →",
                "accent_cta": key == "groups",
            }
            for key in order
        ]
    states = {
        "data": ("Hoàn thành" if report else "Chưa hoàn thành", bool(report)),
        "goal": ("Sẵn sàng", True),
        "local": (
            "Hoàn thành" if local_ctx.has_any_context() else "Chưa hoàn thành",
            local_ctx.has_any_context(),
        ),
        "customer": (
            "Hoàn thành"
            if seg
            else ("Không khả dụng" if not caps.has_customer else "Chưa hoàn thành"),
            bool(seg),
        ),
        "basket": (
            "Hoàn thành"
            if basket
            else ("Không khả dụng" if not caps.has_transaction else "Chưa hoàn thành"),
            bool(basket),
        ),
        "segments": (
            "Hoàn thành" if seg and seg.sufficient_data else "Chưa hoàn thành",
            bool(seg and seg.sufficient_data),
        ),
        "groups": (
            "Hoàn thành" if basket is not None and basket.sufficient_data else "Chưa hoàn thành",
            bool(basket is not None and basket.sufficient_data),
        ),
        "signals": ("Chưa kết nối", False),
    }
    cards = []
    for key in order:
        state, ok = states[key]
        action = "Phân tích ngay →" if key == "groups" and not ok else "Xem chi tiết →"
        cards.append(
            {
                "id": key,
                **CARD_META[key],
                "state": state,
                "ok": ok,
                "action": action,
                "accent_cta": key == "groups" and not ok,
            }
        )
    return cards


def _cards() -> None:
    cards = _status_cards()
    for start in range(0, len(cards), 4):
        columns = st.columns(4, gap="medium")
        for column, item in zip(columns, cards[start : start + 4]):
            with column, st.container(border=True):
                show(
                    insight_input_card(
                        title=item["title"],
                        subtitle=item["subtitle"],
                        description=item["description"],
                        status=item["state"],
                        accent=item["accent"],
                        icon_name=item["icon"],
                        ok=item["ok"],
                    )
                )
                if st.button(item["action"], type="secondary", key=f"open_{item['id']}", width="stretch"):
                    _open_detail(item["id"])


def _bottom_actions() -> None:
    left, right = st.columns([1, 2], gap="medium")
    with left:
        if st.button("Lưu nháp", type="secondary", key="und_draft", width="stretch"):
            st.session_state["understand_draft_saved"] = True
            st.toast("Đã lưu nháp trong phiên hiện tại.")
    with right:
        continue_button("Tiếp tục đến Bước 2: Forecast →", "forecast", key="und_next")


def _open_detail(card_id: str) -> None:
    if card_id == "data":
        data_workspace.open_modal()
    elif card_id == "goal":
        _dlg_goal()
    elif card_id == "local":
        _dlg_local()
    elif card_id in {"customer", "segments"}:
        _dlg_customers()
    elif card_id in {"basket", "groups"}:
        _dlg_basket()
    else:
        _dlg_signals()


@st.dialog("Business goal", width="large")
def _dlg_goal() -> None:
    _goal()


@st.dialog("Local context", width="large")
def _dlg_local() -> None:
    _local()


@st.dialog("Customer insight", width="large")
def _dlg_customers() -> None:
    _customers()


@st.dialog("Product & Basket insight", width="large")
def _dlg_basket() -> None:
    _basket()


@st.dialog("Local market signals", width="large")
def _dlg_signals() -> None:
    _signals()


def _goal() -> None:
    st.caption("Mục tiêu này được dùng khi chấm điểm kịch bản khuyến mãi.")
    objective = st.radio(
        "Mục tiêu",
        OBJECTIVES,
        index=OBJECTIVES.index(st.session_state["objective"]) if st.session_state["objective"] in OBJECTIVES else 1,
        format_func=lambda item: OBJECTIVE_LABELS_VI[item],
        horizontal=True,
        key="objective_radio",
    )
    st.session_state["objective"] = objective
    st.session_state["business_profile"].primary_objective = objective
    st.caption("Chỉ số ưu tiên: " + ", ".join(OBJECTIVE_PRIORITY_METRICS_VI[objective]))
    suggestion = st.session_state["local_context"].suggested_objective()
    if suggestion:
        suggested, reason = suggestion
        st.info(f"Gợi ý từ bối cảnh địa phương: {OBJECTIVE_LABELS_VI[suggested]}. {reason}")
        if st.button("Áp dụng gợi ý", key="apply_suggested"):
            st.session_state["objective"] = suggested
            st.rerun()


def _local() -> None:
    ctx = st.session_state["local_context"]
    st.caption("Nhập thủ công. Nguồn tự động chưa kết nối nên không có số liệu ngoài.")
    store_name = st.text_input("Tên cửa hàng / khu vực", value=ctx.store_name, key="lc_store")
    events_sel = st.multiselect("Sự kiện kinh doanh", BUSINESS_EVENTS, default=ctx.business_events, key="lc_events")
    customers = st.multiselect("Khách hàng khu vực", CUSTOMER_CONTEXTS, default=ctx.customer_contexts, key="lc_customers")
    stores = st.multiselect("Tình hình cửa hàng", STORE_CONTEXTS, default=ctx.store_contexts, key="lc_stores")
    note = st.text_area("Ghi chú", value=ctx.free_text, key="lc_note")
    if st.button("Lưu bối cảnh", type="primary", key="save_local"):
        st.session_state["local_context"] = LocalContext(
            store_name=store_name,
            business_events=events_sel,
            customer_contexts=customers,
            store_contexts=stores,
            free_text=note,
        )
        st.rerun()


def _customers() -> None:
    caps = st.session_state.get("capabilities")
    if caps is None or st.session_state.get("clean_df") is None:
        show(card(kicker("Customer insight") + muted(EMPTY) + f'<div class="pp-value">{DASH}</div>'))
        return
    if not caps.has_customer:
        st.warning("Dữ liệu không có mã khách hàng nên không chạy RFM.")
        return
    if st.button("Phân tích RFM và phân cụm", type="primary", key="run_rfm") or st.session_state.get("segmentation_result"):
        if st.session_state.get("rfm_result") is None:
            with st.spinner("Đang phân cụm khách hàng..."):
                rfm, seg = ENGINE.segment_customers(st.session_state["clean_df"])
            st.session_state["rfm_result"] = rfm
            st.session_state["segmentation_result"] = seg
        seg = st.session_state["segmentation_result"]
        st.info(seg.message)
        if seg.sufficient_data and not seg.cluster_summary.empty:
            st.dataframe(seg.cluster_summary, width="stretch", hide_index=True)


def _basket() -> None:
    caps = st.session_state.get("capabilities")
    df = st.session_state.get("clean_df")
    if caps is None or df is None:
        show(card(kicker("Product & Basket insight") + muted(EMPTY) + f'<div class="pp-value">{DASH}</div>'))
        return
    stats = (
        df.groupby("product_id")
        .agg(doanh_thu=("revenue", "sum"), san_luong=("quantity", "sum"))
        .reset_index()
        .sort_values("doanh_thu", ascending=False)
        .head(8)
    )
    st.dataframe(stats, width="stretch", hide_index=True)
    if not caps.has_transaction:
        st.warning("Không có mã giao dịch nên không phân tích được giỏ hàng.")
        return
    if st.button("Phân tích giỏ hàng", type="primary", key="run_basket") or st.session_state.get("basket_result"):
        if st.session_state.get("basket_result") is None:
            with st.spinner("Đang tìm luật kết hợp sản phẩm (có thể xếp hàng nếu nhiều người đang tính)..."):
                try:
                    st.session_state["basket_result"] = run_basket_analysis(df)
                except RuntimeError as exc:
                    st.warning(str(exc))
                    return
        result = st.session_state["basket_result"]
        st.info(result.message)
        if result.sufficient_data:
            st.dataframe(result.rules.head(12), width="stretch", hide_index=True)


def _signals() -> None:
    st.caption("Kiến trúc sẵn sàng cho nguồn ngoài. Bản này chưa kết nối nên không hiển thị số liệu giả.")
    blocks = []
    for module in (social_listener, weather, competitor, google_trends, events):
        status = module.get_status()
        blocks.append(card(kicker(status.source_name) + muted(status.message) + badge("Chưa kết nối", "muted")))
    show(grid(blocks, columns=2))


def _insight() -> None:
    df = st.session_state.get("clean_df")
    if df is None or getattr(df, "empty", True):
        show(
            model_insight_panel(
                insight_text=EMPTY,
                factors=[],
                confidence_pct=None,
                confidence_note="Chưa có dữ liệu để ước lượng độ tin cậy.",
            )
        )
        return

    text = "Chưa đủ lịch sử để nêu một insight định lượng."
    factors: list[tuple[str, float]] = []
    months_span = 0
    try:
        span_days = int((df["date"].max() - df["date"].min()).days)
        months_span = max(1, round(span_days / 30))
    except Exception:
        months_span = 0

    try:
        cutoff = df["date"].max() - pd.Timedelta(days=30)
        recent = df[df["date"] >= cutoff]["quantity"].sum()
        prior_df = df[(df["date"] < cutoff) & (df["date"] >= cutoff - pd.Timedelta(days=30))]
        if not prior_df.empty and prior_df["quantity"].sum():
            change = (recent - prior_df["quantity"].sum()) / prior_df["quantity"].sum()
            text = explain_trend(float(change))
            factors.append(("Biến động sản lượng gần đây", abs(float(change))))
    except Exception:
        pass

    try:
        timing = analyze_best_timing(aggregate_daily(df))
        if timing.seasonal_note:
            factors.append(("Mùa vụ trong dữ liệu bán", 0.35))
        if timing.best_weekdays_reason:
            factors.append((timing.best_weekdays_reason, 0.25))
    except Exception:
        pass

    local_ctx = st.session_state.get("local_context")
    if local_ctx is not None and local_ctx.has_any_context():
        factors.append(("Bối cảnh địa phương đã nhập", 0.15))

    confidence_pct = None
    confidence_note = "Chưa chạy dự báo trong phiên này."
    cache = st.session_state.get("forecast_cache") or {}
    if cache:
        result = next(iter(cache.values()))
        text = result.explanation.replace("**", "")
        band = CONFIDENCE_PCT_BY_LABEL.get(result.confidence)
        if band:
            confidence_pct = int(round((band[0] + band[1]) / 2))
        elif result.wape == result.wape:
            confidence_pct = int(max(0, min(99, round(100 * (1 - float(result.wape))))))
        note_bits = [f"Nhãn mô hình: {result.confidence}"]
        if result.wape == result.wape:
            note_bits.append(f"WAPE {result.wape:.0%}")
        if months_span:
            note_bits.append(f"dựa trên khoảng {months_span} tháng dữ liệu")
        confidence_note = " · ".join(note_bits)
    elif months_span:
        confidence_note = f"Đã có khoảng {months_span} tháng dữ liệu. Chạy Forecast để có độ tin cậy mô hình."

    show(
        model_insight_panel(
            insight_text=text,
            factors=factors[:5],
            confidence_pct=confidence_pct,
            confidence_note=confidence_note,
        )
    )
