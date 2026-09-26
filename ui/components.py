"""Component trình bày dùng chung. Không tính số liệu nghiệp vụ."""
from __future__ import annotations

from html import escape

import streamlit as st

from ui.formatters import delta_class, integer, signed_pct, sparkline
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


def chart_workspace_header(title: str, subtitle: str, icon_name: str = "file") -> str:
    return f"""
<div class="pp-chart-head">
  <div class="pp-chart-head-ico">{icon(icon_name, 18)}</div>
  <div>
    <div class="pp-chart-head-title">{esc(title)}</div>
    <div class="pp-chart-head-sub">{esc(subtitle)}</div>
  </div>
</div>
"""


def forecast_metric_card(
    title: str,
    value: str,
    icon_name: str,
    unit: str | None = None,
    delta: str | None = None,
    comparison: str | None = None,
    accent: str = "purple",
    note: str | None = None,
) -> str:
    value_html = esc(value)
    if unit and value not in {DASH, "—", ""}:
        value_html = f'{value_html}<span class="pp-fm-unit">{esc(unit)}</span>'
    delta_html = ""
    if delta:
        klass = "up" if str(delta).startswith("+") else ("down" if str(delta).startswith("-") else "flat")
        extra = f' {esc(comparison)}' if comparison else ""
        delta_html = f'<div class="pp-fm-delta {klass}">{esc(delta)}{extra}</div>'
    elif note:
        delta_html = f'<div class="pp-fm-delta flat">{esc(note)}</div>'
    return f"""
<div class="pp-forecast-metric accent-{esc(accent)}">
  <div class="pp-fm-top">
    <div class="pp-fm-label">{esc(title)}</div>
    <div class="pp-fm-ico">{icon(icon_name, 18)}</div>
  </div>
  <div class="pp-fm-value">{value_html}</div>
  {delta_html}
</div>
"""


def forecast_summary_panel(title: str, subtitle: str, cards_html: str, icon_name: str = "chart-column") -> str:
    return f"""
<div class="pp-forecast-summary">
  <div class="pp-fs-head">
    <div class="pp-fs-ico">{icon(icon_name, 18)}</div>
    <div>
      <div class="pp-fs-title">{esc(title)}</div>
      <div class="pp-fs-sub">{esc(subtitle)}</div>
    </div>
  </div>
  <div class="pp-fs-stack">{cards_html}</div>
</div>
"""


def model_insight_card(title: str, subtitle: str, bullets_list: list[str], icon_name: str = "lightbulb") -> str:
    if bullets_list:
        items = "".join(f"<li>{esc(item)}</li>" for item in bullets_list)
        body = f'<ul class="pp-mi-bullets">{items}</ul>'
    else:
        body = muted(EMPTY)
    return f"""
<div class="pp-fc-insight">
  <div class="pp-fc-section-head">
    <div class="pp-fc-section-ico">{icon(icon_name, 18)}</div>
    <div>
      <div class="pp-fc-section-title">{esc(title)}</div>
      <div class="pp-fc-section-sub">{esc(subtitle)}</div>
    </div>
  </div>
  {body}
</div>
"""


def contribution_factor_card(
    title: str,
    value: str,
    description: str,
    icon_name: str,
    direction: str = "neutral",
) -> str:
    return f"""
<div class="pp-factor-card is-{esc(direction)}">
  <div class="pp-factor-top">
    <div class="pp-factor-ico">{icon(icon_name, 18)}</div>
    <div class="pp-factor-value">{esc(value)}</div>
  </div>
  <div class="pp-factor-title">{esc(title)}</div>
  <div class="pp-factor-desc">{esc(description)}</div>
</div>
"""


def contribution_factor_grid(cards: list[str]) -> str:
    return f'<div class="pp-factor-grid">{"".join(cards)}</div>'


