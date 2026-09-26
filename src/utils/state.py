"""Quản lý session state dùng chung cho toàn bộ ứng dụng Streamlit (tránh lặp code giữa các trang)."""
from __future__ import annotations

import streamlit as st

from src.business.profile import BusinessProfile
from src.context.local_context import LocalContext
from src.promotion.mechanics import MECHANIC_LABELS_VI

# Kết quả mô hình / phân tích — không xoá khi chuyển trang bằng left menu.
SESSION_RESULT_KEYS = (
    "forecast_cache",
    "forecast_history",
    "rfm_result",
    "segmentation_result",
    "basket_result",
    "historical_uplifts",
    "inventory_plan",
    "last_scenario_table",
    "last_scenario_baseline",
    "last_scenario_meta",
    "last_rule_context",
    "last_rule_verdicts",
    "last_recommendation_card",
    "last_campaign_plan",
    "last_execution_plan",
    "selected_mechanic",
    "execute_campaign",
    "execute_tasks",
    "active_campaign_id",
    "campaign_records",
    "campaign_actual_data",
    "prepare_draft",
)


def init_session_state() -> None:
    defaults = {
        "raw_df": None,
        "raw_filename": None,
        "column_mapping": None,
        "mapped_df": None,
        "capabilities": None,
        "clean_df": None,
        "quality_report": None,
        "business_profile": BusinessProfile.with_yaml_defaults(),
        "objective": "REVENUE",
        "business_events": [],
        "local_context": LocalContext(),
        "forecast_cache": {},
        "forecast_history": {},
        "rfm_result": None,
        "segmentation_result": None,
        "basket_result": None,
        "historical_uplifts": None,
        "last_scenario_table": None,
        "last_scenario_baseline": None,
        "last_scenario_meta": None,
        "last_rule_context": None,
        "last_rule_verdicts": None,
        "last_recommendation_card": None,
        "last_campaign_plan": None,
        "last_execution_plan": None,
        "active_campaign_id": None,
        "campaign_records": {},
        "campaign_actual_data": None,
        "demo_access_granted": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    # Nạp snapshot đĩa SAU defaults — ghi đè bằng dữ liệu đã lưu qua lần reload trước.
    # Phải chạy sớm (trước cổng demo) để giữ mã truy cập + toàn bộ kết quả mô hình.
    try:
        from src.utils.session_persistence import hydrate_session_state

        hydrate_session_state()
    except Exception:  # noqa: BLE001 — persistence lỗi không được chặn app
        pass


def persist_session_inputs() -> None:
    """Đồng bộ giá trị widget → đối tượng phiên trước/khi chuyển trang (left menu).

    Giữ nguyên các kết quả mô hình đã có trong session (forecast, RFM, simulate...).
    Chỉ ghi đè các field người dùng đang nhập qua widget keys.
    Đồng thời đánh dấu dirty + ghi đĩa để sống sót qua F5/reload trình duyệt.
    """
    init_session_state()
    _persist_local_context()
    _persist_business_profile()
    _persist_prepare_and_simulate()
    _persist_page_controls()
    try:
        from src.utils.session_persistence import mark_session_dirty, persist_session_to_disk

        mark_session_dirty()
        persist_session_to_disk()
    except Exception:  # noqa: BLE001
        pass


def save_workspace_now() -> None:
    """Ép ghi snapshot ngay (sau tải dữ liệu / chạy mô hình)."""
    try:
        from src.utils.session_persistence import mark_session_dirty, persist_session_to_disk

        mark_session_dirty()
        persist_session_to_disk(force=True)
    except Exception:  # noqa: BLE001
        pass


def _persist_local_context() -> None:
    lc_keys = ("lc_store", "lc_events", "lc_customers", "lc_stores", "lc_note")
    if not any(key in st.session_state for key in lc_keys):
        return
    prev = st.session_state.get("local_context") or LocalContext()
    st.session_state["local_context"] = LocalContext(
        store_name=str(st.session_state.get("lc_store", prev.store_name) or "").strip(),
        business_events=list(st.session_state.get("lc_events", prev.business_events) or []),
        customer_contexts=list(st.session_state.get("lc_customers", prev.customer_contexts) or []),
        store_contexts=list(st.session_state.get("lc_stores", prev.store_contexts) or []),
        free_text=str(st.session_state.get("lc_note", prev.free_text) or ""),
        latitude=prev.latitude,
        longitude=prev.longitude,
    )
    st.session_state["business_events"] = list(st.session_state["local_context"].business_events)


def _persist_business_profile() -> None:
    if "bp_business_name" not in st.session_state:
        return
    from ui.formatters import parse_int_commas

    # Chỉ ĐỌC giá trị widget → ghi business_profile.
    # Không gán lại bất kỳ bp_* session key nào (kể cả bp_budget) — sau khi
    # widget đã instantiate sẽ gây StreamlitWidgetAlreadyInstantiatedError.
    prev = st.session_state.get("business_profile") or BusinessProfile.with_yaml_defaults()
    if "bp_allowed_mechanics" in st.session_state:
        mechanics = [
            m for m in (st.session_state.get("bp_allowed_mechanics") or []) if m in MECHANIC_LABELS_VI
        ]
    else:
        mechanics = list(prev.allowed_mechanics)
    objective = st.session_state.get("bp_objective", st.session_state.get("objective", prev.primary_objective))
    target = float(st.session_state.get("bp_target_margin", int(prev.target_margin_pct * 100))) / 100
    min_margin = float(st.session_state.get("bp_min_margin", int(prev.min_margin_pct * 100))) / 100
    max_disc = float(st.session_state.get("bp_max_discount", int(prev.max_discount_pct * 100))) / 100
    min_roi = float(st.session_state.get("bp_min_roi", int(prev.min_roi_pct * 100))) / 100

    if "bp_budget_fmt" in st.session_state:
        budget = float(parse_int_commas(st.session_state.get("bp_budget_fmt"), default=0, minimum=0))
    else:
        try:
            budget = float(max(0, int(float(st.session_state.get("bp_budget", prev.promotion_budget)))))
        except (TypeError, ValueError):
            budget = float(prev.promotion_budget)

    if "bp_capacity_fmt" in st.session_state:
        raw_cap = str(st.session_state.get("bp_capacity_fmt") or "").strip()
        if raw_cap:
            capacity = float(parse_int_commas(raw_cap, default=0, minimum=0))
        else:
            try:
                capacity = float(max(0, int(round(float(st.session_state.get("bp_capacity", 0) or 0)))))
            except (TypeError, ValueError):
                capacity = float(prev.service_capacity_per_staff_per_hour)
    else:
        try:
            capacity = float(
                max(0, int(round(float(st.session_state.get("bp_capacity", prev.service_capacity_per_staff_per_hour)))))
            )
        except (TypeError, ValueError):
            capacity = float(prev.service_capacity_per_staff_per_hour)

    model_raw = str(st.session_state.get("bp_model", prev.b2b_or_b2c) or "").strip()
    model = model_raw if model_raw in {"B2C", "B2B", "Cả hai"} else (prev.b2b_or_b2c or "B2C")
    profile = BusinessProfile(
        business_name=str(st.session_state.get("bp_business_name", prev.business_name) or ""),
        industry=str(st.session_state.get("bp_industry", prev.industry) or ""),
        b2b_or_b2c=model,
        n_stores=int(st.session_state.get("bp_n_stores", prev.n_stores) or 0),
        sku_range=str(st.session_state.get("bp_sku_range", prev.sku_range) or ""),
        typical_purchase_cycle_days=int(
            st.session_state.get("bp_cycle_days", prev.typical_purchase_cycle_days) or 0
        ),
        target_margin_pct=target,
        min_margin_pct=min_margin,
        max_discount_pct=max_disc,
        safety_stock_days=int(st.session_state.get("bp_safety", prev.safety_stock_days) or 0),
        lead_time_days=max(1, int(st.session_state.get("bp_lead", prev.lead_time_days) or 1)),
        allowed_mechanics=mechanics,
        promotion_budget=budget,
        service_capacity_per_staff_per_hour=capacity,
        primary_objective=str(objective or prev.primary_objective),
        has_seasonality=bool(st.session_state.get("bp_seasonality", prev.has_seasonality)),
        min_roi_pct=min_roi,
        max_campaign_duration_days=int(
            st.session_state.get("bp_max_days", prev.max_campaign_duration_days) or 0
        ),
        mask_customer_id=bool(st.session_state.get("bp_mask_cid", prev.mask_customer_id)),
    )
    st.session_state["business_profile"] = profile
    st.session_state["objective"] = profile.primary_objective
    # Snapshot form bền vững (dialog đóng sẽ xóa widget keys bp_*).
    from ui.formatters import format_int_commas

    budget_i = int(profile.promotion_budget or 0)
    capacity_i = max(0, int(round(float(profile.service_capacity_per_staff_per_hour or 0))))
    model = profile.b2b_or_b2c if profile.b2b_or_b2c in ("B2C", "B2B", "Cả hai") else "B2C"
    st.session_state["bp_form_snapshot"] = {
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
        "bp_safety": int(profile.safety_stock_days or 0),
        "bp_lead": max(1, int(profile.lead_time_days or 1)),
        "bp_budget": budget_i,
        "bp_budget_fmt": format_int_commas(budget_i) if budget_i else "",
        "bp_capacity": capacity_i,
        "bp_capacity_fmt": format_int_commas(capacity_i) if capacity_i else "",
        "bp_min_roi": int(profile.min_roi_pct * 100),
        "bp_max_days": max(1, int(profile.max_campaign_duration_days or 1)),
        "bp_mask_cid": bool(profile.mask_customer_id),
        "bp_allowed_mechanics": [m for m in (profile.allowed_mechanics or []) if m in MECHANIC_LABELS_VI],
        "bp_objective": str(profile.primary_objective or "REVENUE"),
    }


def prep_profile_fingerprint(profile: BusinessProfile) -> tuple:
    """Fingerprint 4 tham số Prepare lấy từ hồ sơ — dùng để biết khi cần seed lại."""
    lead = max(0, int(profile.lead_time_days or 0))
    safety = max(0, int(profile.safety_stock_days or 0))
    budget = max(0, int(round(float(profile.promotion_budget or 0))))
    margin = round(min(0.9, max(0.0, float(profile.min_margin_pct or 0.0))), 4)
    return (lead, safety, budget, margin)


def apply_business_profile_to_prepare(
    profile: BusinessProfile | None = None,
    *,
    write_widgets: bool = True,
) -> None:
    """Ghi tham số Prepare từ business_profile.

    write_widgets=False: chỉ cập nhật prepare_params + khóa số (prep_lead, …),
    không đụng prep_*_fmt — dùng khi persist/goto chạy SAU khi widget đã instantiate
    (tránh StreamlitWidgetAlreadyInstantiatedError).
    """
    from ui.formatters import format_int_commas

    profile = profile or st.session_state.get("business_profile")
    if profile is None:
        return
    lead, safety, budget, margin = prep_profile_fingerprint(profile)

    lead_v = lead if lead >= 1 else None
    lead_fmt = str(lead) if lead >= 1 else ""
    safety_fmt = str(safety)
    budget_v = float(budget) if budget > 0 else None
    budget_fmt = format_int_commas(budget) if budget > 0 else ""
    margin_v = margin if margin > 0 else None
    margin_fmt = f"{margin:.2f}" if margin > 0 else ""

    st.session_state["prep_lead"] = lead_v
    st.session_state["prep_safety"] = safety
    st.session_state["prep_budget"] = budget_v
    st.session_state["prep_margin"] = margin_v
    st.session_state["prep_autofill_fp"] = (lead, safety, budget, margin)
    st.session_state["prep_autofilled_from_bp"] = True
    st.session_state["prep_fields_initialized"] = True
    st.session_state["params_authority"] = "bp"
    st.session_state["prepare_params"] = {
        "prep_lead": lead_v,
        "prep_lead_fmt": lead_fmt,
        "prep_safety": safety,
        "prep_safety_fmt": safety_fmt,
        "prep_budget": budget_v,
        "prep_budget_fmt": budget_fmt,
        "prep_margin": margin_v,
        "prep_margin_fmt": margin_fmt,
    }

    if write_widgets:
        st.session_state["prep_lead_fmt"] = lead_fmt
        st.session_state["prep_safety_fmt"] = safety_fmt
        st.session_state["prep_budget_fmt"] = budget_fmt
        st.session_state["prep_margin_fmt"] = margin_fmt


def _persist_prepare_and_simulate() -> None:
    profile = st.session_state.get("business_profile")
    if profile is None:
        return
    # Đồng bộ ô text → số. Không ghi đè *_fmt (widget keys) sau khi đã instantiate.
    from ui.formatters import parse_int_commas

    if "prep_lead_fmt" in st.session_state:
        raw = st.session_state.get("prep_lead_fmt")
        if str(raw or "").strip():
            value = parse_int_commas(raw, default=0, minimum=0)
            st.session_state["prep_lead"] = value if value >= 1 else None
        else:
            st.session_state["prep_lead"] = None
    if "prep_safety_fmt" in st.session_state:
        raw = st.session_state.get("prep_safety_fmt")
        if str(raw or "").strip():
            st.session_state["prep_safety"] = parse_int_commas(raw, default=0, minimum=0)
        else:
            st.session_state["prep_safety"] = None
    if "prep_budget_fmt" in st.session_state:
        raw = st.session_state.get("prep_budget_fmt")
        if str(raw or "").strip():
            value = parse_int_commas(raw, default=0, minimum=0)
            st.session_state["prep_budget"] = float(value) if value > 0 else None
        else:
            st.session_state["prep_budget"] = None
    if "prep_margin_fmt" in st.session_state:
        raw = str(st.session_state.get("prep_margin_fmt") or "").strip().replace(",", ".")
        if raw:
            try:
                st.session_state["prep_margin"] = min(0.9, max(0.0, float(raw)))
            except ValueError:
                st.session_state["prep_margin"] = None
        else:
            st.session_state["prep_margin"] = None

    # Hồ sơ là nguồn sự thật trừ khi user vừa sửa tay trên Prepare (params_authority=prep).
    authority = st.session_state.get("params_authority")
    if authority == "prep":
        if st.session_state.get("prep_lead") is not None and int(st.session_state["prep_lead"]) >= 1:
            profile.lead_time_days = int(st.session_state["prep_lead"])
        elif st.session_state.get("prep_lead") is not None:
            st.session_state["prep_lead"] = None
            profile.lead_time_days = max(1, int(getattr(profile, "lead_time_days", 1) or 1))
        if st.session_state.get("prep_safety") is not None:
            profile.safety_stock_days = int(st.session_state["prep_safety"])
        if st.session_state.get("prep_budget") is not None:
            profile.promotion_budget = float(st.session_state["prep_budget"])
        if st.session_state.get("prep_margin") is not None:
            profile.min_margin_pct = float(st.session_state["prep_margin"])
        st.session_state["prep_autofill_fp"] = prep_profile_fingerprint(profile)
        st.session_state["prepare_params"] = {
            "prep_lead": st.session_state.get("prep_lead"),
            "prep_lead_fmt": st.session_state.get("prep_lead_fmt", ""),
            "prep_safety": st.session_state.get("prep_safety"),
            "prep_safety_fmt": st.session_state.get("prep_safety_fmt", ""),
            "prep_budget": st.session_state.get("prep_budget"),
            "prep_budget_fmt": st.session_state.get("prep_budget_fmt", ""),
            "prep_margin": st.session_state.get("prep_margin"),
            "prep_margin_fmt": st.session_state.get("prep_margin_fmt", ""),
        }
    elif st.session_state.get("bp_profile_committed"):
        # BP đã lưu — khớp prepare_params; không ghi prep_*_fmt (widget có thể đã tạo).
        apply_business_profile_to_prepare(profile, write_widgets=False)
    else:
        st.session_state["prepare_params"] = {
            "prep_lead": st.session_state.get("prep_lead"),
            "prep_lead_fmt": st.session_state.get("prep_lead_fmt", ""),
            "prep_safety": st.session_state.get("prep_safety"),
            "prep_safety_fmt": st.session_state.get("prep_safety_fmt", ""),
            "prep_budget": st.session_state.get("prep_budget"),
            "prep_budget_fmt": st.session_state.get("prep_budget_fmt", ""),
            "prep_margin": st.session_state.get("prep_margin"),
            "prep_margin_fmt": st.session_state.get("prep_margin_fmt", ""),
        }

    if "sim_budget_fmt" in st.session_state:
        from ui.formatters import parse_int_commas

        raw = st.session_state.get("sim_budget_fmt")
        if str(raw or "").strip():
            value = parse_int_commas(raw, default=0, minimum=0)
            st.session_state["sim_budget"] = float(value)
            profile.promotion_budget = float(value)
        else:
            st.session_state["sim_budget"] = 0.0
    elif "sim_budget" in st.session_state:
        try:
            profile.promotion_budget = float(st.session_state["sim_budget"])
        except (TypeError, ValueError):
            pass
    if "sim_gift_fmt" in st.session_state:
        from ui.formatters import parse_int_commas

        raw = st.session_state.get("sim_gift_fmt")
        if str(raw or "").strip():
            st.session_state["sim_gift"] = parse_int_commas(raw, default=0, minimum=0)
        else:
            st.session_state["sim_gift"] = 0
    if "sim_max_disc" in st.session_state:
        profile.max_discount_pct = float(st.session_state["sim_max_disc"])
    if "sim_min_margin" in st.session_state:
        profile.min_margin_pct = float(st.session_state["sim_min_margin"])
    st.session_state["business_profile"] = profile


def _persist_page_controls() -> None:
    """Gương các lựa chọn UI (forecast/simulate/prepare) sang khóa ổn định trong session."""
    drafts = dict(st.session_state.get("ui_control_drafts") or {})
    for key in (
        "fc_scope",
        "fc_horizon",
        "fc_cat",
        "fc_sku",
        "sim_scope",
        "sim_cat",
        "sim_sku",
        "sim_period",
        "sim_gift",
        "sim_gift_fmt",
        "sim_budget",
        "sim_budget_fmt",
        "prep_search",
        "prep_cat",
        "bp_objective",
        "selected_mechanic",
    ):
        if key in st.session_state:
            drafts[key] = st.session_state[key]
    if drafts:
        st.session_state["ui_control_drafts"] = drafts


def has_data() -> bool:
    return st.session_state.get("clean_df") is not None and not st.session_state["clean_df"].empty


def require_data_warning() -> bool:
    """Hiển thị cảnh báo nếu chưa có dữ liệu. Trả về True nếu THIẾU dữ liệu (nên dừng trang)."""
    if not has_data():
        st.warning(
            "⚠️ Chưa có dữ liệu để phân tích. Vui lòng vào trang **Tải dữ liệu** để upload file CSV/XLSX trước, "
            "hoặc bấm **Dùng dữ liệu demo** ở trang Tổng quan."
        )
        return True
    return False
