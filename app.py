"""PromotionPilot AI — navigation của nền tảng quyết định marketing."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
from dotenv import load_dotenv

from src.utils.demo_access import require_demo_access
from styles.theme import inject_css
from ui import nav
from ui.pages import command_center, decide, execute, forecast, model_info, monitor, prepare, reports, simulate, understand

load_dotenv()
st.set_page_config(
    page_title="PromotionPilot AI",
    page_icon=":material/insights:",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()
# Khôi phục phiên từ đĩa TRƯỚC cổng demo — giữ dữ liệu/kết quả/mã truy cập qua F5.
from src.utils.state import init_session_state

init_session_state()
try:
    from src.utils.session_persistence import inject_workspace_cookie

    inject_workspace_cookie()
except Exception:  # noqa: BLE001
    pass
require_demo_access()

pages = {
    "command": st.Page(command_center.render, title="Tổng quan", url_path="command-center", default=True),
    "understand": st.Page(understand.render, title="Hiểu thị trường", url_path="understand"),
    "forecast": st.Page(forecast.render, title="Dự báo", url_path="forecast"),
    "prepare": st.Page(prepare.render, title="Chuẩn bị", url_path="prepare"),
    "simulate": st.Page(simulate.render, title="Mô phỏng chiến dịch", url_path="simulate"),
    "decide": st.Page(decide.render, title="Quyết định", url_path="decide"),
    "execute": st.Page(execute.render, title="Triển khai", url_path="execute"),
    "monitor": st.Page(monitor.render, title="Học hỏi và tối ưu", url_path="monitor"),
    "reports": st.Page(reports.render, title="Báo cáo", url_path="reports"),
    "model": st.Page(model_info.render, title="Thông tin thêm", url_path="model-info"),
}
nav.bind(pages)
try:
    navigation = st.navigation(list(pages.values()), position="hidden")
except TypeError:
    navigation = st.navigation(list(pages.values()))
navigation.run()