def factors_panel(title: str, subtitle: str, cards_html: str, icon_name: str = "chart") -> str:
    return f"""
<div class="pp-fc-factors">
  <div class="pp-fc-section-head">
    <div class="pp-fc-section-ico">{icon(icon_name, 18)}</div>
    <div>
      <div class="pp-fc-section-title">{esc(title)}</div>
      <div class="pp-fc-section-sub">{esc(subtitle)}</div>
    </div>
  </div>
  {cards_html}
</div>
"""


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


def simulation_setup_header(title: str, subtitle: str, icon_name: str = "settings") -> str:
    return f"""
<div class="pp-sim-setup-head">
  <div class="pp-sim-setup-ico">{icon(icon_name, 18)}</div>
  <div>
    <div class="pp-sim-setup-title">{esc(title)}</div>
    <div class="pp-sim-setup-sub">{esc(subtitle)}</div>
  </div>
</div>
"""


def simulation_empty_state(title: str, description: str, icon_name: str = "flask") -> str:
    return f"""
<div class="pp-sim-empty">
  <div class="pp-sim-empty-ico">{icon(icon_name, 28)}</div>
  <div class="pp-sim-empty-title">{esc(title)}</div>
  <p class="pp-sim-empty-desc">{esc(description)}</p>
</div>
"""


def scenario_metric_row(icon_name: str, label: str, value_html: str) -> str:
    return f"""
<div class="pp-sim-metric">
  <div class="pp-sim-metric-left">{icon(icon_name, 14)}<span>{esc(label)}</span></div>
  <div class="pp-sim-metric-value">{value_html}</div>
</div>
"""


def simulation_scenario_card(
    letter: str,
    title: str,
    subtitle: str,
    description: str,
    metrics_html: str,
    icon_name: str = "flask",
    selected: bool = False,
    recommended: bool = False,
    rejected: bool = False,
    badges_html: str = "",
    href: str | None = None,
) -> str:
    klass = "pp-sim-card"
    if selected:
        klass += " is-selected"
    if rejected:
        klass += " is-rejected"
    if href and not rejected:
        klass += " is-clickable"
    flags = ""
    if recommended:
        flags += badge("Được mô hình đề xuất", "purple")
    if rejected:
        flags += badge("Không khả thi", "bad")
    if selected:
        flags += badge("Đang chọn", "ok")
    if badges_html:
        flags += badges_html
    flag_row = f'<div class="pp-sim-flags">{flags}</div>' if flags else ""
    desc = f'<p class="pp-sim-desc">{esc(description)}</p>' if description else ""
    if rejected:
        foot = '<div class="pp-sim-card-foot muted">Không thể chọn — vi phạm ràng buộc.</div>'
    elif selected:
        foot = '<div class="pp-sim-card-foot selected">✓ Phương án này sẽ dùng cho Decide</div>'
    else:
        foot = '<div class="pp-sim-card-foot">Nhấn vào card để chọn phương án này</div>'
    body = f"""
<div class="{klass}">
  <div class="pp-sim-card-head">
    <div class="pp-sim-card-ico">{icon(icon_name, 18)}</div>
    <div class="pp-sim-card-head-text">
      <div class="pp-sim-letter">Phương án {esc(letter)}</div>
      <div class="pp-sim-card-title">{esc(title)}</div>
      <div class="pp-sim-card-sub">{esc(subtitle)}</div>
    </div>
  </div>
  {desc}
  {flag_row}
  <div class="pp-sim-metrics">{metrics_html}</div>
  {foot}
</div>
"""
    if href and not rejected:
        return f'<a class="pp-sim-card-link" href="{esc(href)}">{body}</a>'
    return body


