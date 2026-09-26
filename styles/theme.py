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
  padding-top: 0.15rem;
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
.pp-stage {
  min-width: 0; flex: 1 1 0; text-align: center; position: relative;
  padding: 8px 4px 10px; border-radius: 12px;
  pointer-events: none; user-select: none;
}
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
.pp-stage .t .pp-icon { flex: none; }
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
.pp-chip .pp-icon { flex: none; }
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
.pp-mi-title .pp-icon { color: #7C3AED; }
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
.pp-mi-quote .pp-icon { flex: none; color: #7C3AED; margin-top: 2px; }
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
  background: transparent !important;
}
.stTabs [aria-selected="true"] {
  background: #FFFFFF !important; color: #2563EB !important;
  box-shadow: 0 1px 2px rgba(15,23,42,0.06);
  border-bottom: 2px solid #2563EB !important;
}

/* —— Forecast page —— */
.pp-chart-head { display: flex; gap: 12px; align-items: flex-start; margin-bottom: 4px; }
.pp-chart-head-ico {
  width: 40px; height: 40px; border-radius: 12px; flex: none;
  display: grid; place-items: center; background: #F5F3FF; color: #7C3AED;
}
.pp-chart-head-title { font-size: 16px; font-weight: 650; color: #0F172A; line-height: 1.3; }
.pp-chart-head-sub { margin-top: 2px; font-size: 13px; color: #64748B; line-height: 1.4; }

.pp-forecast-summary { display: flex; flex-direction: column; gap: 12px; height: 100%; min-height: 100%; }
.pp-fs-head { display: flex; gap: 10px; align-items: flex-start; }
.pp-fs-ico {
  width: 36px; height: 36px; border-radius: 10px; flex: none;
  display: grid; place-items: center; background: #EFF6FF; color: #2563EB;
}
.pp-fs-title { font-size: 15px; font-weight: 650; color: #0F172A; }
.pp-fs-sub { margin-top: 2px; font-size: 12.5px; color: #64748B; }
.pp-fs-stack { display: flex; flex-direction: column; gap: 10px; }

.pp-forecast-metric {
  background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px;
  padding: 14px 14px 12px; min-width: 0;
}
.pp-fm-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; }
.pp-fm-label { font-size: 13px; font-weight: 600; color: #475569; line-height: 1.35; }
.pp-fm-ico {
  width: 36px; height: 36px; border-radius: 10px; flex: none;
  display: grid; place-items: center;
}
.pp-forecast-metric.accent-blue .pp-fm-ico { background: #EFF6FF; color: #2563EB; }
.pp-forecast-metric.accent-purple .pp-fm-ico { background: #F5F3FF; color: #7C3AED; }
.pp-forecast-metric.accent-green .pp-fm-ico { background: #ECFDF5; color: #059669; }
.pp-forecast-metric.accent-orange .pp-fm-ico { background: #FFF7ED; color: #EA580C; }
.pp-fm-value {
  margin-top: 8px; font-size: 24px; font-weight: 700; color: #0F172A;
  letter-spacing: -0.02em; line-height: 1.2;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.pp-fm-unit { margin-left: 6px; font-size: 13px; font-weight: 500; color: #64748B; white-space: nowrap; }
.pp-fm-delta { margin-top: 6px; font-size: 12.5px; font-weight: 600; line-height: 1.35; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.pp-fm-delta.up { color: #059669; }
.pp-fm-delta.down { color: #DC2626; }
.pp-fm-delta.flat { color: #64748B; font-weight: 500; }

.pp-fc-insight, .pp-fc-factors {
  background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px;
  box-shadow: 0 1px 2px rgba(15,23,42,0.04), 0 8px 24px rgba(15,23,42,0.04);
  padding: 16px 18px; min-height: 190px; height: 100%; box-sizing: border-box;
}

/* Cân chiều cao card chart ↔ kết quả, insight ↔ yếu tố */
div[data-testid="stHorizontalBlock"]:has(.pp-forecast-summary),
div[data-testid="stHorizontalBlock"]:has(.pp-fc-insight) {
  align-items: stretch !important;
}
div[data-testid="stHorizontalBlock"]:has(.pp-forecast-summary) > div[data-testid="stColumn"],
div[data-testid="stHorizontalBlock"]:has(.pp-fc-insight) > div[data-testid="stColumn"] {
  display: flex !important;
  flex-direction: column !important;
}
div[data-testid="stHorizontalBlock"]:has(.pp-forecast-summary) > div[data-testid="stColumn"] > div,
div[data-testid="stHorizontalBlock"]:has(.pp-fc-insight) > div[data-testid="stColumn"] > div {
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  height: 100%;
}
div[data-testid="stHorizontalBlock"]:has(.pp-forecast-summary) [data-testid="stVerticalBlockBorderWrapper"],
div[data-testid="stHorizontalBlock"]:has(.pp-fc-insight) [data-testid="stVerticalBlockBorderWrapper"] {
  flex: 1 1 auto;
  height: 100%;
  display: flex;
  flex-direction: column;
}
div[data-testid="stHorizontalBlock"]:has(.pp-forecast-summary) [data-testid="stVerticalBlockBorderWrapper"] > div,
div[data-testid="stHorizontalBlock"]:has(.pp-fc-insight) [data-testid="stVerticalBlockBorderWrapper"] > div {
  flex: 1 1 auto;
  height: 100%;
}

/* Tooltip Plotly: bo góc nhẹ 4 cạnh */
.js-plotly-plot .hoverlayer .hovertext path {
  stroke-linejoin: round;
}
.js-plotly-plot .hoverlayer .hovertext rect {
  rx: 8px;
  ry: 8px;
}

.pp-fc-section-head { display: flex; gap: 10px; align-items: flex-start; margin-bottom: 12px; }
.pp-fc-section-ico {
  width: 36px; height: 36px; border-radius: 10px; flex: none;
  display: grid; place-items: center; background: #F5F3FF; color: #7C3AED;
}
.pp-fc-section-title { font-size: 15px; font-weight: 650; color: #0F172A; }
.pp-fc-section-sub { margin-top: 2px; font-size: 12.5px; color: #64748B; line-height: 1.4; }
.pp-mi-bullets {
  margin: 0; padding: 0 0 0 0; list-style: none;
  display: flex; flex-direction: column; gap: 10px;
}
.pp-mi-bullets li {
  position: relative; padding-left: 16px; color: #475569;
  font-size: 13.5px; line-height: 1.5;
}
.pp-mi-bullets li::before {
  content: ""; position: absolute; left: 0; top: 0.55em;
  width: 6px; height: 6px; border-radius: 999px; background: #7C3AED;
}

.pp-factor-grid {
  display: grid; grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.pp-factor-card {
  background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px;
  padding: 12px 14px; min-width: 0;
}
.pp-factor-top { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.pp-factor-ico {
  width: 34px; height: 34px; border-radius: 10px; flex: none;
  display: grid; place-items: center;
}
.pp-factor-card.is-positive .pp-factor-ico { background: #ECFDF5; color: #059669; }
.pp-factor-card.is-negative .pp-factor-ico { background: #FEF2F2; color: #DC2626; }
.pp-factor-card.is-neutral .pp-factor-ico { background: #F5F3FF; color: #7C3AED; }
.pp-factor-card.is-positive .pp-factor-value { color: #059669; }
.pp-factor-card.is-negative .pp-factor-value { color: #DC2626; }
.pp-factor-card.is-neutral .pp-factor-value { color: #7C3AED; }
.pp-factor-value { font-size: 18px; font-weight: 700; letter-spacing: -0.02em; }
.pp-factor-title { margin-top: 8px; font-size: 13.5px; font-weight: 650; color: #0F172A; }
.pp-factor-desc { margin-top: 2px; font-size: 12px; color: #64748B; line-height: 1.4; }

.pp-page-actions { margin-top: 16px; }

/* Nút chuyển bước — cùng độ dài full-width, pill */
.pp-continue-row {
  margin: 4px 0 0 0;
  height: 0;
  overflow: hidden;
  pointer-events: none;
}
div[data-testid="stElementContainer"]:has(.pp-continue-row) + div[data-testid="stElementContainer"] {
  width: 100%;
  max-width: 100%;
}
div[data-testid="stElementContainer"]:has(.pp-continue-row) + div[data-testid="stElementContainer"] button[data-testid="stBaseButton-primary"],
div[data-testid="stElementContainer"]:has(.pp-continue-row) + div[data-testid="stElementContainer"] button {
  width: 100% !important;
  min-height: 48px !important;
  border-radius: 999px !important;
  justify-content: center !important;
  font-weight: 600 !important;
}

@media (max-width: 1100px) {
  .pp-factor-grid { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 720px) {
  .pp-factor-grid { grid-template-columns: 1fr; }
  .pp-fm-value { font-size: 20px; }
}

/* —— Prepare page —— */
.pp-prep-kpi-grid {
  display: grid; grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px; margin: 8px 0 16px 0;
}
.pp-prep-metric {
  background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px;
  box-shadow: 0 1px 2px rgba(15,23,42,0.04), 0 8px 24px rgba(15,23,42,0.04);
  padding: 16px 18px; min-width: 0; box-sizing: border-box;
}
.pp-prep-metric-top { display: flex; justify-content: space-between; gap: 10px; align-items: flex-start; }
.pp-prep-metric-title { font-size: 14px; font-weight: 650; color: #0F172A; }
.pp-prep-metric-sub { margin-top: 2px; font-size: 12.5px; color: #64748B; line-height: 1.35; }
.pp-prep-metric-ico {
  width: 40px; height: 40px; border-radius: 12px; flex: none;
  display: grid; place-items: center;
}
.pp-prep-metric.accent-green .pp-prep-metric-ico { background: #ECFDF5; color: #059669; }
.pp-prep-metric.accent-purple .pp-prep-metric-ico { background: #F5F3FF; color: #7C3AED; }
.pp-prep-metric.accent-pink .pp-prep-metric-ico { background: #FDF2F8; color: #DB2777; }
.pp-prep-metric.accent-orange .pp-prep-metric-ico { background: #FFF7ED; color: #EA580C; }
.pp-prep-metric.accent-blue .pp-prep-metric-ico { background: #EFF6FF; color: #2563EB; }
.pp-prep-value {
  margin-top: 12px; font-size: 26px; font-weight: 700; color: #0F172A;
  letter-spacing: -0.02em; line-height: 1.2; overflow-wrap: anywhere;
}
.pp-prep-status { margin-top: 12px; }
.pp-prep-bar {
  margin-top: 10px; height: 8px; border-radius: 999px; background: #F1F5F9; overflow: hidden;
}
.pp-prep-bar > div { height: 100%; border-radius: 999px; }
.pp-prep-bar.accent-green > div { background: #10B981; }
.pp-prep-bar.accent-purple > div { background: #7C3AED; }
.pp-prep-bar.accent-pink > div { background: #DB2777; }
.pp-prep-bar.accent-orange > div { background: #F59E0B; }
.pp-prep-bar.accent-blue > div { background: #2563EB; }
.pp-prep-support { margin-top: 8px; font-size: 12.5px; color: #64748B; }
.pp-prep-trend { margin-top: 6px; font-size: 12.5px; font-weight: 600; color: #059669; }

.pp-product-ready, .pp-readiness-score, .pp-issue-panel {
  background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px;
  box-shadow: 0 1px 2px rgba(15,23,42,0.04), 0 8px 24px rgba(15,23,42,0.04);
  padding: 16px 18px; box-sizing: border-box; min-width: 0;
}
.pp-product-ready {
  display: flex; flex-direction: column; min-height: 0;
}
.pp-product-ready .pp-scroll {
  /* Tự co theo viewport; bảng dài scroll bên trong, header sticky. */
  max-height: min(400px, calc(100vh - 340px));
  overflow: auto;
  border: 1px solid #E2E8F0;
  border-radius: 12px;
  -webkit-overflow-scrolling: touch;
}
.pp-fc-section-ico.warn { background: #FFF7ED; color: #EA580C; }
.pp-prep-table { border-collapse: separate; border-spacing: 0; }
.pp-prep-table thead th {
  background: #F8FAFC;
  position: sticky; top: 0; z-index: 1;
  box-shadow: inset 0 -1px 0 #E2E8F0;
}
.pp-prep-table tbody td { padding-top: 10px; padding-bottom: 10px; }
.pp-prep-table tbody tr:hover td { background: #F8FAFC; }
.pp-table-empty { text-align: center; color: #64748B; padding: 18px 8px !important; }
.pp-gap { font-weight: 650; }
.pp-gap.up { color: #059669; }
.pp-gap.down { color: #DC2626; }
.pp-gap.flat { color: #64748B; }

.pp-readiness-score .pp-prep-value { margin-top: 4px; }
.pp-readiness-msg { margin-top: 12px; }

.pp-issue-stack {
  display: flex; flex-direction: column; gap: 10px;
  max-height: min(260px, calc(100vh - 480px));
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}
.pp-issue-item {
  display: flex; gap: 12px; align-items: flex-start;
  border-radius: 12px; padding: 12px 14px;
}
.pp-issue-item.severity-critical { background: #FEF2F2; border: 1px solid #FECACA; }
.pp-issue-item.severity-warn { background: #FFFBEB; border: 1px solid #FDE68A; }
.pp-issue-item.severity-info { background: #EFF6FF; border: 1px solid #BFDBFE; }
.pp-issue-rank {
  width: 24px; height: 24px; border-radius: 999px; flex: none;
  display: grid; place-items: center; font-size: 12px; font-weight: 700;
  background: #FFFFFF; color: #0F172A; border: 1px solid #E2E8F0;
}
.pp-issue-title { font-size: 13.5px; font-weight: 650; color: #0F172A; line-height: 1.35; }
.pp-issue-desc { margin-top: 2px; font-size: 12.5px; color: #64748B; line-height: 1.45; }

.pp-prep-cta-note {
  text-align: right; color: #7C3AED; font-size: 14px; font-weight: 600;
  font-style: italic; margin: 8px 0 4px;
}

/* —— Execute page —— */
.pp-exec-panel {
  background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px;
  box-shadow: 0 1px 2px rgba(15,23,42,0.04), 0 8px 24px rgba(15,23,42,0.04);
  padding: 16px 18px; box-sizing: border-box; min-width: 0; height: 100%;
}
.pp-exec-panel.pp-card { overflow: hidden; }
.pp-exec-panel-head {
  display: flex; gap: 10px; align-items: flex-start; margin-bottom: 12px;
}
.pp-exec-panel-ico {
  width: 40px; height: 40px; border-radius: 12px; flex: none;
  display: grid; place-items: center; background: #EFF6FF; color: #2563EB;
}
.pp-exec-panel-ico.is-blue { background: #EFF6FF; color: #2563EB; }
.pp-exec-panel-title { font-size: 15px; font-weight: 650; color: #0F172A; line-height: 1.3; }
.pp-exec-panel-sub { margin-top: 2px; font-size: 12.5px; color: #64748B; line-height: 1.4; }

.pp-exec-fields { display: flex; flex-direction: column; gap: 0; }
.pp-exec-field {
  display: grid;
  grid-template-columns: 40px minmax(100px, 0.9fr) minmax(0, 1.5fr);
  gap: 10px 14px;
  align-items: center;
  padding: 10px 2px;
  border-bottom: 1px solid #E2E8F0;
}
.pp-exec-field:last-child { border-bottom: none; padding-bottom: 2px; }
.pp-exec-field:first-child { padding-top: 2px; }
.pp-exec-field-ico {
  width: 40px; height: 40px; border-radius: 12px; flex: none;
  display: grid; place-items: center;
}
.pp-exec-field-ico.purple { background: #F5F3FF; color: #7C3AED; }
.pp-exec-field-ico.green { background: #ECFDF5; color: #059669; }
.pp-exec-field-ico.pink { background: #FDF2F8; color: #DB2777; }
.pp-exec-field-ico.orange { background: #FFFBEB; color: #D97706; }
.pp-exec-field-ico.blue { background: #EFF6FF; color: #2563EB; }
.pp-exec-field-label {
  font-size: 13.5px; font-weight: 650; color: #334155; line-height: 1.35;
}
.pp-exec-field-content { min-width: 0; }
.pp-exec-field-value {
  margin: 0; font-size: 14.5px; font-weight: 650; color: #0F172A; line-height: 1.4;
  overflow-wrap: anywhere;
}
.pp-exec-field-sub {
  margin-top: 2px; font-size: 12.5px; color: #64748B; line-height: 1.4;
  overflow-wrap: anywhere;
}
@media (max-width: 720px) {
  .pp-exec-field {
    grid-template-columns: 36px minmax(0, 1fr);
    gap: 6px 10px;
  }
  .pp-exec-field-label { grid-column: 2; }
  .pp-exec-field-content { grid-column: 2; }
}

.pp-exec-table-wrap { overflow-x: auto; margin-top: 4px; }
.pp-exec-table-scroll {
  margin-top: 2px;
  max-height: min(420px, calc(100vh - 360px));
  overflow: auto;
  border-radius: 10px;
  border: 1px solid #E2E8F0;
}
.pp-exec-table {
  width: 100%; border-collapse: collapse; min-width: 640px;
  border: 1px solid #CBD5E1;
}
.pp-exec-table thead th {
  background: #F1F5F9; color: #334155; font-size: 12.5px; font-weight: 700;
  text-align: left; padding: 10px 12px; border: 1px solid #CBD5E1;
  white-space: nowrap;
}
.pp-exec-table tbody td {
  padding: 10px 12px; border: 1px solid #E2E8F0; vertical-align: middle;
  font-size: 13.5px; color: #0F172A; background: #FFFFFF;
}
.pp-exec-table tbody tr:hover td { background: #F8FAFC; }
.pp-exec-task-cell {
  display: inline-flex; align-items: center; gap: 6px; min-width: 0;
  font-size: 13px; line-height: 1.35; color: #0F172A;
}
.pp-exec-task-ico {
  width: 28px; height: 28px; border-radius: 8px; flex: none;
  display: grid; place-items: center; background: #F8FAFC; color: #64748B; border: 1px solid #E2E8F0;
}
.pp-exec-owner {
  display: inline-flex; align-items: center; gap: 8px; min-width: 0;
}
.pp-exec-owner-av {
  width: 24px; height: 24px; border-radius: 999px; flex: none;
  display: grid; place-items: center; font-size: 10px; font-weight: 700;
  background: #EFF6FF; color: #2563EB; border: 1px solid #DBEAFE;
}
.pp-exec-owner-av.mk { background: #F5F3FF; color: #7C3AED; border-color: #DDD6FE; }
.pp-exec-owner-av.it { background: #ECFDF5; color: #059669; border-color: #A7F3D0; }
.pp-exec-owner-av.sc { background: #FFFBEB; color: #D97706; border-color: #FDE68A; }
.pp-exec-owner-av.rt { background: #FDF2F8; color: #DB2777; border-color: #FBCFE8; }
.pp-exec-owner-name { font-size: 12.5px; color: #0F172A; overflow-wrap: anywhere; line-height: 1.3; }

.pp-exec-status {
  display: inline-flex; align-items: center; gap: 5px;
  border-radius: 999px; padding: 3px 8px; font-size: 11.5px; font-weight: 600; white-space: nowrap;
}
.pp-exec-status.ok { background: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; }
.pp-exec-status.warn { background: #FFFBEB; color: #D97706; border: 1px solid #FDE68A; }
.pp-exec-status.info { background: #EFF6FF; color: #2563EB; border: 1px solid #BFDBFE; }
.pp-exec-status.bad { background: #FEF2F2; color: #DC2626; border: 1px solid #FECACA; }
.pp-exec-status.muted { background: #F8FAFC; color: #64748B; border: 1px solid #E2E8F0; }

/* Task list read-only: hàng gọn, 5 cột (không cột Xóa) */
.pp-exec-grid-head, .pp-exec-grid-row {
  display: grid;
  grid-template-columns: 36px minmax(0, 2.6fr) minmax(100px, 1.35fr) minmax(88px, 0.95fr) minmax(110px, 1.15fr);
  gap: 0;
  border: none;
  border-bottom: 1px solid #E2E8F0;
  background: #FFFFFF;
  align-items: center;
}
.pp-exec-grid-head {
  background: #F8FAFC;
  border-bottom: 1px solid #E2E8F0;
  position: sticky; top: 0; z-index: 2;
}
.pp-exec-grid-head > div {
  padding: 8px 10px; font-size: 12px; font-weight: 700; color: #475569;
  border-right: none;
}
.pp-exec-grid-head > div:last-child { border-right: none; }
.pp-exec-grid-row {
  border-top: none;
  min-height: 0;
}
.pp-exec-grid-row.is-new { background: #F8FAFC; }
.pp-exec-grid-row > div {
  padding: 7px 10px; border-right: none;
  display: flex; align-items: center; min-width: 0;
  font-size: 13px; color: #0F172A; line-height: 1.35;
}
.pp-exec-grid-row > div:last-child { border-right: none; justify-content: flex-start; }
.pp-exec-grid-row:last-child { border-bottom: none; border-radius: 0; }
.pp-exec-grid-row:hover { background: #F8FAFC; }
.pp-exec-due { font-size: 12.5px; color: #334155; white-space: nowrap; }
.pp-exec-idx { font-size: 12.5px; font-weight: 650; color: #64748B; }

.pp-exec-new-badge {
  display: inline-flex; align-items: center; border-radius: 999px;
  background: #EFF6FF; color: #2563EB; border: 1px solid #BFDBFE;
  font-size: 11px; font-weight: 650; padding: 2px 8px; margin-left: 6px;
}

.pp-exec-ready-top {
  display: flex; justify-content: space-between; align-items: baseline; gap: 8px; margin-bottom: 10px;
}
.pp-exec-ready-count { font-size: 13.5px; font-weight: 650; color: #0F172A; }
.pp-exec-ready-bar-row {
  display: flex; align-items: center; gap: 12px;
}
.pp-exec-ready-bar {
  flex: 1; height: 12px; border-radius: 999px; background: #E2E8F0; overflow: hidden;
}
.pp-exec-ready-bar > div {
  height: 100%; border-radius: 999px; background: #10B981;
}
.pp-exec-ready-bar.is-mid > div { background: #F59E0B; }
.pp-exec-ready-bar.is-low > div { background: #94A3B8; }
.pp-exec-ready-pct { font-size: 22px; font-weight: 700; color: #0F172A; min-width: 3ch; text-align: right; }

.pp-exec-check-grid {
  display: grid; grid-template-columns: 1fr; gap: 12px 0; margin-top: 4px;
}
.pp-exec-check-scroll {
  max-height: 300px;
  overflow-y: auto;
  padding-right: 4px;
  margin-top: 4px;
}
.pp-exec-check-scroll::-webkit-scrollbar { width: 6px; }
.pp-exec-check-scroll::-webkit-scrollbar-thumb {
  background: #CBD5E1; border-radius: 999px;
}
.pp-exec-check-item {
  display: flex; align-items: flex-start; gap: 10px; min-width: 0;
}
.pp-exec-check-box {
  width: 20px; height: 20px; border-radius: 6px; flex: none; margin-top: 1px;
  display: grid; place-items: center; border: 1.5px solid #CBD5E1; background: #FFFFFF; color: white;
}
.pp-exec-check-box.is-on { background: #10B981; border-color: #10B981; }
/* Checklist Execute: 1 cột + wrap đủ tên (Streamlit mặc định ellipsis/nowrap) */
.pp-exec-check-label {
  font-size: 13.5px;
  color: #0F172A;
  line-height: 1.45;
  overflow-wrap: break-word;
  word-break: normal;
  white-space: normal;
  hyphens: none;
  padding-top: 2px;
  min-width: 0;
}
.pp-exec-check-label.is-on { color: #334155; }

[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCheckbox"] {
  align-items: flex-start !important;
}
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCheckbox"] label {
  align-items: flex-start !important;
  white-space: normal !important;
  height: auto !important;
  min-height: 1.5rem;
  gap: 0.55rem;
}
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCheckbox"] label p,
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCheckbox"] label span,
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCheckbox"] [data-testid="stWidgetLabel"] p {
  white-space: normal !important;
  overflow: visible !important;
  text-overflow: unset !important;
  overflow-wrap: break-word !important;
  word-break: normal !important;
  line-height: 1.45 !important;
  max-width: 100% !important;
}
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCheckbox"] > label > div:first-child {
  margin-top: 0.15rem;
  flex: none;
}

.pp-exec-see-all { font-size: 12.5px; font-weight: 600; color: #2563EB; }
.pp-exec-see-all-btn button,
.pp-exec-see-all-btn [data-testid="stBaseButton-secondary"] {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  color: #2563EB !important;
  font-size: 12.5px !important;
  font-weight: 600 !important;
  padding: 4px 0 !important;
  min-height: 0 !important;
  justify-content: flex-end !important;
}
.pp-exec-see-all-btn button:hover {
  color: #1D4ED8 !important;
  text-decoration: underline !important;
  background: transparent !important;
}

.pp-exec-actions {
  display: flex; justify-content: flex-end; gap: 10px; margin-top: 16px; flex-wrap: wrap;
}
[data-testid="stVerticalBlockBorderWrapper"] {
  background: #FFFFFF;
  border: 1px solid #E2E8F0 !important;
  border-radius: 16px !important;
  box-shadow: 0 1px 2px rgba(15,23,42,0.04), 0 8px 24px rgba(15,23,42,0.04);
  padding: 4px 6px;
}

@media (max-width: 1100px) {
  .pp-exec-check-grid { grid-template-columns: 1fr; }
}
@media (max-width: 720px) {
  .pp-exec-check-grid { grid-template-columns: 1fr; }
}

/* —— Monitor & Learn page —— */
.pp-mon-kpi-grid {
  display: grid; grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px; margin: 8px 0 16px;
}
.pp-mon-kpi {
  background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px;
  box-shadow: 0 1px 2px rgba(15,23,42,0.04), 0 8px 24px rgba(15,23,42,0.04);
  padding: 16px 18px; min-width: 0; box-sizing: border-box;
}
.pp-mon-kpi-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; }
.pp-mon-kpi-title { font-size: 13px; font-weight: 600; color: #64748B; }
.pp-mon-kpi-ico {
  width: 44px; height: 44px; border-radius: 12px; flex: none;
  display: grid; place-items: center;
}
.pp-mon-kpi-ico.blue { background: #EFF6FF; color: #2563EB; }
.pp-mon-kpi-ico.purple { background: #F5F3FF; color: #7C3AED; }
.pp-mon-kpi-ico.pink { background: #FDF2F8; color: #DB2777; }
.pp-mon-kpi-ico.orange { background: #FFFBEB; color: #D97706; }
.pp-mon-kpi-value {
  margin-top: 10px; font-size: 28px; font-weight: 700; color: #0F172A;
  letter-spacing: -0.02em; line-height: 1.15; overflow-wrap: anywhere;
}
.pp-mon-kpi-delta { margin-top: 8px; font-size: 13.5px; font-weight: 600; }
.pp-mon-kpi-delta.up { color: #059669; }
.pp-mon-kpi-delta.down { color: #DC2626; }
.pp-mon-kpi-delta.flat { color: #64748B; }

.pp-mon-panel {
  background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px;
  box-shadow: 0 1px 2px rgba(15,23,42,0.04), 0 8px 24px rgba(15,23,42,0.04);
  padding: 16px 18px; box-sizing: border-box; min-width: 0; height: 100%;
}
.pp-mon-panel-head {
  display: flex; justify-content: space-between; align-items: flex-start; gap: 10px; margin-bottom: 12px;
}
.pp-mon-panel-head-left { display: flex; gap: 10px; align-items: flex-start; min-width: 0; }
.pp-mon-panel-ico {
  width: 40px; height: 40px; border-radius: 12px; flex: none;
  display: grid; place-items: center; background: #F5F3FF; color: #7C3AED;
}
.pp-mon-panel-ico.warn { background: #FFF7ED; color: #EA580C; }
.pp-mon-panel-ico.green { background: #ECFDF5; color: #059669; }
.pp-mon-panel-title { font-size: 15px; font-weight: 650; color: #0F172A; line-height: 1.3; }
.pp-mon-panel-sub { margin-top: 2px; font-size: 12.5px; color: #64748B; line-height: 1.4; }
.pp-mon-link { font-size: 12.5px; font-weight: 600; color: #2563EB; white-space: nowrap; }

/* Nút Xuất / Nhập góc phải card số liệu thực tế */
.pp-mon-actual-tools {
  display: flex; justify-content: flex-end; align-items: flex-start;
  margin-top: 2px;
}
.pp-mon-actual-tools button,
.pp-mon-actual-tools [data-testid="stBaseButton-secondary"],
.pp-mon-actual-tools [data-testid="stPopoverButton"] button {
  min-height: 36px !important;
  padding: 6px 10px !important;
  font-size: 12.5px !important;
  font-weight: 600 !important;
  border-radius: 10px !important;
  white-space: nowrap !important;
}

.pp-mon-alert-stack { display: flex; flex-direction: column; gap: 10px; }
.pp-mon-alert-scroll {
  max-height: 420px;
  overflow-y: auto;
  padding-right: 4px;
  margin-top: 2px;
}
.pp-mon-alert-scroll::-webkit-scrollbar { width: 6px; }
.pp-mon-alert-scroll::-webkit-scrollbar-thumb {
  background: #CBD5E1; border-radius: 999px;
}
.pp-mon-alert {
  border-radius: 12px; padding: 12px 14px; border: 1px solid #E2E8F0; background: #F8FAFC;
}
.pp-mon-alert.is-critical { background: #FEF2F2; border-color: #FECACA; }
.pp-mon-alert.is-warning { background: #FFFBEB; border-color: #FDE68A; }
.pp-mon-alert.is-info { background: #EFF6FF; border-color: #BFDBFE; }
.pp-mon-alert-top { display: flex; gap: 10px; align-items: flex-start; }
.pp-mon-alert-ico {
  width: 32px; height: 32px; border-radius: 10px; flex: none;
  display: grid; place-items: center; background: #FFFFFF; color: #64748B; border: 1px solid #E2E8F0;
}
.pp-mon-alert-title { font-size: 13.5px; font-weight: 650; color: #0F172A; line-height: 1.35; }
.pp-mon-alert-desc { margin-top: 3px; font-size: 12.5px; color: #475569; line-height: 1.45; }
.pp-mon-alert-foot { margin-top: 8px; display: flex; justify-content: space-between; align-items: center; gap: 8px; }

.pp-mon-learn-list { display: flex; flex-direction: column; gap: 12px; margin-top: 4px; }
.pp-mon-learn-item { display: flex; gap: 10px; align-items: flex-start; }
.pp-mon-learn-ico {
  width: 28px; height: 28px; border-radius: 999px; flex: none;
  display: grid; place-items: center; background: #ECFDF5; color: #059669;
}
.pp-mon-learn-ico.is-neutral { background: #F1F5F9; color: #64748B; }
.pp-mon-learn-ico.is-warn { background: #FFFBEB; color: #D97706; }
.pp-mon-learn-text { font-size: 13.5px; color: #0F172A; line-height: 1.45; }

.pp-mon-action-item {
  display: flex; gap: 10px; align-items: flex-start;
  padding: 10px 0; border-bottom: 1px solid #F1F5F9;
}
.pp-mon-action-item:last-child { border-bottom: none; }
.pp-mon-action-ico {
  width: 32px; height: 32px; border-radius: 10px; flex: none;
  display: grid; place-items: center; background: #EFF6FF; color: #2563EB;
}
.pp-mon-action-title { font-size: 13.5px; font-weight: 650; color: #0F172A; }
.pp-mon-action-desc { margin-top: 2px; font-size: 12.5px; color: #64748B; line-height: 1.45; }

.pp-mon-empty {
  background: #FFFFFF; border: 1px dashed #CBD5E1; border-radius: 16px;
  padding: 36px 20px; text-align: center;
}
.pp-mon-empty-title { font-size: 16px; font-weight: 650; color: #0F172A; margin-top: 8px; }
.pp-mon-empty-desc { margin: 6px auto 0; max-width: 480px; font-size: 13.5px; color: #64748B; line-height: 1.5; }

@media (max-width: 1100px) {
  .pp-mon-kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 720px) {
  .pp-mon-kpi-grid { grid-template-columns: 1fr; }
}

@media (max-width: 1100px) {
  .pp-prep-kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 720px) {
  .pp-prep-kpi-grid { grid-template-columns: 1fr; }
}

/* —— Simulate page —— */
.pp-sim-setup-head { display: flex; gap: 10px; align-items: flex-start; margin-bottom: 12px; }
.pp-sim-setup-ico {
  width: 40px; height: 40px; border-radius: 12px; flex: none;
  display: grid; place-items: center; background: #F5F3FF; color: #7C3AED;
}
.pp-sim-setup-title { font-size: 15px; font-weight: 650; color: #0F172A; }
.pp-sim-setup-sub { margin-top: 2px; font-size: 12.5px; color: #64748B; line-height: 1.4; }

.pp-sim-empty {
  background: #FFFFFF; border: 1px dashed #CBD5E1; border-radius: 16px;
  padding: 36px 20px; text-align: center; min-height: 220px;
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px;
}
.pp-sim-empty-ico {
  width: 56px; height: 56px; border-radius: 16px;
  display: grid; place-items: center; background: #F5F3FF; color: #7C3AED; margin-bottom: 4px;
}
.pp-sim-empty-title { font-size: 16px; font-weight: 650; color: #0F172A; }
.pp-sim-empty-desc { margin: 0; max-width: 420px; font-size: 13.5px; color: #64748B; line-height: 1.5; }

.pp-sim-card {
  background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px;
  box-shadow: 0 1px 2px rgba(15,23,42,0.04), 0 8px 24px rgba(15,23,42,0.04);
  padding: 16px; min-width: 0; height: 100%; box-sizing: border-box;
  display: flex; flex-direction: column; gap: 10px;
}
a.pp-sim-card-link {
  display: block; height: 100%; text-decoration: none; color: inherit; min-width: 0;
}
a.pp-sim-card-link:hover .pp-sim-card {
  border-color: #A78BFA;
  box-shadow: 0 0 0 1px rgba(124,58,237,0.25), 0 8px 24px rgba(15,23,42,0.08);
  transform: translateY(-1px);
  transition: box-shadow 0.15s ease, transform 0.15s ease, border-color 0.15s ease;
}
.pp-sim-card.is-clickable { cursor: pointer; }
.pp-sim-card.is-selected {
  border-color: #EC4899; box-shadow: 0 0 0 1px #EC4899, 0 8px 24px rgba(236,72,153,0.12);
  background: #FFF7FB;
}
.pp-sim-card.is-rejected { opacity: 0.78; cursor: not-allowed; }
.pp-sim-card-head { display: flex; gap: 10px; align-items: flex-start; min-width: 0; }
.pp-sim-card-head-text { min-width: 0; flex: 1; }
.pp-sim-card-ico {
  width: 40px; height: 40px; border-radius: 12px; flex: none;
  display: grid; place-items: center; background: #EFF6FF; color: #2563EB;
}
.pp-sim-letter { font-size: 12px; font-weight: 650; color: #64748B; text-transform: uppercase; letter-spacing: 0.02em; }
.pp-sim-card-title {
  font-size: 15px; font-weight: 650; color: #0F172A; line-height: 1.3;
  overflow-wrap: anywhere; word-break: break-word;
}
.pp-sim-card-sub {
  margin-top: 2px; font-size: 12.5px; color: #64748B; line-height: 1.35;
  overflow-wrap: anywhere; word-break: break-word;
}
.pp-sim-desc {
  margin: 0; font-size: 13px; color: #475569; line-height: 1.45;
  overflow-wrap: anywhere;
}
.pp-sim-flags { display: flex; flex-wrap: wrap; gap: 6px; }
.pp-sim-metrics { display: flex; flex-direction: column; gap: 8px; margin-top: auto; min-width: 0; }
.pp-sim-metric {
  display: flex; justify-content: space-between; align-items: flex-start; gap: 8px;
  padding: 6px 0; border-top: 1px solid #F1F5F9;
}
.pp-sim-metric-left {
  display: inline-flex; align-items: center; gap: 6px;
  font-size: 12.5px; color: #64748B; min-width: 0;
}
.pp-sim-metric-left .pp-icon { color: #94A3B8; flex: none; }
.pp-sim-metric-value {
  font-size: 13px; font-weight: 650; color: #0F172A; text-align: right;
  overflow-wrap: anywhere; max-width: 55%;
}
.pp-sim-metric-value .up { color: #059669; }
.pp-sim-metric-value .down { color: #DC2626; }
.pp-sim-metric-value .ok { color: #059669; }
.pp-sim-metric-value .warn { color: #D97706; }
.pp-sim-metric-value .bad { color: #DC2626; }
.pp-sim-card-foot {
  margin-top: 4px; padding-top: 10px; border-top: 1px dashed #E2E8F0;
  font-size: 12.5px; font-weight: 600; color: #7C3AED; text-align: center;
}
.pp-sim-card-foot.selected { color: #DB2777; }
.pp-sim-card-foot.muted { color: #94A3B8; font-weight: 500; }
.pp-sim-board-note {
  margin: 0 0 10px; font-size: 12.5px; color: #64748B;
}
/* Cột cùng hàng cao bằng nhau — card/link kéo full height, tránh rớt chữ/vỡ layout. */
div[data-testid="stHorizontalBlock"]:has(.pp-sim-card) > div[data-testid="stColumn"] {
  display: flex; flex-direction: column;
}
div[data-testid="stHorizontalBlock"]:has(.pp-sim-card) > div[data-testid="stColumn"] > div {
  flex: 1 1 auto; height: 100%; min-width: 0;
}
div[data-testid="stHorizontalBlock"]:has(.pp-sim-card) .pp-sim-card-link,
div[data-testid="stHorizontalBlock"]:has(.pp-sim-card) [data-testid="stHtml"] {
  height: 100%; display: block;
}

.pp-sim-compare {
  background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px;
  box-shadow: 0 1px 2px rgba(15,23,42,0.04), 0 8px 24px rgba(15,23,42,0.04);
  padding: 16px 18px; margin-top: 16px;
}
.pp-sim-roi-strip {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 10px; margin-top: 12px;
}
.pp-sim-roi-item {
  border: 1px solid #E2E8F0; border-radius: 12px; padding: 10px 12px; background: #F8FAFC;
}
.pp-sim-roi-item .l { font-size: 12px; color: #64748B; }
.pp-sim-roi-item .v { margin-top: 4px; font-size: 16px; font-weight: 700; color: #0F172A; }
.pp-sim-roi-item .u { margin-top: 2px; font-size: 11.5px; color: #94A3B8; }
.pp-sim-selected-note {
  margin: 12px 0 4px; text-align: right; font-size: 13.5px; color: #475569;
}
.pp-sim-selected-note b { color: #0F172A; }

/* —— Decide page —— */
.pp-dec-hero {
  background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 18px;
  box-shadow: 0 1px 2px rgba(15,23,42,0.04), 0 8px 24px rgba(15,23,42,0.04);
  padding: 18px 20px; margin: 8px 0 16px; border-top: 3px solid #7C3AED;
}
.pp-dec-hero-top { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; flex-wrap: wrap; }
.pp-dec-hero-badge {
  display: inline-flex; align-items: center; gap: 6px;
  background: #F5F3FF; color: #6D28D9; border-radius: 999px;
  padding: 5px 10px; font-size: 12.5px; font-weight: 650;
}
.pp-dec-hero-badge.is-alt { background: #EFF6FF; color: #1D4ED8; }
.pp-dec-hero-status {
  background: #ECFDF5; border: 1px solid #A7F3D0; border-radius: 12px;
  padding: 8px 12px; text-align: right;
}
.pp-dec-hero-status-title {
  display: inline-flex; align-items: center; gap: 6px;
  color: #047857; font-size: 13px; font-weight: 650;
}
.pp-dec-hero-status-sub { margin-top: 2px; font-size: 12px; color: #059669; }
.pp-dec-hero-body { display: flex; gap: 16px; align-items: flex-start; margin-top: 14px; }
.pp-dec-hero-ico {
  width: 64px; height: 64px; border-radius: 16px; flex: none;
  display: grid; place-items: center; background: #FDF2F8; color: #DB2777;
}
.pp-dec-hero-title { font-size: 22px; font-weight: 700; color: #0F172A; line-height: 1.25; letter-spacing: -0.02em; }
.pp-dec-hero-sub { margin-top: 4px; font-size: 13.5px; color: #64748B; }
.pp-dec-hero-desc { margin: 8px 0 0; font-size: 14px; color: #475569; line-height: 1.5; max-width: 720px; }

.pp-dec-metrics {
  display: grid; grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px; margin: 0 0 16px;
}
.pp-dec-metric {
  background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px;
  padding: 14px; min-width: 0; box-sizing: border-box;
}
.pp-dec-metric-top { display: flex; justify-content: space-between; gap: 8px; align-items: flex-start; }
.pp-dec-metric-label { font-size: 12.5px; font-weight: 600; color: #64748B; }
.pp-dec-metric-ico {
  width: 30px; height: 30px; border-radius: 9px; flex: none;
  display: grid; place-items: center;
}
.pp-dec-metric.accent-blue .pp-dec-metric-ico { background: #EFF6FF; color: #2563EB; }
.pp-dec-metric.accent-purple .pp-dec-metric-ico { background: #F5F3FF; color: #7C3AED; }
.pp-dec-metric.accent-orange .pp-dec-metric-ico { background: #FFF7ED; color: #EA580C; }
.pp-dec-metric.accent-green .pp-dec-metric-ico { background: #ECFDF5; color: #059669; }
.pp-dec-metric.accent-pink .pp-dec-metric-ico { background: #FDF2F8; color: #DB2777; }
.pp-dec-metric-value {
  margin-top: 10px; font-size: 22px; font-weight: 700; color: #0F172A;
  letter-spacing: -0.02em; line-height: 1.2; overflow-wrap: anywhere;
}
.pp-dec-metric-sub { margin-top: 4px; font-size: 12px; color: #94A3B8; }

.pp-dec-panel {
  border-radius: 16px; padding: 16px 18px; min-height: 180px; box-sizing: border-box;
  border: 1px solid #E2E8F0;
}
.pp-dec-panel.tone-ok { background: #F0FDF4; border-color: #BBF7D0; }
.pp-dec-panel.tone-warn { background: #FFFBEB; border-color: #FDE68A; }
.pp-dec-panel-head { display: flex; gap: 10px; align-items: center; margin-bottom: 12px; }
.pp-dec-panel-ico {
  width: 34px; height: 34px; border-radius: 10px; flex: none;
  display: grid; place-items: center; background: #FFFFFF;
}
.pp-dec-panel.tone-ok .pp-dec-panel-ico { color: #059669; }
.pp-dec-panel.tone-warn .pp-dec-panel-ico { color: #D97706; }
.pp-dec-panel-title { font-size: 15px; font-weight: 650; color: #0F172A; }
.pp-dec-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 10px; }
.pp-dec-list li {
  display: flex; gap: 8px; align-items: flex-start;
  font-size: 13.5px; color: #334155; line-height: 1.45;
}
.pp-dec-li-ico { flex: none; margin-top: 2px; }
.pp-dec-panel.tone-ok .pp-dec-li-ico { color: #059669; }
.pp-dec-panel.tone-warn .pp-dec-li-ico { color: #D97706; }

.pp-dec-alt-grid {
  display: grid; grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px; margin-top: 8px;
}
.pp-dec-alt {
  background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px;
  padding: 14px; min-width: 0; box-sizing: border-box;
}
.pp-dec-alt-head { display: flex; gap: 10px; align-items: flex-start; margin-bottom: 10px; }
.pp-dec-alt-ico {
  width: 36px; height: 36px; border-radius: 10px; flex: none;
  display: grid; place-items: center; background: #EFF6FF; color: #2563EB;
}
.pp-dec-alt-title { font-size: 14px; font-weight: 650; color: #0F172A; }
.pp-dec-alt-desc { margin-top: 2px; font-size: 12.5px; color: #64748B; line-height: 1.4; }
.pp-dec-alt-metrics { display: flex; flex-direction: column; gap: 6px; }
.pp-dec-alt-metric {
  display: flex; justify-content: space-between; gap: 8px;
  font-size: 12.5px; color: #64748B; border-top: 1px solid #F1F5F9; padding-top: 6px;
}
.pp-dec-alt-metric b { color: #0F172A; font-weight: 650; }

@media (max-width: 1200px) {
  .pp-dec-metrics { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
@media (max-width: 900px) {
  .pp-dec-alt-grid { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 720px) {
  .pp-dec-metrics { grid-template-columns: 1fr 1fr; }
  .pp-dec-alt-grid { grid-template-columns: 1fr; }
  .pp-dec-hero-body { flex-direction: column; }
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
div[data-testid="stDialog"] [data-testid="stVerticalBlockBorderWrapper"] {
  box-shadow: none;
  overflow: visible;
  padding: 4px 2px 10px;
}
div[data-testid="stDialog"] [data-testid="stPlotlyChart"] {
  width: 100% !important;
  overflow: visible;
}
div[data-testid="stDialog"] .js-plotly-plot .plotly {
  max-width: 100%;
}
div[data-testid="stDialog"] .pp-def {
  padding: 8px 10px;
  background: #F8FAFC;
  border: 1px solid #E2E8F0;
  border-radius: 12px;
  margin: 0 0 10px 0;
}
div[data-testid="stDialog"] .pp-def:last-child { margin-bottom: 0; }
div[data-testid="stDialog"] .pp-def span {
  display: block;
  font-weight: 500;
  line-height: 1.45;
  overflow-wrap: anywhere;
}
"""


def inject_css() -> None:
    from ui.icons import icon_library_css, sidebar_icon_css
    from ui.nav import NAV

    extra = "\n".join(
        [
            icon_library_css(),
            sidebar_icon_css([(slug, name) for _key, _label, name, slug in NAV]),
        ]
    )
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
