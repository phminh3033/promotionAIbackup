"""Quản lý session state dùng chung cho toàn bộ ứng dụng Streamlit (tránh lặp code giữa các trang)."""
from __future__ import annotations

import streamlit as st

from src.business.profile import BusinessProfile
from src.context.local_context import LocalContext


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
        "campaign_actual_data": None,
        "demo_access_granted": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


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