def recommendation_hero(
    title: str,
    subtitle: str,
    description: str,
    icon_name: str = "boxes",
    status_label: str = "Được hệ thống đề xuất",
    status_sub: str = "",
    is_recommended: bool = True,
) -> str:
    status_block = ""
    if status_label:
        status_sub_html = f'<div class="pp-dec-hero-status-sub">{esc(status_sub)}</div>' if status_sub else ""
        status_block = f"""
    <div class="pp-dec-hero-status">
      <div class="pp-dec-hero-status-title">{icon("check", 14)}<span>{esc(status_label)}</span></div>
      {status_sub_html}
    </div>"""
    badge_top = (
        f'<div class="pp-dec-hero-badge">{icon("trophy", 14)}<span>Phương án đề xuất</span></div>'
        if is_recommended
        else f'<div class="pp-dec-hero-badge is-alt">{icon("target", 14)}<span>Phương án đang chọn</span></div>'
    )
    return f"""
<div class="pp-dec-hero">
  <div class="pp-dec-hero-top">
    {badge_top}
    {status_block}
  </div>
  <div class="pp-dec-hero-body">
    <div class="pp-dec-hero-ico">{icon(icon_name, 28)}</div>
    <div>
      <div class="pp-dec-hero-title">{esc(title)}</div>
      <div class="pp-dec-hero-sub">{esc(subtitle)}</div>
      <p class="pp-dec-hero-desc">{esc(description)}</p>
    </div>
  </div>
</div>
"""


def recommendation_metric_card(
    title: str,
    value: str,
    icon_name: str,
    subtitle: str = "",
    accent: str = "blue",
) -> str:
    sub = f'<div class="pp-dec-metric-sub">{esc(subtitle)}</div>' if subtitle else ""
    return f"""
<div class="pp-dec-metric accent-{esc(accent)}">
  <div class="pp-dec-metric-top">
    <div class="pp-dec-metric-label">{esc(title)}</div>
    <div class="pp-dec-metric-ico">{icon(icon_name, 16)}</div>
  </div>
  <div class="pp-dec-metric-value">{esc(value)}</div>
  {sub}
</div>
"""


def reason_list_panel(title: str, items: list[str], icon_name: str = "circle-check", tone: str = "ok") -> str:
    if items:
        body = "".join(
            f'<li><span class="pp-dec-li-ico">{icon(icon_name, 14)}</span><span>{esc(item)}</span></li>'
            for item in items
        )
        body = f'<ul class="pp-dec-list">{body}</ul>'
    else:
        body = muted(EMPTY)
    return f"""
<div class="pp-dec-panel tone-{esc(tone)}">
  <div class="pp-dec-panel-head">
    <div class="pp-dec-panel-ico">{icon(icon_name, 18)}</div>
    <div class="pp-dec-panel-title">{esc(title)}</div>
  </div>
  {body}
</div>
"""


def tradeoff_list_panel(title: str, items: list[str]) -> str:
    return reason_list_panel(title, items, icon_name="alert-triangle", tone="warn")


def alternative_option_card(
    title: str,
    description: str,
    metrics: list[tuple[str, str]],
    icon_name: str = "flask",
) -> str:
    rows = "".join(
        f'<div class="pp-dec-alt-metric"><span>{esc(label)}</span><b>{esc(value)}</b></div>'
        for label, value in metrics
    )
    return f"""
<div class="pp-dec-alt">
  <div class="pp-dec-alt-head">
    <div class="pp-dec-alt-ico">{icon(icon_name, 18)}</div>
    <div>
      <div class="pp-dec-alt-title">{esc(title)}</div>
      <div class="pp-dec-alt-desc">{esc(description)}</div>
    </div>
  </div>
  <div class="pp-dec-alt-metrics">{rows}</div>
</div>
"""


def model_card(title: str, subtitle: str, rows: list[tuple[str, str]], badge_html: str) -> str:
    facts = "".join(f'<p class="pp-muted"><b>{esc(label)}.</b> {esc(value)}</p>' for label, value in rows)
    return card(kicker(title) + f'<div class="pp-opp-title">{esc(subtitle)}</div>{facts}<div class="pp-meta">{badge_html}</div>')


def footnote(text: str) -> str:
    return f'<p class="pp-foot">{esc(text)}</p>'


def gate_intro() -> str:
    mark = icon("target", 18, color="white")
    return f"""
<div class="pp-gate">
  <div class="pp-logo pp-logo-center">
    <div class="pp-logo-mark">{mark}</div>
  </div>
  <h2>PromotionPilot AI</h2>
  <p class="pp-muted">Bản demo giới hạn truy cập. Nhập mã được cung cấp để tiếp tục.</p>
</div>
"""


