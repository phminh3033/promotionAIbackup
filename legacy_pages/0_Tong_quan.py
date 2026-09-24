"""Trang Tổng quan (Trang chủ) của PromotionPilot AI."""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from dotenv import load_dotenv

from src.business.profile import BusinessProfile
from src.data.loader import load_raw_file
from src.data.mapper import apply_mapping, detect_capabilities, suggest_mapping, validate_mapping
from src.data.quality import run_quality_check
from src.utils.state import has_data, init_session_state

load_dotenv()
init_session_state()

DEMO_ACCESS_CODE = os.getenv("DEMO_ACCESS_CODE", "").strip()

st.markdown(
    """
<div style="text-align:center; padding: 1.2rem 0 0.4rem 0;">
  <h1 style="margin-bottom:0;">🧭 PromotionPilot AI</h1>
  <p style="font-size:1.05rem; color:#4B5563; max-width:720px; margin:0.4rem auto 0 auto;">
  Biến dữ liệu kinh doanh và hiểu biết địa phương thành quyết định Marketing có thể
  <b>dự báo, mô phỏng, triển khai và liên tục tối ưu</b>.
  </p>
</div>
""",
    unsafe_allow_html=True,
)

if DEMO_ACCESS_CODE and not st.session_state.get("demo_access_granted"):
    st.info("🔐 Đây là bản demo giới hạn truy cập. Nhập mã demo được cung cấp để tiếp tục.")
    code_input = st.text_input("Mã truy cập demo", type="password")
    if st.button("Xác nhận"):
        if code_input.strip() == DEMO_ACCESS_CODE:
            st.session_state["demo_access_granted"] = True
            st.rerun()
        else:
            st.error("Mã truy cập không đúng. Vui lòng liên hệ đội ngũ demo để được cấp mã.")
    st.stop()

st.divider()

col1, col2, col3 = st.columns(3)
with col1:
    st.subheader("▶️ Dùng dữ liệu mẫu")
    st.caption("Trải nghiệm ngay với dữ liệu nhà thuốc mẫu (Pharmacity demo) — không cần upload.")
    use_demo = st.button("Dùng dữ liệu Pharmacity mẫu", type="primary", use_container_width=True)
with col2:
    st.subheader("📥 Tải file Excel mẫu")
    st.caption("Tải về, tự điền dữ liệu doanh nghiệp bạn theo đúng cấu trúc, rồi upload lại.")
    template_path = Path(__file__).resolve().parent.parent / "data" / "mau_du_lieu_promotionpilot.xlsx"
    if template_path.exists():
        st.download_button(
            "Tải file Excel mẫu (.xlsx)",
            data=template_path.read_bytes(),
            file_name="mau_du_lieu_promotionpilot.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    else:
        st.warning("Chưa sinh file mẫu. Chạy `python scripts/generate_pharmacity_demo.py`.")
with col3:
    st.subheader("📤 Upload dữ liệu của bạn")
    st.caption("Đã có file Excel/CSV bán hàng thật? Vào thẳng trang Tải dữ liệu để upload.")
    st.page_link("pages/1_Tai_du_lieu.py", label="Đi tới trang Tải dữ liệu →", use_container_width=True)

if use_demo:
    demo_path = Path(__file__).resolve().parent.parent / "data" / "pharmacity_demo.csv"
    if not demo_path.exists():
        st.error("Không tìm thấy file dữ liệu demo. Vui lòng chạy `python scripts/generate_pharmacity_demo.py` trước.")
    else:
        with st.spinner("Đang tải và xử lý dữ liệu demo (~360.000 dòng)..."):
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
                st.session_state["business_profile"] = BusinessProfile.with_yaml_defaults(
                    business_name="Nhà thuốc Demo (Pharmacity-style)",
                    industry="Dược phẩm / Nhà thuốc",
                )
        st.success(
            f"✅ Đã tải dữ liệu demo: {len(clean_df):,} dòng, điểm chất lượng {report.score}/100. "
            "Hãy sang trang **Local Context** hoặc **Dự báo** ở thanh điều hướng bên trái."
        )
        st.rerun()

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

    with st.expander("Module khả dụng với dữ liệu hiện tại"):
        status_cols = st.columns(4)
        for i, (module_name, (enabled, reason)) in enumerate(caps.module_status().items()):
            with status_cols[i % 4]:
                icon = "✅" if enabled else "⛔"
                st.write(f"{icon} **{module_name}**")
                if not enabled:
                    st.caption(reason)
else:
    st.info("Chưa có dữ liệu nào được tải. Hãy dùng dữ liệu mẫu ở trên hoặc vào trang **Tải dữ liệu**.")

st.divider()
st.subheader("🧭 Quy trình 7 bước của PromotionPilot AI")
flow_steps = [
    ("1️⃣ UNDERSTAND", "Hiểu nhu cầu địa phương", "Local Context + Chất lượng dữ liệu"),
    ("2️⃣ FORECAST", "Dự báo demand, traffic, doanh thu", "Trang Dự báo"),
    ("3️⃣ PREPARE", "Chuẩn bị tồn kho, nhân sự, ngân sách", "Trang Tồn kho + Execution Plan"),
    ("4️⃣ SIMULATE", "Mô phỏng giá / khuyến mãi / thương hiệu", "Trang Kịch bản Promotion"),
    ("5️⃣ DECIDE", "Chọn phương án tốt nhất", "Trang AI Recommendation"),
    ("6️⃣ EXECUTE", "Tạo kế hoạch triển khai", "Trang Execution Plan"),
    ("7️⃣ MONITOR & LEARN", "Theo dõi, cảnh báo, tối ưu", "Trang Campaign Monitor + Alerts"),
]
cols = st.columns(4)
for i, (step, desc, page) in enumerate(flow_steps):
    with cols[i % 4]:
        with st.container(border=True):
            st.markdown(f"**{step}**")
            st.caption(desc)
            st.caption(f"📍 {page}")

st.divider()
st.caption(
    "🔒 PromotionPilot AI ưu tiên chạy local. Dữ liệu giao dịch chi tiết không được gửi cho bất kỳ "
    "dịch vụ LLM bên ngoài nào — chỉ số liệu tổng hợp (aggregated) mới được dùng khi sinh nội dung "
    "campaign. Xem README.md mục Privacy."
)
st.caption(
    "⚠️ Khuyến nghị của hệ thống là công cụ hỗ trợ quyết định, không thay thế quyết định kinh doanh "
    "cuối cùng của doanh nghiệp."
)
