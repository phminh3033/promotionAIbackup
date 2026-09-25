"""Monitor & Learn: UI theo template — logic KPI/alert/learning giữ nguyên từ engine hiện có."""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd
import streamlit as st

from src.alerts.engine import decide_action, evaluate_alerts
from src.learning.campaign_log import list_campaign_records, save_campaign_record
from src.monitoring.campaign_monitor import build_daily_baseline, compare_actual_vs_forecast, cumulative_variance
from ui.charts import actual_vs_forecast_overlay, show_chart
from ui.components import (
    DASH,
    EMPTY,
    campaign_alert_card,
    learning_item,
    monitor_empty_state,
    monitor_panel_header,
    muted,
    next_action_item,
    performance_metric_card,
    show,
)
from ui.formatters import integer, pct, roi_label, signed_pct, vnd
from ui.nav import goto
from ui.shell import render_shell

ALERT_VISIBLE = 3

# Metric chart: chỉ các cột có trong compared dataframe (actual + forecast).
CHART_METRICS = [
    ("revenue", "Doanh thu", "đ"),
    ("customers", "Khách hàng", ""),
    ("gp", "Lợi nhuận gộp", "đ"),
    ("units", "Sản lượng", ""),
]


@dataclass
class MetricVM:
    title: str
    value: str = DASH
    delta: str | None = None
    delta_tone: str = "flat"
    icon: str = "chart"
    accent: str = "blue"


@dataclass
class AlertVM:
    code: str
    message: str
    level: str


@dataclass
class MonitorViewModel:
    has_campaign: bool = False
    has_actual: bool = False
    metrics: list[MetricVM] = field(default_factory=list)
    alerts: list[AlertVM] = field(default_factory=list)
    lessons: list[tuple[str, str]] = field(default_factory=list)  # text, tone
    next_actions: list[tuple[str, str, str]] = field(default_factory=list)  # title, desc, icon
    chart_options: list[tuple[str, str]] = field(default_factory=list)  # key, label
    insufficient_learning: bool = False
    action_label: str = ""


def render() -> None:
    render_shell(
        "Học hỏi và tối ưu",
        "Theo dõi hiệu quả thực tế, so với dự báo, cảnh báo và bài học cho chiến dịch tiếp theo.",
        stage=7,
    )
    records = list_campaign_records()
    if not records:
        _render_empty_no_campaign()
        return

    record = _pick(records)
    compared = _ensure_compared(record)
    alerts, action = ([], None)
    if compared is not None:
        alerts, action = _evaluate(record)

    vm = build_monitor_view_model(record, compared, alerts, action)
    _render_view(vm, record, compared)


