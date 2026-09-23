"""Đăng ký trang để sidebar và nút điều hướng dùng chung một đối tượng."""
from __future__ import annotations

import streamlit as st

_PAGES: dict = {}

NAV = [
    ("command", "Command Center", ":material/home:"),
    ("understand", "①  Understand", ":material/travel_explore:"),
    ("forecast", "②  Forecast", ":material/monitoring:"),
    ("prepare", "③  Prepare", ":material/inventory_2:"),
    ("simulate", "④  Simulate", ":material/science:"),
    ("decide", "⑤  Decide", ":material/ads_click:"),
    ("execute", "⑥  Execute", ":material/rocket_launch:"),
    ("monitor", "⑦  Monitor", ":material/query_stats:"),
    ("data", "Data", ":material/database:"),
    ("reports", "Reports", ":material/description:"),
    ("model", "Model Info", ":material/info:"),
]


def bind(pages: dict) -> None:
    _PAGES.clear()
    _PAGES.update(pages)


def page(key: str):
    return _PAGES[key]


def goto(key: str) -> None:
    st.switch_page(_PAGES[key])
