"""Trang Export Report (mục XLIV spec PromotionPilot AI): tổng hợp toàn bộ báo cáo vào 1 file."""
from __future__ import annotations

import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st

from src.utils.state import init_session_state, require_data_warning

init_session_state()

st.title("📤 Export Report — Báo cáo tổng hợp")
st.write(
    "Xuất toàn bộ thông tin phân tích thành 1 file Excel nhiều sheet: Tình hình kinh doanh, "
    "Dự báo, So sánh kịch bản, Đề xuất, Kế hoạch triển khai, Rủi ro, KPI."
)

if require_data_warning():
    st.stop()

report = st.session_state["quality_report"]
caps = st.session_state["capabilities"]

sections_available = {
    "Tình hình kinh doanh (Data Quality)": report is not None,
    "Dự báo": bool(st.session_state.get("forecast_cache")),
    "So sánh kịch bản Promotion": st.session_state.get("last_scenario_table") is not None,
    "AI Recommendation": st.session_state.get("last_recommendation_card") is not None,
    "Execution Plan": st.session_state.get("last_execution_plan") is not None,
}

st.subheader("Các phần sẽ được đưa vào báo cáo")
for name, available in sections_available.items():
    st.write(f"{'✅' if available else '⛔ (chưa có dữ liệu — sẽ bỏ qua)'} {name}")

if st.button("📦 Tạo báo cáo Excel tổng hợp", type="primary"):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        situation_rows = [
            {"Chỉ số": "Số dòng dữ liệu", "Giá trị": f"{report.n_rows:,}"},
            {"Chỉ số": "Số SKU", "Giá trị": f"{report.n_skus:,}"},
            {"Chỉ số": "Số khách hàng", "Giá trị": f"{report.n_customers:,}" if report.n_customers else "N/A"},
            {"Chỉ số": "Điểm chất lượng dữ liệu", "Giá trị": f"{report.score}/100 — {report.score_label}"},
            {"Chỉ số": "Khoảng thời gian", "Giá trị": f"{report.date_min} → {report.date_max}"},
        ]
        pd.DataFrame(situation_rows).to_excel(writer, sheet_name="Tinh hinh kinh doanh", index=False)

        if st.session_state.get("forecast_cache"):
            rows = []
            for key, fr in st.session_state["forecast_cache"].items():
                rows.append(
                    {
                        "Chuỗi dữ liệu": fr.series_name,
                        "Model": fr.model_name,
                        "WAPE": f"{fr.wape:.1%}" if pd.notna(fr.wape) else "N/A",
                        "Độ tin cậy": fr.confidence,
                    }
                )
            pd.DataFrame(rows).to_excel(writer, sheet_name="Du bao", index=False)

        if st.session_state.get("last_scenario_table") is not None:
            st.session_state["last_scenario_table"].to_excel(writer, sheet_name="Kich ban Promotion", index=False)

        card = st.session_state.get("last_recommendation_card")
        if card is not None:
            rec_rows = [
                {"Mục": "Mục tiêu", "Giá trị": card.objective_vi},
                {"Mục": "Sản phẩm/Danh mục", "Giá trị": card.product_focus},
                {"Mục": "Nhóm khách hàng mục tiêu", "Giá trị": card.target_segment},
                {"Mục": "Chương trình khuyến mãi", "Giá trị": card.promotion_label},
                {"Mục": "Thời gian", "Giá trị": card.timing_text},
                {"Mục": "Rủi ro", "Giá trị": card.risk_label},
                {"Mục": "Độ tin cậy", "Giá trị": f"{card.confidence_pct_range[0]}-{card.confidence_pct_range[1]}%"},
                {"Mục": "Doanh thu dự kiến", "Giá trị": f"{card.expected_revenue_range[0]:,.0f}-{card.expected_revenue_range[1]:,.0f}"},
                {"Mục": "Lợi nhuận gộp dự kiến", "Giá trị": f"{card.expected_gp_range[0]:,.0f}-{card.expected_gp_range[1]:,.0f}"},
            ]
            pd.DataFrame(rec_rows).to_excel(writer, sheet_name="AI Recommendation", index=False)
            pd.DataFrame({"Lý do đề xuất": card.why_bullets}).to_excel(writer, sheet_name="Why", index=False)

        if st.session_state.get("last_execution_plan") is not None:
            st.session_state["last_execution_plan"].to_excel(writer, sheet_name="Execution Plan", index=False)

    st.download_button(
        "⬇️ Tải báo cáo Excel tổng hợp",
        data=buffer.getvalue(),
        file_name="promotionpilot_bao_cao_tong_hop.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

st.caption(
    "ℹ️ Xuất PDF chưa được triển khai trong MVP này (đánh dấu 'nếu khả thi' trong yêu cầu gốc) — "
    "xem docs/backlog_tinh_nang.md."
)