def build_monitor_view_model(record, compared, alerts, action) -> MonitorViewModel:
    """UI adapter — chỉ gom output sẵn có; không đổi công thức monitoring/alerts."""
    vm = MonitorViewModel(has_campaign=True)
    actual_rows = record.actual.get("daily_rows") or []
    vm.has_actual = bool(actual_rows)

    variance = record.variance or {}
    revenue = _sum_field(actual_rows, "revenue")
    customers = _sum_field(actual_rows, "customers")
    gp = _sum_field(actual_rows, "gp")
    margin_actual = (gp / revenue) if revenue and revenue > 0 and gp is not None else None
    margin_forecast = _forecast_margin(record)

    rev_delta, rev_tone = _pct_delta_display(variance.get("revenue"), positive_is_good=True)
    cust_delta, cust_tone = _pct_delta_display(variance.get("customers"), positive_is_good=True)
    margin_delta_txt, margin_tone = _margin_delta_display(margin_actual, margin_forecast)
    roi_delta_txt, roi_tone = _roi_delta_display(record.roi_actual, record.roi_forecast)

    vm.metrics = [
        MetricVM(
            "Doanh thu thực tế",
            vnd(revenue) if revenue is not None else DASH,
            rev_delta,
            rev_tone,
            "coins",
            "blue",
        ),
        MetricVM(
            # Dữ liệu thực tế là customers (không có order count) — giữ nhãn đúng nguồn.
            "Khách hàng",
            integer(customers) if customers is not None else DASH,
            cust_delta,
            cust_tone,
            "cart",
            "purple",
        ),
        MetricVM(
            "Biên lợi nhuận",
            pct(margin_actual, 1) if margin_actual is not None else DASH,
            margin_delta_txt,
            margin_tone,
            "percent",
            "pink",
        ),
        MetricVM(
            "ROI",
            roi_label(record.roi_actual) if record.roi_actual is not None else DASH,
            roi_delta_txt,
            roi_tone,
            "trend",
            "orange",
        ),
    ]

    vm.alerts = [AlertVM(a.code, a.message, a.level) for a in (alerts or [])]

    if compared is not None:
        for key, label, _unit in CHART_METRICS:
            if key in compared.columns and f"{key}_forecast" in compared.columns:
                vm.chart_options.append((key, label))

    lessons: list[tuple[str, str]] = []
    if variance.get("revenue") is not None:
        tone = "ok" if variance["revenue"] >= 0 else "warn"
        lessons.append(
            (f"Doanh thu thực tế {signed_pct(variance['revenue'])} so với dự báo baseline của chiến dịch.", tone)
        )
    if variance.get("customers") is not None:
        tone = "ok" if variance["customers"] >= 0 else "warn"
        lessons.append(
            (f"Lượng khách thực tế {signed_pct(variance['customers'])} so với dự báo baseline.", tone)
        )
    if variance.get("gp") is not None:
        tone = "ok" if variance["gp"] >= 0 else "warn"
        lessons.append(
            (f"Lợi nhuận gộp thực tế {signed_pct(variance['gp'])} so với dự báo baseline.", tone)
        )

    if action is not None:
        vm.action_label = action.action_vi or ""
        reasons = [str(r).strip() for r in (action.reasons or []) if str(r).strip()]
        if reasons:
            vm.next_actions.append((action.action_vi or "Đề xuất hành động", reasons[0], "target"))
            for reason in reasons[1:]:
                vm.next_actions.append(("Cơ sở quyết định", reason, "lightbulb"))
        elif action.action_vi:
            vm.next_actions.append(
                (action.action_vi, "Dựa trên luật cảnh báo và chỉ số thực tế hiện có.", "target")
            )

    if not lessons and not vm.next_actions:
        vm.insufficient_learning = True
        lessons.append(("Chưa đủ dữ liệu thực tế để rút bài học có cơ sở.", "neutral"))

    vm.lessons = lessons
    return vm


def _render_empty_no_campaign() -> None:
    show(
        monitor_empty_state(
            "Chưa có dữ liệu hiệu quả chiến dịch",
            "Khởi chạy chiến dịch ở bước Triển khai, rồi quay lại đây để nhập số thực tế và theo dõi.",
        )
    )
    show(
        '<div class="pp-mon-kpi-grid">'
        + "".join(
            performance_metric_card(t, DASH, EMPTY, "flat", ico, acc)
            for t, ico, acc in [
                ("Doanh thu thực tế", "coins", "blue"),
                ("Khách hàng", "cart", "purple"),
                ("Biên lợi nhuận", "percent", "pink"),
                ("ROI", "trend", "orange"),
            ]
        )
        + "</div>"
    )


def _render_view(vm: MonitorViewModel, record, compared) -> None:
    show(
        '<div class="pp-mon-kpi-grid">'
        + "".join(
            performance_metric_card(m.title, m.value, m.delta, m.delta_tone, m.icon, m.accent)
            for m in vm.metrics
        )
        + "</div>"
    )

    if not vm.has_actual:
        st.info("Chưa có số thực tế. Nhập bảng bên dưới rồi bấm lưu để tính so với dự báo.")

    left, right = st.columns([0.74, 0.26], gap="medium")
    with left:
        _render_chart_panel(vm, compared)
    with right:
        _render_alerts_panel(vm)

    b1, b2 = st.columns(2, gap="medium")
    with b1:
        _render_lessons_panel(vm)
    with b2:
        _render_recommendations_panel(vm)

    with st.expander("Nhập / cập nhật số liệu thực tế", expanded=not vm.has_actual):
        _editor(record)

    if compared is not None and st.button("Lưu đánh giá vào nhật ký", key="save_eval"):
        _alerts, action = _evaluate(record)
        record.ai_action = action.action
        record.ai_action_reasons = action.reasons
        save_campaign_record(record)
        st.success("Đã lưu đánh giá cho chiến dịch này.")

    _, cta = st.columns([2.2, 1.0])
    with cta:
        if st.button("Xuất báo cáo →", type="primary", key="mon_export", width="stretch"):
            goto("reports")


