"""Trang Alerts + AI Action (mục XXX, XXXI spec PromotionPilot AI)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from src.alerts.engine import decide_action, evaluate_alerts
from src.learning.campaign_log import list_campaign_records, save_campaign_record
from src.utils.state import init_session_state

init_session_state()

st.title("🚨 Alerts & AI Action")

records = list_campaign_records()
active_id = st.session_state.get("active_campaign_id")
record = next((r for r in records if r.campaign_id == active_id), None)

if record is None or not record.actual.get("daily_rows"):
    st.warning(
        "⚠️ Chưa có dữ liệu thực tế nào để đánh giá. Vào trang **Campaign Monitor**, nhập dữ liệu "
        "thực tế và bấm **Lưu dữ liệu thực tế & Tính toán** trước."
    )
    st.stop()

profile = st.session_state["business_profile"]

st.info(f"Đang đánh giá campaign **{record.campaign_id}** — {record.promotion_label} ({record.product_focus})")

daily_rows = record.actual.get("daily_rows", [])
latest_inventory = None
for row in reversed(daily_rows):
    if row.get("inventory_onhand") is not None:
        latest_inventory = row["inventory_onhand"]
        break

units_per_day = record.forecast.get("expected_demand_range")
avg_daily_units = (sum(units_per_day) / 2 / max(record.forecast.get("promo_days") or 1, 1)) if units_per_day else None
days_of_inventory = (latest_inventory / avg_daily_units) if (latest_inventory is not None and avg_daily_units) else None

current_margin_pct = None
if daily_rows:
    total_gp = sum(r.get("gp") or 0 for r in daily_rows)
    total_revenue = sum(r.get("revenue") or 0 for r in daily_rows)
    if total_revenue > 0:
        current_margin_pct = total_gp / total_revenue

inventory_vs_forecast_ratio = None
recommended_stock = st.session_state["last_recommendation_card"].recommended_stock if st.session_state.get("last_recommendation_card") else None
if latest_inventory is not None and recommended_stock:
    inventory_vs_forecast_ratio = latest_inventory / recommended_stock

alerts = evaluate_alerts(
    cumulative_revenue_variance=record.variance.get("revenue"),
    current_margin_pct=current_margin_pct,
    min_margin_pct=profile.min_margin_pct,
    days_of_inventory=days_of_inventory,
    cumulative_customers_variance=record.variance.get("customers"),
    inventory_vs_forecast_ratio=inventory_vs_forecast_ratio,
    actual_roi=record.roi_actual,
    min_roi_pct=profile.min_roi_pct,
)

st.subheader("🔔 Cảnh báo")
level_icon = {"info": "ℹ️", "warning": "⚠️", "critical": "🔴"}
for a in alerts:
    icon = level_icon[a.level]
    if a.level == "critical":
        st.error(f"{icon} **{a.code}** — {a.message}")
    elif a.level == "warning":
        st.warning(f"{icon} **{a.code}** — {a.message}")
    else:
        st.success(f"{icon} {a.message}")

st.divider()
st.subheader("🤖 Đề xuất AI Action")

action_result = decide_action(
    alerts=alerts,
    cumulative_revenue_variance=record.variance.get("revenue"),
    cumulative_customers_variance=record.variance.get("customers"),
    actual_roi=record.roi_actual,
    min_roi_pct=profile.min_roi_pct,
)

action_color = {"CONTINUE": "green", "SCALE": "green", "ADJUST": "orange", "STOP": "red"}
with st.container(border=True):
    st.markdown(f"## :{action_color[action_result.action]}[{action_result.action_vi}]")
    st.write("**Lý do:**")
    for r in action_result.reasons:
        st.write(f"- {r}")

if st.button("💾 Lưu kết quả đánh giá vào Campaign Record"):
    record.ai_action = action_result.action
    record.ai_action_reasons = action_result.reasons
    save_campaign_record(record)
    st.success("Đã lưu vào nhật ký campaign — có thể xem lại ở đợt sau để so sánh dự báo/quyết định qua các campaign.")

st.divider()
st.subheader("📚 Lịch sử Campaign (Campaign Learning Loop)")
if records:
    import pandas as pd

    history_rows = []
    for r in records:
        history_rows.append(
            {
                "Campaign": r.campaign_id,
                "Sản phẩm": r.product_focus,
                "Chương trình": r.promotion_label,
                "ROI dự báo": f"{r.roi_forecast:.0%}" if r.roi_forecast is not None else "N/A",
                "ROI thực tế": f"{r.roi_actual:.0%}" if r.roi_actual is not None else "N/A",
                "AI Action": r.ai_action or "Chưa đánh giá",
                "Ngày tạo": r.created_at,
            }
        )
    st.dataframe(pd.DataFrame(history_rows), use_container_width=True, hide_index=True)
    st.caption(
        "Dữ liệu lịch sử này là nền tảng để các campaign sau tham chiếu lại — về lâu dài có thể dùng "
        "để tinh chỉnh giả định elasticity mặc định trong Promotion Simulator (xem "
        "docs/backlog_tinh_nang.md)."
    )