def prepare_metric_card(
    title: str,
    subtitle: str,
    value: str,
    icon_name: str,
    supporting: str = "",
    accent: str = "green",
    progress: float | None = None,
    trend: str | None = None,
    status_kind: str | None = None,
) -> str:
    """KPI sẵn sàng cho Prepare — progress/trend tùy chọn từ dữ liệu thật."""
    bar = ""
    if progress is not None:
        width = max(0.0, min(1.0, float(progress)))
        bar = (
            f'<div class="pp-prep-bar accent-{esc(accent)}">'
            f'<div style="width:{width:.0%}"></div></div>'
        )
    trend_html = f'<div class="pp-prep-trend">{esc(trend)}</div>' if trend else ""
    support = f'<div class="pp-prep-support">{esc(supporting)}</div>' if supporting else ""
    status = ""
    if status_kind:
        status = f'<div class="pp-prep-status">{badge(value, status_kind)}</div>'
        value_block = status
    else:
        value_block = f'<div class="pp-prep-value">{esc(value)}</div>'
    return f"""
<div class="pp-prep-metric accent-{esc(accent)}">
  <div class="pp-prep-metric-top">
    <div>
      <div class="pp-prep-metric-title">{esc(title)}</div>
      <div class="pp-prep-metric-sub">{esc(subtitle)}</div>
    </div>
    <div class="pp-prep-metric-ico">{icon(icon_name, 18)}</div>
  </div>
  {value_block}
  {bar}
  {trend_html}
  {support}
</div>
"""


def readiness_score_card(
    title: str,
    score_label: str,
    progress: float | None,
    message: str,
    icon_name: str = "chart-column",
    tone: str = "ok",
) -> str:
    bar = ""
    if progress is not None:
        width = max(0.0, min(1.0, float(progress)))
        bar = f'<div class="pp-prep-bar accent-green"><div style="width:{width:.0%}"></div></div>'
    badge_html = badge(message, tone)
    return f"""
<div class="pp-readiness-score">
  <div class="pp-fc-section-head">
    <div class="pp-fc-section-ico">{icon(icon_name, 18)}</div>
    <div>
      <div class="pp-fc-section-title">{esc(title)}</div>
    </div>
  </div>
  <div class="pp-prep-value">{esc(score_label)}</div>
  {bar}
  <div class="pp-readiness-msg">{badge_html}</div>
</div>
"""


def readiness_issue_item(rank: int, title: str, description: str, severity: str = "warn") -> str:
    return f"""
<div class="pp-issue-item severity-{esc(severity)}">
  <div class="pp-issue-rank">{int(rank)}</div>
  <div>
    <div class="pp-issue-title">{esc(title)}</div>
    <div class="pp-issue-desc">{esc(description)}</div>
  </div>
</div>
"""


def readiness_issue_list(title: str, subtitle: str, items_html: str, icon_name: str = "alert-triangle") -> str:
    body = items_html if items_html.strip() else muted(EMPTY)
    return f"""
<div class="pp-issue-panel">
  <div class="pp-fc-section-head">
    <div class="pp-fc-section-ico warn">{icon(icon_name, 18)}</div>
    <div>
      <div class="pp-fc-section-title">{esc(title)}</div>
      <div class="pp-fc-section-sub">{esc(subtitle)}</div>
    </div>
  </div>
  <div class="pp-issue-stack">{body}</div>
</div>
"""


