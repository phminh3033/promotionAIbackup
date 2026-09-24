"""Monitor: actual vs forecast, cảnh báo và bài học — cùng hàm monitoring/alerts cũ."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from src.alerts.engine import decide_action, evaluate_alerts
from src.learning.campaign_log import list_campaign_records, save_campaign_record
from src.monitoring.campaign_monitor import build_daily_baseline, compare_actual_vs_forecast, cumulative_variance
from ui.charts import show_chart, time_series
from ui.components import DASH, EMPTY, badge, banner, bullets, card, chart_card, grid, kicker, kpi_grid, muted, section, show, stat_card
from ui.formatters import integer, pct, roi_label, signed_pct, vnd
from ui.nav import goto
from ui.shell import render_shell

LEVEL_KIND = {"critical": ("Cao", "bad"), "warning": ("Trung bình", "warn"), "info": ("Thấp", "info")}


def render() -> None:
    render_shell("Monitor & Learn", "Theo dõi hiệu quả, cảnh báo và bài học kinh nghiệm.", stage=7)
    records = list_campaign_records()
    if not records:
        _empty_monitor()
        return
    record = _pick(records)
    _kpis(record)
    compared = _chart(record)
    _editor(record)
    if compared is not None:
        alerts, action = _evaluate(record)
        _alerts(alerts)
        _learning(record, action)
        if st.button("Lưu đánh giá vào nhật ký", key="save_eval"):
            record.ai_action = action.action
            record.ai_action_reasons = action.reasons
            save_campaign_record(record)
            st.success("Đã lưu đánh giá cho chiến dịch này.")
    if st.button("Xuất báo cáo", key="mon_export"):
        goto("reports")


def _empty_monitor() -> None:
    show(kpi_grid([
        stat_card("Doanh thu thực tế", DASH, EMPTY),
        stat_card("Số đơn hàng", DASH, EMPTY),
        stat_card("Biên lợi nhuận", DASH, EMPTY),
        stat_card("ROI", DASH, EMPTY),
    ]))
    show(chart_card("Thực tế và dự báo theo thời gian"))
    show(grid([card(kicker(title) + muted(EMPTY)) for title in ("Tồn kho thấp", "Traffic so với dự báo", "Biên lợi nhuận")], style="margin-top:12px"))
    show(grid([card(kicker(title) + muted(EMPTY)) for title in ("Điểm đang đạt", "Điểm dưới dự báo", "Đề xuất vòng sau")], style="margin-top:12px"))


def _pick(records):
    ids = [item.campaign_id for item in records]
    active = st.session_state.get("active_campaign_id")
    index = ids.index(active) if active in ids else 0
    selected = st.selectbox(
        "Chiến dịch",
        ids,
        index=index,
        format_func=lambda cid: f"{cid} — {next(item.promotion_label for item in records if item.campaign_id == cid)}",
        key="mon_campaign",
    )
    st.session_state["active_campaign_id"] = selected
    return next(item for item in records if item.campaign_id == selected)


def _kpis(record) -> None:
    variance = record.variance or {}
    actual_rows = record.actual.get("daily_rows") or []
    revenue = sum((row.get("revenue") or 0) for row in actual_rows) if actual_rows else None
    orders = sum((row.get("customers") or 0) for row in actual_rows) if actual_rows else None
    gp = sum((row.get("gp") or 0) for row in actual_rows) if actual_rows else None
    margin = (gp / revenue) if revenue else None
    show(kpi_grid([
        stat_card("Doanh thu thực tế", vnd(revenue) if revenue else "—", f"so với dự báo {signed_pct(variance.get('revenue'))}", compact=True),
        stat_card("Khách hàng", integer(orders) if orders else "—", f"so với dự báo {signed_pct(variance.get('customers'))}"),
        stat_card("Biên lợi nhuận", pct(margin, 1) if margin is not None else "—", f"so với dự báo {signed_pct(variance.get('gp'))}"),
        stat_card("ROI", roi_label(record.roi_actual), f"ROI dự báo {roi_label(record.roi_forecast)}"),
    ]))


def _chart(record):
    rows = record.actual.get("daily_rows") or []
    if not rows:
        st.info("Chưa có số thực tế. Nhập bảng bên dưới rồi bấm lưu.")
        return None
    actual = pd.DataFrame(rows)
    actual["date"] = pd.to_datetime(actual["date"])
    for col in ["revenue", "gp", "customers", "units"]:
        if col in actual.columns:
            actual[col] = pd.to_numeric(actual[col], errors="coerce")
    baseline = _baseline(record)
    compared = compare_actual_vs_forecast(actual, baseline)
    if "revenue" in compared.columns and "revenue_forecast" in compared.columns:
        fig = time_series(
            compared["date"],
            compared["revenue"],
            compared["date"],
            compared["revenue_forecast"],
            y_title="Doanh thu",
            title="Thực tế và dự báo theo ngày",
        )
        show_chart(fig)
    st.session_state["campaign_actual_data"] = compared
    return compared


def _editor(record) -> None:
    default = pd.DataFrame(
        record.actual.get("daily_rows")
        or [{"date": record.forecast.get("campaign_start", ""), "revenue": None, "gp": None, "customers": None, "units": None, "inventory_onhand": None}]
    )
    if "date" in default.columns:
        default["date"] = pd.to_datetime(default["date"], errors="coerce")
    edited = st.data_editor(
        default,
        num_rows="dynamic",
        width="stretch",
        key=f"actual_{record.campaign_id}",
        column_config={
            "date": st.column_config.DateColumn("Ngày", required=True),
            "revenue": st.column_config.NumberColumn("Doanh thu"),
            "gp": st.column_config.NumberColumn("Lợi nhuận gộp"),
            "customers": st.column_config.NumberColumn("Khách hàng"),
            "units": st.column_config.NumberColumn("Sản lượng"),
            "inventory_onhand": st.column_config.NumberColumn("Tồn kho"),
        },
    )
    cost = st.number_input("Chi phí khuyến mãi thực tế (đ)", min_value=0.0, value=float(record.actual.get("promo_cost_actual") or 0), step=100000.0, key=f"cost_{record.campaign_id}")
    if st.button("Lưu số thực tế", type="primary", key="save_actual"):
        frame = edited.dropna(subset=["date"]).copy()
        frame["date"] = pd.to_datetime(frame["date"])
        for col in ["revenue", "gp", "customers", "units", "inventory_onhand"]:
            if col in frame.columns:
                frame[col] = pd.to_numeric(frame[col], errors="coerce")
        baseline = _baseline(record)
        compared = compare_actual_vs_forecast(frame, baseline)
        record.variance = {
            "revenue": cumulative_variance(compared, "revenue"),
            "gp": cumulative_variance(compared, "gp"),
            "customers": cumulative_variance(compared, "customers"),
            "units": cumulative_variance(compared, "units"),
        }
        record.roi_actual = _roi(frame, record, cost)
        safe = frame.copy()
        safe["date"] = safe["date"].dt.strftime("%Y-%m-%d")
        record.actual = {"daily_rows": safe.where(pd.notna(safe), None).to_dict("records"), "promo_cost_actual": cost}
        save_campaign_record(record)
        st.success("Đã lưu và tính lại chênh lệch so với dự báo.")
        st.rerun()


def _baseline(record):
    return build_daily_baseline(
        expected_revenue_range=tuple(record.forecast["expected_revenue_range"]),
        expected_gp_range=tuple(record.forecast["expected_gp_range"]),
        expected_customers_range=tuple(record.forecast["expected_customers_range"]),
        expected_demand_range=tuple(record.forecast["expected_demand_range"]),
        promo_days=record.forecast.get("promo_days") or 7,
    )


def _roi(frame, record, cost):
    no_promo = record.forecast.get("no_promo_gp_per_day")
    if cost and no_promo is not None and "gp" in frame.columns and frame["gp"].notna().any():
        incremental = float(frame["gp"].sum()) - no_promo * len(frame)
        return incremental / cost
    return None


def _evaluate(record):
    profile = st.session_state["business_profile"]
    daily_rows = record.actual.get("daily_rows") or []
    latest_inventory = next((row.get("inventory_onhand") for row in reversed(daily_rows) if row.get("inventory_onhand") is not None), None)
    units = record.forecast.get("expected_demand_range")
    avg_daily_units = (sum(units) / 2 / max(record.forecast.get("promo_days") or 1, 1)) if units else None
    days_of_inventory = (latest_inventory / avg_daily_units) if latest_inventory is not None and avg_daily_units else None
    total_gp = sum((row.get("gp") or 0) for row in daily_rows)
    total_revenue = sum((row.get("revenue") or 0) for row in daily_rows)
    margin = total_gp / total_revenue if total_revenue else None
    recommended = st.session_state.get("last_recommendation_card")
    ratio = (latest_inventory / recommended.recommended_stock) if latest_inventory is not None and recommended and recommended.recommended_stock else None
    alerts = evaluate_alerts(
        cumulative_revenue_variance=record.variance.get("revenue"),
        current_margin_pct=margin,
        min_margin_pct=profile.min_margin_pct,
        days_of_inventory=days_of_inventory,
        cumulative_customers_variance=record.variance.get("customers"),
        inventory_vs_forecast_ratio=ratio,
        actual_roi=record.roi_actual,
        min_roi_pct=profile.min_roi_pct,
    )
    action = decide_action(
        alerts=alerts,
        cumulative_revenue_variance=record.variance.get("revenue"),
        cumulative_customers_variance=record.variance.get("customers"),
        actual_roi=record.roi_actual,
        min_roi_pct=profile.min_roi_pct,
    )
    record.ai_action = action.action
    record.ai_action_reasons = action.reasons
    return alerts, action


def _alerts(alerts) -> None:
    if not alerts:
        show(banner("Không có cảnh báo từ các luật hiện tại.", "good"))
        return
    blocks = []
    for item in alerts:
        label, kind = LEVEL_KIND.get(item.level, ("Thấp", "info"))
        blocks.append(card(kicker(item.code) + muted(item.message) + badge(label, kind)))
    show(section("Cảnh báo"))
    show(grid(blocks))


def _learning(record, action) -> None:
    worked, weak = [], []
    if record.variance.get("revenue") is not None:
        (worked if record.variance["revenue"] >= 0 else weak).append(f"Doanh thu thực tế {signed_pct(record.variance['revenue'])} so với dự báo.")
    if record.variance.get("gp") is not None:
        (worked if record.variance["gp"] >= 0 else weak).append(f"Lợi nhuận gộp {signed_pct(record.variance['gp'])} so với dự báo.")
    lessons = list(action.reasons) or ["Chưa đủ tín hiệu để rút bài học."]
    worked_items = worked or ["Chưa có chỉ số vượt dự báo."]
    weak_items = weak or ["Chưa có chỉ số dưới dự báo."]
    show(grid([
        card(kicker("Điểm đang đạt") + bullets(worked_items)),
        card(kicker("Điểm dưới dự báo") + bullets(weak_items)),
        card(kicker("Đề xuất vòng sau") + muted(action.action_vi) + bullets(lessons)),
    ], style="margin-top:12px"))