def _render_chart_panel(vm: MonitorViewModel, compared) -> None:
    with st.container(border=True):
        show(
            monitor_panel_header(
                "Thực tế vs Dự báo theo thời gian",
                "So sánh kết quả thực tế với dự báo baseline khi khởi chạy chiến dịch.",
                "chart",
            )
        )
        if compared is None or not vm.chart_options:
            show(muted("Chưa có chuỗi thời gian thực tế để vẽ biểu đồ."))
            return

        labels = [label for _key, label in vm.chart_options]
        keys = [key for key, _label in vm.chart_options]
        selected_label = st.selectbox("Chỉ số", labels, key="mon_chart_metric")
        metric_key = keys[labels.index(selected_label)]
        fig = actual_vs_forecast_overlay(
            compared["date"],
            compared[metric_key],
            compared[f"{metric_key}_forecast"],
            y_title=selected_label,
            actual_name="Thực tế",
            forecast_name="Dự báo",
            height=360,
        )
        if f"{metric_key}_variance_pct" in compared.columns:
            custom = compared[f"{metric_key}_variance_pct"]
            fig.data[0].customdata = list(custom)
            fig.data[0].hovertemplate = (
                "%{x|%d/%m/%Y}<br>Thực tế: %{y:,.0f}"
                "<br>Chênh lệch ngày: %{customdata:.1%}<extra></extra>"
            )
            fig.data[1].hovertemplate = "%{x|%d/%m/%Y}<br>Dự báo: %{y:,.0f}<extra></extra>"
        show_chart(fig)


def _render_alerts_panel(vm: MonitorViewModel) -> None:
    total = len(vm.alerts)
    show_all = bool(st.session_state.get("mon_show_all_alerts"))
    link = f"Xem tất cả ({total}) →" if total > ALERT_VISIBLE and not show_all else ""
    with st.container(border=True):
        show(
            monitor_panel_header(
                "Cảnh báo",
                "Phát hiện sớm các vấn đề cần chú ý trong chiến dịch.",
                "bell",
                "warn",
                link_text=link,
            )
        )
        if not vm.alerts:
            show(muted("Chưa có cảnh báo từ các luật hiện tại."))
        else:
            visible = vm.alerts if show_all else vm.alerts[:ALERT_VISIBLE]
            show(
                '<div class="pp-mon-alert-stack">'
                + "".join(campaign_alert_card(a.code, a.message, a.level) for a in visible)
                + "</div>"
            )
            if total > ALERT_VISIBLE:
                if not show_all:
                    if st.button(f"Xem tất cả ({total}) →", key="mon_alerts_all", type="secondary"):
                        st.session_state["mon_show_all_alerts"] = True
                        st.rerun()
                else:
                    if st.button("Thu gọn", key="mon_alerts_less", type="secondary"):
                        st.session_state["mon_show_all_alerts"] = False
                        st.rerun()


def _render_lessons_panel(vm: MonitorViewModel) -> None:
    with st.container(border=True):
        show(
            monitor_panel_header(
                "Bài học rút ra",
                "Những insight quan trọng từ chiến dịch này (dựa trên so sánh thực tế / dự báo).",
                "lightbulb",
                "green",
            )
        )
        if vm.insufficient_learning and len(vm.lessons) <= 1:
            show(muted("Chưa đủ dữ liệu để kết luận."))
        show(
            '<div class="pp-mon-learn-list">'
            + "".join(learning_item(text, tone) for text, tone in vm.lessons)
            + "</div>"
        )
        with st.expander("Xem chi tiết →", expanded=False):
            st.caption(
                "Nguồn: chênh lệch luỹ kế actual vs baseline dự báo khi launch (không dùng causal claim)."
            )
            for text, _tone in vm.lessons:
                st.write(f"• {text}")


def _render_recommendations_panel(vm: MonitorViewModel) -> None:
    with st.container(border=True):
        show(
            monitor_panel_header(
                "Đề xuất cho lần sau",
                "Hành động đề xuất từ luật Continue / Adjust / Stop / Scale hiện có.",
                "target",
            )
        )
        if not vm.next_actions:
            show(muted("Chưa đủ tín hiệu để đề xuất hành động có cơ sở."))
        else:
            show("".join(next_action_item(title, desc, ico) for title, desc, ico in vm.next_actions))
        with st.expander("Xem chi tiết →", expanded=False):
            if vm.action_label:
                st.caption(f"Quyết định rule-based: {vm.action_label}")
            for title, desc, _ico in vm.next_actions:
                st.write(f"**{title}** — {desc}")


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


