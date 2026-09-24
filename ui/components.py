"""Component trình bày dùng chung. Không tính số liệu nghiệp vụ."""
from __future__ import annotations

from html import escape

import streamlit as st

from ui.formatters import delta_class, signed_pct, sparkline
from ui.icons import icon

DASH = "---"
EMPTY = "Chưa có dữ liệu"

ICO_DB = icon("database")
ICO_CART = icon("cart")
ICO_PCT = icon("percent")
ICO_TREND = icon("trend")


def esc(value) -> str:
    return escape("" if value is None else str(value), quote=True)


def show(fragment: str) -> None:
    if fragment and fragment.strip():
        st.html(fragment)


def badge(text: str, kind: str = "muted") -> str:
    return f'<span class="pp-badge {kind}">{esc(text)}</span>'


def kicker(text: str) -> str:
    return f'<div class="pp-kicker">{esc(text)}</div>'


def kicker_raw(inner_html: str) -> str:
    return f'<div class="pp-kicker">{inner_html}</div>'


def muted(text: str) -> str:
    return f'<p class="pp-muted">{esc(text)}</p>'


def card(inner_html: str, extra_class: str = "", style: str = "") -> str:
    klass = f"pp-card {extra_class}".strip()
    style_attr = f' style="{style}"' if style else ""
    return f'<div class="{klass}"{style_attr}>{inner_html}</div>'


def kpi_card(label: str, english: str, value: str, delta, spark_values, color: str, icon_html: str, note: str | None = None) -> str:
    if delta is None:
        delta_html = f'<div class="pp-delta flat">{esc(note or "Chưa đủ kỳ so sánh")}</div>'
    else:
        delta_html = f'<div class="pp-delta {delta_class(delta)}">{esc(signed_pct(delta))} so với tháng trước</div>'
    return f"""
<div class="pp-card">
  <div class="pp-kpi-top">
    <div>
      <div class="pp-kicker">{esc(label)}</div>
      <div class="pp-kicker"><span class="en">{esc(english)}</span></div>
    </div>
    <div class="pp-ico" style="background:{color}1A;color:{color}">{icon_html}</div>
  </div>
  <div class="pp-value">{esc(value)}</div>
  <div class="pp-kpi-top">{delta_html}{sparkline(spark_values, color)}</div>
</div>
"""


def stat_card(label: str, value: str, note: str = "", compact: bool = False) -> str:
    size = " is-compact" if compact else ""
    note_html = f'<div class="pp-muted">{esc(note)}</div>' if note else ""
    return card(f'<div class="pp-kicker">{esc(label)}</div><div class="pp-value{size}">{esc(value)}</div>{note_html}')


def kpi_grid(children: list[str]) -> str:
    return f'<div class="pp-kpi-grid">{"".join(children)}</div>'


def grid(children: list[str], columns: int = 3, style: str = "") -> str:
    extra = f' style="{style}"' if style else ""
    return f'<div class="pp-grid-{columns}"{extra}>{"".join(children)}</div>'


def section(title: str, subtitle: str = "", icon_html: str = "") -> str:
    ico = f'<span class="pp-sec-ico">{icon_html}</span>' if icon_html else ""
    sub = f"<p>{esc(subtitle)}</p>" if subtitle else ""
    return f'<div class="pp-section"><div><h2>{ico}{esc(title)}</h2>{sub}</div></div>'


def banner(text: str, kind: str = "") -> str:
    klass = f"pp-banner {kind}".strip()
    return f'<div class="{klass}">{esc(text)}</div>'


def info_banner(title: str, description: str, icon_name: str = "info") -> str:
    return f"""
<div class="pp-info-banner">
  <div class="pp-info-ico">{icon(icon_name, 20)}</div>
  <div>
    <div class="pp-info-title">{esc(title)}</div>
    <p class="pp-info-desc">{esc(description)}</p>
  </div>
</div>
"""


