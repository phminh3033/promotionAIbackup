"""Decide: recommendation card từ build_recommendation_card, không dùng chữ AI nói."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from services.workflow import build_decision, ensure_scores, scenario_views, top_alternatives
from ui.components import (
    DASH,
    EMPTY,
    badge,
    bullets,
    card,
    grid,
    kicker,
    metric_mini,
    metric_mini_html,
    scenario_card,
    section,
    show,
)
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
        if st.button("Chọn phương án này", type="primary", key="dec_accept", width="stretch"):
            build_decision(st.session_state.get("selected_mechanic"))
            goto("execute")


def _empty_decision() -> None:
    show(_decision_card("Phương án đề xuất bởi mô hình", DASH, EMPTY, badge(EMPTY, "muted"), [
        ("Revenue lift", DASH),
        ("Profit impact", DASH),
        ("ROI", DASH),
        ("Confidence", DASH),
        ("Risk", DASH),
        ("Nhu cầu tồn kho", DASH),
    ]))
    show(grid([
        card(kicker("Lý do đề xuất") + f'<p class="pp-muted">{EMPTY}</p>'),
        card(kicker("Đánh đổi cần lưu ý") + f'<p class="pp-muted">{EMPTY}</p>'),
    ], columns=2, style="margin-top:12px"))
    show(section("Các phương án khác"))
    show(grid([
        scenario_card(name, "", [f"Revenue {DASH}", f"Profit {DASH}", f"ROI {DASH}"])
        for name in ("Phương án 2", "Phương án 3", "Không khuyến mãi")
    ]))
    left, right = st.columns([1, 1])
    with left:
        if st.button("Quay lại mô phỏng", key="dec_back_empty"):
            goto("simulate")
    with right:
        st.button("Chọn phương án này", type="primary", key="dec_accept_empty", disabled=True, width="stretch")


def _decision_card(eyebrow, title, subtitle, badge_html, metrics, risk_html: str = "", footer: str = "") -> str:
    from ui.components import esc, muted

    cells = []
    for label, value in metrics:
        if label == "Risk" and risk_html:
            cells.append(metric_mini_html(label, risk_html))
        else:
            cells.append(metric_mini(label, value))
    foot = muted(footer) if footer else ""
    return card(
        kicker(eyebrow)
        + f'<div class="pp-section"><div><h2>{esc(title)}</h2><p>{esc(subtitle)}</p></div>{badge_html}</div>'
        + grid(cells, columns=3)
        + foot
    )


def _hero(card, table: pd.DataFrame) -> None:
    meta = st.session_state.get("last_scenario_meta") or {}
    profile = st.session_state["business_profile"]
    views = {row["mechanic"]: row for row in scenario_views(table, profile, meta)}
    mechanic = st.session_state.get("selected_mechanic")
    view = views.get(mechanic) or next(iter(views.values()))
    conf = f"{card.confidence_pct_range[0]}–{card.confidence_pct_range[1]}%"
    objective = st.session_state.get("decision_objective_label", "")
    show(_decision_card(
        f"Phương án đề xuất bởi mô hình · {objective}" if objective else "Phương án đề xuất bởi mô hình",
        card.promotion_label,
        f"{card.product_focus} · {card.target_segment} · {card.timing_text}",
        badge("Model-based recommendation", "purple"),
        [
            ("Revenue lift", signed_pct(view.get("revenue_lift"))),
            ("Profit impact", signed_pct(view.get("profit_lift"))),
            ("ROI", roi_label(view.get("roi")) if view.get("roi") is not None else "—"),
            ("Confidence", conf),
            ("Risk", None),
            ("Nhu cầu tồn kho", integer(card.recommended_stock)),
        ],
        risk_html=badge(card.risk_label, RISK_KIND.get(card.risk_label, "muted")),
        footer=(
            f"Doanh thu dự kiến {vnd(card.expected_revenue_range[0])} – {vnd(card.expected_revenue_range[1])}. "
            f"Lợi nhuận gộp {vnd(card.expected_gp_range[0])} – {vnd(card.expected_gp_range[1])}."
        ),
    ))


def _lists(card) -> None:
    tradeoffs = list(st.session_state.get("decision_tradeoffs") or card.data_caveats) or ["Không có đánh đổi nổi bật từ các luật hiện tại."]
    left, right = st.columns(2)
    with left:
        show(card(kicker("Lý do đề xuất") + bullets(list(card.why_bullets))))
    with right:
        show(card(kicker("Đánh đổi cần lưu ý") + bullets(tradeoffs)))


def _alternatives(table: pd.DataFrame, card) -> None:
    meta = st.session_state.get("last_scenario_meta") or {}
    profile = st.session_state["business_profile"]
    views = {row["scenario"]: row for row in scenario_views(table, profile, meta)}
    chosen_mechanic = st.session_state.get("selected_mechanic") or ""
    alts = top_alternatives(table, chosen_mechanic)
    show(section("Các phương án khác", "Cùng bảng mô phỏng, xếp theo điểm mục tiêu."))
    if alts.empty:
        st.caption("Không còn phương án khác hợp lệ.")
        return
    cols = st.columns(len(alts))
    for col, (_, row) in zip(cols, alts.iterrows()):
        view = views.get(row["scenario"], {})
        with col:
            show(scenario_card(row["scenario"], "", [
                f"Revenue lift {signed_pct(view.get('revenue_lift'))}",
                f"Profit {vnd(row['loi_nhuan_gop'])}",
                f"ROI {roi_label(row['roi'])}",
            ]))
            if st.button("Chọn phương án này", key=f"alt_{row['mechanic']}"):
                st.session_state["selected_mechanic"] = row["mechanic"]
                st.session_state["last_recommendation_card"] = None
                st.session_state["_decision_for"] = None
                st.rerun()
