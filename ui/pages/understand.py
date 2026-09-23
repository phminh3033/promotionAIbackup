"""Understand: mục tiêu, bối cảnh, khách hàng, giỏ hàng — gọi module src/ sẵn có."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from services.scientific_model_engine import ScientificModelEngine
from src.basket.market_basket import run_market_basket_analysis
from src.context.local_context import BUSINESS_EVENTS, CUSTOMER_CONTEXTS, STORE_CONTEXTS, LocalContext
from src.explainability.explainer import explain_trend
from src.external_signals import competitor, events, google_trends, social_listener, weather
from src.features.engineering import aggregate_daily
from src.optimization.objective import OBJECTIVE_LABELS_VI, OBJECTIVE_PRIORITY_METRICS_VI, OBJECTIVES
from src.recommendation.timing import analyze_best_timing
from ui.components import DASH, EMPTY, badge
from ui.shell import continue_button, render_shell

ENGINE = ScientificModelEngine()


def render() -> None:
    render_shell(
        "Understand the market",
        "Hiểu rõ thị trường, khách hàng và cơ hội tăng trưởng của bạn.",
        stage=1,
    )
    st.markdown(
        '<div class="pp-banner">Cần hoàn thành các phần dưới đây để mô hình dự báo và mô phỏng bám đúng bối cảnh kinh doanh. Thiếu dữ liệu thì module tương ứng được ghi rõ, không bịa kết quả.</div>',
        unsafe_allow_html=True,
    )
    _cards()
    _detail()
    _insight()
    left, right = st.columns([1, 1])
    with right:
        continue_button("Tiếp tục đến bước 2: Forecast", "forecast", key="und_next")


def _status_cards() -> list[dict]:
    caps = st.session_state.get("capabilities")
    report = st.session_state.get("quality_report")
    local_ctx = st.session_state["local_context"]
    seg = st.session_state.get("segmentation_result")
    basket = st.session_state.get("basket_result")
    if caps is None:
        titles = [
            ("data", "Data readiness", "Kiểm tra và chuẩn bị dữ liệu bán hàng."),
            ("goal", "Business goal", "Mục tiêu kinh doanh của chiến dịch."),
            ("local", "Local context", "Bối cảnh địa phương, sự kiện, khách khu vực."),
            ("customer", "Customer insight", "Phân tích RFM và phân cụm khách hàng."),
            ("basket", "Product & Basket insight", "Xếp hạng sản phẩm và luật mua kèm."),
            ("segments", "Main customer segments", "Nhóm khách hàng chính."),
            ("groups", "Potential product groups", "Nhóm sản phẩm có cơ hội mua kèm."),
            ("signals", "Local market signals", "Tín hiệu thị trường bên ngoài."),
        ]
        return [{"id": key, "title": title, "desc": desc, "state": EMPTY, "ok": False} for key, title, desc in titles]
    return [
        {"id": "data", "title": "Data readiness", "desc": "Kiểm tra và chuẩn bị dữ liệu bán hàng.", "state": "Hoàn thành" if report else "Chưa hoàn thành", "ok": bool(report)},
        {"id": "goal", "title": "Business goal", "desc": OBJECTIVE_LABELS_VI[st.session_state["objective"]], "state": "Sẵn sàng", "ok": True},
        {"id": "local", "title": "Local context", "desc": local_ctx.summary_text() if local_ctx.has_any_context() else "Bối cảnh địa phương, sự kiện, khách khu vực.", "state": "Hoàn thành" if local_ctx.has_any_context() else "Chưa hoàn thành", "ok": local_ctx.has_any_context()},
        {"id": "customer", "title": "Customer insight", "desc": "Phân tích RFM và phân cụm khách hàng." if caps.has_customer else "Cần cột mã khách hàng.", "state": "Hoàn thành" if seg else ("Không khả dụng" if not caps.has_customer else "Chưa hoàn thành"), "ok": bool(seg)},
        {"id": "basket", "title": "Product & Basket insight", "desc": "Xếp hạng sản phẩm và luật mua kèm." if caps.has_transaction else "Cần mã giao dịch để phân tích giỏ hàng.", "state": "Hoàn thành" if basket else ("Không khả dụng" if not caps.has_transaction else "Chưa hoàn thành"), "ok": bool(basket)},
        {"id": "segments", "title": "Main customer segments", "desc": seg.message if seg else "Chạy Customer insight để có nhóm khách.", "state": "Hoàn thành" if seg and seg.sufficient_data else "Chưa hoàn thành", "ok": bool(seg and seg.sufficient_data)},
        {"id": "groups", "title": "Potential product groups", "desc": f"{len(basket.rules)} luật kết hợp." if basket is not None and basket.sufficient_data else "Chạy phân tích giỏ hàng để thấy nhóm mua kèm.", "state": "Hoàn thành" if basket is not None and basket.sufficient_data else "Chưa hoàn thành", "ok": bool(basket is not None and basket.sufficient_data)},
        {"id": "signals", "title": "Local market signals", "desc": "Nguồn ngoài (thời tiết, xu hướng, đối thủ) chưa được kết nối.", "state": "Chưa kết nối", "ok": False},
    ]


def _cards() -> None:
    blocks = []
    for card in _status_cards():
        kind = "ok" if card["ok"] else "warn"
        blocks.append(
            f"""
