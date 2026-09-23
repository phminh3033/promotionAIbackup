"""Decide: recommendation card từ build_recommendation_card, không dùng chữ AI nói."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from services.workflow import build_decision, ensure_scores, scenario_views, top_alternatives
from ui.components import DASH, EMPTY, badge
from ui.formatters import integer, roi_label, signed_pct, vnd
from ui.nav import goto
from ui.shell import render_shell

RISK_KIND = {"Thấp": "ok", "Trung bình": "warn", "Cao": "bad"}


def render() -> None:
    render_shell(
        "Strategy Recommendation",
        "Lựa chọn phương án tối ưu dựa trên kết quả mô phỏng và ràng buộc kinh doanh.",
        stage=5,
    )
    from src.utils.state import has_data

    table = ensure_scores() if has_data() else None
    if table is None or st.session_state.get("last_scenario_baseline") is None:
        _empty_decision()
        return
    card = st.session_state.get("last_recommendation_card")
    if card is None or st.session_state.get("_decision_for") != st.session_state.get("selected_mechanic"):
        card = build_decision(st.session_state.get("selected_mechanic"))
        st.session_state["_decision_for"] = st.session_state.get("selected_mechanic")
    if card is None:
        st.error("Không dựng được đề xuất từ bảng kịch bản hiện tại.")
        return
    _hero(card, table)
    _lists(card)
    _alternatives(table, card)
    left, right = st.columns([1, 1])
    with left:
        if st.button("Quay lại mô phỏng", key="dec_back"):
            goto("simulate")
    with right:
        if st.button("Chọn phương án này", type="primary", key="dec_accept", use_container_width=True):
            build_decision(st.session_state.get("selected_mechanic"))
            goto("execute")


def _empty_decision() -> None:
    st.markdown(
        f"""
<div class="pp-card">
  <div class="pp-kicker">Phương án đề xuất bởi mô hình</div>
  <div class="pp-section"><div><h2>{DASH}</h2><p>{EMPTY}</p></div>{badge(EMPTY, "muted")}</div>
  <div class="pp-grid-3">
    <div class="pp-metric-mini"><div class="l">Revenue lift</div><div class="v">{DASH}</div></div>
    <div class="pp-metric-mini"><div class="l">Profit impact</div><div class="v">{DASH}</div></div>
    <div class="pp-metric-mini"><div class="l">ROI</div><div class="v">{DASH}</div></div>
    <div class="pp-metric-mini"><div class="l">Confidence</div><div class="v">{DASH}</div></div>
    <div class="pp-metric-mini"><div class="l">Risk</div><div class="v">{DASH}</div></div>
    <div class="pp-metric-mini"><div class="l">Nhu cầu tồn kho</div><div class="v">{DASH}</div></div>
  </div>
</div>
<div class="pp-grid-2" style="margin-top:12px">
  <div class="pp-card"><div class="pp-kicker">Lý do đề xuất</div><p class="pp-muted">{EMPTY}</p></div>
  <div class="pp-card"><div class="pp-kicker">Đánh đổi cần lưu ý</div><p class="pp-muted">{EMPTY}</p></div>
</div>
<div class="pp-section"><div><h2>Các phương án khác</h2></div></div>
<div class="pp-grid-3">
  <div class="pp-card"><div class="pp-kicker">Phương án 2</div><p class="pp-muted">Revenue {DASH}<br>Profit {DASH}<br>ROI {DASH}</p></div>
  <div class="pp-card"><div class="pp-kicker">Phương án 3</div><p class="pp-muted">Revenue {DASH}<br>Profit {DASH}<br>ROI {DASH}</p></div>
  <div class="pp-card"><div class="pp-kicker">Không khuyến mãi</div><p class="pp-muted">Revenue {DASH}<br>Profit {DASH}<br>ROI {DASH}</p></div>
</div>
""",
        unsafe_allow_html=True,
    )
    left, right = st.columns([1, 1])
    with left:
        if st.button("Quay lại mô phỏng", key="dec_back_empty"):
            goto("simulate")
    with right:
        st.button("Chọn phương án này", type="primary", key="dec_accept_empty", disabled=True, use_container_width=True)


def _hero(card, table: pd.DataFrame) -> None:
    meta = st.session_state.get("last_scenario_meta") or {}
    profile = st.session_state["business_profile"]
    views = {row["mechanic"]: row for row in scenario_views(table, profile, meta)}
    mechanic = st.session_state.get("selected_mechanic")
    view = views.get(mechanic) or next(iter(views.values()))
    conf = f"{card.confidence_pct_range[0]}–{card.confidence_pct_range[1]}%"
    st.markdown(
        f"""
