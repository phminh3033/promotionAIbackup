"""Design tokens và CSS dùng chung. Gradient chỉ trên CTA, thẻ nhấn và accent."""
from __future__ import annotations

import streamlit as st

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"], .stApp, .stMarkdown, button, input, textarea, select {
  font-family: Inter, system-ui, sans-serif;
}
.stApp { background: #F8FAFC; color: #0F172A; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"] { display: none; }
footer { visibility: hidden; }
#MainMenu { visibility: hidden; }

section[data-testid="stSidebar"] {
  background: #FFFFFF;
  border-right: 1px solid #E2E8F0;
  width: 260px;
}
section[data-testid="stSidebar"] > div {
  padding-top: 0.6rem;
}
[data-testid="stHeadingActionElements"], .stHeadingAction { display: none !important; }
[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] { display: none; }

section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"],
section[data-testid="stSidebar"] a {
  border-radius: 12px !important;
  padding: 0.48rem 0.72rem !important;
  margin: 1px 0;
  color: #475569 !important;
  font-weight: 500 !important;
  font-size: 14px !important;
  text-decoration: none !important;
  gap: 8px;
}
section[data-testid="stSidebar"] a[aria-current="page"] {
  background: #EFF6FF !important;
  color: #2563EB !important;
  font-weight: 600 !important;
}
section[data-testid="stSidebar"] a:hover {
  background: #F8FAFC !important;
  color: #1D4ED8 !important;
}
section[data-testid="stSidebar"] a[aria-current="page"]:hover {
  background: #EFF6FF !important;
}

[data-testid="stMain"] .block-container {
  padding: 1.25rem 1.75rem 2.75rem 1.75rem;
  max-width: 100%;
}
[data-testid="stMain"] [data-testid="stVerticalBlock"] { gap: 0.85rem; }
[data-testid="stMain"] [data-testid="column"] { min-width: 0; }
[data-testid="stMain"] [data-testid="stHorizontalBlock"] { gap: 1rem; align-items: stretch; }

.pp-logo { display: flex; gap: 10px; align-items: center; padding: 4px 8px 14px 8px; }
.pp-logo-mark {
  width: 36px; height: 36px; border-radius: 12px; flex: none;
  background: linear-gradient(135deg, #2563EB 0%, #7C3AED 100%);
  display: grid; place-items: center;
}
.pp-logo strong { display: block; font-size: 14px; color: #0F172A; line-height: 1.2; }
.pp-logo span { display: block; font-size: 11px; color: #64748B; font-weight: 500; }
.pp-side-card {
  margin: 16px 8px 8px 8px; padding: 14px 14px 16px 14px; border-radius: 16px; color: white;
  background: linear-gradient(160deg, #2563EB 0%, #7C3AED 100%);
  box-shadow: 0 8px 24px rgba(37, 99, 235, 0.18);
}
.pp-side-card strong { display: block; font-size: 13.5px; line-height: 1.35; margin-bottom: 6px; }
.pp-side-card p { margin: 0; font-size: 11.5px; line-height: 1.4; color: rgba(255,255,255,0.88); }
.pp-side-rule { height: 1px; background: #E2E8F0; margin: 10px 8px; }

.pp-head { margin-bottom: 8px; }
.pp-head-top { display: flex; justify-content: space-between; gap: 12px; align-items: center; margin-bottom: 4px; }
.pp-eyebrow { color: #64748B; font-size: 13px; margin-bottom: 2px; }
.pp-head h1 { margin: 0; font-size: 32px; line-height: 1.25; font-weight: 700; color: #0F172A; letter-spacing: -0.02em; overflow-wrap: anywhere; }
.pp-sub { margin: 6px 0 0 0; color: #475569; font-size: 16px; line-height: 1.5; max-width: 760px; }
.pp-chips { display: flex; flex-wrap: wrap; gap: 8px; justify-content: flex-end; }
.pp-chip {
  display: inline-flex; align-items: center; gap: 6px;
  background: #FFFFFF; border: 1px solid #E2E8F0; color: #475569;
  border-radius: 999px; padding: 5px 10px; font-size: 12px; font-weight: 500;
  box-shadow: 0 1px 2px rgba(15,23,42,0.04);
}
.pp-chip b { color: #0F172A; font-weight: 600; }
.pp-chip.demo { background: #F5F3FF; border-color: #DDD6FE; color: #6D28D9; }

.pp-stagebar {
  background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px;
  box-shadow: 0 1px 2px rgba(15,23,42,0.04), 0 4px 16px rgba(15,23,42,0.04);
  padding: 14px 10px 12px; margin: 16px 0 18px;
}
.pp-stages { display: flex; gap: 6px; align-items: stretch; overflow-x: auto; padding: 2px; }
.pp-stage { min-width: 108px; flex: 1 1 0; text-align: center; position: relative; padding: 8px 6px 10px; border-radius: 12px; }
.pp-stage:not(:last-child)::after {
  content: ""; position: absolute; top: 22px; left: calc(50% + 18px); right: calc(-50% + 18px);
  height: 2px; background: #E2E8F0; z-index: 0;
}
.pp-num {
  width: 30px; height: 30px; border-radius: 999px; margin: 0 auto 6px auto;
  display: grid; place-items: center; font-size: 13px; font-weight: 700;
  background: #E2E8F0; color: #475569; position: relative; z-index: 1;
}
.pp-stage.is-done .pp-num { background: #DBEAFE; color: #1D4ED8; }
.pp-stage.is-done:not(:last-child)::after { background: #93C5FD; }
.pp-stage.is-done .t { color: #1E40AF; }
.pp-stage.is-current {
  background: #EFF6FF; outline: 1px solid #BFDBFE;
  box-shadow: 0 6px 16px rgba(37, 99, 235, 0.14);
}
.pp-stage.is-current .pp-num { background: #2563EB; color: white; box-shadow: 0 0 0 4px #DBEAFE; }
.pp-stage .t {
  display: flex; align-items: center; justify-content: center; gap: 4px;
  font-size: 14px; font-weight: 650; color: #475569; line-height: 1.3;
}
.pp-stage .t svg { flex: none; }
.pp-stage .s { display: block; margin-top: 2px; font-size: 12px; color: #64748B; line-height: 1.3; }
.pp-stage.is-current .t, .pp-stage.is-current .s { color: #1D4ED8; font-weight: 650; }

.pp-card {
  background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px;
  box-shadow: 0 1px 2px rgba(15,23,42,0.05), 0 8px 20px rgba(15,23,42,0.06);
  padding: 16px 18px; min-width: 0; box-sizing: border-box; overflow: hidden;
}
.pp-card:hover { box-shadow: 0 10px 28px rgba(15,23,42,0.1); }
.pp-kpi-grid, .pp-grid-3, .pp-grid-2, .pp-grid-4 { align-items: stretch; }
.pp-kpi-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; margin: 8px 0 16px 0; }
.pp-grid-3 { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; }
.pp-grid-2 { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
.pp-grid-4 { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; }
.pp-kicker { display: flex; align-items: center; gap: 8px; color: #334155; font-size: 14px; font-weight: 650; line-height: 1.35; }
.pp-kicker .en { color: #64748B; font-weight: 500; font-size: 13px; }
.pp-value { font-size: 28px; font-weight: 700; color: #0F172A; letter-spacing: -0.03em; margin: 8px 0 4px 0; line-height: 1.15; overflow-wrap: anywhere; }
.pp-delta { font-size: 13px; font-weight: 600; line-height: 1.35; overflow-wrap: anywhere; }
.pp-delta.up { color: #059669; }
.pp-delta.down { color: #DC2626; }
.pp-delta.flat { color: #64748B; }
.pp-kpi-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 10px; min-width: 0; }
.pp-ico {
  width: 34px; height: 34px; border-radius: 10px; display: grid; place-items: center; flex: none;
}
.pp-chip svg { flex: none; }
.pp-section { display: flex; justify-content: space-between; align-items: flex-end; gap: 12px; margin: 18px 0 12px 0; }
.pp-section h2 { margin: 0; font-size: 20px; font-weight: 700; color: #0F172A; line-height: 1.3; }
.pp-section p { margin: 4px 0 0 0; color: #64748B; font-size: 14px; line-height: 1.45; }
.pp-link { color: #2563EB; font-size: 13px; font-weight: 600; text-decoration: none; }
.pp-badge {
  display: inline-flex; align-items: center; gap: 4px; border-radius: 999px;
  padding: 3px 8px; font-size: 12px; font-weight: 600; line-height: 1.3;
}
.pp-badge.ok { background: #ECFDF5; color: #047857; }
.pp-badge.warn { background: #FFFBEB; color: #B45309; }
.pp-badge.bad { background: #FEF2F2; color: #B91C1C; }
.pp-badge.info { background: #EFF6FF; color: #1D4ED8; }
.pp-badge.muted { background: #F1F5F9; color: #475569; }
.pp-badge.purple { background: #F5F3FF; color: #6D28D9; }
.pp-banner {
  background: #EFF6FF; border: 1px solid #DBEAFE; color: #1E3A8A;
  border-radius: 12px; padding: 10px 14px; font-size: 13.5px; margin: 8px 0 14px 0;
}
.pp-banner.good { background: #ECFDF5; border-color: #A7F3D0; color: #065F46; }
.pp-banner.warn { background: #FFFBEB; border-color: #FDE68A; color: #92400E; }
.pp-list { margin: 8px 0 0 0; padding: 0; list-style: none; }
.pp-list li { display: flex; gap: 8px; align-items: flex-start; font-size: 13.5px; color: #334155; margin: 6px 0; }
.pp-opp-title { font-size: 16px; font-weight: 650; color: #0F172A; margin: 8px 0 4px 0; line-height: 1.35; overflow-wrap: anywhere; }
.pp-muted { color: #64748B; font-size: 14px; line-height: 1.5; overflow-wrap: anywhere; }
.pp-impact { font-size: 20px; font-weight: 700; color: #059669; margin-top: 8px; overflow-wrap: anywhere; }
.pp-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.pp-table th { text-align: left; color: #64748B; font-weight: 650; font-size: 13px; padding: 10px 8px; border-bottom: 1px solid #E2E8F0; white-space: nowrap; }
.pp-table td { padding: 12px 8px; border-bottom: 1px solid #F1F5F9; color: #0F172A; vertical-align: middle; overflow-wrap: anywhere; }
.pp-ring-wrap { display: flex; gap: 16px; align-items: center; }
.pp-ring {
  width: 116px; height: 116px; border-radius: 50%; display: grid; place-items: center; flex: none;
  background: conic-gradient(var(--c) calc(var(--p) * 1%), #E2E8F0 0);
}
.pp-ring span {
  width: 86px; height: 86px; border-radius: 50%; background: white;
  display: grid; place-items: center; font-size: 26px; font-weight: 700; color: #0F172A;
}
.pp-chart-ph {
  height: 260px; border: 1px dashed #E2E8F0; border-radius: 14px; background: #F8FAFC;
  display: grid; place-items: center; color: #94A3B8; font-size: 14px; font-weight: 600;
}
.pp-empty { text-align: center; padding: 28px 16px; color: #64748B; }
.pp-empty h3 { margin: 0 0 6px 0; color: #0F172A; font-size: 16px; }
.pp-metric-mini { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 12px 14px; min-width: 0; }
.pp-metric-mini .l { color: #64748B; font-size: 13px; font-weight: 650; }
.pp-metric-mini .v { color: #0F172A; font-size: 20px; font-weight: 700; margin-top: 4px; line-height: 1.25; overflow-wrap: anywhere; }
.pp-selected { border: 1.5px solid #7C3AED; box-shadow: 0 0 0 3px rgba(124,58,237,0.12); }
.pp-foot { color: #94A3B8; font-size: 12px; margin-top: 18px; }
.pp-hr { height: 1px; background: #E2E8F0; margin: 12px 0; }
.pp-bar { height: 8px; background: #E2E8F0; border-radius: 999px; overflow: hidden; }
.pp-bar > div { height: 100%; border-radius: 999px; background: linear-gradient(90deg, #2563EB, #7C3AED); }
.pp-spark { width: 86px; height: 32px; }
@media (max-width: 860px) {
  .pp-kpi-grid, .pp-grid-4 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .pp-grid-3 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .pp-head-top { flex-direction: column; align-items: flex-start; }
  .pp-chips { justify-content: flex-start; }
}
@media (max-width: 720px) {
  .pp-kpi-grid, .pp-grid-3, .pp-grid-2, .pp-grid-4 { grid-template-columns: 1fr; }
  .pp-head h1 { font-size: 24px; }
}
div[data-testid="stButton"] > button, button[data-testid="stBaseButton-primary"], button[data-testid="stBaseButton-secondary"] {
  border-radius: 12px; font-weight: 600; border: 1px solid transparent;
}
button[data-testid="stBaseButton-primary"] {
  background: linear-gradient(90deg, #2563EB 0%, #7C3AED 100%) !important;
  color: white !important; border: none !important;
}
button[data-testid="stBaseButton-primary"]:hover {
  background: linear-gradient(90deg, #1D4ED8 0%, #6D28D9 100%) !important;
}
button[data-testid="stBaseButton-secondary"] {
  background: #FFFFFF !important; color: #0F172A !important; border: 1px solid #E2E8F0 !important;
}
button[data-testid="stBaseButton-secondary"]:hover { background: #F8FAFC !important; }
button:disabled { opacity: 0.55 !important; }
div[data-testid="stPlotlyChart"],
[data-testid="stDataFrame"],
[data-testid="stExpander"] {
  background: #FFFFFF;
  border: 1px solid #E2E8F0 !important;
  border-radius: 16px !important;
  box-shadow: 0 1px 2px rgba(15,23,42,0.05), 0 8px 20px rgba(15,23,42,0.06);
  overflow: hidden;
}
div[data-testid="stPlotlyChart"] { padding: 8px 8px 0; margin: 4px 0 8px; }
[data-testid="stDataFrame"] { margin: 4px 0 8px; }
.stTabs [data-baseweb="tab-list"] {
  gap: 6px; background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px;
  padding: 6px; box-shadow: 0 1px 2px rgba(15,23,42,0.04);
}
.stTabs [data-baseweb="tab"] {
  border-radius: 10px; padding: 8px 14px; font-size: 14px; font-weight: 600;
}
.stTabs [aria-selected="true"] { background: #EFF6FF !important; color: #1D4ED8 !important; }
[data-testid="stFileUploader"],
[data-testid="stNumberInput"] > div,
div[data-baseweb="select"] > div {
  border-radius: 12px;
}
"""


def inject_css() -> None:
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)
