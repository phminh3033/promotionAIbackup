"""Forecast: cùng pipeline select_and_forecast, chỉ đổi lớp hiển thị theo template."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from services.workflow import run_forecast
from src.features.engineering import analyze_series_characteristics
from src.recommendation.engine import CONFIDENCE_PCT_BY_LABEL
from ui.charts import show_chart, time_series
from ui.components import (
    DASH,
    EMPTY,
    chart_placeholder,
    chart_workspace_header,
    contribution_factor_card,
    contribution_factor_grid,
    factors_panel,
    forecast_metric_card,
    forecast_summary_panel,
    model_insight_card,
    show,
)
from ui.formatters import integer_comma, pct, signed_pct
from ui.shell import continue_button, render_shell

# tab_label, chart_title, chart_subtitle, metric_col, y_title, unit, expected_title, growth_title, icon
TAB_SPECS = [
    {
        "tab": "Dự báo nhu cầu",
        "chart_title": "Dự báo nhu cầu sản phẩm",
        "chart_subtitle": "Nhu cầu thực tế trong quá khứ và dự báo từ mô hình.",
        "metric": "quantity",
        "label": "Sản lượng bán",
        "y_title": "Đơn vị",
        "unit": "đơn vị",
        "expected_title": "Sản lượng dự kiến",
        "growth_title": "Tăng trưởng sản lượng dự kiến",
        "actual_name": "Nhu cầu thực tế",
        "icon": "cart",
        "expected_icon": "package",
        "growth_icon": "trend",
    },
    {
        "tab": "Dự báo doanh thu",
        "chart_title": "Dự báo doanh thu",
        "chart_subtitle": "Doanh thu thực tế trong quá khứ và dự báo từ mô hình.",
        "metric": "revenue",
        "label": "Doanh thu",
        "y_title": "Doanh thu",
        "unit": "đ",
        "expected_title": "Doanh thu dự kiến",
        "growth_title": "Tăng trưởng doanh thu dự kiến",
        "actual_name": "Doanh thu thực tế",
        "icon": "chart-column",
        "expected_icon": "dollar",
        "growth_icon": "trend",
    },
    {
        "tab": "Dự báo traffic",
        "chart_title": "Dự báo traffic",
        "chart_subtitle": "Lưu lượng giao dịch/khách hàng trong quá khứ và dự báo từ mô hình.",
        "metric": "n_transactions",
        "label": "Số giao dịch",
        "y_title": "Giao dịch",
        "unit": "giao dịch",
        "expected_title": "Traffic dự kiến",
        "growth_title": "Tăng trưởng traffic dự kiến",
        "actual_name": "Traffic thực tế",
        "icon": "users",
        "expected_icon": "users",
        "growth_icon": "trend",
        "fallback_metric": "n_customers",
        "fallback_label": "Số khách hàng",
        "fallback_unit": "khách hàng",
        "fallback_y": "Khách hàng",
    },
]

HORIZON_OPTIONS = [7, 14, 30]


def render() -> None:
    render_shell(
        "Forecast",
        "Dự báo nhu cầu, doanh thu và traffic từ dữ liệu lịch sử.",
        stage=2,
    )
    from src.utils.state import has_data

    if not has_data():
        _empty_forecast()
        _page_actions(detail_key="fc_detail_empty", next_key="fc_next_empty")
        return

    df = st.session_state["clean_df"]
    caps = st.session_state["capabilities"]
    scope, scope_value, horizon = _controls(df, caps)
    _prune_forecast_cache_if_params_changed(scope, scope_value, horizon)

    tabs = st.tabs([spec["tab"] for spec in TAB_SPECS])
    for tab, spec in zip(tabs, TAB_SPECS):
        with tab:
            _panel(scope, scope_value, horizon, caps, spec)

    _page_actions(detail_key="fc_detail", next_key="fc_next")


def _prune_forecast_cache_if_params_changed(scope: str, scope_value, horizon: int) -> None:
    """Giữ cache khi đổi tab; chỉ xóa khi đổi Phạm vi / Danh mục-SKU / Số ngày dự báo."""
    fingerprint = f"{scope}|{scope_value}|{horizon}"
    prev = st.session_state.get("fc_param_fingerprint")
    if prev is None:
        st.session_state["fc_param_fingerprint"] = fingerprint
        return
    if prev == fingerprint:
        return
    st.session_state["fc_param_fingerprint"] = fingerprint
    st.session_state["forecast_cache"] = {}
    st.session_state["forecast_history"] = {}


def _empty_forecast() -> None:
    tabs = st.tabs([spec["tab"] for spec in TAB_SPECS])
    for tab, spec in zip(tabs, TAB_SPECS):
        with tab:
            main, side = st.columns([3, 1], gap="medium")
            with main, st.container(border=True):
                show(chart_workspace_header(spec["chart_title"], spec["chart_subtitle"], spec["icon"]))
                show(chart_placeholder("Chưa có dữ liệu. Tải dữ liệu ở Understand để chạy dự báo."))
            with side, st.container(border=True):
                show(
                    forecast_summary_panel(
                        "Kết quả dự báo",
                        "Tổng hợp kết quả từ mô hình",
                        _empty_metric_cards(spec),
                    )
                )
            insight, factors = st.columns([2, 3], gap="medium")
            with insight:
                show(
                    model_insight_card(
                        "Insight từ mô hình",
                        "Các yếu tố chính tác động đến dự báo",
                        [],
                    )
                )
            with factors:
                show(
                    factors_panel(
                        "Các yếu tố tác động chính",
                        "Đóng góp của từng yếu tố trong mô hình dự báo",
                        contribution_factor_grid(_empty_factor_cards()),
                    )
                )


def _empty_metric_cards(spec: dict) -> str:
    return "".join(
        [
            forecast_metric_card(spec["expected_title"], DASH, spec["expected_icon"], unit=spec["unit"], accent="purple", note=EMPTY),
            forecast_metric_card(spec["growth_title"], DASH, spec["growth_icon"], accent="purple", note=EMPTY),
            forecast_metric_card("Khoảng dự báo (~80%)", DASH, "chart", unit=spec["unit"], accent="green", note=EMPTY),
            forecast_metric_card("Độ tin cậy của mô hình", DASH, "shield-check", accent="green", note=EMPTY),
        ]
    )


def _empty_factor_cards() -> list[str]:
    return [
        contribution_factor_card("Nhu cầu theo mùa", DASH, EMPTY, "calendar", "neutral"),
        contribution_factor_card("Đà gần đây", DASH, EMPTY, "map-pin", "neutral"),
        contribution_factor_card("Biến động chuỗi", DASH, EMPTY, "users-round", "neutral"),
        contribution_factor_card("Xu hướng doanh số", DASH, EMPTY, "trend", "neutral"),
    ]


def _controls(df, caps):
    scope_options = ["Toàn công ty", "Theo Danh mục", "Theo SKU"]
    c1, c2, c3 = st.columns(3)
    with c1:
        scope = st.selectbox("Phạm vi", scope_options, key="fc_scope")

    scope_value = None
    horizon = None
    with c2:
        if scope == "Toàn công ty":
            # Ẩn Danh mục/Sản phẩm — đặt Số ngày dự báo sát Phạm vi.
            horizon = st.selectbox(
                "Số ngày dự báo",
                HORIZON_OPTIONS,
                index=1,
                key="fc_horizon",
            )
        elif scope == "Theo Danh mục":
            if not caps.has_category:
                st.warning("Dữ liệu không có danh mục.")
            else:
                scope_value = st.selectbox(
                    "Danh mục",
                    sorted(df["category"].dropna().unique()),
                    key="fc_cat",
                )
        elif scope == "Theo SKU":
            top = (
                df.groupby("product_id")["revenue"]
                .sum()
                .sort_values(ascending=False)
                .index.tolist()
            )
            scope_value = st.selectbox("Sản phẩm", top, key="fc_sku")

    with c3:
        if scope != "Toàn công ty":
            horizon = st.selectbox(
                "Số ngày dự báo",
                HORIZON_OPTIONS,
                index=1,
                key="fc_horizon",
            )

    return scope, scope_value, int(horizon)


def _resolve_metric(spec: dict, caps) -> tuple[str, str, str, str] | None:
    metric = spec["metric"]
    label = spec["label"]
    unit = spec["unit"]
    y_title = spec["y_title"]
    if metric == "n_transactions":
        if caps.has_transaction:
            return metric, label, unit, y_title
        if caps.has_customer:
            return (
                spec["fallback_metric"],
                spec["fallback_label"],
                spec["fallback_unit"],
                spec["fallback_y"],
            )
        return None
    return metric, label, unit, y_title


def _panel(scope, scope_value, horizon, caps, spec: dict) -> None:
    resolved = _resolve_metric(spec, caps)
    if resolved is None:
        st.info(
            "Cần mã giao dịch hoặc mã khách hàng để dự báo traffic. "
            "Hệ thống không ước lượng traffic khi thiếu cột này."
        )
        return
    metric, label, unit, y_title = resolved
    if scope != "Toàn công ty" and scope_value is None:
        return

    cache_key = f"{scope}|{scope_value}|{metric}|{horizon}"
    if st.button(f"Chạy {label.lower()}", type="primary", key=f"run_{metric}_{scope}_{horizon}"):
        try:
            with st.spinner("Đang backtest và chọn mô hình (có thể xếp hàng nếu nhiều người đang tính)..."):
                run_forecast(scope, scope_value, metric, label, horizon)
        except (ValueError, RuntimeError) as exc:
            st.warning(str(exc)) if isinstance(exc, RuntimeError) else st.error(str(exc))
            return

    result = st.session_state.get("forecast_cache", {}).get(cache_key)
    history = st.session_state.get("forecast_history", {}).get(cache_key)
    if result is None or history is None:
        main, side = st.columns([3, 1], gap="medium")
        with main, st.container(border=True):
            show(chart_workspace_header(spec["chart_title"], spec["chart_subtitle"], spec["icon"]))
            show(chart_placeholder("Chọn phạm vi rồi bấm chạy dự báo. Kết quả được lưu trong phiên."))
        with side, st.container(border=True):
            show(
                forecast_summary_panel(
                    "Kết quả dự báo",
                    "Tổng hợp kết quả từ mô hình",
                    _empty_metric_cards({**spec, "unit": unit, "expected_title": spec["expected_title"]}),
                )
            )
        return

    # Mặc định hiển thị theo ngày — không còn dropdown độ phân giải.
    hist_x, hist_y, fc_x, fc_y, low, high = _display_series(history, result, "D")
    conf_pct = _confidence_pct(result)
    band_label = f"Khoảng tin cậy (~80%{f', {conf_pct}%' if conf_pct else ''})" if conf_pct else "Khoảng tin cậy (~80%)"
    # Chỉ vẽ band khi lower/upper thực sự khác nhau (model luôn trả về; naive cũng có).
    has_band = low is not None and high is not None

    main, side = st.columns([3, 1], gap="medium")
    with main, st.container(border=True):
        show(chart_workspace_header(spec["chart_title"], spec["chart_subtitle"], spec["icon"]))
        fig = time_series(
            hist_x,
            hist_y,
            fc_x,
            fc_y,
            low if has_band else None,
            high if has_band else None,
            y_title=y_title,
            title="",
            actual_name=spec["actual_name"],
            forecast_name="Dự báo từ mô hình",
            band_name=band_label if has_band else None,
            height=420,
        )
        show_chart(fig)
        if not has_band:
            st.caption("Khoảng dự báo chưa khả dụng cho mô hình hiện tại.")

    with side, st.container(border=True):
        show(_summary_from_result(spec, unit, result, history, conf_pct))

    insight, factors = st.columns([2, 3], gap="medium")
    with insight:
        show(
            model_insight_card(
                "Insight từ mô hình",
                f"Các yếu tố chính tác động đến {spec['tab'].lower()}",
                _insight_bullets(result, history, spec),
            )
        )
    with factors:
        show(
            factors_panel(
                "Các yếu tố tác động chính",
                "Đóng góp ước lượng từ đặc điểm chuỗi và kết quả dự báo",
                contribution_factor_grid(_factor_cards(history, result, spec)),
            )
        )

    if not result.data_sufficient:
        st.warning("Chuỗi chưa đủ dài để backtest chắc chắn. Hãy xem dự báo này là tham khảo sơ bộ.")


def _summary_from_result(spec: dict, unit: str, result, history, conf_pct: int | None) -> str:
    expected = float(pd.Series(result.yhat).sum())
    hist_sum = float(pd.Series(history.values).sum()) or None
    growth = (expected / (hist_sum / max(len(history), 1) * len(result.yhat)) - 1) if hist_sum else None
    low = float(pd.Series(result.yhat_lower).sum())
    high = float(pd.Series(result.yhat_upper).sum())
    growth_txt = signed_pct(growth) if growth is not None else DASH
    conf_value = f"{conf_pct}%" if conf_pct is not None else result.confidence
    conf_note = f"WAPE {pct(result.wape, 1) if pd.notna(result.wape) else '—'} · {result.model_name}"

    cards = "".join(
        [
            forecast_metric_card(
                spec["expected_title"],
                integer_comma(expected),
                spec["expected_icon"],
                unit=unit,
                delta=growth_txt if growth is not None else None,
                comparison="so với kỳ trước" if growth is not None else None,
                accent="purple",
                note=None if growth is not None else EMPTY,
            ),
            forecast_metric_card(
                spec["growth_title"],
                f"{growth_txt} so với kỳ trước" if growth is not None else DASH,
                spec["growth_icon"],
                accent="purple",
                note=None if growth is not None else EMPTY,
            ),
            forecast_metric_card(
                "Khoảng dự báo (~80%)",
                f"{integer_comma(low)} – {integer_comma(high)}",
                "chart",
                unit=unit,
                accent="green",
            ),
            forecast_metric_card(
                "Độ tin cậy của mô hình",
                conf_value,
                "shield-check",
                accent="green",
                note=conf_note,
            ),
        ]
    )
    return forecast_summary_panel("Kết quả dự báo", "Tổng hợp kết quả từ mô hình", cards)


def _confidence_pct(result) -> int | None:
    band = CONFIDENCE_PCT_BY_LABEL.get(result.confidence)
    if band:
        return int(round((band[0] + band[1]) / 2))
    if pd.notna(result.wape):
        return int(max(0, min(99, round(100 * (1 - float(result.wape))))))
    return None


def _display_series(history: pd.Series, result, freq: str):
    """Resample chỉ để hiển thị — không đổi kết quả model đã cache."""
    hist = pd.Series(history.values, index=pd.to_datetime(history.index)).astype(float)
    fc = pd.Series(result.yhat, index=pd.to_datetime(result.dates)).astype(float)
    lo = pd.Series(result.yhat_lower, index=pd.to_datetime(result.dates)).astype(float)
    hi = pd.Series(result.yhat_upper, index=pd.to_datetime(result.dates)).astype(float)

    if freq == "D":
        return hist.index, hist.values, fc.index, fc.values, lo.values, hi.values

    how = "sum"
    hist_r = hist.resample(freq).agg(how)
    fc_r = fc.resample(freq).agg(how)
    lo_r = lo.resample(freq).agg(how)
    hi_r = hi.resample(freq).agg(how)
    return hist_r.index, hist_r.values, fc_r.index, fc_r.values, lo_r.values, hi_r.values


def _insight_bullets(result, history: pd.Series, spec: dict) -> list[str]:
    bullets: list[str] = []
    # Tách explanation deterministic sẵn có (bỏ markdown **).
    raw = (result.explanation or "").replace("**", "")
    for part in raw.replace(". ", ".\n").split("\n"):
        text = part.strip(" .")
        if text:
            bullets.append(text if text.endswith(".") else f"{text}.")

    chars = analyze_series_characteristics(history)
    if chars.get("has_weekly_seasonality"):
        strength = chars.get("weekly_seasonality_strength", 0) * 100
        bullets.append(
            f"Chuỗi có mùa vụ theo tuần rõ (biến thiên ~{strength:.0f}% so với trung bình)."
        )
    if chars.get("has_trend"):
        direction = "tăng" if chars.get("trend_slope", 0) > 0 else "giảm"
        bullets.append(f"Xu hướng {direction} gần đây được mô hình đưa vào dự báo {spec['tab'].lower()}.")
    if chars.get("is_intermittent"):
        bullets.append("Chuỗi có nhiều ngày không phát sinh — dự báo có thể biến động mạnh hơn bình thường.")

    # Giới hạn 4 bullet như template.
    return bullets[:4] or ["Chưa đủ tín hiệu để nêu insight định lượng."]


def _factor_cards(history: pd.Series, result, spec: dict) -> list[str]:
    """Ước lượng đóng góp từ đặc điểm chuỗi thực tế — không hard-code số mockup."""
    chars = analyze_series_characteristics(history)
    mean = float(chars.get("mean") or 0) or 1.0
    season = float(chars.get("weekly_seasonality_strength") or 0)
    season_pct = season  # đã là hệ số biến thiên tương đối
    trend_slope = float(chars.get("trend_slope") or 0)
    trend_pct = (trend_slope * max(len(result.yhat), 1)) / mean
    cv = float(chars.get("cv") or 0)
    if cv == float("inf"):
        cv = 0.0

    # Đà gần đây: 14 ngày cuối vs 14 ngày trước đó.
    hist = pd.Series(history.values, index=pd.to_datetime(history.index)).astype(float)
    recent_pct = 0.0
    if len(hist) >= 28:
        recent = float(hist.tail(14).mean())
        prior = float(hist.iloc[-28:-14].mean()) or 1e-9
        recent_pct = (recent / prior) - 1.0
    elif len(hist) >= 14:
        recent = float(hist.tail(7).mean())
        prior = float(hist.iloc[:-7].mean()) or 1e-9
        recent_pct = (recent / prior) - 1.0

    volatility_pct = -min(cv, 1.5)  # CV cao → tác động tiêu cực tới độ ổn định

    items = [
        (
            "Nhu cầu theo mùa",
            season_pct,
            "calendar",
            "Biến thiên theo ngày trong tuần trên chuỗi lịch sử.",
            "positive" if season_pct >= 0 else "negative",
        ),
        (
            "Đà gần đây",
            recent_pct,
            "map-pin",
            "So sánh nhịp gần đây với kỳ liền trước trên cùng chỉ số.",
            "positive" if recent_pct >= 0 else "negative",
        ),
        (
            "Biến động chuỗi",
            volatility_pct,
            "users-round",
            "Hệ số biến thiên (CV) — biến động cao làm dự báo kém ổn định hơn.",
            "negative" if volatility_pct < 0 else "neutral",
        ),
        (
            "Xu hướng doanh số",
            trend_pct,
            "trend",
            "Độ dốc xu hướng ước lượng trên lịch sử, quy về chân trời dự báo.",
            "positive" if trend_pct >= 0 else "negative",
        ),
    ]

    cards = []
    for title, value, icon_name, desc, direction in items:
        cards.append(
            contribution_factor_card(
                title,
                signed_pct(value),
                desc,
                icon_name,
                direction=direction,
            )
        )
    return cards


def _page_actions(*, detail_key: str, next_key: str) -> None:
    st.markdown('<div class="pp-page-actions"></div>', unsafe_allow_html=True)
    if st.button("Xem chi tiết phân tích →", type="secondary", key=detail_key, width="stretch"):
        _dlg_forecast_detail()
    continue_button("Tiếp tục đến Bước 3: Prepare →", "prepare", key=next_key)


@st.dialog("Chi tiết phân tích & bảng backtest", width="large")
def _dlg_forecast_detail() -> None:
    _render_forecast_detail()


def _format_forecast_version(cache_key: str) -> str:
    """Cache key → nhãn tham số có tên (Phạm vi / Danh mục|SKU / Số ngày)."""
    parts = str(cache_key).split("|")
    if len(parts) < 4:
        return cache_key
    scope, scope_value, _metric, horizon = parts[0], parts[1], parts[2], parts[3]
    labels = [f"Phạm vi: {scope}"]
    if scope == "Theo Danh mục" and scope_value not in {None, "None", ""}:
        labels.append(f"Danh mục: {scope_value}")
    elif scope == "Theo SKU" and scope_value not in {None, "None", ""}:
        labels.append(f"SKU: {scope_value}")
    labels.append(f"Số ngày dự báo: {horizon}")
    return " | ".join(labels)


def _format_backtest_scores(scores: pd.DataFrame) -> pd.DataFrame:
    display = scores.copy()
    if "WAPE" in display.columns:
        display["WAPE"] = display["WAPE"].map(lambda value: f"{value:.1%}" if pd.notna(value) else "—")
    if "MAE" in display.columns:
        display["MAE"] = display["MAE"].map(lambda value: f"{float(value):.2f}" if pd.notna(value) else "—")
    if "RMSE" in display.columns:
        display["RMSE"] = display["RMSE"].map(lambda value: f"{float(value):.2f}" if pd.notna(value) else "—")
    if "MAPE" in display.columns:
        display["MAPE"] = display["MAPE"].map(
            lambda value: f"{float(value):.1%}" if pd.notna(value) else "—"
        )
    return display


def _render_forecast_detail() -> None:
    cache = st.session_state.get("forecast_cache") or {}
    if not cache:
        st.info("Chưa có kết quả dự báo trong phiên để xem chi tiết.")
        return
    for key, result in cache.items():
        st.caption(
            f"Phiên bản: `{_format_forecast_version(key)}` · "
            f"Mô hình: **{result.model_name}** · Độ tin cậy: **{result.confidence}**"
        )
        st.write(result.explanation.replace("**", ""))
        if not result.all_model_scores.empty:
            st.dataframe(_format_backtest_scores(result.all_model_scores), width="stretch", hide_index=True)
        st.divider()
