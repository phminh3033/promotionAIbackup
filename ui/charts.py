"""Biểu đồ Plotly dùng chung một bảng màu."""
from __future__ import annotations

import plotly.graph_objects as go

ACTUAL = "#2563EB"
FORECAST = "#7C3AED"
POSITIVE = "#10B981"
WARNING = "#F59E0B"
NEGATIVE = "#EF4444"
GRID = "#E2E8F0"
SCENARIO_COLORS = ["#2563EB", "#7C3AED", "#F97316", "#10B981"]


def base_layout(title: str, y_title: str, height: int = 360) -> dict:
    return dict(
        title=dict(text=title, font=dict(size=15, color="#0F172A")),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Inter, system-ui, sans-serif", color="#475569", size=12),
        margin=dict(l=48, r=16, t=48, b=40),
        height=height,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        xaxis=dict(showgrid=False, linecolor=GRID, title=""),
        yaxis=dict(gridcolor=GRID, title=y_title, zeroline=False),
        hovermode="x unified",
    )


def time_series(actual_x, actual_y, forecast_x=None, forecast_y=None, lower=None, upper=None, y_title="Giá trị", title=""):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(actual_x), y=list(actual_y), name="Thực tế", mode="lines", line=dict(color=ACTUAL, width=2.4)))
    if forecast_x is not None and lower is not None and upper is not None:
        fig.add_trace(
            go.Scatter(
                x=list(forecast_x) + list(forecast_x)[::-1],
                y=list(upper) + list(lower)[::-1],
                fill="toself",
                fillcolor="rgba(124,58,237,0.14)",
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
                line=dict(color=FORECAST, width=2.4, dash="dash"),
            )
        )
    fig.update_layout(**base_layout(title, y_title))
    return fig


def grouped_bars(categories: list[str], series: list[tuple[str, list[float]]], y_title: str, title: str, as_percent: bool = False):
    fig = go.Figure()
    for index, (name, values) in enumerate(series):
        fig.add_trace(go.Bar(name=name, x=categories, y=values, marker_color=SCENARIO_COLORS[index % len(SCENARIO_COLORS)]))
    layout = base_layout(title, y_title, height=320)
    fig.update_layout(**layout, barmode="group")
    if as_percent:
        fig.update_yaxes(tickformat=".0%")
    return fig
