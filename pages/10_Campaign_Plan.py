"""Trang Campaign Generator + Export (mục XXV, XXVII yêu cầu gốc)."""
from __future__ import annotations

import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st

from src.recommendation.campaign import generate_campaign_plan, is_llm_enabled
from src.utils.state import init_session_state

init_session_state()

st.title("📋 Kế hoạch Campaign")

card = st.session_state.get("last_recommendation_card")
if card is None:
    st.warning(
        "⚠️ Chưa có đề xuất nào được tạo. Vui lòng hoàn thành trang **9. AI Recommendation** trước."
    )
    st.stop()

profile = st.session_state["business_profile"]

plan = generate_campaign_plan(
    card,
    business_name=profile.business_name,
    service_capacity_per_staff_per_hour=profile.service_capacity_per_staff_per_hour,
)

if is_llm_enabled():
    st.caption("ℹ️ Đã phát hiện cấu hình LLM trong .env — nội dung dưới đây vẫn dùng template rule-based mặc định của MVP.")
else:
    st.caption("ℹ️ Nội dung được sinh bằng template rule-based (không cần internet/API key).")

st.header(plan.name)

col1, col2 = st.columns(2)
with col1:
    st.markdown(f"**Mục tiêu:** {plan.objective}")
    st.markdown(f"**Nhóm khách hàng mục tiêu:** {plan.target}")
    st.markdown(f"**Sản phẩm:** {plan.product}")
    st.markdown(f"**Ưu đãi:** {plan.offer}")
    st.markdown(f"**Thời gian:** {plan.timing}")
with col2:
    st.markdown("**KPI mục tiêu:**")
    for k in plan.kpi:
        st.write(f"- {k}")

st.subheader("📦 Kế hoạch tồn kho")
st.write(plan.inventory_plan)

st.subheader("👥 Kế hoạch nhân sự")
st.write(plan.staffing_plan)

st.divider()
st.subheader("✍️ Nội dung Marketing")
tab_fb, tab_zalo, tab_sms = st.tabs(["Facebook", "Zalo", "SMS"])
with tab_fb:
    st.text_area("Nội dung Facebook", plan.fb_copy, height=160)
with tab_zalo:
    st.text_area("Nội dung Zalo", plan.zalo_copy, height=160)
with tab_sms:
    st.text_area("Nội dung SMS", plan.sms_copy, height=80)

st.divider()
st.subheader("📤 Xuất báo cáo")

summary_rows = [
    {"Mục": "Tên chương trình", "Giá trị": plan.name},
    {"Mục": "Mục tiêu", "Giá trị": plan.objective},
    {"Mục": "Nhóm khách hàng mục tiêu", "Giá trị": plan.target},
    {"Mục": "Sản phẩm/Danh mục", "Giá trị": plan.product},
    {"Mục": "Ưu đãi", "Giá trị": plan.offer},
    {"Mục": "Thời gian", "Giá trị": plan.timing},
    {"Mục": "Khách hàng dự kiến", "Giá trị": f"{card.expected_customers_range[0]:.0f}-{card.expected_customers_range[1]:.0f}"},
    {"Mục": "Nhu cầu dự kiến", "Giá trị": f"{card.expected_demand_range[0]:.0f}-{card.expected_demand_range[1]:.0f}"},
    {"Mục": "Tồn kho đề xuất", "Giá trị": f"{card.recommended_stock:.0f}"},
    {"Mục": "Doanh thu dự kiến", "Giá trị": f"{card.expected_revenue_range[0]:,.0f} - {card.expected_revenue_range[1]:,.0f}"},
    {"Mục": "Lợi nhuận gộp dự kiến", "Giá trị": f"{card.expected_gp_range[0]:,.0f} - {card.expected_gp_range[1]:,.0f}"},
    {"Mục": "Rủi ro", "Giá trị": card.risk_label},
    {"Mục": "Độ tin cậy", "Giá trị": f"{card.confidence_pct_range[0]}-{card.confidence_pct_range[1]}%"},
]
summary_df = pd.DataFrame(summary_rows)
kpi_df = pd.DataFrame({"KPI": plan.kpi})
why_df = pd.DataFrame({"Lý do đề xuất": card.why_bullets})
content_df = pd.DataFrame(
    {"Kênh": ["Facebook", "Zalo", "SMS"], "Nội dung": [plan.fb_copy, plan.zalo_copy, plan.sms_copy]}
)

col_csv, col_xlsx = st.columns(2)
with col_csv:
    csv_bytes = summary_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "⬇️ Tải CSV (Tóm tắt kế hoạch)",
        data=csv_bytes,
        file_name="promopilot_campaign_summary.csv",
        mime="text/csv",
    )

with col_xlsx:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Tom tat", index=False)
        kpi_df.to_excel(writer, sheet_name="KPI", index=False)
        why_df.to_excel(writer, sheet_name="Ly do de xuat", index=False)
        content_df.to_excel(writer, sheet_name="Noi dung Marketing", index=False)
        st.session_state["last_scenario_table"].to_excel(writer, sheet_name="Kich ban Promotion", index=False)
    st.download_button(
        "⬇️ Tải Excel (Đầy đủ)",
        data=buffer.getvalue(),
        file_name="promopilot_campaign_plan.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
