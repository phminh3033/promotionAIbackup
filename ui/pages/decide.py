"""Decide: recommendation card từ build_decision — chỉ đổi lớp trình bày theo template."""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd
import streamlit as st

from services.workflow import build_decision, default_choice, ensure_scores, scenario_views, top_alternatives
from src.promotion.mechanics import MECHANIC_LABELS_VI
from ui.components import (
    DASH,
    EMPTY,
    alternative_option_card,
    recommendation_hero,
    recommendation_metric_card,
    reason_list_panel,
    section,
    show,
    simulation_empty_state,
    tradeoff_list_panel,
)
from ui.formatters import integer, roi_label, signed_pct, vnd
from ui.nav import goto
from ui.shell import render_shell

RISK_KIND = {"Thấp": "ok", "Trung bình": "warn", "Cao": "bad"}

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

# Mô tả ngắn deterministic theo loại cơ chế — không gắn claim định lượng.
MECHANIC_DESC = {
    "bundle": "Combo/bundle khuyến khích mua kèm, tăng giá trị giỏ hàng theo cơ chế đã mô phỏng.",
    "discount_percent": "Giảm giá theo % trên sản phẩm mục tiêu theo độ sâu đã mô phỏng.",
    "discount_fixed": "Giảm giá số tiền cố định trên mỗi đơn vị bán.",
    "member_price": "Giá thành viên áp dụng cho nhóm khách phù hợp hồ sơ phân khúc.",
    "bogo": "Mua 1 tặng 1 — tăng sản lượng, biên đơn vị thấp hơn theo mô phỏng.",
    "buy_x_get_y": "Mua X tặng Y theo tỷ lệ đã cấu hình trong mô phỏng.",
    "gift": "Tặng quà kèm theo đơn vị bán; giá bán giữ nguyên, chi phí quà đã tính.",
    "coupon": "Coupon giảm giá theo điều kiện mô phỏng.",
    "buy_more_save_more": "Mua nhiều giảm nhiều theo bậc đã mô phỏng.",
    "no_promo": "Không áp dụng khuyến mãi — baseline so sánh.",
}


@dataclass
class DecideViewModel:
    mechanic: str = ""
    title: str = DASH
    subtitle: str = EMPTY
    description: str = EMPTY
    icon: str = "flask"
    is_recommended: bool = False
    status_label: str = "Được hệ thống đề xuất"
    status_sub: str = ""

    revenue_lift: str = DASH
    profit_impact: str = DASH
    roi: str = DASH
    confidence: str = DASH
    risk: str = DASH
    inventory: str = DASH
    inventory_sub: str = "Đơn vị sản phẩm"

    reasons: list[str] = field(default_factory=list)
    tradeoffs: list[str] = field(default_factory=list)
    alternatives: list[dict] = field(default_factory=list)
    footer_note: str = ""
    can_accept: bool = False


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

    profile = st.session_state["business_profile"]
    recommended_row = default_choice(table, profile)
    recommended_mechanic = str(recommended_row["mechanic"])
    st.session_state["recommended_mechanic"] = recommended_mechanic

    # User selection vs system recommendation — không ghi đè recommendation.
    selected = st.session_state.get("selected_mechanic") or recommended_mechanic
    if selected:
        st.session_state["selected_mechanic"] = selected

    rec = st.session_state.get("last_recommendation_card")
    if rec is None or st.session_state.get("_decision_for") != selected:
        rec = build_decision(selected)
        st.session_state["_decision_for"] = st.session_state.get("selected_mechanic")
    if rec is None:
        st.error("Không dựng được đề xuất từ bảng kịch bản hiện tại.")
        return

    vm = build_decide_view_model(table, rec, recommended_mechanic)
    _render_view(vm)


