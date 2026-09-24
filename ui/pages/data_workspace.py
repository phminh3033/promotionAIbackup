"""Data Workspace: demo, upload, mapping và điểm chất lượng thật."""
from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from services.workflow import TEMPLATE_PATH, commit_dataset, load_demo_dataset
from src.data.loader import DataLoadError, list_excel_sheets, load_raw_file
from src.data.mapper import suggest_mapping
from src.data.schema import ALL_CANONICAL_FIELDS, FIELD_HINTS_VI, FIELD_LABELS_VI, REQUIRED_FIELDS
from ui.components import badge
from ui.shell import continue_button, render_shell

CHECKS = [
    ("Dữ liệu bán hàng", lambda report, caps: (True, f"{report.n_rows:,} dòng")),
    ("Dữ liệu sản phẩm", lambda report, caps: (report.n_skus > 0, f"{report.n_skus:,} sản phẩm")),
    ("Dữ liệu khách hàng", lambda report, caps: (bool(caps.has_customer), f"{report.n_customers:,} khách" if report.n_customers else "Thiếu mã khách hàng")),
    ("Dữ liệu tồn kho", lambda report, caps: (bool(caps.has_inventory), "Có cột tồn kho" if caps.has_inventory else "Thiếu dữ liệu")),
    ("Dữ liệu khuyến mãi", lambda report, caps: (bool(caps.has_promotion), "Có lịch sử khuyến mãi" if caps.has_promotion else "Thiếu lịch sử khuyến mãi")),
]

_MAX_UPLOAD_MB = max(1, int(os.getenv("DEMO_MAX_UPLOAD_MB", "5")))


def render() -> None:
    render_shell(
        "Data Workspace",
        "Tải dữ liệu và kiểm tra chất lượng. Bắt đầu bằng dữ liệu mẫu hoặc file bán hàng của bạn.",
    )
    _sources()
    _mapping()
    _quality()
    cols = st.columns([1, 1])
    with cols[1]:
        continue_button("Tiếp tục sang bước 1: Understand", "understand", key="data_next")


