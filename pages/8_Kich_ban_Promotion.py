"""Trang Kịch bản Promotion — module trung tâm (mục XIV, XV, XVI yêu cầu gốc)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import plotly.express as px
import streamlit as st

from src.explainability.explainer import (
    explain_basket_lift,
    explain_customer_value_share,
    explain_inventory_status,
    explain_margin_after_promotion,
    explain_repeat_rate,
    explain_trend,
    explain_uplift_source,
)
from src.features.engineering import aggregate_daily
from src.optimization.objective import OBJECTIVE_LABELS_VI, score_scenarios
from src.promotion.mechanics import BaselineMetrics, estimate_historical_uplift
from src.promotion.rules import SkuRuleContext, evaluate_sku_rules, max_allowed_depth
from src.promotion.simulator import simulate_scenarios
from src.recommendation.timing import analyze_best_timing
from src.roi.calculator import compute_roi_breakdown, format_roi_summary_vi
from src.utils.state import init_session_state, require_data_warning

init_session_state()

st.title("🎁 Mô phỏng Kịch bản Promotion")

if require_data_warning():
    st.stop()

df = st.session_state["clean_df"]
caps = st.session_state["capabilities"]
profile = st.session_state["business_profile"]
objective = st.session_state["objective"]

st.info(f"🎯 Mục tiêu kinh doanh hiện tại: **{OBJECTIVE_LABELS_VI[objective]}**. Đổi ở trang *7. Mục tiêu kinh doanh*.")

col1, col2, col3 = st.columns(3)
with col1:
    scope = st.radio("Áp dụng khuyến mãi cho", ["Một SKU cụ thể", "Một Danh mục"], horizontal=False)
with col2:
    if scope == "Một SKU cụ thể":
        top_skus = df.groupby("product_id")["revenue"].sum().sort_values(ascending=False).index.tolist()
        scope_value = st.selectbox("Chọn sản phẩm", top_skus)
        scoped_df = df[df["product_id"] == scope_value]
        product_focus_label = scope_value
    else:
        if not caps.has_category:
            st.warning("Dữ liệu không có cột Danh mục.")
            st.stop()
        scope_value = st.selectbox("Chọn danh mục", sorted(df["category"].dropna().unique()))
        scoped_df = df[df["category"] == scope_value]
        product_focus_label = scope_value
with col3:
    promo_days = st.number_input("Thời gian chạy khuyến mãi (ngày)", min_value=1, max_value=30, value=7)

RECENT_DAYS = 60
cutoff = df["date"].max() - pd.Timedelta(days=RECENT_DAYS)
recent = scoped_df[scoped_df["date"] >= cutoff]
if recent.empty or recent["quantity"].sum() == 0:
    st.warning("Không đủ dữ liệu gần đây cho lựa chọn này để mô phỏng.")
    st.stop()

n_days_recent = (recent["date"].max() - recent["date"].min()).days + 1
avg_daily_units = recent["quantity"].sum() / max(n_days_recent, 1)
avg_price = recent["selling_price"].mean() if caps.has_price else (recent["revenue"].sum() / max(recent["quantity"].sum(), 1))
unit_cost = recent["cost"].mean() if caps.has_cost else avg_price * (1 - profile.target_margin_pct)
avg_daily_customers = (
    recent.groupby(recent["date"].dt.normalize())["customer_id"].nunique().mean() if caps.has_customer else None
)

current_margin = (avg_price - unit_cost) / avg_price if avg_price > 0 else 0
st.caption(
    f"Dữ liệu {RECENT_DAYS} ngày gần nhất: nhu cầu TB {avg_daily_units:.1f} sp/ngày, "
    f"giá bán TB {avg_price:,.0f}đ, giá vốn TB {unit_cost:,.0f}đ (margin hiện tại {current_margin:.0%})."
)

gift_cost_default = round(unit_cost * 0.25) if unit_cost > 0 else 5000
gift_cost_per_unit = st.number_input(
    "Giá trị quà tặng kèm/đơn vị (áp dụng cho kịch bản 'Tặng quà') — VNĐ",
    min_value=0,
    value=int(gift_cost_default),
    step=1000,
)

baseline = BaselineMetrics(
    avg_daily_units=avg_daily_units,
    avg_price=avg_price,
    unit_cost=unit_cost,
    promo_days=promo_days,
    avg_daily_customers=avg_daily_customers,
)

# --- Business Rules được tính TRƯỚC khi mô phỏng, để có thể loại các mechanic bị "rejected"
# (vd hết hàng) ra khỏi danh sách được phép chọn làm "kịch bản tốt nhất" — tránh tình trạng đề
# xuất một kịch bản mà chính luật kinh doanh đã cảnh báo không nên làm (mục XV yêu cầu gốc).
trend_recent = recent["quantity"].sum()
older = scoped_df[(scoped_df["date"] < cutoff) & (scoped_df["date"] >= cutoff - pd.Timedelta(days=RECENT_DAYS))]
velocity_change = (trend_recent - older["quantity"].sum()) / max(older["quantity"].sum(), 1) if not older.empty else 0.0

basket_result = st.session_state.get("basket_result")
has_partner, partner_id = False, None
if basket_result is not None and not basket_result.rules.empty and scope == "Một SKU cụ thể":
    match = basket_result.rules[basket_result.rules["antecedent"] == scope_value]
    if not match.empty:
        has_partner = True
        partner_id = match.iloc[0]["consequent"]

seg_result = st.session_state.get("segmentation_result")
repeat_rate, high_value_share = None, None
if seg_result is not None and seg_result.sufficient_data:
    labeled = seg_result.rfm_labeled
    repeat_rate = float((labeled["frequency"] > 1).mean())
    hv_customers = labeled[labeled["segment"] == "Khách giá trị cao"]["customer_id"]
    if caps.has_customer and len(hv_customers) > 0:
        scope_revenue = scoped_df["revenue"].sum()
        hv_revenue = scoped_df[scoped_df["customer_id"].isin(hv_customers)]["revenue"].sum()
        high_value_share = float(hv_revenue / scope_revenue) if scope_revenue > 0 else 0.0

days_of_inventory = float("inf")
if caps.has_inventory and scope == "Một SKU cụ thể":
    latest_inv = scoped_df.sort_values("date")["inventory"].iloc[-1]
    days_of_inventory = latest_inv / avg_daily_units if avg_daily_units > 0 else float("inf")

ctx = SkuRuleContext(
    product_id=product_focus_label,
    days_of_inventory=days_of_inventory,
    sales_velocity_change_pct=velocity_change,
    margin_pct=current_margin,
    has_basket_partner=has_partner,
    basket_partner_id=partner_id,
    repeat_rate=repeat_rate,
    high_value_customer_share=high_value_share,
    lead_time_days=profile.lead_time_days,
)
verdicts = evaluate_sku_rules(ctx, profile.min_margin_pct, profile.max_discount_pct)
st.session_state["last_rule_context"] = ctx
st.session_state["last_rule_verdicts"] = verdicts
rejected_mechanics = {v.mechanic for v in verdicts if v.verdict == "rejected"}

if st.button("🚀 Chạy mô phỏng kịch bản", type="primary"):
    max_overrides = {
        "discount_percent": max_allowed_depth("discount_percent", unit_cost, avg_price, profile.min_margin_pct, profile.max_discount_pct),
        "bundle": max_allowed_depth("bundle", unit_cost, avg_price, profile.min_margin_pct, profile.max_discount_pct),
    }
    hist_uplift = estimate_historical_uplift(scoped_df) if caps.has_promotion else {}
    sim = simulate_scenarios(
        baseline,
        historical_uplifts=hist_uplift,
        gift_cost_per_unit=gift_cost_per_unit,
        max_discount_overrides=max_overrides,
    )
    roi_table = compute_roi_breakdown(sim.table, baseline)
    scored_table = score_scenarios(roi_table, objective, current_inventory=None)
    # "no_promo" không bao giờ bị reject (không tiêu thêm tồn kho), các mechanic khác bị loại nếu
    # Business Rules đã đánh giá "rejected" (vd tồn kho không đủ so với lead time).
    scored_table["bi_tu_choi"] = scored_table["mechanic"].isin(rejected_mechanics) & (scored_table["mechanic"] != "no_promo")

    st.session_state["last_scenario_table"] = scored_table
    st.session_state["last_scenario_baseline"] = baseline
    st.session_state["last_scenario_meta"] = {
        "scope": scope,
        "scope_value": scope_value,
        "product_focus_label": product_focus_label,
        "promo_days": promo_days,
        "gift_cost_per_unit": gift_cost_per_unit,
        "hist_uplift": hist_uplift,
    }

table = st.session_state.get("last_scenario_table")
meta = st.session_state.get("last_scenario_meta")

if table is not None and meta and meta["scope_value"] == scope_value:
    st.divider()
    st.warning(f"⚠️ {simulate_scenarios(baseline, {}).disclaimer}")

    if "bi_tu_choi" not in table.columns:
        table["bi_tu_choi"] = False

    display = table.copy()
    display["margin"] = display["margin"].map(lambda v: f"{v:.0%}")
    display["roi"] = display["roi"].map(lambda v: f"{v:.0%}" if pd.notna(v) else "N/A")
    display["uplift_gia_dinh"] = display["uplift_gia_dinh"].map(lambda v: f"{v:.0%}")
    display["trang_thai"] = display["bi_tu_choi"].map(lambda v: "⛔ Bị từ chối (Business Rules)" if v else "✅ Hợp lệ")
    st.dataframe(
        display[
            ["scenario", "trang_thai", "san_luong", "doanh_thu", "loi_nhuan_gop", "margin", "chi_phi_khuyen_mai", "roi", "uplift_gia_dinh", "nguon_uplift", "diem_muc_tieu"]
        ].rename(
            columns={
                "scenario": "Kịch bản",
                "trang_thai": "Trạng thái",
                "san_luong": "Sản lượng",
                "doanh_thu": "Doanh thu",
                "loi_nhuan_gop": "Lợi nhuận gộp",
                "margin": "Margin",
                "chi_phi_khuyen_mai": "Chi phí KM",
                "roi": "ROI",
                "uplift_gia_dinh": "Uplift giả định",
                "nguon_uplift": "Nguồn uplift",
                "diem_muc_tieu": f"Điểm mục tiêu ({OBJECTIVE_LABELS_VI[objective]})",
            }
        ),
        use_container_width=True,
    )

    eligible = table[~table["bi_tu_choi"]]
    best_row = eligible.iloc[0] if not eligible.empty else table.iloc[0]
    if table["bi_tu_choi"].any():
        st.caption(
            "⛔ Một số kịch bản bị loại khỏi đề xuất vì Business Rules đánh giá không khả thi "
            "(xem chi tiết lý do ở mục Business Rules bên dưới) — kịch bản tốt nhất chỉ chọn trong "
            "số các kịch bản còn hợp lệ."
        )
    st.success(
        f"🏆 Kịch bản tốt nhất cho mục tiêu **{OBJECTIVE_LABELS_VI[objective]}**: **{best_row['scenario']}**"
    )
    st.write(format_roi_summary_vi(best_row))

    col_a, col_b = st.columns(2)
    with col_a:
        fig1 = px.bar(table, x="scenario", y="loi_nhuan_gop", title="Lợi nhuận gộp theo kịch bản", labels={"scenario": "Kịch bản", "loi_nhuan_gop": "Lợi nhuận gộp (VNĐ)"})
        st.plotly_chart(fig1, use_container_width=True)
    with col_b:
        roi_chart_df = table[table["roi"].notna()]
        fig2 = px.bar(roi_chart_df, x="scenario", y="roi", title="ROI theo kịch bản", labels={"scenario": "Kịch bản", "roi": "ROI"})
        fig2.update_yaxes(tickformat=".0%")
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.subheader("📐 Đánh giá theo Business Rules")
    st.caption(
        "Các kịch bản bị đánh dấu ⛔ dưới đây đã được loại khỏi lựa chọn 'kịch bản tốt nhất' ở trên."
    )

    verdict_icon = {"recommended": "✅", "neutral": "➖", "caution": "⚠️", "rejected": "⛔"}
    for v in verdicts:
        if v.reasons:
            from src.promotion.mechanics import MECHANIC_LABELS_VI

            st.write(f"{verdict_icon[v.verdict]} **{MECHANIC_LABELS_VI.get(v.mechanic, v.mechanic)}**: " + " ".join(v.reasons))

    st.subheader("💬 Giải thích thêm (Explainable AI)")
    st.write(f"- {explain_trend(velocity_change)}")
    st.write(f"- {explain_inventory_status(days_of_inventory, profile.lead_time_days)}")
    if repeat_rate is not None:
        st.write(f"- {explain_repeat_rate(repeat_rate)}")
    if has_partner:
        rule_row = basket_result.rules[basket_result.rules["antecedent"] == scope_value].iloc[0]
        st.write(f"- {explain_basket_lift(partner_id, rule_row['lift'], rule_row['confidence'])}")
    if high_value_share is not None:
        st.write(f"- {explain_customer_value_share(high_value_share)}")
    st.write(f"- {explain_margin_after_promotion(best_row['margin'], profile.min_margin_pct)}")
    st.write(f"- {explain_uplift_source(str(best_row['nguon_uplift']))}")

    st.caption("👉 Sang trang **9. AI Recommendation** để xem thẻ đề xuất tổng hợp và kế hoạch campaign.")
