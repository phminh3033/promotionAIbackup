"""Đăng ký trang để sidebar và nút điều hướng dùng chung một đối tượng."""
from __future__ import annotations

import streamlit as st

_PAGES: dict = {}

# key, nhãn, icon Lucide, url_path — url_path phải khớp st.Page trong app.py
NAV = [
    ("command", "Command Center", "home", "command-center"),
    ("understand", "Understand", "compass", "understand"),
    ("forecast", "Forecast", "chart", "forecast"),
    ("prepare", "Prepare", "package", "prepare"),
    ("simulate", "Simulate", "flask", "simulate"),
    ("decide", "Decide", "target", "decide"),
    ("execute", "Execute", "rocket", "execute"),
    ("monitor", "Monitor", "activity", "monitor"),
    ("reports", "Reports", "file", "reports"),
    ("model", "Model Info", "info", "model-info"),
]


def bind(pages: dict) -> None:
    _PAGES.clear()
    _PAGES.update(pages)


def page(key: str):
    return _PAGES[key]


def goto(key: str) -> None:
    st.switch_page(_PAGES[key])
