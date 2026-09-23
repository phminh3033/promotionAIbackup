"""Command Center — số liệu lấy từ dữ liệu phiên làm việc."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from services.workflow import company_revenue_forecast, kpi_snapshot, opportunity_cards, revenue_by_grain
from src.learning.campaign_log import list_campaign_records
from ui.charts import time_series
from ui.components import DASH, EMPTY, ICO_CART, ICO_DB, ICO_PCT, ICO_TREND, badge, chart_placeholder, kpi_card, placeholder_table
from ui.formatters import compact_vnd, integer, pct, roi_label, vnd
from ui.shell import render_shell

STATUS = {
    "CONTINUE": ("On track", "ok"),
    "SCALE": ("On track", "ok"),
    "ADJUST": ("Cần chú ý", "warn"),
    "STOP": ("Cần chú ý", "bad"),
}


def render() -> None:
    render_shell(
        "Chào mừng bạn đến với PromotionPilot AI",
        "Nền tảng ra quyết định marketing dựa trên dữ liệu và khoa học, giúp bạn tăng trưởng hiệu quả hơn.",
        stage=0,
    )
    snap = kpi_snapshot()
    if snap is None:
        cards = "".join(
            [
                kpi_card("Doanh thu", "Revenue", DASH, None, [], "#2563EB", ICO_DB, note=EMPTY),
                kpi_card("Số đơn hàng", "Orders", DASH, None, [], "#7C3AED", ICO_CART, note=EMPTY),
                kpi_card("Biên lợi nhuận", "Margin", DASH, None, [], "#EC4899", ICO_PCT, note=EMPTY),
                kpi_card("Hiệu quả marketing", "ROI mô phỏng", DASH, None, [], "#F97316", ICO_TREND, note=EMPTY),
            ]
        )
        st.markdown(f'<div class="pp-kpi-grid">{cards}</div>', unsafe_allow_html=True)
        st.radio("Kỳ biểu đồ", ["Tháng", "Quý", "Năm"], horizontal=True, key="cc_grain_empty", label_visibility="collapsed")
        st.markdown(
            '<div class="pp-card" style="margin-bottom:14px"><div class="pp-kicker">Xu hướng doanh thu theo thời gian</div>'
            + chart_placeholder()
            + "</div>",
            unsafe_allow_html=True,
        )
    else:
        cards = "".join(
            [
                kpi_card("Doanh thu", "Revenue", compact_vnd(snap["revenue"]), snap["revenue_delta"], snap["revenue_spark"], "#2563EB", ICO_DB),
                kpi_card("Số đơn hàng", "Orders", integer(snap["orders"]), snap["orders_delta"], snap["orders_spark"], "#7C3AED", ICO_CART),
                kpi_card(
                    "Biên lợi nhuận",
                    "Margin",
                    pct(snap["margin"], 1) if snap["margin"] is not None else "—",
                    snap["margin_delta"],
                    snap["margin_spark"],
                    "#EC4899",
                    ICO_PCT,
                    note=None if snap["margin"] is not None else "Cần cột lợi nhuận gộp hoặc giá vốn",
                ),
                kpi_card("Hiệu quả marketing", "ROI mô phỏng", roi_label(snap["roi"]), None, [], "#F97316", ICO_TREND, note=snap["roi_note"]),
            ]
        )
        st.markdown(f'<div class="pp-kpi-grid">{cards}</div>', unsafe_allow_html=True)
        _chart(snap)
    left, right = st.columns([1.35, 1], gap="medium")
    with left:
        _opportunities()
    with right:
        _campaigns()
    st.markdown(
        '<p class="pp-foot">Khuyến nghị là công cụ hỗ trợ quyết định, không thay thế quyết định cuối cùng của doanh nghiệp. Số liệu trên lấy từ dữ liệu đã tải trong phiên này.</p>',
        unsafe_allow_html=True,
    )


def _chart(snap) -> None:
    grain = st.radio("Kỳ biểu đồ", ["Tháng", "Quý", "Năm"], horizontal=True, key="cc_grain", label_visibility="collapsed")
    series = revenue_by_grain(grain)
    forecast = company_revenue_forecast()
    forecast_x = forecast_y = None
    if forecast is not None and grain == "Tháng":
        frame = pd.DataFrame({"bucket": pd.to_datetime(forecast.dates), "revenue": forecast.yhat})
        frame["bucket"] = frame["bucket"].dt.to_period("M").dt.to_timestamp()
        rolled = frame.groupby("bucket", as_index=False)["revenue"].sum()
        forecast_x, forecast_y = rolled["bucket"], rolled["revenue"]
    fig = time_series(
        series["bucket"],
        series["revenue"],
        forecast_x,
        forecast_y,
        y_title="Doanh thu",
        title="Xu hướng doanh thu theo thời gian",
    )
    st.plotly_chart(fig, use_container_width=True)
    if forecast is None:
        st.caption("Đường dự báo xuất hiện sau khi chạy Forecast cho toàn công ty, chỉ số doanh thu.")


def _opportunities() -> None:
    cards = opportunity_cards()
    st.markdown(
        f'<div class="pp-section"><div><h2 style="display:flex;align-items:center;gap:8px">{ICO_TREND} Cơ hội nổi bật từ mô hình</h2><p>Tính từ dữ liệu bán, phân khúc và thời điểm bán — không dùng số liệu minh hoạ.</p></div></div>',
        unsafe_allow_html=True,
    )
    if not cards:
        blocks = []
        for title in ("Cơ hội nhu cầu", "Kích hoạt khách hàng", "Thời điểm traffic"):
            blocks.append(
                f'<div class="pp-card"><div class="pp-opp-title">{title}</div><p class="pp-muted">{EMPTY}</p><div class="pp-impact">{DASH}</div></div>'
            )
        st.markdown(f'<div class="pp-grid-3">{"".join(blocks)}</div>', unsafe_allow_html=True)
        return
    blocks = []
    for card in cards:
        impact = f'<div class="pp-impact">{compact_vnd(card["impact"])}</div>' if card["impact"] else ""
        blocks.append(
            f"""
