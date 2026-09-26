"""Đăng ký trang để sidebar và nút điều hướng dùng chung một đối tượng."""
from __future__ import annotations

import streamlit as st

_PAGES: dict = {}

# key, nhãn, icon Lucide, url_path — url_path phải khớp st.Page trong app.py
NAV = [
    ("command", "Tổng quan", "home", "command-center"),
    ("understand", "Hiểu thị trường", "compass", "understand"),
    ("forecast", "Dự báo", "chart", "forecast"),
    ("prepare", "Chuẩn bị", "package", "prepare"),
    ("simulate", "Mô phỏng chiến dịch", "flask", "simulate"),
    ("decide", "Quyết định", "target", "decide"),
    ("execute", "Triển khai", "rocket", "execute"),
    ("monitor", "Học hỏi và tối ưu", "activity", "monitor"),
    ("reports", "Báo cáo", "file", "reports"),
    ("model", "Thông tin thêm", "info", "model-info"),
]


def bind(pages: dict) -> None:
    _PAGES.clear()
    _PAGES.update(pages)


def page(key: str):
    return _PAGES[key]


def goto(key: str) -> None:
    """Chuyển trang — đồng bộ input phiên trước để không mất dữ liệu/kết quả mô hình."""
    from src.utils.state import persist_session_inputs

    persist_session_inputs()
    st.switch_page(_PAGES[key])
