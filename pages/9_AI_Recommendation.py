"""Trang AI Recommendation Card (mục XXII, XXIII yêu cầu gốc)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from src.features.engineering import aggregate_daily
from src.inventory.planning import plan_sku_inventory
from src.optimization.objective import OBJECTIVE_LABELS_VI
from src.recommendation.engine import build_recommendation_card
from src.recommendation.timing import analyze_best_timing
from src.utils.state import init_session_state, require_data_warning

init_session_state()

st.title("🤖 AI Recommendation Card")

if require_data_warning():
    st.stop()

table = st.session_state.get("last_scenario_table")
baseline = st.session_state.get("last_scenario_baseline")
meta = st.session_state.get("last_scenario_meta")

if table is None or baseline is None or meta is None:
    st.warning(
        "⚠️ Chưa có kịch bản khuyến mãi nào được mô phỏng. Vui lòng sang trang "
        "**8. Kịch bản Promotion**, chọn sản phẩm/danh mục và bấm **Chạy mô phỏng kịch bản** trước."
    )
    st.stop()

df = st.session_state["clean_df"]
caps = st.session_state["capabilities"]
profile = st.session_state["business_profile"]
objective = st.session_state["objective"]

candidates = table[table["mechanic"] != "no_promo"]
candidates = candidates[candidates["margin"] >= profile.min_margin_pct]
if candidates.empty:
    candidates = table[table["mechanic"] != "no_promo"]
chosen_scenario = candidates.iloc[0]

ctx = st.session_state.get("last_rule_context")
verdicts = st.session_state.get("last_rule_verdicts")

target_segment = "Khách hàng nói chung"
if ctx:
    if ctx.high_value_customer_share and ctx.high_value_customer_share >= 0.3:
        target_segment = "Khách giá trị cao"
    elif ctx.repeat_rate and ctx.repeat_rate >= 0.35:
        target_segment = "Khách mua lặp lại"

company_daily = aggregate_daily(df)
timing = analyze_best_timing(company_daily)

stockout_risk = None
recommended_stock = chosen_scenario["san_luong"]
if caps.has_inventory and meta["scope"] == "Một SKU cụ thể":
    scoped_df = df[df["product_id"] == meta["scope_value"]]
    current_inv = scoped_df.sort_values("date")["inventory"].iloc[-1]
    inv_rec = plan_sku_inventory(
        meta["scope_value"], baseline.avg_daily_units, current_inv, profile.lead_time_days, profile.safety_stock_days
    )
    recommended_stock = max(chosen_scenario["san_luong"], inv_rec.expected_demand_leadtime + inv_rec.safety_stock)
    stockout_risk = inv_rec.stockout_risk

why_bullets = []
if ctx and verdicts:
    for v in verdicts:
        if v.mechanic == chosen_scenario["mechanic"] and v.reasons:
            why_bullets.extend(v.reasons)
if not why_bullets:
    why_bullets.append(f"Kịch bản này có điểm phù hợp mục tiêu cao nhất trong số các kịch bản đã mô phỏng (điểm {chosen_scenario['diem_muc_tieu']:.2f}/1.0).")
why_bullets.append(f"Margin dự kiến sau khuyến mãi: {chosen_scenario['margin']:.0%}.")
why_bullets.append(timing.best_weekdays_reason)
if timing.seasonal_note:
    why_bullets.append(timing.seasonal_note)

confidence_forecast = "Trung bình"
forecast_cache = st.session_state.get("forecast_cache", {})
for v in forecast_cache.values():
    confidence_forecast = v.confidence
    break

data_caveats = []
if str(chosen_scenario["nguon_uplift"]) == "assumption":
    data_caveats.append(
        "Uplift dùng giả định elasticity mặc định (chưa có đủ lịch sử khuyến mãi thật cho sản phẩm/cơ chế này)."
    )

card = build_recommendation_card(
    objective=objective,
    chosen_scenario=chosen_scenario,
    baseline=baseline,
    business_profile=profile,
    product_focus=meta["product_focus_label"],
    target_segment=target_segment,
    timing=timing,
    recommended_stock=recommended_stock,
    confidence_label_forecast=confidence_forecast,
    why_bullets=why_bullets,
    stockout_risk=stockout_risk,
    data_caveats=data_caveats,
)
st.session_state["last_recommendation_card"] = card

risk_color = {"Thấp": "green", "Trung bình": "orange", "Cao": "red"}[card.risk_label]

with st.container(border=True):
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown(f"### 🎯 Mục tiêu: {card.objective_vi}")
        st.markdown(f"**Sản phẩm/Danh mục:** {card.product_focus}")
        st.markdown(f"**Nhóm khách hàng mục tiêu:** {card.target_segment}")
        st.markdown(f"**Chương trình khuyến mãi:** {card.promotion_label}")
        st.markdown(f"**Thời gian đề xuất:** {card.timing_text}")
    with c2:
        st.markdown(f"**Rủi ro:** :{risk_color}[{card.risk_label}]")
        st.markdown(f"**Độ tin cậy:** {card.confidence_pct_range[0]}–{card.confidence_pct_range[1]}%")

    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Khách hàng dự kiến", f"{card.expected_customers_range[0]:.0f}–{card.expected_customers_range[1]:.0f}")
    m2.metric("Nhu cầu dự kiến (sp)", f"{card.expected_demand_range[0]:.0f}–{card.expected_demand_range[1]:.0f}")
    m3.metric("Tồn kho đề xuất", f"{card.recommended_stock:.0f}")
    if card.expected_roi_range:
        m4.metric("ROI dự kiến", f"{card.expected_roi_range[0]:.0%}–{card.expected_roi_range[1]:.0%}")
    else:
        m4.metric("ROI dự kiến", "N/A")

    m5, m6 = st.columns(2)
    m5.metric("Doanh thu dự kiến", f"{card.expected_revenue_range[0]:,.0f}đ – {card.expected_revenue_range[1]:,.0f}đ")
    m6.metric("Lợi nhuận gộp dự kiến", f"{card.expected_gp_range[0]:,.0f}đ – {card.expected_gp_range[1]:,.0f}đ")

st.subheader("💬 Tại sao PromoPilot AI đề xuất phương án này?")
for bullet in card.why_bullets:
    st.markdown(f"- {bullet}")

if card.data_caveats:
    st.warning("⚠️ Lưu ý về độ tin cậy: " + " ".join(card.data_caveats))

st.caption("👉 Sang trang **10. Campaign Plan** để sinh kế hoạch chiến dịch và nội dung marketing.")