def build_decide_view_model(table: pd.DataFrame, rec, recommended_mechanic: str) -> DecideViewModel:
    """UI adapter — chỉ gom output sẵn có từ build_decision / scenario_views / top_alternatives."""
    meta = st.session_state.get("last_scenario_meta") or {}
    profile = st.session_state["business_profile"]
    views = {row["mechanic"]: row for row in scenario_views(table, profile, meta)}
    mechanic = str(st.session_state.get("selected_mechanic") or recommended_mechanic)
    view = views.get(mechanic) or {}
    is_rec = mechanic == recommended_mechanic

    conf_lo, conf_hi = rec.confidence_pct_range
    conf_mid = int(round((conf_lo + conf_hi) / 2))

    reasons = [str(x).strip() for x in (rec.why_bullets or []) if str(x).strip()]
    tradeoffs = _derive_tradeoffs(rec, view, views, recommended_mechanic, mechanic)

    alts = []
    alt_table = top_alternatives(table, mechanic)
    views_by_scenario = {row["scenario"]: row for row in views.values()}
    for _, row in alt_table.iterrows():
        v = views.get(str(row["mechanic"])) or views_by_scenario.get(row["scenario"], {})
        mech = str(row["mechanic"])
        alts.append(
            {
                "mechanic": mech,
                "title": MECHANIC_LABELS_VI.get(mech, row.get("scenario", mech)),
                "description": MECHANIC_DESC.get(mech, "Kịch bản đã mô phỏng trong bước Simulate."),
                "icon": MECHANIC_ICON.get(mech, "flask"),
                "metrics": [
                    ("Revenue lift", signed_pct(v.get("revenue_lift")) if v.get("revenue_lift") is not None else DASH),
                    ("Profit impact", signed_pct(v.get("profit_lift")) if v.get("profit_lift") is not None else DASH),
                    ("ROI", roi_label(v.get("roi")) if v.get("roi") is not None else (roi_label(row["roi"]) if pd.notna(row.get("roi")) else DASH)),
                ],
                "rejected": bool(row.get("bi_tu_choi", False)),
            }
        )

    objective = st.session_state.get("decision_objective_label", "")
    subtitle_parts = [rec.product_focus, rec.target_segment, rec.timing_text]
    subtitle = " · ".join(p for p in subtitle_parts if p)

    return DecideViewModel(
        mechanic=mechanic,
        title=rec.promotion_label,
        subtitle=subtitle,
        description=MECHANIC_DESC.get(mechanic, "Phương án được chọn từ bảng mô phỏng theo điểm mục tiêu và ràng buộc."),
        icon=MECHANIC_ICON.get(mechanic, "flask"),
        is_recommended=is_rec,
        status_label="Được hệ thống đề xuất" if is_rec else "Phương án do bạn chọn",
        status_sub=(f"Mục tiêu: {objective}" if objective and is_rec else ("Có thể chọn lại ở danh sách bên dưới" if not is_rec else "")),
        revenue_lift=signed_pct(view.get("revenue_lift")) if view.get("revenue_lift") is not None else DASH,
        profit_impact=signed_pct(view.get("profit_lift")) if view.get("profit_lift") is not None else DASH,
        roi=roi_label(view.get("roi")) if view.get("roi") is not None else DASH,
        confidence=f"{conf_mid}%",
        risk=rec.risk_label or DASH,
        inventory=integer(rec.recommended_stock),
        inventory_sub="Đơn vị sản phẩm (theo mô phỏng / tồn kho)",
        reasons=reasons,
        tradeoffs=tradeoffs,
        alternatives=alts,
        footer_note=(
            f"Doanh thu dự kiến {vnd(rec.expected_revenue_range[0])} – {vnd(rec.expected_revenue_range[1])}. "
            f"Lợi nhuận gộp {vnd(rec.expected_gp_range[0])} – {vnd(rec.expected_gp_range[1])}."
        ),
        can_accept=not bool(view.get("rejected", False)),
    )


def _derive_tradeoffs(rec, view: dict, views: dict, recommended_mechanic: str, mechanic: str) -> list[str]:
    """Chỉ thêm trade-off khi có cơ sở từ rule/caveat/so sánh số liệu thật."""
    items: list[str] = []
    seen: set[str] = set()

    def add(text: str) -> None:
        t = text.strip()
        if t and t not in seen:
            seen.add(t)
            items.append(t)

    for raw in st.session_state.get("decision_tradeoffs") or []:
        add(str(raw))
    for raw in rec.data_caveats or []:
        add(str(raw))

    # So sánh với các phương án khác (chỉ khi có số liệu).
    others = [v for m, v in views.items() if m != mechanic and not v.get("rejected")]
    if view.get("revenue_lift") is not None and others:
        max_rev = max((o.get("revenue_lift") or float("-inf")) for o in others)
        if max_rev != float("-inf") and view["revenue_lift"] + 1e-9 < max_rev:
            add(
                f"Revenue lift ({signed_pct(view['revenue_lift'])}) thấp hơn phương án khác "
                f"({signed_pct(max_rev)}) trong cùng bảng mô phỏng."
            )
    if view.get("roi") is not None and others:
        max_roi = max((o.get("roi") if o.get("roi") is not None else float("-inf")) for o in others)
        if max_roi != float("-inf") and view["roi"] + 1e-9 < max_roi:
            add(
                f"ROI ({roi_label(view['roi'])}) thấp hơn phương án khác "
                f"({roi_label(max_roi)}) đã mô phỏng."
            )
    if view.get("inventory_gap") is not None and float(view["inventory_gap"]) > 0:
        add(
            f"Nhu cầu hàng vượt tồn hiện có khoảng {integer(view['inventory_gap'])} đơn vị "
            "theo kết quả mô phỏng."
        )
    if mechanic != recommended_mechanic:
        add("Bạn đang xem phương án khác với đề xuất mặc định theo điểm mục tiêu.")

    if not items:
        add("Chưa phát hiện trade-off đáng kể từ các chỉ số và luật hiện có.")
    return items