def _ensure_compared(record):
    rows = record.actual.get("daily_rows") or []
    if not rows:
        return None
    actual = pd.DataFrame(rows)
    actual["date"] = pd.to_datetime(actual["date"])
    for col in ["revenue", "gp", "customers", "units"]:
        if col in actual.columns:
            actual[col] = pd.to_numeric(actual[col], errors="coerce")
    baseline = _baseline(record)
    compared = compare_actual_vs_forecast(actual, baseline)
    st.session_state["campaign_actual_data"] = compared
    return compared


def _editor(record) -> None:
    default = pd.DataFrame(
        record.actual.get("daily_rows")
        or [
            {
                "date": record.forecast.get("campaign_start", ""),
                "revenue": None,
                "gp": None,
                "customers": None,
                "units": None,
                "inventory_onhand": None,
            }
        ]
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
    cost = st.number_input(
        "Chi phí khuyến mãi thực tế (đ)",
        min_value=0.0,
        value=float(record.actual.get("promo_cost_actual") or 0),
        step=100000.0,
        key=f"cost_{record.campaign_id}",
    )
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
        record.actual = {
            "daily_rows": safe.where(pd.notna(safe), None).to_dict("records"),
            "promo_cost_actual": cost,
        }
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
    latest_inventory = next(
        (row.get("inventory_onhand") for row in reversed(daily_rows) if row.get("inventory_onhand") is not None),
        None,
    )
    units = record.forecast.get("expected_demand_range")
    avg_daily_units = (
        (sum(units) / 2 / max(record.forecast.get("promo_days") or 1, 1)) if units else None
    )
    days_of_inventory = (
        (latest_inventory / avg_daily_units) if latest_inventory is not None and avg_daily_units else None
    )
    total_gp = sum((row.get("gp") or 0) for row in daily_rows)
    total_revenue = sum((row.get("revenue") or 0) for row in daily_rows)
    margin = total_gp / total_revenue if total_revenue else None
    recommended = st.session_state.get("last_recommendation_card")
    ratio = (
        (latest_inventory / recommended.recommended_stock)
        if latest_inventory is not None and recommended and recommended.recommended_stock
        else None
    )
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


def _sum_field(rows: list, field_name: str) -> float | None:
    if not rows:
        return None
    values = [row.get(field_name) for row in rows if row.get(field_name) is not None]
    if not values:
        return None
    return float(sum(values))


def _forecast_margin(record) -> float | None:
    """Margin dự báo từ mid-point khoảng forecast đã lưu lúc launch — không invent."""
    rev = record.forecast.get("expected_revenue_range")
    gp = record.forecast.get("expected_gp_range")
    if not rev or not gp:
        return None
    mid_rev = (float(rev[0]) + float(rev[1])) / 2
    mid_gp = (float(gp[0]) + float(gp[1])) / 2
    if mid_rev <= 0:
        return None
    return mid_gp / mid_rev


def _pct_delta_display(variance: float | None, *, positive_is_good: bool) -> tuple[str | None, str]:
    if variance is None:
        return None, "flat"
    text = f"{signed_pct(variance)} so với dự báo"
    if variance > 1e-9:
        tone = "up" if positive_is_good else "down"
    elif variance < -1e-9:
        tone = "down" if positive_is_good else "up"
    else:
        tone = "flat"
    return text, tone


def _margin_delta_display(actual: float | None, forecast: float | None) -> tuple[str | None, str]:
    if actual is None or forecast is None:
        return None, "flat"
    delta = actual - forecast
    points = delta * 100
    sign = "+" if points >= 0 else ""
    text = f"{sign}{points:.1f} điểm % so với biên dự báo"
    if delta > 1e-9:
        return text, "up"
    if delta < -1e-9:
        return text, "down"
    return text, "flat"


def _roi_delta_display(actual: float | None, forecast: float | None) -> tuple[str | None, str]:
    if actual is None and forecast is None:
        return None, "flat"
    if actual is None:
        return f"ROI dự báo {roi_label(forecast)}", "flat"
    if forecast is None:
        return None, "flat"
    delta = actual - forecast
    sign = "+" if delta >= 0 else ""
    text = f"{sign}{delta:.1%} so với ROI dự báo ({roi_label(forecast)})"
    if delta > 1e-9:
        return text, "up"
    if delta < -1e-9:
        return text, "down"
    return text, "flat"
