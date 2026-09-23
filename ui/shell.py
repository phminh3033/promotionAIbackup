"""Khung ứng dụng: CSS, sidebar, header, thanh 7 bước."""
from __future__ import annotations

import streamlit as st

from services.workflow import dataset_chip, period_chip
from styles.theme import inject_css
from ui.formatters import relative_time
from ui.nav import NAV, page
from src.utils.state import init_session_state

def _svg(paths: str, size: int = 14) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{paths}</svg>'
    )


_ICO = {
    "search": _svg('<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>'),
    "chart": _svg('<path d="M4 19V5"/><path d="M4 19h16"/><path d="m7 14 4-4 3 3 5-6"/>'),
    "box": _svg('<path d="M21 8 12 3 3 8l9 5 9-5Z"/><path d="M3 8v8l9 5 9-5V8"/><path d="M12 13v8"/>'),
    "flask": _svg('<path d="M10 2h4"/><path d="M9 2v6L4.5 18A3 3 0 0 0 7.2 22h9.6a3 3 0 0 0 2.7-4L15 8V2"/>'),
    "target": _svg('<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2"/>'),
    "rocket": _svg('<path d="M5 15c-1 2-1 4 0 5 2 0 4-1 5-2"/><path d="M9 15 15 9"/><path d="M14 4c3 1 6 4 7 7-4 1-8 0-11-3S10 1 14 4Z"/><path d="M5 19c2 0 3-2 3-3"/>'),
    "pulse": _svg('<path d="M3 12h4l2-5 4 10 2-5h6"/>'),
    "spark": _svg('<path d="m12 3 1.6 4.8L18.5 9.5 14 12.2 15.2 17 12 14.4 8.8 17 10 12.2 5.5 9.5l4.9-1.7Z"/>'),
    "db": _svg('<ellipse cx="12" cy="6" rx="7" ry="3"/><path d="M5 6v6c0 1.7 3.1 3 7 3s7-1.3 7-3V6"/><path d="M5 12v6c0 1.7 3.1 3 7 3s7-1.3 7-3v-6"/>'),
    "cal": _svg('<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>'),
    "clock": _svg('<circle cx="12" cy="12" r="8"/><path d="M12 8v5l3 2"/>'),
}

STAGES = [
    (1, "Understand", "Hiểu thị trường", "search"),
    (2, "Forecast", "Dự báo", "chart"),
    (3, "Prepare", "Chuẩn bị", "box"),
    (4, "Simulate", "Mô phỏng", "flask"),
    (5, "Decide", "Quyết định", "target"),
    (6, "Execute", "Triển khai", "rocket"),
    (7, "Monitor", "Theo dõi & tối ưu", "pulse"),
]

LOGO = """
<div class="pp-logo">
  <div class="pp-logo-mark">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="8" stroke="white" stroke-width="1.8"/>
      <circle cx="12" cy="12" r="2" fill="white"/>
      <path d="M12 2v3M12 19v3M2 12h3M19 12h3" stroke="white" stroke-width="1.8" stroke-linecap="round"/>
    </svg>
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
    st.markdown(
        f"""
<div class="pp-head">
  <div class="pp-head-top">
    <div class="pp-eyebrow">{eyebrow}</div>
    <div class="pp-chips">{chips}</div>
  </div>
  <h1>{title}</h1>
  <p class="pp-sub">{subtitle}</p>
</div>
{stage_html}
""",
        unsafe_allow_html=True,
    )


def _chips() -> str:
    updated = relative_time(st.session_state.get("data_loaded_at"))
    return (
        f'<span class="pp-chip demo">{_ICO["spark"]} Demo Mode</span>'
        f'<span class="pp-chip">{_ICO["db"]} Dataset: <b>{dataset_chip()}</b></span>'
        f'<span class="pp-chip">{_ICO["cal"]} Period: <b>{period_chip()}</b></span>'
        f'<span class="pp-chip">{_ICO["clock"]} Cập nhật: <b>{updated}</b></span>'
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
            f'<span class="t">{_ICO[icon_key]}<span>{label}</span></span>'
            f'<span class="s">{sub}</span></div>'
        )
    parts.append("</div></div>")
    return "".join(parts)


def _sidebar() -> None:
    with st.sidebar:
        st.markdown(LOGO, unsafe_allow_html=True)
        for key, label, icon in NAV:
            if key == "data":
                st.markdown('<div class="pp-side-rule"></div>', unsafe_allow_html=True)
            st.page_link(page(key), label=label, icon=icon)
        st.markdown(
            """
<div class="pp-side-card">
  <strong>Biến dữ liệu thành tăng trưởng thực tế</strong>
  <p>Các mô hình khoa học hỗ trợ quyết định marketing hiệu quả hơn.</p>
</div>
""",
            unsafe_allow_html=True,
        )


def continue_button(label: str, target: str, key: str) -> None:
    from ui.nav import goto

    if st.button(label, type="primary", key=key, use_container_width=True):
        goto(target)


def need_data(key: str) -> bool:
    from src.utils.state import has_data

    if has_data():
        return False
    st.markdown(
        """
<div class="pp-card pp-empty">
  <h3>Chưa có dữ liệu để phân tích</h3>
  <p>Hãy dùng dữ liệu mẫu hoặc tải file bán hàng ở Data Workspace. Các màn sau dùng chung một bộ dữ liệu của phiên làm việc.</p>
</div>
""",
        unsafe_allow_html=True,
    )
    continue_button("Tới Data Workspace", "data", key=key)
    return True