def product_readiness_table(
    headers: list[str],
    rows: list[list[str]],
    title: str,
    subtitle: str,
    icon_name: str = "package",
) -> str:
    head = "".join(f"<th>{esc(name)}</th>" for name in headers)
    body = "".join("<tr>" + "".join(f"<td>{col}</td>" for col in row) + "</tr>" for row in rows)
    empty = f'<tr><td colspan="{len(headers)}" class="pp-table-empty">{esc(EMPTY)}</td></tr>' if not rows else ""
    return f"""
<div class="pp-product-ready">
  <div class="pp-fc-section-head">
    <div class="pp-fc-section-ico">{icon(icon_name, 18)}</div>
    <div>
      <div class="pp-fc-section-title">{esc(title)}</div>
      <div class="pp-fc-section-sub">{esc(subtitle)}</div>
    </div>
  </div>
  <div class="pp-scroll">
    <table class="pp-table pp-prep-table">
      <thead><tr>{head}</tr></thead>
      <tbody>{body}{empty}</tbody>
    </table>
  </div>
</div>
"""


def gap_cell(value: float) -> str:
    if not isinstance(value, (int, float)) or value != value:  # NaN
        return esc(DASH)
    number = float(value)
    klass = "up" if number > 0 else ("down" if number < 0 else "flat")
    sign = "+" if number > 0 else ""
    return f'<span class="pp-gap {klass}">{sign}{esc(integer(number))}</span>'


# —— Execute page components ——

STATUS_BADGE_KIND = {
    "Hoàn thành": "ok",
    "Đang thực hiện": "warn",
    "Chưa bắt đầu": "info",
    "Trễ hạn": "bad",
    "Blocked": "bad",
    "Completed": "ok",
    "In Progress": "warn",
    "Not Started": "info",
}

STATUS_BADGE_ICON = {
    "Hoàn thành": "circle-check",
    "Đang thực hiện": "clock",
    "Chưa bắt đầu": "circle",
    "Trễ hạn": "circle-x",
    "Blocked": "circle-x",
}


def exec_panel_header(title: str, subtitle: str, icon_name: str = "rocket", ico_class: str = "is-blue") -> str:
    """Header panel Execute — icon xanh đồng bộ section header hệ thống (.pp-sec-ico)."""
    klass = f"pp-exec-panel-ico {ico_class}".strip()
    return f"""
<div class="pp-exec-panel-head">
  <div class="{klass}">{icon(icon_name, 18)}</div>
  <div>
    <div class="pp-exec-panel-title">{esc(title)}</div>
    <div class="pp-exec-panel-sub">{esc(subtitle)}</div>
  </div>
</div>
"""


def campaign_info_field(label: str, value: str, sub: str = "", icon_name: str = "info", accent: str = "blue") -> str:
    """3 cột: icon | label | nội dung chi tiết (value + sub) — theo template Execute."""
    sub_html = f'<div class="pp-exec-field-sub">{esc(sub)}</div>' if sub else ""
    return f"""
<div class="pp-exec-field">
  <div class="pp-exec-field-ico {esc(accent)}">{icon(icon_name, 20)}</div>
  <div class="pp-exec-field-label">{esc(label)}</div>
  <div class="pp-exec-field-content">
    <div class="pp-exec-field-value">{esc(value)}</div>
    {sub_html}
  </div>
</div>
"""


def campaign_info_card(fields_html: str, title: str = "Thông tin chiến dịch", subtitle: str = "Tóm tắt các thông tin chính của chiến dịch") -> str:
    return f"""
<div class="pp-exec-panel pp-card">
  {exec_panel_header(title, subtitle, "rocket", "is-blue")}
  <div class="pp-exec-fields">{fields_html}</div>
</div>
"""


def task_status_badge(status: str) -> str:
    kind = STATUS_BADGE_KIND.get(status, "muted")
    ico = STATUS_BADGE_ICON.get(status, "circle")
    return f'<span class="pp-exec-status {kind}">{icon(ico, 14)}{esc(status)}</span>'


def task_owner_badge(initials: str, name: str) -> str:
    av_class = "pp-exec-owner-av"
    key = (initials or "").lower()
    if key in {"mk", "it", "sc", "rt", "hr", "dp", "td"}:
        av_class += f" {key}"
    initial_html = esc(initials) if initials else "—"
    return (
        f'<span class="pp-exec-owner"><span class="{av_class}">{initial_html}</span>'
        f'<span class="pp-exec-owner-name">{esc(name or DASH)}</span></span>'
    )


