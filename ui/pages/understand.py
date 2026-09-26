"""Understand: mục tiêu, bối cảnh, khách hàng, giỏ hàng — gọi module src/ sẵn có."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from services.scientific_model_engine import ScientificModelEngine
from services.workflow import run_basket_analysis
from src.basket.market_basket import explain_rule
from src.business.profile import BusinessProfile, list_profiles, load_profile, save_profile
from src.context.local_context import BUSINESS_EVENTS, CUSTOMER_CONTEXTS, STORE_CONTEXTS, LocalContext
from src.explainability.explainer import explain_trend
from src.external_signals import competitor, events, google_trends, social_listener, weather
from src.features.engineering import aggregate_daily
from src.optimization.objective import OBJECTIVE_LABELS_VI, OBJECTIVE_PRIORITY_METRICS_VI, OBJECTIVES
from src.promotion.mechanics import MECHANIC_LABELS_VI
from src.recommendation.engine import CONFIDENCE_PCT_BY_LABEL
from src.recommendation.timing import analyze_best_timing
from src.segmentation.clustering import SegmentationResult
from src.utils.privacy import mask_dataframe_customer_id
from ui.charts import FONT, INK, show_chart
from ui.components import (
    DASH,
    EMPTY,
    badge,
    card,
    chart_placeholder,
    defs,
    grid,
    info_banner,
    insight_input_card,
    kicker,
    model_insight_panel,
    muted,
    show,
)
from ui.formatters import format_int_commas, integer, parse_int_commas
from ui.pages import data_workspace
from ui.shell import continue_button, render_shell

ENGINE = ScientificModelEngine()

SEGMENT_MEANING_VI = {
    "Khách giá trị cao": (
        "Chi tiêu nhiều, mua thường xuyên, mới mua gần đây — nhóm quan trọng nhất, "
        "nên ưu tiên giữ chân bằng ưu đãi thành viên/quà tặng thay vì giảm giá đại trà."
    ),
    "Khách mua thường xuyên": (
        "Mua lặp lại nhiều nhưng chi tiêu/lần thấp hơn nhóm giá trị cao — phù hợp với "
        "BOGO/Mua nhiều giảm nhiều để tăng giá trị đơn hàng."
    ),
    "Khách có nguy cơ rời bỏ": (
        "Đã lâu không quay lại mua — cần chương trình win-back "
        "(ưu đãi đặc biệt để kéo họ quay lại) trước khi mất hẳn."
    ),
    "Khách mới": (
        "Mới mua gần đây, chưa đủ dữ liệu để đánh giá lòng trung thành — "
        "nên tập trung trải nghiệm lần mua tiếp theo."
    ),
    "Khách ít mua": (
        "Tần suất và giá trị mua thấp — cân nhắc chi phí marketing hợp lý, "
        "không nên đầu tư ưu đãi sâu cho nhóm này."
    ),
}

# Bản đồ RFM: lấy mẫu có tầng khi quá nhiều khách để tránh chồng chấm khó đọc.
CUSTOMER_MAP_POINT_CAP = 900
CUSTOMER_MAP_JITTER = 0.75

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
        "title": "Business Profile & Goal",
        "subtitle": "Hồ sơ doanh nghiệp và Mục tiêu kinh doanh",
        "description": "Thiết lập hồ sơ doanh nghiệp và mục tiêu chiến dịch (doanh thu, lợi nhuận, tồn kho…).",
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
                "action": "Xem chi tiết →",
                "accent_cta": False,
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
        "signals": ("Chưa kết nối", False),
    }
    cards = []
    for key in order:
        state, ok = states[key]
        cards.append(
            {
                "id": key,
                **CARD_META[key],
                "state": state,
                "ok": ok,
                "action": "Xem chi tiết →",
                "accent_cta": False,
            }
        )
    return cards


def _cards() -> None:
    """6 card còn lại → lưới 2 hàng × 3 cột."""
    cards = _status_cards()
    cols_per_row = 3
    for start in range(0, len(cards), cols_per_row):
        columns = st.columns(cols_per_row, gap="medium")
        for column, item in zip(columns, cards[start : start + cols_per_row]):
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
    continue_button("Tiếp tục đến Bước 2: Forecast →", "forecast", key="und_next")


def _open_detail(card_id: str) -> None:
    if card_id == "data":
        data_workspace.open_modal()
    elif card_id == "goal":
        _dlg_goal()
    elif card_id == "local":
        # Đồng bộ widget từ bối cảnh đã lưu trước khi mở modal → tự động điền.
        _sync_local_widgets_from_ctx(st.session_state["local_context"], force=True)
        _dlg_local()
    elif card_id == "customer":
        _dlg_customers()
    elif card_id == "basket":
        _dlg_basket()
    else:
        _dlg_signals()


@st.dialog("Business Profile & Goal", width="large")
def _dlg_goal() -> None:
    _goal()


@st.dialog("Local context", width="large")
def _dlg_local() -> None:
    _local()


def _sync_local_widgets_from_ctx(ctx: LocalContext, *, force: bool = False) -> None:
    """Gán session widget keys từ LocalContext đã lưu (để autofill khi mở lại modal)."""
    values = {
        "lc_store": ctx.store_name or "",
        "lc_events": [item for item in ctx.business_events if item in BUSINESS_EVENTS],
        "lc_customers": [item for item in ctx.customer_contexts if item in CUSTOMER_CONTEXTS],
        "lc_stores": [item for item in ctx.store_contexts if item in STORE_CONTEXTS],
        "lc_note": ctx.free_text or "",
    }
    for key, value in values.items():
        if force or key not in st.session_state:
            st.session_state[key] = value


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
    """Hồ sơ + mục tiêu — widget có key để left menu sync vào session khi chuyển trang."""
    st.caption("Hồ sơ doanh nghiệp và Mục tiêu kinh doanh")
    profile: BusinessProfile = st.session_state["business_profile"]
    current_objective = st.session_state.get("objective", profile.primary_objective)
    if current_objective not in OBJECTIVES:
        current_objective = OBJECTIVES[1]

    if st.session_state.pop("_bp_save_ok", None):
        st.success("Đã lưu hồ sơ doanh nghiệp vào phiên hiện tại.")

    # Áp dụng thay đổi widget keys TRƯỚC khi tạo widget (tránh AlreadyInstantiated).
    pending_obj = st.session_state.pop("_bp_pending_objective", None)
    if pending_obj in OBJECTIVES:
        st.session_state["bp_objective"] = pending_obj
        st.session_state["objective"] = pending_obj
        current_objective = pending_obj
        profile.primary_objective = pending_obj

    pending_load = st.session_state.pop("_bp_pending_load_profile", None)
    if pending_load is not None:
        st.session_state["business_profile"] = pending_load
        st.session_state["objective"] = pending_load.primary_objective
        st.session_state["bp_blank_defaults_v1"] = True
        st.session_state["bp_profile_committed"] = True
        st.session_state.pop("prep_autofilled_from_bp", None)
        _seed_profile_widgets(pending_load, pending_load.primary_objective, force=True)
        _snapshot_bp_form(pending_load, pending_load.primary_objective)
        from src.utils.state import apply_business_profile_to_prepare

        apply_business_profile_to_prepare(pending_load)
        profile = pending_load
        current_objective = pending_load.primary_objective

    # Sau Lưu: ép seed lại từ business_profile đã persist.
    if st.session_state.pop("_bp_pending_after_save", None):
        profile = st.session_state["business_profile"]
        current_objective = st.session_state.get("objective", profile.primary_objective)
        if current_objective not in OBJECTIVES:
            current_objective = OBJECTIVES[1]
        _seed_profile_widgets(profile, current_objective, force=True)
        _snapshot_bp_form(profile, current_objective)
        from src.utils.state import apply_business_profile_to_prepare

        apply_business_profile_to_prepare(profile)
    else:
        _restore_bp_form_snapshot()
        _seed_profile_widgets(profile, current_objective)

    model_options = ["B2C", "B2B", "Cả hai"]

    st.markdown("**Hồ sơ doanh nghiệp**")
    c1, c2 = st.columns(2)
    with c1:
        _required_label("Tên doanh nghiệp")
        st.text_input("Tên doanh nghiệp", key="bp_business_name", label_visibility="collapsed")
        _required_label("Ngành kinh doanh")
        st.text_input("Ngành kinh doanh", key="bp_industry", label_visibility="collapsed")
        _required_label("Mô hình")
        st.selectbox(
            "Mô hình",
            model_options,
            key="bp_model",
            label_visibility="collapsed",
        )
        _required_label("Số cửa hàng/chi nhánh")
        st.number_input(
            "Số cửa hàng/chi nhánh",
            min_value=1,
            step=1,
            key="bp_n_stores",
            label_visibility="collapsed",
        )
        _required_label("Khoảng số lượng SKU (vd: 30-100)")
        st.text_input(
            "Khoảng số lượng SKU (vd: 30-100)",
            key="bp_sku_range",
            label_visibility="collapsed",
        )
        _required_label("Chu kỳ mua hàng phổ biến (ngày)")
        st.number_input(
            "Chu kỳ mua hàng phổ biến (ngày)",
            min_value=1,
            step=1,
            key="bp_cycle_days",
            label_visibility="collapsed",
        )
    with c2:
        _required_label("Biên lợi nhuận mục tiêu (%)")
        st.slider(
            "Biên lợi nhuận mục tiêu (%)",
            0,
            80,
            key="bp_target_margin",
            label_visibility="collapsed",
        )
        _required_label("Margin tối thiểu chấp nhận được (%)")
        st.slider(
            "Margin tối thiểu chấp nhận được (%)",
            0,
            80,
            key="bp_min_margin",
            label_visibility="collapsed",
            on_change=_mark_bp_params_authority,
        )
        _required_label("Mức giảm giá tối đa cho phép (%)")
        st.slider(
            "Mức giảm giá tối đa cho phép (%)",
            0,
            90,
            key="bp_max_discount",
            label_visibility="collapsed",
        )
        _required_label("Safety Stock mong muốn (ngày)")
        st.number_input(
            "Safety Stock mong muốn (ngày)",
            min_value=0,
            key="bp_safety",
            label_visibility="collapsed",
            on_change=_mark_bp_params_authority,
        )
        _required_label("Lead Time nhập hàng (ngày)")
        st.number_input(
            "Lead Time nhập hàng (ngày)",
            min_value=1,
            key="bp_lead",
            label_visibility="collapsed",
            on_change=_mark_bp_params_authority,
        )
        _required_label("Ngân sách Promotion (VNĐ)")
        st.text_input(
            "Ngân sách Promotion (VNĐ)",
            key="bp_budget_fmt",
            on_change=_sync_bp_budget_fmt,
            label_visibility="collapsed",
            help="Nhập số nguyên; hệ thống tự thêm dấu phẩy phân tách hàng nghìn.",
        )
        _required_label("Năng lực phục vụ (khách/nhân viên/giờ)")
        st.text_input(
            "Năng lực phục vụ (khách/nhân viên/giờ)",
            key="bp_capacity_fmt",
            on_change=_sync_bp_capacity_fmt,
            label_visibility="collapsed",
            help="Nhập số nguyên; hệ thống tự thêm dấu phẩy phân tách hàng nghìn.",
        )
        _required_label("ROI tối thiểu chấp nhận được (%)")
        st.slider(
            "ROI tối thiểu chấp nhận được (%)",
            0,
            200,
            key="bp_min_roi",
            label_visibility="collapsed",
        )
        _required_label("Thời gian chạy campaign tối đa (ngày)")
        st.number_input(
            "Thời gian chạy campaign tối đa (ngày)",
            min_value=1,
            step=1,
            key="bp_max_days",
            label_visibility="collapsed",
        )

    _required_label("Cơ chế khuyến mãi doanh nghiệp cho phép sử dụng")
    st.multiselect(
        "Cơ chế khuyến mãi doanh nghiệp cho phép sử dụng",
        options=list(MECHANIC_LABELS_VI.keys()),
        format_func=lambda key: MECHANIC_LABELS_VI[key],
        key="bp_allowed_mechanics",
        label_visibility="collapsed",
    )

    existing_profiles = list_profiles()
    if existing_profiles:
        with st.expander("Tải hồ sơ đã lưu trước đó"):
            chosen_profile = st.selectbox("Chọn hồ sơ", existing_profiles, key="bp_load_select")
            if st.button("Tải hồ sơ này", key="bp_load_btn"):
                loaded = load_profile(chosen_profile)
                if loaded:
                    # Không ghi widget keys tại đây — để lần rerun kế tiếp seed trước instantiate.
                    st.session_state["_bp_pending_load_profile"] = loaded
                    st.rerun()

    st.divider()
    st.markdown("**Mục tiêu kinh doanh**")
    st.caption("Mục tiêu này được dùng khi chấm điểm kịch bản khuyến mãi.")
    _required_label("Mục tiêu")
    objective = st.radio(
        "Mục tiêu",
        OBJECTIVES,
        format_func=lambda item: OBJECTIVE_LABELS_VI[item],
        horizontal=True,
        key="bp_objective",
        label_visibility="collapsed",
    )
    st.caption("Chỉ số ưu tiên: " + ", ".join(OBJECTIVE_PRIORITY_METRICS_VI[objective]))

    suggestion = st.session_state["local_context"].suggested_objective()
    if suggestion:
        suggested, reason = suggestion
        st.info(f"Gợi ý từ bối cảnh địa phương: {OBJECTIVE_LABELS_VI[suggested]}. {reason}")
        if st.button("Áp dụng gợi ý", key="bp_apply_suggested"):
            st.session_state["_bp_pending_objective"] = suggested
            st.rerun()

    can_save = _bp_form_complete()
    if st.button(
        "Lưu hồ sơ doanh nghiệp",
        type="primary",
        key="bp_save",
        disabled=not can_save,
    ):
        from src.utils.state import apply_business_profile_to_prepare, persist_session_inputs

        # Đồng bộ widget → business_profile, ghi JSON, snapshot form bền vững.
        persist_session_inputs()
        new_profile = st.session_state["business_profile"]
        apply_business_profile_to_prepare(new_profile)
        save_profile(
            new_profile,
            name=(new_profile.business_name or "default").strip().replace(" ", "_").lower() or "default",
        )
        obj = new_profile.primary_objective if new_profile.primary_objective in OBJECTIVES else current_objective
        _snapshot_bp_form(new_profile, obj)
        st.session_state["bp_blank_defaults_v1"] = True
        st.session_state["bp_profile_committed"] = True
        st.session_state["bp_defaults_restored_v2"] = True
        st.session_state.pop("prep_autofilled_from_bp", None)
        st.session_state["_bp_pending_after_save"] = True
        st.session_state["_bp_save_ok"] = True
        st.rerun()
    if not can_save:
        st.caption("Vui lòng điền đầy đủ các trường bắt buộc (*) trước khi lưu.")


def _bp_form_complete() -> bool:
    """True khi mọi trường bắt buộc đã có giá trị hợp lệ."""
    name = str(st.session_state.get("bp_business_name") or "").strip()
    industry = str(st.session_state.get("bp_industry") or "").strip()
    model = st.session_state.get("bp_model")
    sku = str(st.session_state.get("bp_sku_range") or "").strip()
    mechanics = st.session_state.get("bp_allowed_mechanics") or []
    objective = st.session_state.get("bp_objective")
    try:
        n_stores = int(st.session_state.get("bp_n_stores") or 0)
        cycle = int(st.session_state.get("bp_cycle_days") or 0)
        max_days = int(st.session_state.get("bp_max_days") or 0)
        budget = int(float(st.session_state.get("bp_budget") or 0))
        capacity = int(float(st.session_state.get("bp_capacity") or 0))
        # Cho phép đọc từ ô format nếu chưa sync.
        if not budget and st.session_state.get("bp_budget_fmt"):
            budget = parse_int_commas(st.session_state["bp_budget_fmt"], default=0, minimum=0)
        if not capacity and st.session_state.get("bp_capacity_fmt"):
            capacity = parse_int_commas(st.session_state["bp_capacity_fmt"], default=0, minimum=0)
    except (TypeError, ValueError):
        return False
    return bool(
        name
        and industry
        and model in {"B2C", "B2B", "Cả hai"}
        and n_stores > 0
        and sku
        and cycle > 0
        and max_days > 0
        and budget > 0
        and capacity > 0
        and mechanics
        and objective in OBJECTIVES
        and "bp_target_margin" in st.session_state
        and "bp_min_margin" in st.session_state
        and "bp_max_discount" in st.session_state
        and "bp_min_roi" in st.session_state
        and "bp_safety" in st.session_state
        and "bp_lead" in st.session_state
    )


def _mark_bp_params_authority() -> None:
    """Hồ sơ là nguồn sự thật cho 4 ô Prepare — seed lại ở lần render kế."""
    st.session_state["params_authority"] = "bp"
    st.session_state.pop("prep_autofilled_from_bp", None)


def _sync_bp_budget_fmt() -> None:
    raw = st.session_state.get("bp_budget_fmt")
    if not str(raw or "").strip():
        st.session_state["bp_budget"] = 0
        st.session_state["bp_budget_fmt"] = ""
        _mark_bp_params_authority()
        return
    value = parse_int_commas(raw, default=0, minimum=0)
    st.session_state["bp_budget"] = value
    st.session_state["bp_budget_fmt"] = format_int_commas(value) if value else ""
    _mark_bp_params_authority()


def _sync_bp_capacity_fmt() -> None:
    raw = st.session_state.get("bp_capacity_fmt")
    if not str(raw or "").strip():
        st.session_state["bp_capacity"] = 0
        st.session_state["bp_capacity_fmt"] = ""
        return
    value = parse_int_commas(raw, default=0, minimum=0)
    st.session_state["bp_capacity"] = value
    st.session_state["bp_capacity_fmt"] = format_int_commas(value) if value else ""


def _profile_to_seeds(profile: BusinessProfile, objective: str) -> dict:
    budget = int(profile.promotion_budget)
    capacity = max(0, int(round(float(profile.service_capacity_per_staff_per_hour))))
    model = profile.b2b_or_b2c if profile.b2b_or_b2c in ("B2C", "B2B", "Cả hai") else "B2C"
    return {
        "bp_business_name": profile.business_name or "",
        "bp_industry": profile.industry or "",
        "bp_model": model,
        "bp_n_stores": max(1, int(profile.n_stores or 1)),
        "bp_sku_range": profile.sku_range or "",
        "bp_cycle_days": max(1, int(profile.typical_purchase_cycle_days or 1)),
        "bp_seasonality": bool(profile.has_seasonality),
        "bp_target_margin": int(profile.target_margin_pct * 100),
        "bp_min_margin": int(profile.min_margin_pct * 100),
        "bp_max_discount": int(profile.max_discount_pct * 100),
        "bp_safety": int(profile.safety_stock_days),
        "bp_lead": max(1, int(profile.lead_time_days or 1)),
        "bp_budget": budget,
        "bp_budget_fmt": format_int_commas(budget) if budget else "",
        "bp_capacity": capacity,
        "bp_capacity_fmt": format_int_commas(capacity) if capacity else "",
        "bp_min_roi": int(profile.min_roi_pct * 100),
        "bp_max_days": max(1, int(profile.max_campaign_duration_days or 1)),
        "bp_mask_cid": bool(profile.mask_customer_id),
        "bp_allowed_mechanics": [m for m in profile.allowed_mechanics if m in MECHANIC_LABELS_VI],
        "bp_objective": objective if objective in OBJECTIVES else OBJECTIVES[1],
    }


def _snapshot_bp_form(profile: BusinessProfile, objective: str) -> None:
    """Bản sao form bền vững — dialog đóng sẽ xóa widget keys bp_*."""
    st.session_state["bp_form_snapshot"] = _profile_to_seeds(profile, objective)


def _restore_bp_form_snapshot() -> None:
    """Khôi phục widget keys từ snapshot khi mở lại modal / quay lại trang."""
    snap = st.session_state.get("bp_form_snapshot")
    if not isinstance(snap, dict):
        return
    for key, value in snap.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _seed_profile_widgets(profile: BusinessProfile, objective: str, *, force: bool = False) -> None:
    """Khởi tạo widget keys từ BusinessProfile (giá trị demo/đã lưu)."""
    # Luôn clamp trước — session cũ có bp_lead=0 sẽ crash number_input(min_value=1).
    if "bp_lead" in st.session_state:
        try:
            if int(st.session_state["bp_lead"]) < 1:
                st.session_state["bp_lead"] = 1
        except (TypeError, ValueError):
            st.session_state["bp_lead"] = 1
    for key, minimum in (("bp_n_stores", 1), ("bp_cycle_days", 1), ("bp_max_days", 1)):
        if key in st.session_state:
            try:
                if int(st.session_state[key]) < minimum:
                    st.session_state[key] = minimum
            except (TypeError, ValueError):
                st.session_state[key] = minimum
    if "bp_model" in st.session_state and st.session_state["bp_model"] not in ("B2C", "B2B", "Cả hai"):
        st.session_state["bp_model"] = "B2C"

    if force:
        seeds = _profile_to_seeds(profile, objective)
        for key, value in seeds.items():
            st.session_state[key] = value
        _snapshot_bp_form(profile, objective)
        return

    # Ưu tiên snapshot đã lưu / hồ sơ đã commit khi thiếu widget key.
    _restore_bp_form_snapshot()
    if st.session_state.get("bp_profile_committed"):
        for key, value in _profile_to_seeds(profile, objective).items():
            if key not in st.session_state:
                st.session_state[key] = value
        return

    # Lần đầu phiên: seed từ profile hiện tại (demo/yaml).
    if not st.session_state.get("bp_defaults_restored_v2"):
        for key, value in _profile_to_seeds(profile, objective).items():
            st.session_state[key] = value
        st.session_state["bp_defaults_restored_v2"] = True
        return

    seeds = _profile_to_seeds(profile, objective)
    for key, value in seeds.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _required_label(text: str) -> None:
    """Nhãn trường bắt buộc kèm dấu * đỏ."""
    st.markdown(
        f'{text} <span style="color:#DC2626;font-weight:700">*</span>',
        unsafe_allow_html=True,
    )


def _local() -> None:
    ctx = st.session_state["local_context"]
    # Đảm bảo widget keys tồn tại (tránh value=/default= xung đột với key=).
    _sync_local_widgets_from_ctx(ctx, force=False)

    st.caption("Nhập thủ công. Nguồn tự động chưa kết nối nên không có số liệu ngoài.")
    _required_label("Tên cửa hàng / khu vực")
    store_name = st.text_input(
        "Tên cửa hàng / khu vực",
        key="lc_store",
        label_visibility="collapsed",
    )
    _required_label("Sự kiện kinh doanh")
    events_sel = st.multiselect(
        "Sự kiện kinh doanh",
        BUSINESS_EVENTS,
        key="lc_events",
        label_visibility="collapsed",
    )
    _required_label("Khách hàng khu vực")
    customers = st.multiselect(
        "Khách hàng khu vực",
        CUSTOMER_CONTEXTS,
        key="lc_customers",
        label_visibility="collapsed",
    )
    _required_label("Tình hình cửa hàng")
    stores = st.multiselect(
        "Tình hình cửa hàng",
        STORE_CONTEXTS,
        key="lc_stores",
        label_visibility="collapsed",
    )
    note = st.text_area("Ghi chú", key="lc_note")

    can_save = bool(
        str(store_name or "").strip()
        and events_sel
        and customers
        and stores
    )
    if st.button("Lưu bối cảnh", type="primary", key="save_local", disabled=not can_save):
        new_ctx = LocalContext(
            store_name=str(store_name or "").strip(),
            business_events=list(events_sel or []),
            customer_contexts=list(customers or []),
            store_contexts=list(stores or []),
            free_text=str(note or ""),
        )
        # Lưu vào phiên — các bước sau đọc st.session_state["local_context"].
        st.session_state["local_context"] = new_ctx
        st.session_state["business_events"] = list(new_ctx.business_events)
        st.success("Đã lưu bối cảnh địa phương vào phiên hiện tại.")
        st.rerun()


def _customers() -> None:
    caps = st.session_state.get("capabilities")
    df = st.session_state.get("clean_df")
    if caps is None or df is None:
        st.caption("Cần tải và chuẩn hoá dữ liệu bán hàng trước khi phân tích khách hàng.")
        _customer_segment_placeholders()
        return
    if not caps.has_customer:
        st.warning("Dữ liệu không có mã khách hàng nên không chạy RFM.")
        _customer_segment_placeholders()
        return

    run_clicked = st.button("Phân tích RFM và phân cụm", type="primary", key="run_rfm")
    if run_clicked or st.session_state.get("segmentation_result") is not None:
        if st.session_state.get("rfm_result") is None or run_clicked:
            with st.spinner("Đang phân cụm khách hàng..."):
                rfm, seg = ENGINE.segment_customers(df)
            st.session_state["rfm_result"] = rfm
            st.session_state["segmentation_result"] = seg

    seg = st.session_state.get("segmentation_result")
    if seg is None:
        _customer_segment_placeholders()
        return

    st.info(seg.message)
    if not seg.sufficient_data or seg.cluster_summary.empty:
        _customer_segment_placeholders()
        return

    _render_customer_segments(seg)


def _customer_segment_placeholders() -> None:
    with st.container(border=True):
        show(kicker("Tổng quan các nhóm khách hàng"))
        show(muted(EMPTY))
    col1, col2 = st.columns(2, gap="medium")
    with col1, st.container(border=True):
        show(kicker("Tỷ trọng số lượng khách hàng theo nhóm") + chart_placeholder(EMPTY))
    with col2, st.container(border=True):
        show(kicker("Doanh thu trung bình/khách theo nhóm") + chart_placeholder(EMPTY))
    with st.container(border=True):
        show(kicker("Bản đồ khách hàng") + chart_placeholder(EMPTY))
    with st.container(border=True):
        show(kicker("Ý nghĩa từng nhóm khách hàng"))
        show(muted(EMPTY))
    with st.expander("Xem dữ liệu RFM chi tiết theo từng khách hàng"):
        show(muted(EMPTY))


def _segment_summary_table(seg: SegmentationResult) -> pd.DataFrame:
    summary = seg.cluster_summary.copy()
    total = float(summary["n_customers"].sum()) or 1.0
    summary["% khách hàng"] = (summary["n_customers"] / total * 100).round(1)
    display = summary.rename(
        columns={
            "segment": "Nhóm khách hàng",
            "recency_mean": "Recency TB (ngày)",
            "frequency_mean": "Frequency TB (lần)",
            "monetary_mean": "Monetary TB (VNĐ)",
            "n_customers": "Số khách hàng",
        }
    )[
        [
            "Nhóm khách hàng",
            "Số khách hàng",
            "% khách hàng",
            "Recency TB (ngày)",
            "Frequency TB (lần)",
            "Monetary TB (VNĐ)",
        ]
    ].copy()
    display["Recency TB (ngày)"] = display["Recency TB (ngày)"].round(0)
    display["Frequency TB (lần)"] = display["Frequency TB (lần)"].round(1)
    display["Số khách hàng"] = display["Số khách hàng"].map(integer)
    display["Monetary TB (VNĐ)"] = display["Monetary TB (VNĐ)"].map(integer)
    return display


def _rfm_detail_table(seg: SegmentationResult) -> pd.DataFrame:
    """Bảng RFM theo từng khách — chỉ bản hiển thị; có thể mask mã KH theo hồ sơ."""
    detail = seg.rfm_labeled.copy()
    if detail.empty:
        return detail
    profile = st.session_state.get("business_profile")
    mask_on = bool(getattr(profile, "mask_customer_id", False)) if profile is not None else False
    detail = mask_dataframe_customer_id(detail, enabled=mask_on)
    rename = {
        "customer_id": "Mã khách hàng",
        "recency": "Recency (ngày)",
        "frequency": "Frequency (lần)",
        "monetary": "Monetary (VNĐ)",
        "first_purchase": "Lần mua đầu",
        "last_purchase": "Lần mua cuối",
        "cluster": "Cụm",
        "segment": "Nhóm khách hàng",
    }
    cols = [c for c in rename if c in detail.columns]
    display = detail[cols].rename(columns=rename)
    if "Recency (ngày)" in display.columns:
        display["Recency (ngày)"] = display["Recency (ngày)"].round(0)
    if "Frequency (lần)" in display.columns:
        display["Frequency (lần)"] = display["Frequency (lần)"].round(1)
    if "Monetary (VNĐ)" in display.columns:
        display["Monetary (VNĐ)"] = display["Monetary (VNĐ)"].map(integer)
    return display


def _chart_hoverlabel() -> dict:
    """Tooltip hover Plotly — align chỉ nhận left/right/auto (không có center)."""
    return dict(
        bordercolor="rgba(255,255,255,0.45)",
        font=dict(size=13, family=FONT),
        align="auto",
        namelength=-1,
    )


def _contrast_ink(color) -> str:
    """Chữ trắng/đen tương phản với nền marker."""
    if color is None:
        return INK
    text = str(color).strip()
    if not text or text.lower() in {"none", "null"}:
        return INK
    if text.startswith("rgba"):
        try:
            inner = text[text.find("(") + 1 : text.find(")")].split(",")
            r, g, b = (int(float(inner[0])), int(float(inner[1])), int(float(inner[2])))
        except (ValueError, IndexError):
            return "#FFFFFF"
    elif text.startswith("rgb"):
        try:
            inner = text[text.find("(") + 1 : text.find(")")].split(",")
            r, g, b = (int(float(inner[0])), int(float(inner[1])), int(float(inner[2])))
        except (ValueError, IndexError):
            return "#FFFFFF"
    elif text.startswith("#"):
        hex_color = text[1:]
        if len(hex_color) == 3:
            hex_color = "".join(ch * 2 for ch in hex_color)
        if len(hex_color) < 6:
            return "#FFFFFF"
        try:
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        except ValueError:
            return "#FFFFFF"
    else:
        return "#FFFFFF"
    # Relative luminance — ngưỡng ~0.55 để chữ luôn dễ đọc trên màu chart.
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#0F172A" if luminance > 0.55 else "#FFFFFF"


def _trace_marker_colors(trace) -> str | list | None:
    marker = getattr(trace, "marker", None)
    if marker is None:
        return None
    colors = getattr(marker, "colors", None)
    if colors is not None:
        return list(colors)
    color = getattr(marker, "color", None)
    if color is None:
        return None
    if isinstance(color, (list, tuple)):
        return list(color)
    return str(color)


def _apply_colored_hoverlabels(fig: go.Figure) -> None:
    """Nền tooltip = màu giá trị trên chart; chữ tương phản (merge dict để override bordercolor)."""
    base = _chart_hoverlabel()
    colorway = list(fig.layout.colorway) if fig.layout.colorway else [
        "#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A", "#19D3F3", "#FF6692", "#B6E880",
    ]
    for index, trace in enumerate(fig.data):
        colors = _trace_marker_colors(trace)
        # Pie: một trace nhiều sector — phải gán màu từng lát, không dùng 1 màu cho cả trace.
        n_points = 0
        if getattr(trace, "type", None) == "pie":
            labels = getattr(trace, "labels", None)
            values = getattr(trace, "values", None)
            if labels is not None:
                n_points = len(labels)
            elif values is not None:
                n_points = len(values)
        if n_points > 0 and (colors is None or isinstance(colors, str)):
            colors = [colorway[i % len(colorway)] for i in range(n_points)]
            trace.update(marker=dict(colors=colors))
        elif colors is None:
            colors = colorway[index % len(colorway)]
        if isinstance(colors, list):
            fonts = [_contrast_ink(c) for c in colors]
            trace.update(
                hoverlabel={
                    **base,
                    "bgcolor": colors,
                    "font": dict(size=13, color=fonts, family=FONT),
                }
            )
        else:
            ink = _contrast_ink(colors)
            trace.update(
                hoverlabel={
                    **base,
                    "bgcolor": colors,
                    "bordercolor": (
                        "rgba(255,255,255,0.45)" if ink == "#FFFFFF" else "rgba(15,23,42,0.2)"
                    ),
                    "font": dict(size=13, color=ink, family=FONT),
                }
            )


def _apply_segment_chart_frame(fig, *, height: int, bottom: int = 56, left: int = 56, right: int = 24, top: int = 20) -> None:
    """Margin/padding đủ để không cắt title/axis/legend trong modal hẹp."""
    fig.update_layout(
        title=None,
        height=height,
        margin=dict(l=left, r=right, t=top, b=bottom, pad=4),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="white",
        font=dict(size=12),
        autosize=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            x=0,
            xanchor="left",
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0,
            font=dict(size=11),
        ),
    )
    fig.update_xaxes(automargin=True, title_standoff=10, tickfont=dict(size=11))
    fig.update_yaxes(automargin=True, title_standoff=10, tickfont=dict(size=11))
    fig.update_layout(hovermode="closest", hoverlabel=_chart_hoverlabel())
    _apply_colored_hoverlabels(fig)


def _sample_customer_map_points(labeled: pd.DataFrame, cap: int = CUSTOMER_MAP_POINT_CAP) -> tuple[pd.DataFrame, bool]:
    """Lấy mẫu cân bằng theo nhóm — giữ phân bố segment, giảm chồng chấm."""
    n = len(labeled)
    if n <= cap:
        return labeled.copy(), False
    parts: list[pd.DataFrame] = []
    groups = list(labeled.groupby("segment", sort=False))
    per = max(80, cap // max(len(groups), 1))
    for _name, group in groups:
        if len(group) <= per:
            parts.append(group)
        else:
            parts.append(group.sample(n=per, random_state=42))
    sampled = pd.concat(parts, ignore_index=True)
    if len(sampled) > cap:
        sampled = sampled.sample(n=cap, random_state=42).reset_index(drop=True)
    return sampled, True


def _build_customer_map_figure(labeled: pd.DataFrame) -> tuple[go.Figure, str]:
    """Scatter thưa + viền + tâm nhóm — dễ đọc hơn khi n lớn."""
    plot_df, sampled = _sample_customer_map_points(labeled)
    rng = np.random.default_rng(42)
    # Jitter nhỏ trên Recency để tách các điểm trùng toạ độ (không đổi số liệu gốc trong session).
    plot_df = plot_df.copy()
    plot_df["recency_plot"] = (
        plot_df["recency"].astype(float) + rng.uniform(-CUSTOMER_MAP_JITTER, CUSTOMER_MAP_JITTER, len(plot_df))
    ).clip(lower=0)
    plot_df["recency_i"] = plot_df["recency"].astype(float).round(0).astype(int)
    plot_df["freq_i"] = plot_df["frequency"].astype(float).round(0).astype(int)
    plot_df["monetary_m"] = (plot_df["monetary"].astype(float) / 1_000_000).round(2)
    if "customer_id" not in plot_df.columns:
        plot_df["customer_id"] = "—"

    fig = px.scatter(
        plot_df,
        x="recency_plot",
        y="monetary",
        size="frequency",
        color="segment",
        size_max=14,
        opacity=0.62,
        labels={
            "recency_plot": "Recency (ngày từ lần mua cuối)",
            "monetary": "Monetary (Tổng chi tiêu)",
            "segment": "Nhóm",
            "frequency": "Frequency",
        },
        custom_data=["segment", "customer_id", "recency_i", "freq_i", "monetary_m"],
    )
    fig.update_traces(
        marker=dict(
            line=dict(width=0.9, color="rgba(255,255,255,0.95)"),
            opacity=0.62,
        ),
        hovertemplate=(
            "Nhóm %{customdata[0]}<br>"
            "Mã khách hàng = %{customdata[1]}<br>"
            "Recency = %{customdata[2]} ngày<br>"
            "Frequency = %{customdata[3]} lần<br>"
            "Monetary = %{customdata[4]:.2f} M"
            "<extra></extra>"
        ),
        selector=dict(mode="markers"),
    )

    # Tâm từng nhóm (tính trên toàn bộ dữ liệu, không chỉ mẫu) — điểm mốc dễ nhận biết.
    centroids = (
        labeled.groupby("segment", as_index=False)
        .agg(recency=("recency", "mean"), monetary=("monetary", "mean"), n=("segment", "size"))
        .sort_values("monetary", ascending=False)
    )
    fig.add_trace(
        go.Scatter(
            x=centroids["recency"],
            y=centroids["monetary"],
            mode="markers+text",
            name="Tâm nhóm",
            text=["★"] * len(centroids),
            textposition="top center",
            textfont=dict(size=11, color="#0F172A"),
            marker=dict(
                symbol="diamond",
                size=14,
                color="rgba(15,23,42,0.08)",
                line=dict(width=2, color="#0F172A"),
            ),
            customdata=np.stack([centroids["segment"], centroids["n"]], axis=-1),
            hovertemplate=(
                "<b>Tâm nhóm</b><br>%{customdata[0]}<br>"
                "Recency TB: %{x:.0f} ngày<br>"
                "Monetary TB: %{y:,.0f} đ<br>"
                "Số khách: %{customdata[1]:,}<extra></extra>"
            ),
            showlegend=True,
        )
    )

    _apply_segment_chart_frame(fig, height=460, bottom=72, left=72, right=24, top=56)
    fig.update_xaxes(title=dict(text="Recency (ngày từ lần mua cuối)", font=dict(size=11)))
    fig.update_yaxes(
        tickformat="~s",
        title=dict(text="Monetary (Tổng chi tiêu)", font=dict(size=11)),
    )
    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            x=0,
            xanchor="left",
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=11),
        )
    )

    total = len(labeled)
    shown = len(plot_df)
    if sampled:
        note = (
            f"Hiển thị mẫu {shown:,}/{total:,} khách (cân bằng theo nhóm) kèm viền trắng để tách chấm. "
            "Hình thoi đậm = tâm nhóm trên toàn bộ dữ liệu. Kích thước chấm ∝ Frequency."
        )
    else:
        note = (
            "Mỗi chấm là một khách (có viền trắng). Hình thoi đậm = tâm nhóm. "
            "Kích thước chấm ∝ Frequency."
        )
    return fig, note


def _render_customer_segments(seg: SegmentationResult) -> None:
    summary = seg.cluster_summary.copy()

    with st.container(border=True):
        show(kicker("Tổng quan các nhóm khách hàng"))
        st.dataframe(_segment_summary_table(seg), width="stretch", hide_index=True)

    col1, col2 = st.columns(2, gap="medium")
    with col1, st.container(border=True):
        show(kicker("Tỷ trọng số lượng khách hàng theo nhóm"))
        pie_df = summary.copy()
        pie_df["n_label"] = pie_df["n_customers"].map(integer)
        fig_pie = px.pie(
            pie_df,
            names="segment",
            values="n_customers",
            custom_data=["n_label"],
        )
        fig_pie.update_traces(
            textposition="inside",
            textinfo="percent",
            hole=0.38,
            textfont=dict(size=12),
            hovertemplate="%{label}; %{customdata[0]}<extra></extra>",
        )
        _apply_segment_chart_frame(fig_pie, height=360, bottom=72, left=16, right=16, top=36)
        fig_pie.update_layout(
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.08,
                x=0.5,
                xanchor="center",
                bgcolor="rgba(0,0,0,0)",
                font=dict(size=11),
            ),
            uniformtext_minsize=10,
            uniformtext_mode="hide",
        )
        show_chart(fig_pie)

    with col2, st.container(border=True):
        show(kicker("Doanh thu trung bình/khách theo nhóm"))
        bar_df = summary.sort_values("monetary_mean", ascending=False).copy()
        bar_df["monetary_label"] = bar_df["monetary_mean"].map(integer)
        fig_bar = px.bar(
            bar_df,
            x="segment",
            y="monetary_mean",
            custom_data=["monetary_label"],
            labels={"segment": "", "monetary_mean": "Doanh thu TB (VNĐ)"},
        )
        fig_bar.update_traces(
            marker_line_width=0,
            width=0.55,
            hovertemplate="%{x}; %{customdata[0]}<extra></extra>",
        )
        _apply_segment_chart_frame(fig_bar, height=360, bottom=96, left=72, right=16, top=16)
        fig_bar.update_xaxes(tickangle=-28, tickfont=dict(size=10), title="")
        fig_bar.update_yaxes(tickformat="~s", title=dict(text="Doanh thu TB (VNĐ)", font=dict(size=11)))
        fig_bar.update_layout(showlegend=False, bargap=0.35)
        show_chart(fig_bar)

    with st.container(border=True):
        show(kicker("Bản đồ khách hàng: Recency vs Monetary"))
        labeled = seg.rfm_labeled
        if labeled.empty or not {"recency", "monetary", "frequency", "segment"}.issubset(labeled.columns):
            show(chart_placeholder(EMPTY))
        else:
            fig_map, map_note = _build_customer_map_figure(labeled)
            show_chart(fig_map)
            st.caption(map_note)

    with st.container(border=True):
        show(kicker("Ý nghĩa từng nhóm khách hàng"))
        meanings = [
            (name, SEGMENT_MEANING_VI[name])
            for name in summary["segment"].tolist()
            if name in SEGMENT_MEANING_VI
        ]
        if not meanings:
            show(muted(EMPTY))
        else:
            show(defs(meanings))

    with st.expander("Xem dữ liệu RFM chi tiết theo từng khách hàng"):
        detail = _rfm_detail_table(seg)
        if detail.empty:
            show(muted(EMPTY))
        else:
            st.caption(f"{len(detail):,} khách hàng · Recency / Frequency / Monetary / nhóm phân cụm.")
            st.dataframe(detail, width="stretch", hide_index=True)


def _basket() -> None:
    caps = st.session_state.get("capabilities")
    df = st.session_state.get("clean_df")
    if caps is None or df is None:
        st.caption("Cần tải và chuẩn hoá dữ liệu bán hàng trước khi xem sản phẩm & giỏ hàng.")
        _basket_placeholders()
        return

    product_stats = (
        df.groupby("product_id")
        .agg(doanh_thu=("revenue", "sum"), san_luong=("quantity", "sum"))
        .reset_index()
        .sort_values("doanh_thu", ascending=False)
    )
    _render_product_ranking(product_stats, caps, df)

    st.divider()
    st.markdown("**Phân tích giỏ hàng (Market Basket)**")
    if not caps.has_transaction:
        st.warning("Không có mã giao dịch nên không phân tích được giỏ hàng.")
        _basket_rules_placeholders()
        return

    run_clicked = st.button("Phân tích giỏ hàng", type="primary", key="run_basket")
    if run_clicked or st.session_state.get("basket_result") is not None:
        if st.session_state.get("basket_result") is None or run_clicked:
            with st.spinner("Đang tìm luật kết hợp sản phẩm (có thể xếp hàng nếu nhiều người đang tính)..."):
                try:
                    st.session_state["basket_result"] = run_basket_analysis(df)
                except RuntimeError as exc:
                    st.warning(str(exc))
                    _basket_rules_placeholders()
                    return

    result = st.session_state.get("basket_result")
    if result is None:
        _basket_rules_placeholders()
        return

    st.info(result.message)
    if not result.sufficient_data or result.rules is None or result.rules.empty:
        _basket_rules_placeholders()
        return

    _render_basket_rules(result)


def _basket_placeholders() -> None:
    with st.container(border=True):
        show(kicker("Xếp hạng sản phẩm"))
        show(muted(EMPTY))
    col1, col2 = st.columns(2, gap="medium")
    with col1, st.container(border=True):
        show(kicker("Top sản phẩm theo doanh thu") + chart_placeholder(EMPTY))
    with col2, st.container(border=True):
        show(kicker("Tỷ trọng doanh thu theo danh mục") + chart_placeholder(EMPTY))
    _basket_rules_placeholders()


def _basket_rules_placeholders() -> None:
    with st.container(border=True):
        show(kicker("Luật kết hợp sản phẩm"))
        show(muted(EMPTY))
    with st.container(border=True):
        show(kicker("Diễn giải"))
        show(muted(EMPTY))


def _to_ty_vnd(series: pd.Series) -> pd.Series:
    """VNĐ → Tỷ VNĐ, làm tròn 2 chữ số thập phân (chỉ dùng để hiển thị chart)."""
    return (series.astype(float) / 1_000_000_000).round(2)


def _render_product_ranking(product_stats: pd.DataFrame, caps, df: pd.DataFrame) -> None:
    with st.container(border=True):
        show(kicker("Xếp hạng sản phẩm"))
        if product_stats.empty:
            show(muted(EMPTY))
        else:
            display = product_stats.rename(
                columns={
                    "product_id": "Sản phẩm",
                    "doanh_thu": "Doanh thu (VNĐ)",
                    "san_luong": "Sản lượng",
                }
            ).copy()
            display["Doanh thu (VNĐ)"] = display["Doanh thu (VNĐ)"].map(integer)
            display["Sản lượng"] = display["Sản lượng"].map(integer)
            st.dataframe(display.head(30), width="stretch", hide_index=True)
            st.caption(f"{len(product_stats):,} SKU · sắp xếp theo doanh thu giảm dần.")

    top_n = 10
    col1, col2 = st.columns(2, gap="medium")
    with col1, st.container(border=True):
        show(kicker("Top 10 sản phẩm theo doanh thu"))
        if product_stats.empty:
            show(chart_placeholder(EMPTY))
        else:
            top = product_stats.head(top_n).copy()
            top["doanh_thu_ty"] = _to_ty_vnd(top["doanh_thu"])
            fig = px.bar(
                top,
                x="doanh_thu_ty",
                y="product_id",
                orientation="h",
                labels={"doanh_thu_ty": "Tỷ VNĐ", "product_id": "Sản phẩm"},
                text="doanh_thu_ty",
            )
            fig.update_yaxes(categoryorder="total ascending", title="")
            fig.update_xaxes(
                tickformat=".2f",
                title=dict(text="Tỷ VNĐ", font=dict(size=11)),
            )
            # Giá trị hiện trên thanh; không dùng tooltip.
            fig.update_traces(
                marker_line_width=0,
                texttemplate="%{x:.2f}",
                textposition="inside",
                insidetextanchor="middle",
                textfont=dict(size=12, color="#FFFFFF"),
                hoverinfo="none",
                hovertemplate=None,
            )
            _apply_segment_chart_frame(fig, height=380, bottom=48, left=96, right=24, top=16)
            fig.update_layout(showlegend=False, hovermode=False)
            show_chart(fig)

    with col2, st.container(border=True):
        show(kicker("Tỷ trọng doanh thu theo danh mục"))
        if not getattr(caps, "has_category", False) or "category" not in df.columns:
            show(chart_placeholder(EMPTY))
            st.caption("Chưa có cột danh mục trong dữ liệu.")
        else:
            cat_stats = (
                df.groupby("category", dropna=True)["revenue"]
                .sum()
                .reset_index()
                .sort_values("revenue", ascending=False)
            )
            cat_stats = cat_stats[cat_stats["category"].astype(str).str.strip() != ""]
            if cat_stats.empty:
                show(chart_placeholder(EMPTY))
            else:
                cat_stats = cat_stats.copy()
                cat_stats["revenue_ty"] = _to_ty_vnd(cat_stats["revenue"])
                colorway = [
                    "#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A", "#19D3F3", "#FF6692", "#B6E880",
                ]
                slice_colors = [colorway[i % len(colorway)] for i in range(len(cat_stats))]
                fig2 = px.pie(
                    cat_stats,
                    names="category",
                    values="revenue_ty",
                )
                fig2.update_traces(
                    textposition="inside",
                    textinfo="percent",
                    hole=0.38,
                    textfont=dict(size=12),
                    marker=dict(colors=slice_colors),
                    hovertemplate="%{label}; %{value:.2f}<extra></extra>",
                )
                _apply_segment_chart_frame(fig2, height=380, bottom=72, left=16, right=16, top=36)
                fig2.update_layout(
                    legend=dict(
                        orientation="h",
                        yanchor="top",
                        y=-0.08,
                        x=0.5,
                        xanchor="center",
                        bgcolor="rgba(0,0,0,0)",
                        font=dict(size=11),
                    ),
                    uniformtext_minsize=10,
                    uniformtext_mode="hide",
                )
                show_chart(fig2)


def _render_basket_rules(result) -> None:
    rules = result.rules
    with st.container(border=True):
        show(kicker("Luật kết hợp sản phẩm"))
        rules_display = rules.head(12).copy()
        for col in ("support", "confidence"):
            if col in rules_display.columns:
                rules_display[col] = rules_display[col].map(lambda v: f"{v:.1%}")
        if "lift" in rules_display.columns:
            rules_display["lift"] = rules_display["lift"].map(lambda v: f"{v:.2f}")
        rules_display = rules_display.rename(
            columns={
                "antecedent": "Mua sản phẩm",
                "consequent": "Có xu hướng mua thêm",
                "support": "Support",
                "confidence": "Confidence",
                "lift": "Lift",
            }
        )
        st.dataframe(rules_display, width="stretch", hide_index=True)

    with st.container(border=True):
        show(kicker("Diễn giải"))
        top_rules = rules.head(5)
        if top_rules.empty:
            show(muted(EMPTY))
        else:
            bullets = [explain_rule(row) for _, row in top_rules.iterrows()]
            for text in bullets:
                st.markdown(f"- {text}")
            st.caption(
                "Gợi ý: cặp có **lift > 1** và **confidence** cao phù hợp Bundle/Combo — "
                "xem tiếp ở bước Simulate / Decide."
            )


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