<div class="pp-card">
  <div class="pp-opp-title">{card["title"]}</div>
  <div class="pp-muted">{card["body"]}</div>
  {impact}
  <div style="margin-top:8px">{badge(card["priority"], card["tone"])}</div>
</div>
"""
        )
    st.markdown(f'<div class="pp-grid-3">{"".join(blocks)}</div>', unsafe_allow_html=True)


def _campaigns() -> None:
    records = list_campaign_records()
    st.markdown(f'<div class="pp-section"><div><h2 style="display:flex;align-items:center;gap:8px">{ICO_CART} Chiến dịch đang triển khai</h2><p>Nhật ký campaign đã lưu trên máy.</p></div></div>', unsafe_allow_html=True)
    if not records:
        st.markdown(
            placeholder_table(["Chiến dịch", "Thời gian", "Doanh thu", "ROI", "Trạng thái"], rows=3),
            unsafe_allow_html=True,
        )
        return
    rows = []
    for record in records[:6]:
        label, kind = STATUS.get(record.ai_action or "", ("Nháp", "muted"))
        if record.actual.get("daily_rows") and not record.ai_action:
            label, kind = "Đang theo dõi", "info"
        revenue = None
        daily = record.actual.get("daily_rows") or []
        if daily:
            revenue = sum((row.get("revenue") or 0) for row in daily)
        elif record.forecast.get("expected_revenue_range"):
            low, high = record.forecast["expected_revenue_range"]
            revenue = (low + high) / 2
        roi = record.roi_actual if record.roi_actual is not None else record.roi_forecast
        rows.append(
            "<tr>"
            f"<td>{record.promotion_label}</td>"
            f"<td>{record.forecast.get('campaign_start', '—')}</td>"
            f"<td>{vnd(revenue) if revenue is not None else '—'}</td>"
            f"<td>{roi_label(roi)}</td>"
            f"<td>{badge(label, kind)}</td>"
            "</tr>"
        )
    st.markdown(
        '<div class="pp-card" style="overflow-x:auto"><table class="pp-table"><thead><tr>'
        "<th>Chiến dịch</th><th>Bắt đầu</th><th>Doanh thu</th><th>ROI</th><th>Trạng thái</th>"
        f"</tr></thead><tbody>{''.join(rows)}</tbody></table></div>",
        unsafe_allow_html=True,
    )