def task_name_cell(name: str, icon_name: str = "clipboard-check", is_new: bool = False) -> str:
    """Hiển thị tên công việc — không kèm icon (theo yêu cầu Execute)."""
    badge_html = '<span class="pp-exec-new-badge">Mới</span>' if is_new else ""
    return f'<span class="pp-exec-task-cell"><span>{esc(name or "—")}{badge_html}</span></span>'


def task_list_card(
    rows_html: str,
    title: str = "Danh sách công việc thực thi",
    subtitle: str = "Các đầu việc cần hoàn thành để triển khai chiến dịch",
    empty_html: str = "",
) -> str:
    """Bảng công việc read-only — cùng chrome pp-exec-panel / pp-card với card khác."""
    body = empty_html if empty_html else (
        '<div class="pp-exec-table-scroll">'
        '<div class="pp-exec-grid-head is-readonly">'
        "<div>#</div><div>Công việc</div><div>Phụ trách</div>"
        "<div>Hạn hoàn thành</div><div>Trạng thái</div>"
        f"</div>{rows_html}</div>"
    )
    return f"""
<div class="pp-exec-panel pp-card">
  {exec_panel_header(title, subtitle, "clipboard-check", "is-blue")}
  {body}
</div>
"""

def campaign_readiness_card(
    completed: int,
    total: int,
    percentage: int,
    message: str,
    title: str = "Mức độ sẵn sàng chiến dịch",
    subtitle: str = "Hoàn thành các công việc để sẵn sàng triển khai",
) -> str:
    ratio = max(0.0, min(1.0, (percentage / 100.0) if total else 0.0))
    bar_class = "pp-exec-ready-bar"
    if percentage < 34:
        bar_class += " is-low"
    elif percentage < 70:
        bar_class += " is-mid"
    count_label = f"{completed}/{total} hoàn thành" if total else EMPTY
    banner = info_banner("Gợi ý", message, "info") if message else ""
    return f"""
<div class="pp-exec-panel pp-card">
  {exec_panel_header(title, subtitle, "gauge", "is-blue")}
  <div class="pp-exec-ready-top">
    <div class="pp-exec-ready-count">{esc(count_label)}</div>
  </div>
  <div class="pp-exec-ready-bar-row">
    <div class="{bar_class}"><div style="width:{ratio:.0%}"></div></div>
    <div class="pp-exec-ready-pct">{int(percentage)}%</div>
  </div>
  <div style="margin-top:14px">{banner}</div>
</div>
"""


def prelaunch_checklist_card(
    items: list[dict],
    title: str = "Checklist trước khi khởi động",
    subtitle: str = "Các hạng mục bắt buộc cần hoàn tất",
) -> str:
    """items: [{label, checked}] — bản HTML tĩnh (vd. empty state). Checklist tương tác ở Execute dùng Streamlit checkbox."""
    if items:
        cells = []
        for item in items:
            on = bool(item.get("checked"))
            box_class = "pp-exec-check-box is-on" if on else "pp-exec-check-box"
            label_class = "pp-exec-check-label is-on" if on else "pp-exec-check-label"
            mark = icon("check", 12, color="white") if on else ""
            cells.append(
                f'<div class="pp-exec-check-item">'
                f'<div class="{box_class}">{mark}</div>'
                f'<div class="{label_class}">{esc(item.get("label") or DASH)}</div></div>'
            )
        body = f'<div class="pp-exec-check-scroll"><div class="pp-exec-check-grid">{"".join(cells)}</div></div>'
    else:
        body = muted(EMPTY)
    return f"""
<div class="pp-exec-panel pp-card">
  {exec_panel_header(title, subtitle, "clipboard-check", "is-blue")}
  {body}
</div>
"""


# —— Monitor & Learn components ——

