"""Trang Business Onboarding + Business Objective Engine (mục VII, VIII, XXI yêu cầu gốc)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from src.business.profile import BusinessProfile, list_profiles, load_profile, save_profile
from src.optimization.objective import OBJECTIVE_LABELS_VI, OBJECTIVE_PRIORITY_METRICS_VI, OBJECTIVES
from src.promotion.mechanics import MECHANIC_LABELS_VI
from src.recommendation.timing import EVENT_TO_OBJECTIVE
from src.utils.state import init_session_state

init_session_state()

st.title("🎯 Hồ sơ Doanh nghiệp & Mục tiêu Kinh doanh")

profile: BusinessProfile = st.session_state["business_profile"]

st.subheader("1️⃣ Hồ sơ doanh nghiệp (Business Profile)")
with st.form("business_profile_form"):
    c1, c2 = st.columns(2)
    with c1:
        business_name = st.text_input("Tên doanh nghiệp", value=profile.business_name)
        industry = st.text_input("Ngành kinh doanh", value=profile.industry)
        b2b_or_b2c = st.selectbox("Mô hình", ["B2C", "B2B", "Cả hai"], index=["B2C", "B2B", "Cả hai"].index(profile.b2b_or_b2c) if profile.b2b_or_b2c in ["B2C", "B2B", "Cả hai"] else 0)
        n_stores = st.number_input("Số cửa hàng/chi nhánh", min_value=1, value=profile.n_stores)
        sku_range = st.text_input("Khoảng số lượng SKU (vd: 30-100)", value=profile.sku_range)
        typical_purchase_cycle_days = st.number_input("Chu kỳ mua hàng phổ biến (ngày)", min_value=1, value=profile.typical_purchase_cycle_days)
        has_seasonality = st.checkbox("Ngành hàng có yếu tố mùa vụ rõ rệt", value=profile.has_seasonality)
    with c2:
        target_margin_pct = st.slider("Biên lợi nhuận mục tiêu (%)", 0, 80, int(profile.target_margin_pct * 100)) / 100
        min_margin_pct = st.slider("Margin tối thiểu chấp nhận được (%)", 0, 80, int(profile.min_margin_pct * 100)) / 100
        max_discount_pct = st.slider("Mức giảm giá tối đa cho phép (%)", 0, 90, int(profile.max_discount_pct * 100)) / 100
        safety_stock_days = st.number_input("Safety Stock mong muốn (ngày)", min_value=0, value=profile.safety_stock_days)
        lead_time_days = st.number_input("Lead Time nhập hàng (ngày)", min_value=0, value=profile.lead_time_days)
        promotion_budget = st.number_input("Ngân sách Promotion (VNĐ)", min_value=0, value=int(profile.promotion_budget), step=1_000_000)
        service_capacity = st.number_input("Năng lực phục vụ (khách/nhân viên/giờ)", min_value=1.0, value=profile.service_capacity_per_staff_per_hour)

    allowed_mechanics = st.multiselect(
        "Cơ chế khuyến mãi doanh nghiệp cho phép sử dụng",
        options=list(MECHANIC_LABELS_VI.keys()),
        default=profile.allowed_mechanics,
        format_func=lambda k: MECHANIC_LABELS_VI[k],
    )

    submitted = st.form_submit_button("💾 Lưu hồ sơ doanh nghiệp", type="primary")
    if submitted:
        new_profile = BusinessProfile(
            business_name=business_name,
            industry=industry,
            b2b_or_b2c=b2b_or_b2c,
            n_stores=n_stores,
            sku_range=sku_range,
            typical_purchase_cycle_days=typical_purchase_cycle_days,
            target_margin_pct=target_margin_pct,
            min_margin_pct=min_margin_pct,
            max_discount_pct=max_discount_pct,
            safety_stock_days=safety_stock_days,
            lead_time_days=lead_time_days,
            allowed_mechanics=allowed_mechanics,
            promotion_budget=promotion_budget,
            service_capacity_per_staff_per_hour=service_capacity,
            primary_objective=profile.primary_objective,
            has_seasonality=has_seasonality,
        )
        st.session_state["business_profile"] = new_profile
        save_profile(new_profile, name=business_name.strip().replace(" ", "_").lower() or "default")
        st.success("Đã lưu hồ sơ doanh nghiệp.")
        st.rerun()

existing_profiles = list_profiles()
if existing_profiles:
    with st.expander("📂 Tải hồ sơ đã lưu trước đó"):
        chosen = st.selectbox("Chọn hồ sơ", existing_profiles)
        if st.button("Tải hồ sơ này"):
            loaded = load_profile(chosen)
            if loaded:
                st.session_state["business_profile"] = loaded
                st.success(f"Đã tải hồ sơ '{chosen}'.")
                st.rerun()

st.divider()
st.subheader("2️⃣ Chọn Mục tiêu Kinh doanh chính")
st.write("Mỗi mục tiêu sẽ dẫn tới cách đề xuất khuyến mãi khác nhau ở các bước sau.")

objective = st.radio(
    "Mục tiêu",
    OBJECTIVES,
    index=OBJECTIVES.index(st.session_state["objective"]) if st.session_state["objective"] in OBJECTIVES else 1,
    format_func=lambda o: OBJECTIVE_LABELS_VI[o],
    horizontal=True,
)
st.session_state["objective"] = objective
st.session_state["business_profile"].primary_objective = objective

st.markdown(f"**Chỉ số ưu tiên cho mục tiêu '{OBJECTIVE_LABELS_VI[objective]}':**")
for m in OBJECTIVE_PRIORITY_METRICS_VI[objective]:
    st.write(f"- {m}")

st.divider()
st.subheader("3️⃣ Sự kiện kinh doanh đặc biệt (tuỳ chọn)")
st.write("Nếu có sự kiện đặc biệt sắp diễn ra, hệ thống sẽ gợi ý mục tiêu phù hợp.")

event_options = ["-- Không có sự kiện đặc biệt --"] + list(EVENT_TO_OBJECTIVE.keys())
chosen_event = st.selectbox("Sự kiện", event_options)
if chosen_event != "-- Không có sự kiện đặc biệt --":
    suggested_objective, reason = EVENT_TO_OBJECTIVE[chosen_event]
    st.info(f"💡 Với sự kiện **{chosen_event}**, gợi ý mục tiêu: **{OBJECTIVE_LABELS_VI[suggested_objective]}**. Lý do: {reason}")
    if st.button("Áp dụng gợi ý này làm mục tiêu"):
        st.session_state["objective"] = suggested_objective
        st.session_state["business_events"] = [chosen_event]
        st.rerun()