def _render_view(vm: DecideViewModel) -> None:
    show(
        recommendation_hero(
            title=vm.title,
            subtitle=vm.subtitle,
            description=vm.description,
            icon_name=vm.icon,
            status_label=vm.status_label,
            status_sub=vm.status_sub,
            is_recommended=vm.is_recommended,
        )
    )

    metrics = [
        recommendation_metric_card("Revenue lift", vm.revenue_lift, "chart", "so với không khuyến mãi", "blue"),
        recommendation_metric_card("Profit impact", vm.profit_impact, "dollar", "so với không khuyến mãi", "blue"),
        recommendation_metric_card("ROI", vm.roi, "trend", "so với chi phí khuyến mãi", "orange"),
        recommendation_metric_card("Confidence", vm.confidence, "shield-check", "Độ tin cậy mô hình dự báo", "purple"),
        recommendation_metric_card("Risk", vm.risk, "shield-check", "Mức độ rủi ro", "green" if vm.risk == "Thấp" else ("orange" if vm.risk == "Trung bình" else "pink")),
        recommendation_metric_card("Nhu cầu tồn kho", vm.inventory, "package", vm.inventory_sub, "purple"),
    ]
    show(f'<div class="pp-dec-metrics">{"".join(metrics)}</div>')
    if vm.footer_note:
        st.caption(vm.footer_note)

    left, right = st.columns(2, gap="medium")
    with left:
        show(reason_list_panel("Lý do đề xuất", vm.reasons))
    with right:
        show(tradeoff_list_panel("Đánh đổi cần lưu ý", vm.tradeoffs))

    show(section("Các phương án khác", "So sánh nhanh các phương án dựa trên kết quả mô phỏng và ràng buộc kinh doanh."))
    if not vm.alternatives:
        st.caption("Không còn phương án khác hợp lệ.")
    else:
        cards = [
            alternative_option_card(a["title"], a["description"], a["metrics"], a["icon"])
            for a in vm.alternatives
        ]
        show(f'<div class="pp-dec-alt-grid">{"".join(cards)}</div>')
        cols = st.columns(len(vm.alternatives))
        for col, alt in zip(cols, vm.alternatives):
            with col:
                if alt.get("rejected"):
                    st.caption("Không khả thi")
                    st.button("Xem chi tiết →", key=f"alt_{alt['mechanic']}", width="stretch", disabled=True)
                else:
                    if st.button("Xem chi tiết →", key=f"alt_{alt['mechanic']}", width="stretch"):
                        st.session_state["selected_mechanic"] = alt["mechanic"]
                        st.session_state["last_recommendation_card"] = None
                        st.session_state["_decision_for"] = None
                        st.rerun()

    left, spacer, right = st.columns([1.2, 1.2, 1.4])
    with left:
        if st.button("← Quay lại mô phỏng", type="secondary", key="dec_back", width="stretch"):
            goto("simulate")
    with right:
        if vm.can_accept:
            if st.button("Chọn phương án này →", type="primary", key="dec_accept", width="stretch"):
                build_decision(st.session_state.get("selected_mechanic"))
                goto("execute")
        else:
            st.button("Chọn phương án này →", type="primary", key="dec_accept", width="stretch", disabled=True)
            st.caption("Phương án hiện tại bị ràng buộc loại — hãy chọn phương án khác.")


def _empty_decision() -> None:
    show(
        simulation_empty_state(
            "Chưa có phương án đề xuất",
            "Hãy hoàn tất bước Simulate trước khi đưa ra quyết định.",
            "target",
        )
    )
    empty_metrics = [
        recommendation_metric_card("Revenue lift", DASH, "chart", EMPTY, "blue"),
        recommendation_metric_card("Profit impact", DASH, "dollar", EMPTY, "blue"),
        recommendation_metric_card("ROI", DASH, "trend", EMPTY, "orange"),
        recommendation_metric_card("Confidence", DASH, "shield-check", EMPTY, "purple"),
        recommendation_metric_card("Risk", DASH, "shield-check", EMPTY, "green"),
        recommendation_metric_card("Nhu cầu tồn kho", DASH, "package", EMPTY, "purple"),
    ]
    show(f'<div class="pp-dec-metrics">{"".join(empty_metrics)}</div>')
    left, right = st.columns(2, gap="medium")
    with left:
        show(reason_list_panel("Lý do đề xuất", []))
    with right:
        show(tradeoff_list_panel("Đánh đổi cần lưu ý", []))
    show(section("Các phương án khác", EMPTY))
    left, spacer, right = st.columns([1.2, 1.2, 1.4])
    with left:
        if st.button("← Quay lại mô phỏng", type="secondary", key="dec_back_empty", width="stretch"):
            goto("simulate")
    with right:
        st.button("Chọn phương án này →", type="primary", key="dec_accept_empty", disabled=True, width="stretch")