def insight_input_card(
    title: str,
    subtitle: str,
    description: str,
    status: str,
    accent: str = "blue",
    icon_name: str = "info",
    ok: bool = False,
) -> str:
    """Phần đầu thẻ Insight — nút CTA vẫn là Streamlit button bên dưới."""
    status_l = status.lower()
    if ok or status_l in {"hoàn thành"}:
        kind = "ok"
    elif status_l in {"sẵn sàng", "ready"}:
        kind = "info"
    elif status_l in {"cần chú ý"}:
        kind = "warn"
    else:
        kind = "muted"
    return f"""
<div class="pp-insight-card">
  <div class="pp-insight-head">
    <div class="pp-insight-ico accent-{esc(accent)}">{icon(icon_name, 20)}</div>
    <div>
      <div class="pp-insight-title">{esc(title)}</div>
      <div class="pp-insight-sub">{esc(subtitle)}</div>
    </div>
  </div>
  <p class="pp-insight-desc">{esc(description)}</p>
  <div class="pp-insight-foot">{badge(status, kind)}</div>
</div>
"""


def contribution_bar(label: str, percent: float) -> str:
    value = max(0.0, min(100.0, float(percent)))
    return f"""
<div class="pp-contrib">
  <div class="pp-contrib-row"><span>{esc(label)}</span><b>{value:.0f}%</b></div>
  <div class="pp-contrib-track"><div style="width:{value:.0f}%"></div></div>
</div>
"""


def model_insight_panel(
    insight_text: str,
    factors: list[tuple[str, float]],
    confidence_pct: int | None,
    confidence_note: str,
) -> str:
    if factors:
        total = sum(max(0.0, float(weight)) for _label, weight in factors) or 1.0
        bars = "".join(
            contribution_bar(label, 100.0 * max(0.0, float(weight)) / total)
            for label, weight in factors
        )
    else:
        bars = muted(EMPTY)
    if confidence_pct is None:
        ring = f'<div class="pp-conf-empty"><span>{DASH}</span><small>{esc(EMPTY)}</small></div>'
    else:
        ring = (
            f'<div class="pp-conf-ring" style="--p:{int(confidence_pct)}">'
            f"<span>{int(confidence_pct)}%</span></div>"
        )
    return f"""
<div class="pp-model-insight">
  <div class="pp-mi-head">
    <div class="pp-mi-title">{icon("sparkles", 18)} Model Insight</div>
    <p>Phát hiện quan trọng từ dữ liệu của bạn</p>
  </div>
  <div class="pp-mi-grid">
    <div class="pp-mi-main">
      <div class="pp-mi-quote">{icon("lightbulb", 18)}<span>{esc(insight_text)}</span></div>
    </div>
    <div class="pp-mi-factors">
      <div class="pp-kicker">Các yếu tố đóng góp</div>
      {bars}
    </div>
    <div class="pp-mi-conf">
      <div class="pp-kicker">Độ tin cậy</div>
      {ring}
      <p class="pp-muted">{esc(confidence_note)}</p>
    </div>
  </div>
</div>
"""


def metric_mini(label: str, value: str, small: bool = False) -> str:
    size = ' style="font-size:14px"' if small else ""
    return f'<div class="pp-metric-mini"><div class="l">{esc(label)}</div><div class="v"{size}>{esc(value)}</div></div>'


def metric_mini_html(label: str, value_html: str) -> str:
    return f'<div class="pp-metric-mini"><div class="l">{esc(label)}</div><div class="v">{value_html}</div></div>'


def bullets(items: list[str]) -> str:
    return '<ul class="pp-list">' + "".join(f"<li>{esc(item)}</li>" for item in items) + "</ul>"


def bullets_html(items_html: list[str]) -> str:
    return '<ul class="pp-list">' + "".join(f"<li>{item}</li>" for item in items_html) + "</ul>"


