"""Khung ứng dụng: CSS, sidebar, header, thanh 7 bước."""
from __future__ import annotations

from html import escape

import streamlit as st

from services.workflow import dataset_chip, period_chip
from styles.theme import inject_css
from ui.formatters import relative_time
from ui.icons import icon
from ui.nav import NAV, goto, page
from src.utils.state import init_session_state

STAGES = [
    (1, "Hiểu thị trường", "Bối cảnh & insight", "compass"),
    (2, "Dự báo", "Nhu cầu & doanh thu", "chart"),
    (3, "Chuẩn bị", "Tồn kho & ngân sách", "package"),
    (4, "Mô phỏng chiến dịch", "So sánh phương án", "flask"),
    (5, "Quyết định", "Chọn phương án", "target"),
    (6, "Triển khai", "Kế hoạch thực thi", "rocket"),
    (7, "Học hỏi và tối ưu", "Theo dõi kết quả", "activity"),
]

# Map stage → page key — dùng để Simulate biết user vừa navigate về từ trang khác.
_STAGE_PAGE_KEY = {
    1: "understand",
    2: "forecast",
    3: "prepare",
    4: "simulate",
    5: "decide",
    6: "execute",
    7: "monitor",
}

LOGO = """
<div class="pp-logo">
  <div class="pp-logo-mark">
    """ + icon("target", 18, color="white") + """
  </div>
  <div>
    <strong>PromotionPilot AI</strong>
    <span>Smarter Promotions. Bigger Growth.</span>
  </div>
</div>
"""


def render_shell(title: str, subtitle: str, stage: int | None = None, eyebrow: str = "Xin chào!") -> None:
    from src.utils.state import persist_session_inputs

    init_session_state()
    # Đồng bộ widget → session mỗi lần vào trang (kể cả sau khi click left menu).
    persist_session_inputs()
    if stage in _STAGE_PAGE_KEY:
        st.session_state["_pp_active_page"] = _STAGE_PAGE_KEY[stage]
    try:
        from src.utils.session_persistence import inject_workspace_cookie

        inject_workspace_cookie()
    except Exception:  # noqa: BLE001
        pass
    inject_css()
    _sidebar()
    chips = _chips()
    stage_html = _stages(stage) if stage is not None else ""
    menu_icon = icon("menu", 20)
    st.html(
        f"""
<div class="pp-head">
  <div class="pp-head-top">
    <div class="pp-eyebrow-row">
      <div class="pp-menu-btn" role="button" tabindex="0" aria-label="Mở menu điều hướng">{menu_icon}</div>
      <div class="pp-eyebrow">{escape(eyebrow)}</div>
    </div>
    <div class="pp-chips">{chips}</div>
  </div>
  <h1>{escape(title)}</h1>
  <p class="pp-sub">{escape(subtitle)}</p>
</div>
{stage_html}
"""
    )
    _wire_mobile_menu()


def _chips() -> str:
    updated = relative_time(st.session_state.get("data_loaded_at"))
    return (
        f'<span class="pp-chip demo">{icon("sparkles", 14)} Demo Mode</span>'
        f'<span class="pp-chip">{icon("database", 14)} Dataset: <b>{escape(dataset_chip())}</b></span>'
        f'<span class="pp-chip">{icon("calendar", 14)} Period: <b>{escape(period_chip())}</b></span>'
        f'<span class="pp-chip">{icon("clock", 14)} Cập nhật: <b>{escape(updated)}</b></span>'
    )


def _stages(current: int) -> str:
    """Thanh 7 bước — chỉ hiển thị tiến trình, không click điều hướng."""
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
            f'<span class="t">{icon(icon_key, 14)}<span>{escape(label)}</span></span>'
            f'<span class="s">{escape(sub)}</span></div>'
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


def _wire_mobile_menu() -> None:
    """Nối nút hamburger (chỉ hiện trên mobile) với toggle sidebar gốc của Streamlit."""
    import streamlit.components.v1 as components

    components.html(
        """
<script>
(function () {
  var doc = window.parent.document;
  if (doc.documentElement.dataset.ppMenuWired === "1") return;
  doc.documentElement.dataset.ppMenuWired = "1";
  doc.addEventListener("click", function (e) {
    var t = e.target;
    if (!t || !t.closest) return;
    var btn = t.closest(".pp-menu-btn");
    if (!btn) return;
    e.preventDefault();
    e.stopPropagation();
    var sidebar = doc.querySelector('section[data-testid="stSidebar"]');
    var collapse = doc.querySelector(
      '[data-testid="stSidebarCollapseButton"] button, [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"]'
    );
    var expand = doc.querySelector(
      '[data-testid="stSidebarCollapsedControl"] button, [data-testid="stSidebarCollapsedControl"]'
    );
    var open = false;
    if (sidebar) {
      var aria = sidebar.getAttribute("aria-expanded");
      var w = 0;
      try { w = sidebar.getBoundingClientRect().width; } catch (err) {}
      open = aria === "true" || w > 40;
    }
    if (open && collapse) { collapse.click(); return; }
    if (expand) expand.click();
  }, true);
  doc.addEventListener("keydown", function (e) {
    if (e.key !== "Enter" && e.key !== " ") return;
    var t = e.target;
    if (!t || !t.classList || !t.classList.contains("pp-menu-btn")) return;
    e.preventDefault();
    t.click();
  }, true);
})();
</script>
""",
        height=0,
        width=0,
    )


def continue_button(label: str, target: str, key: str) -> None:
    """Nút chuyển bước — full width, cùng độ dài giữa các trang."""
    st.markdown('<div class="pp-continue-row" aria-hidden="true"></div>', unsafe_allow_html=True)
    if st.button(label, type="primary", key=key, width="stretch"):
        goto(target)


def data_modal_button(key: str, label: str = "Tải dữ liệu", primary: bool = True) -> None:
    """Mở Data Workspace dạng modal — thay cho trang riêng trong menu."""
    from ui.pages import data_workspace

    if st.button(label, type="primary" if primary else "secondary", key=key, width="stretch"):
        data_workspace.open_modal()
