"""Trang Chất lượng dữ liệu (mục VI yêu cầu gốc)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from src.utils.state import init_session_state, require_data_warning

init_session_state()

st.title("✅ Báo cáo Chất lượng Dữ liệu")

if require_data_warning():
    st.stop()

report = st.session_state["quality_report"]
caps = st.session_state["capabilities"]

score_color = "green" if report.score >= 85 else ("orange" if report.score >= 65 else "red")
st.markdown(f"## Điểm chất lượng dữ liệu: :{score_color}[{report.score}/100] — {report.score_label}")
st.progress(report.score / 100)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Số dòng", f"{report.n_rows:,}")
c2.metric("Số SKU", f"{report.n_skus:,}")
c3.metric("Số giao dịch", f"{report.n_transactions:,}" if report.n_transactions else "Không có dữ liệu")
c4.metric("Số khách hàng", f"{report.n_customers:,}" if report.n_customers else "Không có dữ liệu")

c5, c6, c7, c8 = st.columns(4)
c5.metric("Số ngày dữ liệu", report.n_days_span)
c6.metric("Ngày thiếu giao dịch", report.n_missing_dates)
c7.metric("Dòng trùng lặp", report.n_duplicate_rows)
c8.metric("Dòng lỗi đã loại bỏ", report.n_invalid_rows_dropped)

st.divider()
col_a, col_b = st.columns(2)
with col_a:
    st.subheader("⚠️ Cảnh báo")
    if report.warnings:
        for w in report.warnings:
            st.warning(w)
    else:
        st.success("Không có cảnh báo nghiêm trọng nào.")

with col_b:
    st.subheader("📝 Ghi chú")
    if report.notes:
        for n in report.notes:
            st.info(n)
    else:
        st.write("Không có ghi chú thêm.")

if report.missing_values:
    st.subheader("Giá trị bị thiếu theo cột")
    st.dataframe(
        {"Cột": list(report.missing_values.keys()), "Số dòng thiếu": list(report.missing_values.values())},
        use_container_width=True,
    )

st.divider()
st.subheader("🧩 Module nào khả dụng với dữ liệu này?")
st.write(
    "Dựa trên các cột dữ liệu bạn có, hệ thống tự động bật/tắt các module phân tích tương ứng — "
    "không phải toàn bộ SME đều có đầy đủ dữ liệu, PromoPilot AI thích nghi theo dữ liệu thực tế của bạn."
)
for module_name, (enabled, reason) in caps.module_status().items():
    icon = "✅" if enabled else "⛔"
    with st.expander(f"{icon} {module_name}", expanded=not enabled):
        st.write(reason)
