"""Biểu đồ Plotly theo ngôn ngữ shadcn/Recharts. Không đổi số liệu đầu vào."""
from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

ACTUAL = "#2563EB"
FORECAST = "#7C3AED"
DIVIDER = "#A855F7"
GRID = "#E2E8F0"
TICK = "#94A3B8"
INK = "#0F172A"
MUTED = "#64748B"
SCENARIO_COLORS = ["#2563EB", "#7C3AED", "#F97316", "#10B981"]
FONT = "Inter, ui-sans-serif, system-ui, sans-serif"


def show_chart(fig: go.Figure) -> None:
    st.plotly_chart(
        fig,
        width="stretch",
        theme=None,
        config={"displayModeBar": False, "responsive": True},
    )


def base_layout(title: str, y_title: str, height: int = 340) -> dict:
    return dict(
        template="simple_white",
        title=dict(text=title, font=dict(size=14, color=INK, family=FONT), x=0, xanchor="left", y=0.98)
        if title
        else None,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=MUTED, size=12),
        margin=dict(l=8, r=12, t=48 if title else 36, b=28),
        height=height,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.08,
            x=0,
            font=dict(size=11, color=MUTED, family=FONT),
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0,
            itemsizing="constant",
        ),
        hoverlabel=dict(bgcolor="white", bordercolor="#E2E8F0", font=dict(size=12, color=INK, family=FONT)),
        xaxis=dict(showgrid=False, showline=False, zeroline=False, tickfont=dict(size=11, color=TICK), title=""),
        yaxis=dict(
            gridcolor=GRID,
            gridwidth=1,
            showline=False,
            zeroline=False,
            tickfont=dict(size=11, color=TICK),
            title=dict(text=y_title, font=dict(size=11, color=MUTED)),
        ),
        hovermode="x unified",
    )


def apply_plotly_theme(fig: go.Figure, y_title: str = "", height: int = 340, title: str = "") -> go.Figure:
    """Áp theme PromotionPilot tập trung — dùng chung các trang có Plotly."""
    layout = base_layout(title, y_title, height=height)
    if layout.get("title") is None:
        layout.pop("title", None)
    fig.update_layout(**layout)
    return fig


def time_series(
    actual_x,
    actual_y,
    forecast_x=None,
    forecast_y=None,
    lower=None,
    upper=None,
    y_title="Giá trị",
    title="",
    actual_name="Thực tế",
    forecast_name="Dự báo từ mô hình",
    band_name: str | None = "Khoảng tin cậy",
    height: int = 340,
):
    """Historical + forecast + optional CI band + divider Quá khứ | Dự báo."""
    fig = go.Figure()
    ax = list(actual_x)
    ay = list(actual_y)
    fig.add_trace(
        go.Scatter(
            x=ax,
            y=ay,
            name=actual_name,
            mode="lines+markers",
            line=dict(color=ACTUAL, width=2.5, shape="spline"),
            marker=dict(size=6, color=ACTUAL, line=dict(width=1.5, color="white")),
        )
    )

    has_band = (
        forecast_x is not None
        and lower is not None
        and upper is not None
        and band_name is not None
    )
    if has_band:
        fx = list(forecast_x)
        fig.add_trace(
            go.Scatter(
                x=fx + fx[::-1],
                y=list(upper) + list(lower)[::-1],
                fill="toself",
                fillcolor="rgba(124,58,237,0.12)",
                line=dict(color="rgba(255,255,255,0)"),
                name=band_name,
                hoverinfo="skip",
                showlegend=True,
            )
        )

    if forecast_x is not None and forecast_y is not None:
        fx = list(forecast_x)
        fy = list(forecast_y)
        # Nối điểm cuối lịch sử với điểm đầu dự báo để đường liên tục.
        if ax and ay:
            fx_line = [ax[-1], *fx]
            fy_line = [ay[-1], *fy]
        else:
            fx_line, fy_line = fx, fy
        fig.add_trace(
            go.Scatter(
                x=fx_line,
                y=fy_line,
                name=forecast_name,
                mode="lines+markers",
                line=dict(color=FORECAST, width=2.5, dash="dash"),
                marker=dict(size=7, color="white", line=dict(width=2, color=FORECAST)),
            )
        )
        _add_forecast_divider(fig, fx[0] if fx else None)

    apply_plotly_theme(fig, y_title=y_title, height=height, title=title)
    return fig


def _add_forecast_divider(fig: go.Figure, x0) -> None:
    if x0 is None:
        return
    fig.add_vline(x=x0, line_width=1.5, line_dash="dash", line_color=DIVIDER, opacity=0.85)
    fig.add_annotation(
        x=x0,
        y=1.02,
        yref="paper",
        text="<b>Quá khứ</b>&nbsp;&nbsp;|&nbsp;&nbsp;<b>Dự báo →</b>",
        showarrow=False,
        font=dict(size=11, color=FORECAST, family=FONT),
        xanchor="center",
        bgcolor="rgba(255,255,255,0.85)",
    )


def actual_vs_forecast_overlay(
    dates,
    actual_y,
    forecast_y,
    *,
    y_title: str = "Giá trị",
    title: str = "",
    actual_name: str = "Thực tế",
    forecast_name: str = "Dự báo",
    height: int = 360,
):
    """Hai series cùng kỳ (Monitor) — trục X theo ngày (không tick theo giờ)."""
    import pandas as pd

    fig = go.Figure()
    # Chuẩn hoá về ngày lịch — tránh Plotly tự chia tick theo giờ khi Timestamp có time.
    x = pd.to_datetime(list(dates), errors="coerce").normalize()
    fig.add_trace(
        go.Scatter(
            x=x,
            y=list(actual_y),
            name=actual_name,
            mode="lines+markers",
            line=dict(color=ACTUAL, width=2.5, shape="linear"),
            marker=dict(size=7, color=ACTUAL, line=dict(width=1.5, color="white")),
            fill="tozeroy",
            fillcolor="rgba(37,99,235,0.08)",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x,
            y=list(forecast_y),
            name=forecast_name,
            mode="lines+markers",
            line=dict(color=FORECAST, width=2.5, dash="dash"),
            marker=dict(size=7, color="white", line=dict(width=2, color=FORECAST)),
        )
    )
    apply_plotly_theme(fig, y_title=y_title, height=height, title=title)
    fig.update_xaxes(
        type="date",
        tickformat="%d/%m/%Y",
        dtick=86_400_000,  # 1 ngày (ms) — không chia 00:00 / 06:00 / 12:00
        hoverformat="%d/%m/%Y",
        ticklabelmode="period",
    )
    return fig


def grouped_bars(categories: list[str], series: list[tuple[str, list[float]]], y_title: str, title: str, as_percent: bool = False):
    fig = go.Figure()
    for index, (name, values) in enumerate(series):
        fig.add_trace(
            go.Bar(
                name=name,
                x=categories,
                y=values,
                marker=dict(color=SCENARIO_COLORS[index % len(SCENARIO_COLORS)], cornerradius=6, line=dict(width=0)),
            )
        )
    apply_plotly_theme(fig, y_title=y_title, height=320, title=title)
    fig.update_layout(barmode="group", bargap=0.28, bargroupgap=0.08)
    if as_percent:
        fig.update_yaxes(tickformat=".0%")
    return fig
