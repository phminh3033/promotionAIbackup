"""Monitor & Learn: UI theo template — logic KPI/alert/learning giữ nguyên từ engine hiện có."""
from __future__ import annotations

import io
from dataclasses import dataclass, field

import pandas as pd
import streamlit as st

from src.alerts.engine import decide_action, evaluate_alerts
from src.learning.campaign_log import list_campaign_records, save_campaign_record
from src.monitoring.campaign_monitor import (
    build_daily_baseline,
    compare_actual_vs_forecast,
    compute_actual_roi,
    cumulative_variance,
    resolve_promo_cost,
)
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
from ui.formatters import format_int_commas, integer, parse_int_commas, pct, roi_label, signed_pct, vnd
from ui.nav import goto
from ui.shell import render_shell

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
    # Ưu tiên bảng compared (cùng nguồn với chart); fallback daily_rows — bỏ NaN khi cộng.
    if compared is not None and not getattr(compared, "empty", True):
        revenue = _sum_series(compared["revenue"]) if "revenue" in compared.columns else _sum_field(actual_rows, "revenue")
        customers = (
            _sum_series(compared["customers"]) if "customers" in compared.columns else _sum_field(actual_rows, "customers")
        )
        gp = _sum_series(compared["gp"]) if "gp" in compared.columns else _sum_field(actual_rows, "gp")
    else:
        revenue = _sum_field(actual_rows, "revenue")
        customers = _sum_field(actual_rows, "customers")
        gp = _sum_field(actual_rows, "gp")

    margin_actual = (gp / revenue) if revenue is not None and revenue > 0 and gp is not None else None
    margin_forecast = _forecast_margin(record)

    # Tính lại ROI mỗi lần render — không phụ thuộc lần lưu cũ (cost=0 → roi_actual=None).
    roi_actual = _roi_from_record(record, compared)
    if roi_actual is not None:
        record.roi_actual = roi_actual

    rev_delta, rev_tone = _pct_delta_display(variance.get("revenue"), positive_is_good=True)
    cust_delta, cust_tone = _pct_delta_display(variance.get("customers"), positive_is_good=True)
    margin_delta_txt, margin_tone = _margin_delta_display(margin_actual, margin_forecast)
    roi_delta_txt, roi_tone = _roi_delta_display(roi_actual, record.roi_forecast)

    vm.metrics = [
        MetricVM(
            "Doanh thu thực tế",
            vnd(revenue),
            rev_delta,
            rev_tone,
            "coins",
            "blue",
        ),
        MetricVM(
            # Dữ liệu thực tế là customers (không có order count) — giữ nhãn đúng nguồn.
            "Khách hàng",
            integer(customers),
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
            roi_label(roi_actual) if roi_actual is not None else DASH,
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

    # Ngay dưới chart + cảnh báo — luôn hiện, không expander.
    _render_actuals_editor(record)

    b1, b2 = st.columns(2, gap="medium")
    with b1:
        _render_lessons_panel(vm)
    with b2:
        _render_recommendations_panel(vm)

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
    with st.container(border=True):
        show(
            monitor_panel_header(
                "Cảnh báo",
                "Phát hiện sớm các vấn đề cần chú ý trong chiến dịch.",
                "bell",
                "warn",
            )
        )
        if not vm.alerts:
            show(muted("Chưa có cảnh báo từ các luật hiện tại."))
        else:
            show(
                '<div class="pp-mon-alert-scroll"><div class="pp-mon-alert-stack">'
                + "".join(campaign_alert_card(a.code, a.message, a.level) for a in vm.alerts)
                + "</div></div>"
            )


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


def _render_actuals_editor(record) -> None:
    """Form nhập số thực tế — luôn hiện, ngay dưới chart + cảnh báo."""
    with st.container(border=True):
        _editor(record)


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


ACTUAL_COL_LABELS = {
    "date": "Ngày",
    "revenue": "Doanh thu",
    "gp": "Lợi nhuận gộp",
    "customers": "Khách hàng",
    "units": "Sản lượng",
    "inventory_onhand": "Tồn kho",
}
ACTUAL_LABEL_TO_COL = {label: key for key, label in ACTUAL_COL_LABELS.items()}
ACTUAL_NUM_COLS = ["revenue", "gp", "customers", "units", "inventory_onhand"]


def _editor(record) -> None:
    cid = record.campaign_id
    rows_key = f"actual_rows_{cid}"
    ver_key = f"actual_editor_ver_{cid}"
    cost_fmt_key = f"cost_fmt_{cid}"
    cost_key = f"cost_num_{cid}"

    if rows_key not in st.session_state:
        st.session_state[rows_key] = _default_actual_frame(record)
    if ver_key not in st.session_state:
        st.session_state[ver_key] = 0
    if cost_fmt_key not in st.session_state:
        # Ưu tiên cost đã lưu → chi phí mô phỏng → ngân sách (tránh ROI = — vì cost=0).
        default_cost = resolve_promo_cost(
            actual_cost=(record.actual or {}).get("promo_cost_actual"),
            expected_promo_cost=(record.forecast or {}).get("expected_promo_cost"),
            budget=(record.forecast or {}).get("budget"),
            forecast=record.forecast or {},
        ) or 0.0
        st.session_state[cost_key] = float(default_cost)
        st.session_state[cost_fmt_key] = (
            format_int_commas(int(round(default_cost))) if default_cost else ""
        )

    export_bytes = _actuals_to_xlsx_bytes(st.session_state[rows_key])

    # Header: tiêu đề trái — nút icon Xuất / Nhập góc phải.
    head_l, head_r = st.columns([4.2, 1.05], vertical_alignment="top")
    with head_l:
        show(
            monitor_panel_header(
                "Nhập / cập nhật số liệu thực tế",
                "Cập nhật kết quả hàng ngày để so với dự báo baseline khi khởi chạy.",
                "clipboard-check",
            )
        )
    with head_r:
        st.markdown('<div class="pp-mon-actual-tools">', unsafe_allow_html=True)
        tool_export, tool_import = st.columns(2, gap="small")
        with tool_export:
            st.download_button(
                label="Xuất",
                icon=":material/download:",
                data=export_bytes,
                file_name=f"so_lieu_thuc_te_{cid}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"export_actual_{cid}",
                help="Xuất số liệu ra Excel",
                width="stretch",
            )
        with tool_import:
            with st.popover(
                "Nhập",
                icon=":material/upload:",
                help="Nhập số liệu từ CSV/Excel (thêm vào cuối bảng)",
                width="stretch",
            ):
                st.caption("Thêm vào cuối bảng, không ghi đè. Cột: Ngày, Doanh thu, Lợi nhuận gộp, Khách hàng, Sản lượng, Tồn kho.")
                uploaded = st.file_uploader(
                    "Chọn file",
                    type=["xlsx", "xls", "csv"],
                    key=f"actual_upload_{cid}",
                    label_visibility="collapsed",
                )
                if uploaded is not None:
                    _handle_actuals_upload(record, cid, rows_key, ver_key, cost_key, uploaded)
        st.markdown("</div>", unsafe_allow_html=True)

    edited = st.data_editor(
        st.session_state[rows_key],
        num_rows="dynamic",
        width="stretch",
        key=f"actual_{cid}_{st.session_state[ver_key]}",
        column_config={
            "date": st.column_config.DateColumn("Ngày", format="DD/MM/YYYY", required=True),
            "revenue": st.column_config.NumberColumn("Doanh thu", format="%,.0f", step=1),
            "gp": st.column_config.NumberColumn("Lợi nhuận gộp", format="%,.0f", step=1),
            "customers": st.column_config.NumberColumn("Khách hàng", format="%,.0f", step=1),
            "units": st.column_config.NumberColumn("Sản lượng", format="%,.0f", step=1),
            "inventory_onhand": st.column_config.NumberColumn("Tồn kho", format="%,.0f", step=1),
        },
    )
    st.session_state[rows_key] = edited

    # Chi phí + Lưu — cùng hàng, kích thước cân đối.
    cost_col, save_col = st.columns([2.4, 1.0], vertical_alignment="bottom", gap="medium")
    with cost_col:
        st.text_input(
            "Chi phí khuyến mãi thực tế (VND)",
            key=cost_fmt_key,
            on_change=_make_sync_cost_fmt(cid),
            help="Nhập số nguyên; hệ thống tự thêm dấu phẩy phân tách hàng nghìn.",
        )
    with save_col:
        if st.button("Lưu số thực tế", type="primary", key="save_actual", width="stretch"):
            _pull_cost_from_fmt(cid)
            cost = float(st.session_state.get(cost_key) or 0)
            _persist_actuals(
                record,
                edited,
                cost,
                success_message="Đã lưu và tính lại chênh lệch so với dự báo.",
            )
            st.rerun()


def _handle_actuals_upload(record, cid: str, rows_key: str, ver_key: str, cost_key: str, uploaded) -> None:
    upload_token = f"{uploaded.name}:{uploaded.size}"
    last_token = st.session_state.get(f"actual_upload_token_{cid}")
    if upload_token == last_token:
        return
    try:
        appended = _parse_actuals_upload(uploaded)
        if appended.empty:
            st.warning("File không có dòng hợp lệ (cần cột Ngày).")
            return
        current = st.session_state[rows_key].copy()
        merged = pd.concat([current, appended], ignore_index=True)
        st.session_state[rows_key] = merged
        st.session_state[ver_key] = int(st.session_state[ver_key]) + 1
        st.session_state[f"actual_upload_token_{cid}"] = upload_token
        cost = float(st.session_state.get(cost_key) or 0)
        _persist_actuals(
            record,
            merged,
            cost,
            success_message="Đã nhập và lưu số liệu (thêm vào cuối bảng).",
        )
        st.rerun()
    except Exception as exc:  # noqa: BLE001
        st.error(f"Không đọc được file: {exc}")

def _make_sync_cost_fmt(cid: str):
    """Callback on_change — được phép ghi lại cost_fmt (widget key)."""

    def _sync() -> None:
        fmt_key = f"cost_fmt_{cid}"
        num_key = f"cost_num_{cid}"
        raw = st.session_state.get(fmt_key)
        if not str(raw or "").strip():
            st.session_state[num_key] = 0.0
            st.session_state[fmt_key] = ""
            return
        value = parse_int_commas(raw, default=0, minimum=0)
        st.session_state[num_key] = float(value)
        st.session_state[fmt_key] = format_int_commas(value) if value else ""

    return _sync


def _pull_cost_from_fmt(cid: str) -> None:
    """Đọc cost_fmt → cost_num sau khi widget đã tạo (không ghi lại fmt)."""
    fmt_key = f"cost_fmt_{cid}"
    num_key = f"cost_num_{cid}"
    raw = st.session_state.get(fmt_key)
    if str(raw or "").strip():
        st.session_state[num_key] = float(parse_int_commas(raw, default=0, minimum=0))
    else:
        st.session_state[num_key] = 0.0


def _default_actual_frame(record) -> pd.DataFrame:
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
    for col in ["date", *ACTUAL_NUM_COLS]:
        if col not in default.columns:
            default[col] = None
    default = default[["date", *ACTUAL_NUM_COLS]]
    default["date"] = pd.to_datetime(default["date"], errors="coerce")
    for col in ACTUAL_NUM_COLS:
        default[col] = pd.to_numeric(default[col], errors="coerce")
    return default


def _normalize_actual_frame(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    if "date" not in out.columns:
        return pd.DataFrame(columns=["date", *ACTUAL_NUM_COLS])
    out["date"] = pd.to_datetime(out["date"], errors="coerce", dayfirst=True).dt.normalize()
    out = out.dropna(subset=["date"])
    for col in ACTUAL_NUM_COLS:
        if col not in out.columns:
            out[col] = None
        else:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out[["date", *ACTUAL_NUM_COLS]].reset_index(drop=True)


def _actuals_display_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """DataFrame xuất file — header tiếng Việt, ngày dd/MM/yyyy."""
    show = _normalize_actual_frame(frame).copy()
    if show.empty:
        return pd.DataFrame(columns=list(ACTUAL_COL_LABELS.values()))
    show["date"] = show["date"].dt.strftime("%d/%m/%Y")
    for col in ACTUAL_NUM_COLS:
        show[col] = show[col].apply(lambda v: None if pd.isna(v) else int(round(float(v))))
    return show.rename(columns=ACTUAL_COL_LABELS)


def _actuals_to_xlsx_bytes(frame: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        _actuals_display_frame(frame).to_excel(writer, sheet_name="So lieu thuc te", index=False)
    return buffer.getvalue()


def _parse_actuals_upload(uploaded) -> pd.DataFrame:
    name = (uploaded.name or "").lower()
    if name.endswith(".csv"):
        raw = pd.read_csv(uploaded)
    else:
        raw = pd.read_excel(uploaded)
    rename = {}
    for col in raw.columns:
        label = str(col).strip()
        if label in ACTUAL_LABEL_TO_COL:
            rename[col] = ACTUAL_LABEL_TO_COL[label]
        elif label.lower() in ACTUAL_COL_LABELS:
            rename[col] = label.lower()
        elif label.lower() in {"inventory", "ton kho", "tồn kho"}:
            rename[col] = "inventory_onhand"
        elif label.lower() in {"gross_profit", "loi nhuan gop", "lợi nhuận gộp"}:
            rename[col] = "gp"
    mapped = raw.rename(columns=rename)
    # Parse số kiểu "25,300,024"
    for col in ACTUAL_NUM_COLS:
        if col in mapped.columns and mapped[col].dtype == object:
            mapped[col] = (
                mapped[col]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.replace(" ", "", regex=False)
            )
    return _normalize_actual_frame(mapped)


def _persist_actuals(record, frame: pd.DataFrame, cost: float, *, success_message: str) -> None:
    normalized = _normalize_actual_frame(frame)
    if normalized.empty:
        st.warning("Không có dòng nào có ngày hợp lệ để lưu.")
        return
    baseline = _baseline(record)
    compared = compare_actual_vs_forecast(normalized, baseline)
    record.variance = {
        "revenue": cumulative_variance(compared, "revenue"),
        "gp": cumulative_variance(compared, "gp"),
        "customers": cumulative_variance(compared, "customers"),
        "units": cumulative_variance(compared, "units"),
    }
    resolved_cost = resolve_promo_cost(
        actual_cost=cost,
        expected_promo_cost=(record.forecast or {}).get("expected_promo_cost"),
        budget=(record.forecast or {}).get("budget"),
        forecast=record.forecast or {},
    )
    # Lưu cost người nhập nếu > 0; nếu không vẫn giữ fallback để ROI tính được.
    stored_cost = float(cost) if cost and float(cost) > 0 else (resolved_cost or 0.0)
    record.roi_actual = _roi(normalized, record, resolved_cost)
    safe = normalized.copy()
    safe["date"] = safe["date"].dt.strftime("%Y-%m-%d")
    # where(...None).to_dict vẫn giữ float('nan') — phải làm sạch tường minh.
    record.actual = {
        "daily_rows": _records_without_nan(safe),
        "promo_cost_actual": float(stored_cost or 0),
    }
    cid = record.campaign_id
    st.session_state[f"actual_rows_{cid}"] = normalized
    save_campaign_record(record)
    st.session_state["campaign_actual_data"] = compared
    st.success(success_message)


def _records_without_nan(frame: pd.DataFrame) -> list[dict]:
    """to_dict('records') an toàn — NaN/NA → None (tránh sum bị nhiễm nan)."""
    import math

    rows: list[dict] = []
    for raw in frame.to_dict(orient="records"):
        cleaned: dict = {}
        for key, value in raw.items():
            if value is None:
                cleaned[key] = None
                continue
            try:
                if pd.isna(value):
                    cleaned[key] = None
                    continue
            except (TypeError, ValueError):
                pass
            if isinstance(value, (float, int)) and not isinstance(value, bool):
                number = float(value)
                cleaned[key] = number if math.isfinite(number) else None
            else:
                cleaned[key] = value
        rows.append(cleaned)
    return rows


def _baseline(record):
    return build_daily_baseline(
        expected_revenue_range=tuple(record.forecast["expected_revenue_range"]),
        expected_gp_range=tuple(record.forecast["expected_gp_range"]),
        expected_customers_range=tuple(record.forecast["expected_customers_range"]),
        expected_demand_range=tuple(record.forecast["expected_demand_range"]),
        promo_days=record.forecast.get("promo_days") or 7,
    )


def _roi(frame, record, cost):
    """ROI thực tế — cost đã resolve (thực tế / mô phỏng / ngân sách)."""
    no_promo = (record.forecast or {}).get("no_promo_gp_per_day")
    if "gp" not in getattr(frame, "columns", []):
        return None
    return compute_actual_roi(
        frame["gp"],
        no_promo_gp_per_day=no_promo,
        promo_cost=cost,
    )


def _roi_from_record(record, compared) -> float | None:
    """Tính ROI từ số đã lưu + fallback chi phí (dùng khi render KPI)."""
    cost = resolve_promo_cost(
        actual_cost=(record.actual or {}).get("promo_cost_actual"),
        expected_promo_cost=(record.forecast or {}).get("expected_promo_cost"),
        budget=(record.forecast or {}).get("budget"),
        forecast=record.forecast or {},
    )
    no_promo = (record.forecast or {}).get("no_promo_gp_per_day")
    if compared is not None and not getattr(compared, "empty", True) and "gp" in compared.columns:
        return compute_actual_roi(
            compared["gp"],
            no_promo_gp_per_day=no_promo,
            promo_cost=cost,
        )
    rows = (record.actual or {}).get("daily_rows") or []
    if not rows:
        return record.roi_actual
    gps = [row.get("gp") for row in rows if isinstance(row, dict)]
    return compute_actual_roi(gps, no_promo_gp_per_day=no_promo, promo_cost=cost)


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
    total_gp = _sum_field(daily_rows, "gp") or 0.0
    total_revenue = _sum_field(daily_rows, "revenue") or 0.0
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
    """Cộng các giá trị hữu hạn; bỏ None/NaN/chuỗi lỗi (tránh sum → nan → KPI hiện —)."""
    import math

    if not rows:
        return None
    total = 0.0
    found = False
    for row in rows:
        raw = row.get(field_name) if isinstance(row, dict) else None
        if raw is None:
            continue
        try:
            if pd.isna(raw):
                continue
        except (TypeError, ValueError):
            pass
        try:
            number = float(raw)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(number):
            continue
        total += number
        found = True
    return total if found else None


def _sum_series(series) -> float | None:
    import math

    if series is None:
        return None
    total = pd.to_numeric(series, errors="coerce").sum(skipna=True)
    try:
        number = float(total)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    # sum toàn NaN → 0.0 với skipna; phân biệt bằng any notna
    if pd.to_numeric(series, errors="coerce").notna().sum() == 0:
        return None
    return number


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
