"""Cổng mã truy cập demo công khai (DEMO_ACCESS_CODE)."""
from __future__ import annotations

import os

import streamlit as st


def require_demo_access() -> None:
    """Chặn toàn bộ app nếu có mã và chưa xác nhận. Gọi sớm trong app.py."""
    code = os.getenv("DEMO_ACCESS_CODE", "").strip()
    if not code:
        return
    if st.session_state.get("demo_access_granted"):
        return

    st.markdown(
        """
<div style="max-width:420px;margin:4rem auto;text-align:center">
  <h2 style="margin-bottom:0.4rem">PromotionPilot AI</h2>
  <p style="color:#64748B">Bản demo giới hạn truy cập. Nhập mã được cung cấp để tiếp tục.</p>
</div>
""",
        unsafe_allow_html=True,
    )
    col = st.columns([1, 1.4, 1])[1]
    with col:
        code_input = st.text_input("Mã truy cập demo", type="password", label_visibility="collapsed", placeholder="Nhập mã demo")
        if st.button("Xác nhận", type="primary", use_container_width=True):
            if code_input.strip() == code:
                st.session_state["demo_access_granted"] = True
                st.rerun()
            st.error("Mã truy cập không đúng. Vui lòng liên hệ đội ngũ demo.")
    st.stop()
