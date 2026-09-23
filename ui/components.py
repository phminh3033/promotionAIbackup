"""Mảnh HTML dùng lại trên các trang."""
from __future__ import annotations

from ui.formatters import delta_class, signed_pct, sparkline


def badge(text: str, kind: str = "muted") -> str:
    return f'<span class="pp-badge {kind}">{text}</span>'


def kpi_card(label: str, english: str, value: str, delta, spark_values, color: str, icon: str, note: str | None = None) -> str:
    if delta is None:
        delta_html = f'<div class="pp-delta flat">{note or "Chưa đủ kỳ so sánh"}</div>'
    else:
        delta_html = f'<div class="pp-delta {delta_class(delta)}">{signed_pct(delta)} so với tháng trước</div>'
    return f"""
<div class="pp-card">
  <div class="pp-kpi-top">
    <div>
      <div class="pp-kicker">{label}</div>
      <div class="pp-kicker"><span class="en">{english}</span></div>
    </div>
    <div class="pp-ico" style="background:{color}1A;color:{color}">{icon}</div>
  </div>
  <div class="pp-value">{value}</div>
  <div class="pp-kpi-top">{delta_html}{sparkline(spark_values, color)}</div>
</div>
"""


ICO_DB = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v6c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 11v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/></svg>'
ICO_CART = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="9" cy="20" r="1"/><circle cx="18" cy="20" r="1"/><path d="M3 4h2l2.4 11.2a2 2 0 0 0 2 1.6h7.8a2 2 0 0 0 2-1.6L21 8H7"/></svg>'
ICO_PCT = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 5 5 19"/><circle cx="7" cy="7" r="2.2"/><circle cx="17" cy="17" r="2.2"/></svg>'
ICO_TREND = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 17l6-6 4 4 8-8"/><path d="M14 7h7v7"/></svg>'

DASH = "---"
EMPTY = "Chưa có dữ liệu"


def chart_placeholder(caption: str = EMPTY) -> str:
    return f'<div class="pp-chart-ph">{caption}</div>'


def placeholder_table(columns: list[str], rows: int = 3) -> str:
    head = "".join(f"<th>{name}</th>" for name in columns)
    body = "".join("<tr>" + "".join(f"<td>{DASH}</td>" for _ in columns) + "</tr>" for _ in range(rows))
    return (
        '<div class="pp-card" style="overflow-x:auto"><table class="pp-table"><thead><tr>'
        f"{head}</tr></thead><tbody>{body}</tbody></table></div>"
    )
