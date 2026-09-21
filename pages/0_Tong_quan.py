"""Trang Tổng quan (Trang chủ) của PromoPilot AI."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from src.business.profile import BusinessProfile
from src.data.loader import load_raw_file
from src.data.mapper import apply_mapping, detect_capabilities, suggest_mapping, validate_mapping
from src.data.quality import run_quality_check
from src.utils.state import has_data, init_session_state

init_session_state()

st.title("🎯 PromoPilot AI")
st.caption("AI Marketing & Demand Planning Copilot dành cho Doanh nghiệp vừa và nhỏ")

st.markdown(
    """
PromoPilot AI giúp doanh nghiệp vừa và nhỏ (SME) dùng dữ liệu bán hàng sẵn có (Excel/CSV từ POS)
để: hiểu tình hình kinh doanh, **dự báo nhu cầu — doanh thu — tồn kho**, và **đề xuất chương trình
khuyến mãi phù hợp với mục tiêu kinh doanh** (kéo traffic / tăng doanh thu / tăng lợi nhuận / giải
phóng tồn kho) — kèm giải thích bằng ngôn ngữ kinh doanh dễ hiểu, không cần đội Data Science.
"""
)

with st.container(border=True):
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("🚀 Bắt đầu nhanh (Pilot Mode)")
        st.write(
            "Chưa có dữ liệu sẵn sàng? Dùng ngay bộ dữ liệu demo mô phỏng một cửa hàng bán lẻ SME "
            "thực tế (18 tháng, 60.000+ dòng, có mùa vụ, khuyến mãi, khách hàng, tồn kho) để trải "
            "nghiệm toàn bộ quy trình trong vài giây."
        )
        if st.button("▶️ Dùng dữ liệu demo", type="primary"):
            demo_path = Path(__file__).resolve().parent.parent / "data" / "demo_sme_sales.csv"
            if not demo_path.exists():
                st.error("Không tìm thấy file dữ liệu demo. Vui lòng chạy `python scripts/generate_demo_data.py` trước.")
            else:
                raw_bytes = demo_path.read_bytes()
                raw_df = load_raw_file(raw_bytes, demo_path.name)
                mapping = suggest_mapping(list(raw_df.columns))
                errors = validate_mapping(mapping)
                if errors:
                    st.error("Lỗi mapping dữ liệu demo: " + "; ".join(errors))
                else:
                    mapped_df = apply_mapping(raw_df, mapping)
                    clean_df, report = run_quality_check(mapped_df)
                    caps = detect_capabilities(mapped_df)

                    st.session_state["raw_df"] = raw_df
                    st.session_state["raw_filename"] = demo_path.name
                    st.session_state["column_mapping"] = mapping
                    st.session_state["mapped_df"] = mapped_df
                    st.session_state["capabilities"] = caps
                    st.session_state["clean_df"] = clean_df
                    st.session_state["quality_report"] = report
                    st.session_state["business_profile"] = BusinessProfile(
                        business_name="Cửa hàng Bán lẻ Demo",
                        industry="Bán lẻ tổng hợp (tạp hoá / siêu thị mini)",
                    )
                    st.success(
                        f"✅ Đã tải dữ liệu demo: {len(clean_df):,} dòng, điểm chất lượng {report.score}/100. "
                        "Hãy sang trang **Chất lượng dữ liệu** hoặc **Dự báo** ở thanh điều hướng bên trái."
                    )
                    st.rerun()
    with col2:
        st.subheader("📤 Hoặc tự tải dữ liệu")
        st.write("Vào trang **1. Tải dữ liệu** ở sidebar để upload file CSV/XLSX của doanh nghiệp bạn.")

st.divider()

if has_data():
    df = st.session_state["clean_df"]
    report = st.session_state["quality_report"]
    caps = st.session_state["capabilities"]

    st.subheader("📊 Tình trạng dữ liệu hiện tại")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Số dòng dữ liệu", f"{report.n_rows:,}")
    c2.metric("Số SKU", f"{report.n_skus:,}")
    c3.metric(
        "Số khách hàng",
        f"{report.n_customers:,}" if report.n_customers is not None else "Không có dữ liệu",
    )
    c4.metric("Điểm chất lượng dữ liệu", f"{report.score}/100")
    date_range = (
        f"{report.date_min.date()} → {report.date_max.date()}" if report.date_min is not None else "N/A"
    )
    c5.metric("Khoảng thời gian", date_range)

    st.markdown("**Module khả dụng với dữ liệu hiện tại:**")
    status_cols = st.columns(4)
    for i, (module_name, (enabled, reason)) in enumerate(caps.module_status().items()):
        with status_cols[i % 4]:
            icon = "✅" if enabled else "⛔"
            st.write(f"{icon} **{module_name}**")
            if not enabled:
                st.caption(reason)
else:
    st.info("Chưa có dữ liệu nào được tải. Hãy dùng dữ liệu demo ở trên hoặc vào trang **Tải dữ liệu**.")

st.divider()
st.subheader("🧭 Các bước sử dụng PromoPilot AI")
steps = [
    ("1. Tải dữ liệu", "Upload file CSV/XLSX bán hàng và ánh xạ cột dữ liệu (Data Mapping Wizard)."),
    ("2. Chất lượng dữ liệu", "Xem báo cáo chất lượng dữ liệu và độ tin cậy có thể kỳ vọng."),
    ("3. Dự báo", "Dự báo doanh thu, sản lượng, số khách hàng theo nhiều mô hình tự động chọn."),
    ("4. Khách hàng", "Phân khúc khách hàng theo RFM (nếu có Mã khách hàng)."),
    ("5. Sản phẩm & Giỏ hàng", "Phân tích sản phẩm bán chạy và giỏ hàng (mua cùng nhau)."),
    ("6. Tồn kho", "Đề xuất số lượng cần nhập dựa trên dự báo nhu cầu và tồn kho hiện tại."),
    ("7. Mục tiêu kinh doanh", "Thiết lập hồ sơ doanh nghiệp và chọn mục tiêu: Traffic/Revenue/Profit/Clearance."),
    ("8. Kịch bản Promotion", "Mô phỏng nhiều kịch bản khuyến mãi và so sánh ROI."),
    ("9. AI Recommendation", "Xem đề xuất tốt nhất phù hợp với mục tiêu, kèm giải thích."),
    ("10. Campaign Plan", "Sinh kế hoạch chiến dịch và nội dung Facebook/Zalo/SMS."),
    ("11. Model & Độ tin cậy", "Xem model nào được chọn và vì sao, độ tin cậy dự báo."),
]
cols = st.columns(3)
for i, (title, desc) in enumerate(steps):
    with cols[i % 3]:
        st.markdown(f"**{title}**")
        st.caption(desc)

st.divider()
st.caption(
    "🔒 PromoPilot AI chạy hoàn toàn local trên máy bạn. Dữ liệu giao dịch không được gửi lên "
    "bất kỳ dịch vụ bên thứ ba nào. Xem chi tiết ở README.md mục Data Privacy."
)