<div class="pp-card">
  <div class="pp-kicker">Phương án đề xuất bởi mô hình <span class="en">{st.session_state.get("decision_objective_label", "")}</span></div>
  <div class="pp-section"><div><h2>{card.promotion_label}</h2><p>{card.product_focus} · {card.target_segment} · {card.timing_text}</p></div>{badge("Model-based recommendation", "purple")}</div>
  <div class="pp-grid-3">
    <div class="pp-metric-mini"><div class="l">Revenue lift</div><div class="v">{signed_pct(view.get("revenue_lift"))}</div></div>
    <div class="pp-metric-mini"><div class="l">Profit impact</div><div class="v">{signed_pct(view.get("profit_lift"))}</div></div>
    <div class="pp-metric-mini"><div class="l">ROI</div><div class="v">{roi_label(view.get("roi")) if view.get("roi") is not None else "—"}</div></div>
    <div class="pp-metric-mini"><div class="l">Confidence</div><div class="v">{conf}</div></div>
    <div class="pp-metric-mini"><div class="l">Risk</div><div class="v">{badge(card.risk_label, RISK_KIND.get(card.risk_label, "muted"))}</div></div>
    <div class="pp-metric-mini"><div class="l">Nhu cầu tồn kho</div><div class="v">{integer(card.recommended_stock)}</div></div>
  </div>
  <p class="pp-muted" style="margin-top:10px">Doanh thu dự kiến {vnd(card.expected_revenue_range[0])} – {vnd(card.expected_revenue_range[1])}. Lợi nhuận gộp {vnd(card.expected_gp_range[0])} – {vnd(card.expected_gp_range[1])}.</p>
</div>
""",
        unsafe_allow_html=True,
    )


def _lists(card) -> None:
    reasons = "".join(f"<li>{item}</li>" for item in card.why_bullets)
    tradeoffs = st.session_state.get("decision_tradeoffs") or card.data_caveats
    trade_html = "".join(f"<li>{item}</li>" for item in tradeoffs) or "<li>Không có đánh đổi nổi bật từ các luật hiện tại.</li>"
    left, right = st.columns(2)
    with left:
        st.markdown(f'<div class="pp-card"><div class="pp-kicker">Lý do đề xuất</div><ul class="pp-list">{reasons}</ul></div>', unsafe_allow_html=True)
    with right:
        st.markdown(f'<div class="pp-card"><div class="pp-kicker">Đánh đổi cần lưu ý</div><ul class="pp-list">{trade_html}</ul></div>', unsafe_allow_html=True)


def _alternatives(table: pd.DataFrame, card) -> None:
    meta = st.session_state.get("last_scenario_meta") or {}
    profile = st.session_state["business_profile"]
    views = {row["scenario"]: row for row in scenario_views(table, profile, meta)}
    chosen_mechanic = st.session_state.get("selected_mechanic") or ""
    alts = top_alternatives(table, chosen_mechanic)
    st.markdown('<div class="pp-section"><div><h2>Các phương án khác</h2><p>Cùng bảng mô phỏng, xếp theo điểm mục tiêu.</p></div></div>', unsafe_allow_html=True)
    if alts.empty:
        st.caption("Không còn phương án khác hợp lệ.")
        return
    cols = st.columns(len(alts))
    for col, (_, row) in zip(cols, alts.iterrows()):
        view = views.get(row["scenario"], {})
        with col:
            st.markdown(
                f"""
<div class="pp-card">
  <div class="pp-kicker">{row["scenario"]}</div>
  <div class="pp-muted">Revenue lift {signed_pct(view.get("revenue_lift"))}</div>
  <div class="pp-muted">Profit {vnd(row["loi_nhuan_gop"])}</div>
  <div class="pp-muted">ROI {roi_label(row["roi"])}</div>
</div>
""",
                unsafe_allow_html=True,
            )
            if st.button("Chọn phương án này", key=f"alt_{row['mechanic']}"):
                st.session_state["selected_mechanic"] = row["mechanic"]
                st.session_state["last_recommendation_card"] = None
                st.session_state["_decision_for"] = None
                st.rerun()