def defs(pairs: list[tuple[str, str]]) -> str:
    return "".join(f'<p class="pp-def"><b>{esc(label)}</b><span>{esc(value)}</span></p>' for label, value in pairs)


def chart_placeholder(caption: str = EMPTY) -> str:
    return f'<div class="pp-chart-ph">{esc(caption)}</div>'


def chart_card(title: str, inner_html: str | None = None) -> str:
    return card(kicker(title) + (inner_html if inner_html is not None else chart_placeholder()))


def data_table(headers: list[str], rows: list[list[str]], title: str = "", raw: bool = False) -> str:
    def cell(value: str) -> str:
        return value if raw else esc(value)

    head = "".join(f"<th>{esc(name)}</th>" for name in headers)
    body = "".join("<tr>" + "".join(f"<td>{cell(col)}</td>" for col in row) + "</tr>" for row in rows)
    title_html = kicker(title) if title else ""
    return card(
        f'{title_html}<div class="pp-scroll"><table class="pp-table"><thead><tr>{head}</tr></thead>'
        f"<tbody>{body}</tbody></table></div>",
        extra_class="pp-table-card",
    )


def placeholder_table(columns: list[str], rows: int = 3) -> str:
    return data_table(columns, [[DASH] * len(columns) for _ in range(rows)])


def score_ring(center: str, percent: float, color: str, title: str, detail: str) -> str:
    return (
        '<div class="pp-card pp-ring-wrap">'
        f'<div class="pp-ring" style="--p:{float(percent):.0f};--c:{esc(color)}"><span>{esc(center)}</span></div>'
        f"<div>{kicker(title)}{muted(detail)}</div></div>"
    )


def progress(ratio: float) -> str:
    width = max(0.0, min(1.0, float(ratio)))
    return f'<div class="pp-bar" style="margin:8px 0"><div style="width:{width:.0%}"></div></div>'


def status_head(title: str, desc: str, state: str, ok: bool) -> str:
    return (
        '<div class="pp-card-head">'
        + kicker(title)
        + muted(desc)
        + f'<div>{badge(state, "ok" if ok else "warn")}</div></div>'
    )


def opportunity_card(title: str, body: str, impact: str = "", badge_html: str = "") -> str:
    impact_html = f'<div class="pp-impact">{esc(impact)}</div>' if impact else ""
    badge_row = f'<div class="pp-meta">{badge_html}</div>' if badge_html else ""
    return card(f'<div class="pp-opp-title">{esc(title)}</div><div class="pp-muted">{esc(body)}</div>{impact_html}{badge_row}')


def scenario_card(label: str, title: str, lines: list[str], badges_html: str = "", selected: bool = False) -> str:
    heading = f'<div class="pp-opp-title">{esc(title)}</div>' if title else ""
    body = "".join(f'<div class="pp-muted">{esc(line)}</div>' for line in lines)
    badges = f'<div class="pp-meta">{badges_html}</div>' if badges_html else ""
    return card(kicker(label) + heading + body + badges, extra_class="pp-selected" if selected else "")


def model_card(title: str, subtitle: str, rows: list[tuple[str, str]], badge_html: str) -> str:
    facts = "".join(f'<p class="pp-muted"><b>{esc(label)}.</b> {esc(value)}</p>' for label, value in rows)
    return card(kicker(title) + f'<div class="pp-opp-title">{esc(subtitle)}</div>{facts}<div class="pp-meta">{badge_html}</div>')


def footnote(text: str) -> str:
    return f'<p class="pp-foot">{esc(text)}</p>'


def gate_intro() -> str:
    mark = icon("target", 18).replace('stroke="currentColor"', 'stroke="white"')
    return f"""
<div class="pp-gate">
  <div class="pp-logo pp-logo-center">
    <div class="pp-logo-mark">{mark}</div>
  </div>
  <h2>PromotionPilot AI</h2>
  <p class="pp-muted">Bản demo giới hạn truy cập. Nhập mã được cung cấp để tiếp tục.</p>
</div>
"""