def _sources() -> None:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            '<div class="pp-card"><div class="pp-kicker">Sử dụng dữ liệu mẫu</div>'
            '<p class="pp-muted">Bộ dữ liệu nhà thuốc demo đã chuẩn bị sẵn (khuyến nghị khi nhiều người dùng thử).</p></div>',
            unsafe_allow_html=True,
        )
        if st.button("Dùng dữ liệu mẫu", type="primary", key="use_demo", use_container_width=True):
            with st.spinner("Đang tải và kiểm tra dữ liệu demo..."):
                ok, message = load_demo_dataset()
            (st.success if ok else st.error)(message)
            if ok:
                st.rerun()
    with c2:
        st.markdown(
            f'<div class="pp-card"><div class="pp-kicker">Tải file dữ liệu</div>'
            f'<p class="pp-muted">CSV/Excel từ POS. Tối đa {_MAX_UPLOAD_MB} MB khi buổi demo đông người.</p></div>',
            unsafe_allow_html=True,
        )
        uploaded = st.file_uploader("Chọn file", type=["csv", "xlsx", "xls"], label_visibility="collapsed")
        if uploaded is not None:
            _read_upload(uploaded)
    with c3:
        st.markdown(
            '<div class="pp-card"><div class="pp-kicker">Tải file mẫu</div>'
            '<p class="pp-muted">File Excel mẫu đúng cấu trúc để điền dữ liệu doanh nghiệp.</p></div>',
            unsafe_allow_html=True,
        )
        if TEMPLATE_PATH.exists():
            st.download_button(
                "Tải file mẫu",
                data=TEMPLATE_PATH.read_bytes(),
                file_name=TEMPLATE_PATH.name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        else:
            st.caption("Chưa có file mẫu. Chạy python scripts/generate_pharmacity_demo.py.")


def _read_upload(uploaded) -> None:
    max_bytes = _MAX_UPLOAD_MB * 1024 * 1024
    if uploaded.size > max_bytes:
        st.error(
            f"File quá lớn ({uploaded.size / (1024 * 1024):.1f} MB). "
            f"Buổi demo giới hạn {_MAX_UPLOAD_MB} MB — hãy dùng nút «Dùng dữ liệu mẫu»."
        )
        return
    file_bytes = uploaded.getvalue()
    sheet_name = None
    if Path(uploaded.name).suffix.lower() in {".xlsx", ".xls"}:
        sheets = list_excel_sheets(file_bytes)
        if len(sheets) > 1:
            default_idx = next(
                (i for i, name in enumerate(sheets) if name.strip().lower() in {"sales_data", "sales data", "data"}),
                0,
            )
            sheet_name = st.selectbox("Sheet dữ liệu bán hàng", sheets, index=default_idx)
    try:
        raw_df = load_raw_file(file_bytes, uploaded.name, sheet_name=sheet_name)
    except DataLoadError as exc:
        st.error(str(exc))
        return
    st.session_state["pending_raw_df"] = raw_df
    st.session_state["pending_filename"] = uploaded.name
    if st.session_state.get("pending_file_token") != (uploaded.name, uploaded.size):
        st.session_state["pending_mapping"] = suggest_mapping(list(raw_df.columns))
        st.session_state["pending_file_token"] = (uploaded.name, uploaded.size)
    st.success(f"Đã đọc {uploaded.name}: {raw_df.shape[0]:,} dòng, {raw_df.shape[1]} cột.")


def _mapping() -> None:
    raw_df = st.session_state.get("pending_raw_df")
    if raw_df is None:
        return
    st.markdown(
        '<div class="pp-section"><div><h2>Ánh xạ cột</h2>'
        "<p>Trường có (*) là bắt buộc. Gợi ý tự động có thể sửa trước khi áp dụng.</p></div></div>",
        unsafe_allow_html=True,
    )
    options = ["-- Không có --"] + list(raw_df.columns)
    suggested = st.session_state.get("pending_mapping") or {}
    new_mapping = {}
    left, right = st.columns(2)
    for index, field in enumerate(ALL_CANONICAL_FIELDS):
        target = left if index % 2 == 0 else right
        current = suggested.get(field)
        default_idx = options.index(current) if current in options else 0
        with target:
            chosen = st.selectbox(
                FIELD_LABELS_VI[field] + (" (*)" if field in REQUIRED_FIELDS else ""),
                options,
                index=default_idx,
                help=FIELD_HINTS_VI[field],
                key=f"map_{field}",
            )
        new_mapping[field] = None if chosen == "-- Không có --" else chosen
    st.session_state["pending_mapping"] = new_mapping
    if st.button("Áp dụng ánh xạ và kiểm tra chất lượng", type="primary", key="apply_map"):
        ok, message = commit_dataset(raw_df, st.session_state.get("pending_filename") or "upload", new_mapping)
        (st.success if ok else st.error)(message)
        if ok:
            st.rerun()


def _quality() -> None:
    report = st.session_state.get("quality_report")
    caps = st.session_state.get("capabilities")
    if report is None or caps is None:
        rows = "".join(
            f"<tr><td>{label}</td><td>{badge('Chưa có dữ liệu', 'muted')}</td><td>---</td></tr>"
            for label, _checker in CHECKS
        )
        st.markdown(
            f"""
<div class="pp-section"><div><h2>Kết quả kiểm tra dữ liệu</h2><p>Chưa có dữ liệu. Hãy dùng dữ liệu mẫu hoặc tải file.</p></div></div>
<div class="pp-grid-2">
  <div class="pp-card pp-ring-wrap">
    <div class="pp-ring" style="--p:0;--c:#E2E8F0"><span>---</span></div>
    <div>
      <div class="pp-kicker">Chất lượng dữ liệu</div>
      <p class="pp-muted">Chưa có dữ liệu</p>
    </div>
  </div>
  <div class="pp-card" style="overflow-x:auto">
    <table class="pp-table"><thead><tr><th>Loại dữ liệu</th><th>Trạng thái</th><th>Chi tiết</th></tr></thead>
    <tbody>{rows}</tbody></table>
  </div>
</div>
<div class="pp-banner">Chưa có dữ liệu để chấm điểm chất lượng.</div>
""",
            unsafe_allow_html=True,
        )
        return
    color = "#10B981" if report.score >= 85 else ("#F59E0B" if report.score >= 65 else "#EF4444")
    rows = []
    missing_inventory = False
    for label, checker in CHECKS:
        ok, detail = checker(report, caps)
        if label.startswith("Dữ liệu tồn kho") and not ok:
            missing_inventory = True
        rows.append(
            f"<tr><td>{label}</td><td>{badge('OK' if ok else 'Thiếu dữ liệu', 'ok' if ok else 'warn')}</td><td>{detail}</td></tr>"
        )
    if missing_inventory:
        note = '<div class="pp-banner">Bổ sung dữ liệu tồn kho để cải thiện chất lượng mô phỏng và đề xuất nhập hàng.</div>'
    elif report.warnings:
        note = f'<div class="pp-banner warn">{report.warnings[0]}</div>'
    else:
        note = '<div class="pp-banner good">Dữ liệu đã sẵn sàng để phân tích các bước tiếp theo.</div>'
    checked = ""
    if st.session_state.get("data_loaded_at"):
        checked = st.session_state["data_loaded_at"].strftime("%d/%m/%Y %H:%M")
    st.markdown(
        f"""
<div class="pp-section"><div><h2>Kết quả kiểm tra dữ liệu</h2><p>Điểm chất lượng {report.score_label}. Kiểm tra lúc {checked}.</p></div></div>
<div class="pp-grid-2">
  <div class="pp-card pp-ring-wrap">
    <div class="pp-ring" style="--p:{report.score};--c:{color}"><span>{report.score}%</span></div>
    <div>
      <div class="pp-kicker">Chất lượng dữ liệu</div>
      <p class="pp-muted">{report.n_days_span} ngày · {report.n_skus:,} SKU · {report.n_invalid_rows_dropped:,} dòng lỗi đã loại.</p>
    </div>
  </div>
  <div class="pp-card" style="overflow-x:auto">
    <table class="pp-table"><thead><tr><th>Loại dữ liệu</th><th>Trạng thái</th><th>Chi tiết</th></tr></thead>
    <tbody>{''.join(rows)}</tbody></table>
  </div>
</div>
{note}
""",
        unsafe_allow_html=True,
    )