<div class="pp-card">
  <div class="pp-kicker">{card["title"]}</div>
  <p class="pp-muted">{card["desc"]}</p>
  <div style="margin-top:10px">{badge(card["state"], kind)}</div>
</div>
"""
        )
    st.markdown(f'<div class="pp-grid-4">{"".join(blocks)}</div>', unsafe_allow_html=True)
    choice = st.selectbox(
        "Mở chi tiết",
        [card["title"] for card in _status_cards()],
        key="understand_focus_label",
    )
    st.session_state["understand_focus"] = next(card["id"] for card in _status_cards() if card["title"] == choice)


def _detail() -> None:
    focus = st.session_state.get("understand_focus") or "goal"
    st.markdown('<div class="pp-hr"></div>', unsafe_allow_html=True)
    if focus == "goal":
        _goal()
    elif focus == "local":
        _local()
    elif focus == "customer" or focus == "segments":
        _customers()
    elif focus == "basket" or focus == "groups":
        _basket()
    elif focus == "signals":
        _signals()
    else:
        report = st.session_state.get("quality_report")
        if report is None:
            st.markdown(f'<div class="pp-card"><div class="pp-kicker">Data readiness</div><p class="pp-muted">{EMPTY}</p><div class="pp-value">{DASH}</div></div>', unsafe_allow_html=True)
            return
        st.markdown(
            f'<div class="pp-card"><div class="pp-kicker">Data readiness</div><p class="pp-muted">Điểm {report.score}/100 — {report.score_label}. Khoảng thời gian {report.date_min.date() if report.date_min is not None else "—"} → {report.date_max.date() if report.date_max is not None else "—"}.</p></div>',
            unsafe_allow_html=True,
        )


def _goal() -> None:
    st.markdown('<div class="pp-section"><div><h2>Mục tiêu kinh doanh</h2><p>Mục tiêu này được dùng khi chấm điểm kịch bản khuyến mãi.</p></div></div>', unsafe_allow_html=True)
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
    st.markdown('<div class="pp-section"><div><h2>Bối cảnh địa phương</h2><p>Nhập thủ công. Nguồn tự động chưa kết nối nên không có số liệu ngoài.</p></div></div>', unsafe_allow_html=True)
    store_name = st.text_input("Tên cửa hàng / khu vực", value=ctx.store_name, key="lc_store")
    events_sel = st.multiselect("Sự kiện kinh doanh", BUSINESS_EVENTS, default=ctx.business_events, key="lc_events")
    customers = st.multiselect("Khách hàng khu vực", CUSTOMER_CONTEXTS, default=ctx.customer_contexts, key="lc_customers")
    stores = st.multiselect("Tình hình cửa hàng", STORE_CONTEXTS, default=ctx.store_contexts, key="lc_stores")
    note = st.text_area("Ghi chú", value=ctx.free_text, key="lc_note")
    if st.button("Lưu bối cảnh", key="save_local"):
        st.session_state["local_context"] = LocalContext(
            store_name=store_name,
            business_events=events_sel,
            customer_contexts=customers,
            store_contexts=stores,
            free_text=note,
        )
        st.success("Đã lưu bối cảnh cho phiên này.")


def _customers() -> None:
    caps = st.session_state.get("capabilities")
    if caps is None or st.session_state.get("clean_df") is None:
        st.markdown(f'<div class="pp-card"><div class="pp-kicker">Customer insight</div><p class="pp-muted">{EMPTY}</p><div class="pp-value">{DASH}</div></div>', unsafe_allow_html=True)
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
            st.dataframe(seg.cluster_summary, use_container_width=True, hide_index=True)


def _basket() -> None:
    caps = st.session_state.get("capabilities")
    df = st.session_state.get("clean_df")
    if caps is None or df is None:
        st.markdown(f'<div class="pp-card"><div class="pp-kicker">Product &amp; Basket insight</div><p class="pp-muted">{EMPTY}</p><div class="pp-value">{DASH}</div></div>', unsafe_allow_html=True)
        return
    stats = (
        df.groupby("product_id")
        .agg(doanh_thu=("revenue", "sum"), san_luong=("quantity", "sum"))
        .reset_index()
        .sort_values("doanh_thu", ascending=False)
        .head(8)
    )
    st.dataframe(stats, use_container_width=True, hide_index=True)
    if not caps.has_transaction:
        st.warning("Không có mã giao dịch nên không phân tích được giỏ hàng.")
        return
    if st.button("Phân tích giỏ hàng", type="primary", key="run_basket") or st.session_state.get("basket_result"):
        if st.session_state.get("basket_result") is None:
            with st.spinner("Đang tìm luật kết hợp sản phẩm..."):
                st.session_state["basket_result"] = run_market_basket_analysis(df)
        result = st.session_state["basket_result"]
        st.info(result.message)
        if result.sufficient_data:
            st.dataframe(result.rules.head(12), use_container_width=True, hide_index=True)


def _signals() -> None:
    cols = st.columns(5)
    for col, module in zip(cols, [social_listener, weather, competitor, google_trends, events]):
        status = module.get_status()
        with col:
            st.markdown(
                f'<div class="pp-card"><div class="pp-kicker">{status.source_name}</div><p class="pp-muted">{status.message}</p></div>',
                unsafe_allow_html=True,
            )


def _insight() -> None:
    df = st.session_state.get("clean_df")
    if df is None or getattr(df, "empty", True):
        st.markdown(
            f"""
