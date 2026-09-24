"""Biểu đồ Plotly theo ngôn ngữ shadcn/Recharts. Không đổi số liệu đầu vào."""
from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

ACTUAL = "#2563EB"
FORECAST = "#7C3AED"
GRID = "#F1F5F9"
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
        title=dict(text=title, font=dict(size=14, color=INK, family=FONT), x=0, xanchor="left", y=0.98),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family=FONT, color=MUTED, size=12),
        margin=dict(l=8, r=8, t=56 if title else 24, b=28),
        height=height,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
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


def time_series(actual_x, actual_y, forecast_x=None, forecast_y=None, lower=None, upper=None, y_title="Giá trị", title=""):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=list(actual_x),
            y=list(actual_y),
            name="Thực tế",
            mode="lines",
            line=dict(color=ACTUAL, width=2, shape="spline"),
        )
    )
    if forecast_x is not None and lower is not None and upper is not None:
        fig.add_trace(
            go.Scatter(
                x=list(forecast_x) + list(forecast_x)[::-1],
                y=list(upper) + list(lower)[::-1],
                fill="toself",
                fillcolor="rgba(124,58,237,0.12)",
                line=dict(color="rgba(255,255,255,0)"),
                name="Khoảng tin cậy",
                hoverinfo="skip",
            )
        )
    if forecast_x is not None and forecast_y is not None:
        fig.add_trace(
            go.Scatter(
                x=list(forecast_x),
                y=list(forecast_y),
                name="Dự báo",
                mode="lines",
                line=dict(color=FORECAST, width=2, dash="dash"),
            )
        )
    fig.update_layout(**base_layout(title, y_title))
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
    layout = base_layout(title, y_title, height=320)
    fig.update_layout(**layout, barmode="group", bargap=0.28, bargroupgap=0.08)
    if as_percent:
        fig.update_yaxes(tickformat=".0%")
    return fig
