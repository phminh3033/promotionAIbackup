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
  display: flex !important;
  align-items: center !important;
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
.pp-stage { min-width: 0; flex: 1 1 0; text-align: center; position: relative; padding: 8px 4px 10px; border-radius: 12px; }
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
  box-shadow: 0 1px 2px rgba(15,23,42,0.04), 0 8px 24px rgba(15,23,42,0.04);
  padding: 16px 18px; min-width: 0; box-sizing: border-box; overflow: hidden;
}
.pp-kpi-grid, .pp-grid-3, .pp-grid-2, .pp-grid-4 { align-items: stretch; }
.pp-kpi-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; margin: 8px 0 16px 0; }
.pp-grid-3 { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; }
.pp-grid-2 { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
.pp-grid-4 { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; }
.pp-kicker { display: flex; align-items: center; gap: 8px; color: #334155; font-size: 14px; font-weight: 650; line-height: 1.35; }
.pp-kicker .en { color: #64748B; font-weight: 500; font-size: 13px; }
.pp-value { font-size: 28px; font-weight: 700; color: #0F172A; letter-spacing: -0.03em; margin: 8px 0 4px 0; line-height: 1.15; overflow-wrap: anywhere; }
.pp-value.is-compact { font-size: 22px; }
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
.pp-card .pp-section { margin: 0 0 10px 0; }
.pp-section h2 { margin: 0; font-size: 18px; font-weight: 650; color: #0F172A; line-height: 1.3; display: flex; align-items: center; }
.pp-sec-ico { display: inline-flex; margin-right: 8px; color: #2563EB; }
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
.pp-info-banner {
  display: flex; gap: 14px; align-items: flex-start;
  background: #EFF6FF; border: 1px solid #DBEAFE; border-radius: 14px;
  padding: 14px 16px; margin: 4px 0 18px 0;
}
.pp-info-ico {
  width: 40px; height: 40px; border-radius: 999px; flex: none;
  display: grid; place-items: center; background: #DBEAFE; color: #2563EB;
}
.pp-info-title { font-size: 15px; font-weight: 650; color: #1E3A8A; line-height: 1.35; }
.pp-info-desc { margin: 4px 0 0 0; color: #475569; font-size: 13.5px; line-height: 1.5; }
.pp-insight-card { display: flex; flex-direction: column; gap: 10px; min-height: 118px; }
.pp-insight-head { display: flex; gap: 12px; align-items: flex-start; }
.pp-insight-ico {
  width: 46px; height: 46px; border-radius: 12px; display: grid; place-items: center; flex: none;
}
.pp-insight-ico.accent-green { background: #ECFDF5; color: #059669; }
.pp-insight-ico.accent-purple { background: #F5F3FF; color: #7C3AED; }
.pp-insight-ico.accent-pink { background: #FDF2F8; color: #DB2777; }
.pp-insight-ico.accent-blue { background: #EFF6FF; color: #2563EB; }
.pp-insight-ico.accent-orange { background: #FFF7ED; color: #EA580C; }
.pp-insight-title { font-size: 15px; font-weight: 650; color: #0F172A; line-height: 1.3; }
.pp-insight-sub { margin-top: 2px; font-size: 12.5px; color: #64748B; line-height: 1.35; }
.pp-insight-desc { margin: 0; color: #475569; font-size: 13.5px; line-height: 1.5; flex: 1; }
.pp-insight-foot { display: flex; align-items: center; min-height: 24px; }
.pp-model-insight {
  background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px;
  box-shadow: 0 1px 2px rgba(15,23,42,0.04), 0 8px 24px rgba(15,23,42,0.04);
  padding: 18px 20px; margin: 8px 0 8px 0;
}
.pp-mi-head { margin-bottom: 14px; }
.pp-mi-title {
  display: flex; align-items: center; gap: 8px;
  font-size: 17px; font-weight: 650; color: #0F172A;
}
.pp-mi-title svg { color: #7C3AED; }
.pp-mi-head > p { margin: 4px 0 0 0; color: #64748B; font-size: 13.5px; }
.pp-mi-grid {
  display: grid; grid-template-columns: minmax(0, 1.5fr) minmax(0, 1fr) minmax(220px, 0.85fr);
  gap: 16px; align-items: stretch;
}
.pp-mi-main, .pp-mi-factors, .pp-mi-conf {
  min-width: 0; border: 1px solid #E2E8F0; border-radius: 14px; padding: 14px;
}
.pp-mi-main { background: #F5F3FF; border-color: #EDE9FE; }
.pp-mi-factors, .pp-mi-conf { background: #FFFFFF; }
.pp-mi-quote {
  display: flex; gap: 10px; align-items: flex-start;
  color: #4C1D95; font-size: 14.5px; font-weight: 600; line-height: 1.55;
}
.pp-mi-quote svg { flex: none; color: #7C3AED; margin-top: 2px; }
.pp-contrib { margin: 10px 0 0 0; }
.pp-contrib-row {
  display: flex; justify-content: space-between; gap: 8px;
  font-size: 12.5px; color: #334155; margin-bottom: 4px;
}
.pp-contrib-row b { color: #0F172A; font-weight: 650; }
.pp-contrib-track {
  height: 8px; background: #E2E8F0; border-radius: 999px; overflow: hidden;
}
.pp-contrib-track > div {
  height: 100%; border-radius: 999px;
  background: linear-gradient(90deg, #2563EB, #7C3AED);
}
.pp-conf-ring {
  width: 112px; height: 112px; border-radius: 50%; margin: 10px auto 8px;
  display: grid; place-items: center;
  background: conic-gradient(#7C3AED calc(var(--p) * 1%), #E2E8F0 0);
}
.pp-conf-ring span {
  width: 82px; height: 82px; border-radius: 50%; background: #FFFFFF;
  display: grid; place-items: center; font-size: 24px; font-weight: 700; color: #0F172A;
}
.pp-conf-empty {
  width: 112px; height: 112px; border-radius: 50%; margin: 10px auto 8px;
  border: 8px solid #E2E8F0; display: grid; place-items: center; text-align: center;
}
.pp-conf-empty span { font-size: 22px; font-weight: 700; color: #94A3B8; }
.pp-conf-empty small { display: block; font-size: 11px; color: #94A3B8; }
.pp-mi-conf .pp-muted { text-align: center; margin-top: 4px; }
.pp-actions {
  display: flex; justify-content: space-between; align-items: center;
  gap: 12px; margin: 18px 0 8px 0; flex-wrap: wrap;
}
[data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] button[data-testid="stBaseButton-secondary"] {
  height: 34px !important; min-height: 34px !important;
  padding: 0 12px !important; font-size: 13px !important; font-weight: 600 !important;
  background: #FFFFFF !important; color: #0F172A !important; border: 1px solid #E2E8F0 !important;
}
[data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] button[data-testid="stBaseButton-secondary"]:hover {
  background: #F8FAFC !important;
}
[data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"]:hover {
  box-shadow: 0 4px 16px rgba(15,23,42,0.08);
  transform: translateY(-1px);
  transition: box-shadow 0.15s ease, transform 0.15s ease;
}
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
.pp-meta { margin-top: 8px; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.pp-stack > .pp-metric-mini + .pp-metric-mini { margin-top: 8px; }
.pp-def { margin: 0 0 10px 0; }
.pp-def b { display: block; font-size: 12px; font-weight: 650; color: #64748B; margin-bottom: 2px; }
.pp-def span { color: #0F172A; font-size: 14px; font-weight: 600; }
.pp-scroll { overflow-x: auto; }
.pp-table-card { padding-bottom: 6px; }
.pp-gate { max-width: 440px; margin: 10vh auto 8px; text-align: center; }
.pp-gate h2 { margin: 8px 0 4px; font-size: 22px; color: #0F172A; }
.pp-logo-center { justify-content: center; padding-bottom: 4px; }
.pp-hr { height: 1px; background: #E2E8F0; margin: 12px 0; }
.pp-bar { height: 8px; background: #E2E8F0; border-radius: 999px; overflow: hidden; }
.pp-bar > div { height: 100%; border-radius: 999px; background: linear-gradient(90deg, #2563EB, #7C3AED); }
.pp-spark { width: 86px; height: 32px; }
@media (max-width: 1399px) {
  .pp-mi-grid { grid-template-columns: 1fr 1fr; }
  .pp-mi-main { grid-column: 1 / -1; }
}
@media (max-width: 860px) {
  .pp-kpi-grid, .pp-grid-4 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .pp-grid-3 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .pp-head-top { flex-direction: column; align-items: flex-start; }
  .pp-chips { justify-content: flex-start; }
  .pp-mi-grid { grid-template-columns: 1fr; }
}
@media (max-width: 720px) {
  .pp-kpi-grid, .pp-grid-3, .pp-grid-2, .pp-grid-4 { grid-template-columns: 1fr; }
  .pp-head h1 { font-size: 24px; }
  .pp-actions { flex-direction: column; align-items: stretch; }
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
div[data-testid="stPlotlyChart"] {
  background: #FFFFFF;
  border: none !important;
  border-radius: 16px;
  box-shadow: 0 1px 2px rgba(15,23,42,0.04);
  padding: 4px 12px 0;
  margin: 4px 0 8px;
}
[data-testid="stDataFrame"],
[data-testid="stExpander"] {
  background: #FFFFFF;
  border: 1px solid #E2E8F0 !important;
  border-radius: 14px !important;
  box-shadow: 0 1px 2px rgba(15,23,42,0.04);
  overflow: hidden;
}
[data-testid="stDataFrame"] { margin: 4px 0 8px; }
.js-plotly-plot .plotly .modebar { display: none !important; }
.stTabs [data-baseweb="tab-list"] {
  gap: 4px; background: #F1F5F9; border: none; border-radius: 12px;
  padding: 4px; box-shadow: none;
}
.stTabs [data-baseweb="tab"] {
  border-radius: 8px; padding: 8px 14px; font-size: 14px; font-weight: 600; color: #64748B;
}
.stTabs [aria-selected="true"] {
  background: #FFFFFF !important; color: #0F172A !important;
  box-shadow: 0 1px 2px rgba(15,23,42,0.06);
}
[data-testid="stFileUploader"],
[data-testid="stNumberInput"] > div,
div[data-baseweb="select"] > div {
  border-radius: 12px;
}

/* Card có nút bên trong: dùng st.container(border=True) nên style theo pp-card */
[data-testid="stVerticalBlockBorderWrapper"] {
  background: #FFFFFF; border-radius: 16px;
  border: 1px solid #E2E8F0 !important;
  box-shadow: 0 1px 2px rgba(15,23,42,0.04), 0 8px 24px rgba(15,23,42,0.04);
  height: 100%;
}
[data-testid="stMain"] [data-testid="column"] > [data-testid="stVerticalBlock"] { height: 100%; }
.pp-card-head { display: flex; flex-direction: column; gap: 6px; min-height: 134px; }
.pp-card-head > div:last-child { margin-top: auto; }
.pp-card-head p { margin: 0; }

div[data-testid="stDialog"] div[role="dialog"] {
  border-radius: 18px; border: 1px solid #E2E8F0;
  box-shadow: 0 24px 60px rgba(15,23,42,0.18);
  width: min(960px, 92vw); max-width: 92vw;
}
div[data-testid="stDialog"] h2 { font-size: 22px; font-weight: 700; color: #0F172A; }
div[data-testid="stDialog"] .pp-grid-2,
div[data-testid="stDialog"] .pp-grid-3,
div[data-testid="stDialog"] .pp-grid-4 { grid-template-columns: 1fr; }
div[data-testid="stDialog"] [data-testid="stVerticalBlockBorderWrapper"] { box-shadow: none; }
"""


def inject_css() -> None:
    from ui.icons import sidebar_icon_css
    from ui.nav import NAV

    extra = sidebar_icon_css([(slug, name) for _key, _label, name, slug in NAV])
    st.html(f"<style>{CSS}\n{extra}\n{_active_nav_css()}</style>")


def _active_nav_css() -> str:
    from ui.nav import NAV

    try:
        url = str(st.context.url or "")
    except Exception:
        return ""
    slug = url.split("?")[0].rstrip("/").split("/")[-1]
    known = {item[3] for item in NAV}
    if slug not in known:
        slug = "command-center"
    selector = "a[href='']" if slug == "command-center" else f"a[href='{slug}']"
    return (
        "section[data-testid='stSidebar'] "
        f"{selector} {{background:#EFF6FF !important;color:#2563EB !important;font-weight:600 !important;}}"
    )