<div class="pp-card" style="margin-top:14px">
  <div class="pp-section"><div><h2>Model Insight</h2><p>Diễn giải từ dữ liệu và mô hình đã chạy.</p></div></div>
  <p class="pp-muted">{EMPTY}</p>
  <div class="pp-grid-2">
    <div><div class="pp-kicker">Yếu tố đang có trong dữ liệu</div><ul class="pp-list"><li>{EMPTY}</li></ul></div>
    <div class="pp-metric-mini"><div class="l">Độ tin cậy dự báo trong phiên</div><div class="v">{DASH}</div></div>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
        return
    text = "Chưa đủ lịch sử để nêu một insight định lượng."
    factors = []
    try:
        cutoff = df["date"].max() - pd.Timedelta(days=30)
        recent = df[df["date"] >= cutoff]["quantity"].sum()
        prior_df = df[(df["date"] < cutoff) & (df["date"] >= cutoff - pd.Timedelta(days=30))]
        if not prior_df.empty and prior_df["quantity"].sum():
            change = (recent - prior_df["quantity"].sum()) / prior_df["quantity"].sum()
            text = explain_trend(float(change))
            factors.append(("Sản lượng 30 ngày gần nhất", abs(float(change))))
    except Exception:
        pass
    timing = None
    try:
        timing = analyze_best_timing(aggregate_daily(df))
        if timing.seasonal_note:
            factors.append(("Mùa vụ trong dữ liệu bán", 0.2))
        factors.append((timing.best_weekdays_reason, 0.15))
    except Exception:
        timing = None
    confidence = "Chưa chạy dự báo"
    cache = st.session_state.get("forecast_cache") or {}
    if cache:
        result = next(iter(cache.values()))
        confidence = f"{result.confidence} · WAPE {result.wape:.0%}" if result.wape == result.wape else result.confidence
        text = result.explanation.replace("**", "")
    factor_html = "".join(f"<li>{name}</li>" for name, _ in factors[:4]) or "<li>Chưa có yếu tố ngoài dữ liệu bán hàng.</li>"
    st.markdown(
        f"""
<div class="pp-card" style="margin-top:14px">
  <div class="pp-section"><div><h2>Model Insight</h2><p>Diễn giải từ dữ liệu và mô hình đã chạy. Không dùng trợ lý hội thoại.</p></div></div>
  <p>{text}</p>
  <div class="pp-grid-2">
    <div><div class="pp-kicker">Yếu tố đang có trong dữ liệu</div><ul class="pp-list">{factor_html}</ul></div>
    <div class="pp-metric-mini"><div class="l">Độ tin cậy dự báo trong phiên</div><div class="v">{confidence}</div></div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