ALERT_CODE_ICON = {
    "REVENUE_BELOW_FORECAST": "trend",
    "MARGIN_BELOW_MINIMUM": "percent",
    "STOCKOUT_RISK": "package",
    "STAFFING_ALERT": "users",
    "OVERSTOCK_ALERT": "package",
    "ROI_BELOW_MINIMUM": "trend",
    "ON_TRACK": "circle-check",
}

ALERT_LEVEL_KIND = {
    "critical": ("Cao", "bad"),
    "warning": ("Trung bình", "warn"),
    "info": ("Thấp", "info"),
}


def performance_metric_card(
    title: str,
    value: str,
    delta: str | None = None,
    delta_tone: str = "flat",
    icon_name: str = "chart",
    accent: str = "blue",
) -> str:
    delta_html = f'<div class="pp-mon-kpi-delta {esc(delta_tone)}">{esc(delta)}</div>' if delta else ""
    return f"""
<div class="pp-mon-kpi">
  <div class="pp-mon-kpi-top">
    <div class="pp-mon-kpi-title">{esc(title)}</div>
    <div class="pp-mon-kpi-ico {esc(accent)}">{icon(icon_name, 20)}</div>
  </div>
  <div class="pp-mon-kpi-value">{esc(value)}</div>
  {delta_html}
</div>
"""


def monitor_panel_header(
    title: str,
    subtitle: str,
    icon_name: str = "chart",
    ico_class: str = "",
    link_text: str = "",
) -> str:
    link = f'<div class="pp-mon-link">{esc(link_text)}</div>' if link_text else ""
    klass = f"pp-mon-panel-ico {ico_class}".strip()
    return f"""
<div class="pp-mon-panel-head">
  <div class="pp-mon-panel-head-left">
    <div class="{klass}">{icon(icon_name, 18)}</div>
    <div>
      <div class="pp-mon-panel-title">{esc(title)}</div>
      <div class="pp-mon-panel-sub">{esc(subtitle)}</div>
    </div>
  </div>
  {link}
</div>
"""


def campaign_alert_card(code: str, message: str, level: str) -> str:
    label, kind = ALERT_LEVEL_KIND.get(level, ("Thấp", "info"))
    ico = ALERT_CODE_ICON.get(code, "bell")
    return f"""
<div class="pp-mon-alert is-{esc(level)}">
  <div class="pp-mon-alert-top">
    <div class="pp-mon-alert-ico">{icon(ico, 16)}</div>
    <div>
      <div class="pp-mon-alert-title">{esc(code.replace("_", " ").title())}</div>
      <div class="pp-mon-alert-desc">{esc(message)}</div>
    </div>
  </div>
  <div class="pp-mon-alert-foot">{badge(label, kind)}</div>
</div>
"""


def learning_item(text: str, tone: str = "ok") -> str:
    ico_class = "pp-mon-learn-ico"
    if tone == "warn":
        ico_class += " is-warn"
        ico = "circle-alert"
    elif tone == "neutral":
        ico_class += " is-neutral"
        ico = "lightbulb"
    else:
        ico = "circle-check"
    return f"""
<div class="pp-mon-learn-item">
  <div class="{ico_class}">{icon(ico, 14)}</div>
  <div class="pp-mon-learn-text">{esc(text)}</div>
</div>
"""


def next_action_item(title: str, description: str = "", icon_name: str = "target") -> str:
    desc = f'<div class="pp-mon-action-desc">{esc(description)}</div>' if description else ""
    return f"""
<div class="pp-mon-action-item">
  <div class="pp-mon-action-ico">{icon(icon_name, 16)}</div>
  <div>
    <div class="pp-mon-action-title">{esc(title)}</div>
    {desc}
  </div>
</div>
"""


def monitor_empty_state(title: str, description: str) -> str:
    return f"""
<div class="pp-mon-empty">
  <div class="pp-mon-panel-ico">{icon("activity", 22)}</div>
  <div class="pp-mon-empty-title">{esc(title)}</div>
  <div class="pp-mon-empty-desc">{esc(description)}</div>
</div>
"""
