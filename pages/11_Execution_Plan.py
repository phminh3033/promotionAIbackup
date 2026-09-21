"""Trang Execution Plan (mục XXV, XXVII, XXVIII spec PromotionPilot AI).

Gộp: (1) timeline triển khai D-7..D+7 theo phòng ban, (2) nội dung campaign marketing (rule-based,
kế thừa từ mục XXV cũ), (3) khởi tạo Campaign Record cho Campaign Learning Loop (mục XXXII) để các
trang Campaign Monitor / Alerts sử dụng ở bước tiếp theo.
"""
from __future__ import annotations

import io
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st

from src.execution.plan import generate_execution_plan, tasks_to_dataframe
from src.learning.campaign_log import CampaignRecord, new_campaign_id, save_campaign_record
from src.recommendation.campaign import generate_campaign_plan, is_llm_enabled
from src.utils.state import init_session_state

init_session_state()

st.title("🗓️ Execution Plan — Kế hoạch Triển khai")

card = st.session_state.get("last_recommendation_card")
if card is None:
    st.warning(
        "⚠️ Chưa có đề xuất nào được tạo. Vui lòng hoàn thành trang **AI Recommendation** trước."
    )
    st.stop()

profile = st.session_state["business_profile"]

st.subheader("1️⃣ Chọn ngày khởi chạy chương trình")
campaign_start = st.date_input("Ngày khởi chạy (D0)", value=date.today())

st.subheader("2️⃣ Timeline triển khai theo phòng ban")
tasks = generate_execution_plan(
    campaign_start=pd.Timestamp(campaign_start),
    product_focus=card.product_focus,
    promotion_label=card.promotion_label,
    recommended_stock=card.recommended_stock,
    objective_vi=card.objective_vi,
)
tasks_df = tasks_to_dataframe(tasks)
st.dataframe(tasks_df, use_container_width=True, hide_index=True)
st.caption(
    "⚠️ Đây là template timeline chuẩn cho MVP — doanh nghiệp cần tự điều chỉnh phụ trách/thời hạn "
    "theo tổ chức thật. MVP chưa kết nối hệ thống ticket thật (Jira/Monday/Asana/Teams) — xem trạng "
    "thái ở `src/integrations/`."
)
st.session_state["last_execution_plan"] = tasks_df

st.divider()
st.subheader("3️⃣ Nội dung Marketing")

plan = generate_campaign_plan(
    card,
    business_name=profile.business_name,
    service_capacity_per_staff_per_hour=profile.service_capacity_per_staff_per_hour,
)

if is_llm_enabled():
    st.caption("ℹ️ Đã phát hiện cấu hình LLM trong .env — nội dung dưới đây vẫn dùng template rule-based mặc định của MVP.")
else:
    st.caption("ℹ️ Nội dung được sinh bằng template rule-based (không cần internet/API key).")

col1, col2 = st.columns(2)
with col1:
    st.markdown(f"**Mục tiêu:** {plan.objective}")
    st.markdown(f"**Nhóm khách hàng mục tiêu:** {plan.target}")
    st.markdown(f"**Sản phẩm:** {plan.product}")
    st.markdown(f"**Ưu đãi:** {plan.offer}")
with col2:
    st.markdown("**KPI mục tiêu:**")
    for k in plan.kpi:
        st.write(f"- {k}")

tab_fb, tab_zalo, tab_sms = st.tabs(["Facebook", "Zalo", "SMS"])
with tab_fb:
    st.text_area("Nội dung Facebook", plan.fb_copy, height=160)
with tab_zalo:
    st.text_area("Nội dung Zalo", plan.zalo_copy, height=160)
with tab_sms:
    st.text_area("Nội dung SMS", plan.sms_copy, height=80)

st.divider()
st.subheader("4️⃣ Khởi tạo Campaign & Xuất kế hoạch")
st.write(
    "Bấm nút dưới đây để lưu campaign này vào hệ thống theo dõi — cần thiết để dùng trang "
    "**Campaign Monitor** và **Alerts** (so sánh Actual vs Forecast, cảnh báo, đề xuất Continue/"
    "Adjust/Stop/Scale)."
)

if st.button("🚀 Khởi tạo Campaign này", type="primary"):
    campaign_id = new_campaign_id()
    promo_days = st.session_state["last_scenario_baseline"].promo_days if st.session_state.get("last_scenario_baseline") else None

    no_promo_gp_per_day = None
    scenario_table = st.session_state.get("last_scenario_table")
    if scenario_table is not None and promo_days:
        no_promo_rows = scenario_table[scenario_table["mechanic"] == "no_promo"]
        if not no_promo_rows.empty:
            no_promo_gp_per_day = float(no_promo_rows.iloc[0]["loi_nhuan_gop"]) / promo_days

    record = CampaignRecord(
        campaign_id=campaign_id,
        objective=card.objective_vi,
        product_focus=card.product_focus,
        promotion_label=card.promotion_label,
        forecast={
            "expected_revenue_range": list(card.expected_revenue_range),
            "expected_gp_range": list(card.expected_gp_range),
            "expected_customers_range": list(card.expected_customers_range),
            "expected_demand_range": list(card.expected_demand_range),
            "expected_roi_range": list(card.expected_roi_range) if card.expected_roi_range else None,
            "campaign_start": str(campaign_start),
            "promo_days": promo_days,
            "no_promo_gp_per_day": no_promo_gp_per_day,
        },
        roi_forecast=sum(card.expected_roi_range) / 2 if card.expected_roi_range else None,
    )
    save_campaign_record(record)
    st.session_state["active_campaign_id"] = campaign_id
    st.success(f"✅ Đã khởi tạo campaign **{campaign_id}**. Sang trang **Campaign Monitor** để nhập dữ liệu thực tế sau khi chạy.")

summary_rows = [
    {"Mục": "Tên chương trình", "Giá trị": plan.name},
    {"Mục": "Mục tiêu", "Giá trị": plan.objective},
    {"Mục": "Nhóm khách hàng mục tiêu", "Giá trị": plan.target},
    {"Mục": "Sản phẩm/Danh mục", "Giá trị": plan.product},
    {"Mục": "Ưu đãi", "Giá trị": plan.offer},
    {"Mục": "Ngày khởi chạy", "Giá trị": str(campaign_start)},
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
        file_name="promotionpilot_execution_summary.csv",
        mime="text/csv",
    )

with col_xlsx:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Tom tat", index=False)
        tasks_df.to_excel(writer, sheet_name="Execution Plan", index=False)
        kpi_df.to_excel(writer, sheet_name="KPI", index=False)
        why_df.to_excel(writer, sheet_name="Ly do de xuat", index=False)
        content_df.to_excel(writer, sheet_name="Noi dung Marketing", index=False)
        if st.session_state.get("last_scenario_table") is not None:
            st.session_state["last_scenario_table"].to_excel(writer, sheet_name="Kich ban Promotion", index=False)
    st.download_button(
        "⬇️ Tải Excel (Đầy đủ)",
        data=buffer.getvalue(),
        file_name="promotionpilot_execution_plan.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
