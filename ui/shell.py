"""Khung ứng dụng: CSS, sidebar, header, thanh 7 bước."""
from __future__ import annotations

from html import escape

import streamlit as st

from services.workflow import dataset_chip, period_chip
from styles.theme import inject_css
from ui.formatters import relative_time
from ui.icons import icon
from ui.nav import NAV, page
from src.utils.state import init_session_state

STAGES = [
    (1, "Understand", "Hiểu thị trường", "compass"),
    (2, "Forecast", "Dự báo", "chart"),
    (3, "Prepare", "Chuẩn bị", "package"),
    (4, "Simulate", "Mô phỏng", "flask"),
    (5, "Decide", "Quyết định", "target"),
    (6, "Execute", "Triển khai", "rocket"),
    (7, "Monitor & Learn", "Theo dõi & học", "activity"),
]

LOGO = """
<div class="pp-logo">
  <div class="pp-logo-mark">
    """ + icon("target", 18).replace('stroke="currentColor"', 'stroke="white"') + """
  </div>
  <div>
    <strong>PromotionPilot AI</strong>
    <span>Smarter Promotions. Bigger Growth.</span>
  </div>
</div>
"""


def render_shell(title: str, subtitle: str, stage: int | None = None, eyebrow: str = "Xin chào!") -> None:
    init_session_state()
    inject_css()
    _sidebar()
    chips = _chips()
    stage_html = _stages(stage) if stage is not None else ""
    st.html(
        f"""
<div class="pp-head">
  <div class="pp-head-top">
    <div class="pp-eyebrow">{escape(eyebrow)}</div>
    <div class="pp-chips">{chips}</div>
  </div>
  <h1>{escape(title)}</h1>
  <p class="pp-sub">{escape(subtitle)}</p>
</div>
{stage_html}
"""
    )


def _chips() -> str:
    updated = relative_time(st.session_state.get("data_loaded_at"))
    return (
        f'<span class="pp-chip demo">{icon("sparkles", 14)} Demo Mode</span>'
        f'<span class="pp-chip">{icon("database", 14)} Dataset: <b>{escape(dataset_chip())}</b></span>'
        f'<span class="pp-chip">{icon("calendar", 14)} Period: <b>{escape(period_chip())}</b></span>'
        f'<span class="pp-chip">{icon("clock", 14)} Cập nhật: <b>{escape(updated)}</b></span>'
    )


def _stages(current: int) -> str:
    parts = ['<div class="pp-stagebar"><div class="pp-stages">']
    for number, label, sub, icon_key in STAGES:
        if current and number < current:
            klass = "pp-stage is-done"
        elif current and number == current:
            klass = "pp-stage is-current"
        else:
            klass = "pp-stage"
        parts.append(
            f'<div class="{klass}"><div class="pp-num">{number}</div>'
            f'<span class="t">{icon(icon_key, 14)}<span>{label}</span></span>'
            f'<span class="s">{sub}</span></div>'
        )
    parts.append("</div></div>")
    return "".join(parts)


def _sidebar() -> None:
    with st.sidebar:
        st.html(LOGO)
        for key, label, _icon_name, _slug in NAV:
            if key == "reports":
                st.html('<div class="pp-side-rule"></div>')
            st.page_link(page(key), label=label)
        st.html(
            """
<div class="pp-side-card">
  <strong>Biến dữ liệu thành tăng trưởng thực tế</strong>
  <p>Các mô hình khoa học hỗ trợ quyết định marketing hiệu quả hơn.</p>
</div>
"""
        )


def continue_button(label: str, target: str, key: str) -> None:
    from ui.nav import goto

    if st.button(label, type="primary", key=key, width="stretch"):
        goto(target)


def data_modal_button(key: str, label: str = "Tải dữ liệu", primary: bool = True) -> None:
    """Mở Data Workspace dạng modal — thay cho trang riêng trong menu."""
    from ui.pages import data_workspace

    if st.button(label, type="primary" if primary else "secondary", key=key, width="stretch"):
        data_workspace.open_modal()
