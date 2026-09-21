"""PromoPilot AI — điểm khởi chạy chính, định nghĩa navigation với tên tiếng Việt đầy đủ."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st

st.set_page_config(page_title="PromoPilot AI", page_icon="🎯", layout="wide")

PAGES_DIR = Path(__file__).resolve().parent / "pages"

pages = [
    st.Page(PAGES_DIR / "0_Tong_quan.py", title="Tổng quan", icon="🏠", default=True),
    st.Page(PAGES_DIR / "1_Tai_du_lieu.py", title="Tải dữ liệu", icon="📤"),
    st.Page(PAGES_DIR / "2_Chat_luong_du_lieu.py", title="Chất lượng dữ liệu", icon="✅"),
    st.Page(PAGES_DIR / "3_Du_bao.py", title="Dự báo", icon="📈"),
    st.Page(PAGES_DIR / "4_Khach_hang.py", title="Khách hàng", icon="👥"),
    st.Page(PAGES_DIR / "5_San_pham_Gio_hang.py", title="Sản phẩm & Giỏ hàng", icon="🛒"),
    st.Page(PAGES_DIR / "6_Ton_kho.py", title="Tồn kho", icon="📦"),
    st.Page(PAGES_DIR / "7_Muc_tieu_kinh_doanh.py", title="Mục tiêu kinh doanh", icon="🎯"),
    st.Page(PAGES_DIR / "8_Kich_ban_Promotion.py", title="Kịch bản Promotion", icon="🎁"),
    st.Page(PAGES_DIR / "9_AI_Recommendation.py", title="AI Recommendation", icon="🤖"),
    st.Page(PAGES_DIR / "10_Campaign_Plan.py", title="Campaign Plan", icon="📋"),
    st.Page(PAGES_DIR / "11_Model_Do_tin_cay.py", title="Model & Độ tin cậy", icon="🧪"),
]

nav = st.navigation(pages)
nav.run()
