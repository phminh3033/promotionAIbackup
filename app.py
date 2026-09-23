"""PromotionPilot AI — navigation của nền tảng quyết định marketing."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
from dotenv import load_dotenv

from ui import nav
from ui.pages import command_center, data_workspace, decide, execute, forecast, model_info, monitor, prepare, reports, simulate, understand

load_dotenv()
st.set_page_config(page_title="PromotionPilot AI", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

pages = {
    "command": st.Page(command_center.render, title="Command Center", url_path="command-center", default=True),
    "understand": st.Page(understand.render, title="Understand", url_path="understand"),
    "forecast": st.Page(forecast.render, title="Forecast", url_path="forecast"),
    "prepare": st.Page(prepare.render, title="Prepare", url_path="prepare"),
    "simulate": st.Page(simulate.render, title="Simulate", url_path="simulate"),
    "decide": st.Page(decide.render, title="Decide", url_path="decide"),
    "execute": st.Page(execute.render, title="Execute", url_path="execute"),
    "monitor": st.Page(monitor.render, title="Monitor", url_path="monitor"),
    "data": st.Page(data_workspace.render, title="Data", url_path="data"),
    "reports": st.Page(reports.render, title="Reports", url_path="reports"),
    "model": st.Page(model_info.render, title="Model Info", url_path="model-info"),
}
nav.bind(pages)
try:
    navigation = st.navigation(list(pages.values()), position="hidden")
except TypeError:
    navigation = st.navigation(list(pages.values()))
navigation.run()
