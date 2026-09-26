"""Data Workspace: demo, upload, mapping và điểm chất lượng thật — hiển thị dạng modal."""
from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from services.workflow import TEMPLATE_PATH, commit_dataset, load_demo_dataset
from src.data.loader import DataLoadError, list_excel_sheets, load_raw_file
from src.data.mapper import suggest_mapping
from src.data.schema import ALL_CANONICAL_FIELDS, FIELD_HINTS_VI, FIELD_LABELS_VI, REQUIRED_FIELDS
from ui.components import badge, banner, card, data_table, esc, grid, kicker, muted, score_ring, section, show

CHECKS = [
    ("Dữ liệu bán hàng", lambda report, caps: (True, f"{report.n_rows:,} dòng")),
    ("Dữ liệu sản phẩm", lambda report, caps: (report.n_skus > 0, f"{report.n_skus:,} sản phẩm")),
    ("Dữ liệu khách hàng", lambda report, caps: (bool(caps.has_customer), f"{report.n_customers:,} khách" if report.n_customers else "Thiếu mã khách hàng")),
    ("Dữ liệu tồn kho", lambda report, caps: (bool(caps.has_inventory), "Có cột tồn kho" if caps.has_inventory else "Thiếu dữ liệu")),
    ("Dữ liệu khuyến mãi", lambda report, caps: (bool(caps.has_promotion), "Có lịch sử khuyến mãi" if caps.has_promotion else "Thiếu lịch sử khuyến mãi")),
]

# Sàn cứng 30 MB — env cũ DEMO_MAX_UPLOAD_MB=5 không được phép hạ thấp hơn.
_MAX_UPLOAD_MB = max(30, int(os.getenv("DEMO_MAX_UPLOAD_MB", "30") or "30"))


@st.dialog("Data Workspace", width="large")
def open_modal() -> None:
    st.caption("Tải dữ liệu và kiểm tra chất lượng. Bắt đầu bằng dữ liệu mẫu hoặc file bán hàng của bạn.")
    _sources()
    _mapping()
    _quality()


def _sources() -> None:
    c1, c2 = st.columns(2)
    with c1, st.container(border=True):
        show(kicker("Sử dụng dữ liệu mẫu") + muted("Bộ dữ liệu nhà thuốc demo đã chuẩn bị sẵn."))
        if st.button("Dùng dữ liệu mẫu", type="primary", key="use_demo", width="stretch"):
            with st.spinner("Đang tải và kiểm tra dữ liệu demo..."):
                ok, message = load_demo_dataset()
            if ok:
                st.rerun()
            st.error(message)
    with c2, st.container(border=True):
        show(kicker("Tải file mẫu") + muted("File Excel đúng cấu trúc để điền dữ liệu doanh nghiệp."))
        if TEMPLATE_PATH.exists():
            st.download_button(
                "Tải file mẫu",
                data=TEMPLATE_PATH.read_bytes(),
                file_name=TEMPLATE_PATH.name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width="stretch",
            )
        else:
            st.caption("Chưa có file mẫu. Chạy python scripts/generate_pharmacity_demo.py.")
    show(card(
        kicker("Tải file dữ liệu của bạn")
        + muted(f"CSV/Excel từ POS. Tối đa {_MAX_UPLOAD_MB} MB mỗi file."),
        style="margin-top:12px",
    ))
    # accept_multiple_files=True giữ nút "+" để thêm file.
    uploaded_files = st.file_uploader(
        "Chọn file",
        type=["csv", "xlsx", "xls"],
        accept_multiple_files=True,
        label_visibility="collapsed",
        key="dw_file_uploader",
    )
    if not uploaded_files:
        return

    max_bytes = _MAX_UPLOAD_MB * 1024 * 1024
    ok_files = []
    for uploaded in uploaded_files:
        if uploaded.size > max_bytes:
            st.error(
                f"File «{uploaded.name}» quá lớn ({uploaded.size / (1024 * 1024):.1f} MB). "
                f"Giới hạn {_MAX_UPLOAD_MB} MB mỗi file."
            )
        else:
            ok_files.append(uploaded)

    if not ok_files:
        return

    # Chọn sheet nếu file Excel gần nhất có nhiều sheet (trước khi xác nhận).
    primary = ok_files[-1]
    sheet_name = _sheet_selector(primary)

    if st.button("Xác nhận", type="primary", key="dw_confirm_upload"):
        with st.spinner(f"Đang nạp {primary.name} vào hệ thống..."):
            ok, message = _confirm_and_load(primary, sheet_name=sheet_name)
        if ok:
            st.success(message)
            st.rerun()
        st.error(message)


def _sheet_selector(uploaded) -> str | None:
    if Path(uploaded.name).suffix.lower() not in {".xlsx", ".xls"}:
        return None
    try:
        sheets = list_excel_sheets(uploaded.getvalue())
    except Exception:
        return None
    if len(sheets) <= 1:
        return sheets[0] if sheets else None
    default_idx = next(
        (i for i, name in enumerate(sheets) if name.strip().lower() in {"sales_data", "sales data", "data"}),
        0,
    )
    return st.selectbox("Sheet dữ liệu bán hàng", sheets, index=default_idx, key="dw_sheet_select")


def _confirm_and_load(uploaded, sheet_name: str | None = None) -> tuple[bool, str]:
    """Đọc file đã upload và nạp vào session (pending + commit nếu map đủ)."""
    try:
        raw_df = load_raw_file(uploaded.getvalue(), uploaded.name, sheet_name=sheet_name)
    except DataLoadError as exc:
        return False, str(exc)

    mapping = suggest_mapping(list(raw_df.columns))
    st.session_state["pending_raw_df"] = raw_df
    st.session_state["pending_filename"] = uploaded.name
    st.session_state["pending_mapping"] = mapping
    st.session_state["pending_file_token"] = (uploaded.name, uploaded.size)

    ok, message = commit_dataset(raw_df, uploaded.name, mapping)
    if ok:
        return True, f"Đã nạp {uploaded.name}: {raw_df.shape[0]:,} dòng, {raw_df.shape[1]} cột. {message}"
    # Map thiếu — giữ pending để user chỉnh ở bước ánh xạ bên dưới.
    return (
        False,
        f"Đã đọc {uploaded.name} ({raw_df.shape[0]:,} dòng) nhưng chưa nạp đủ: {message}. "
        "Hãy chỉnh ánh xạ cột bên dưới rồi bấm «Áp dụng ánh xạ và kiểm tra chất lượng».",
    )


def _mapping() -> None:
    raw_df = st.session_state.get("pending_raw_df")
    if raw_df is None:
        return
    show(section("Ánh xạ cột", "Trường có (*) là bắt buộc. Gợi ý tự động có thể sửa trước khi áp dụng."))
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
        if ok:
            st.rerun()
        st.error(message)


def _quality() -> None:
    report = st.session_state.get("quality_report")
    caps = st.session_state.get("capabilities")
    if report is None or caps is None:
        rows = [[esc(label), badge("Chưa có dữ liệu", "muted"), esc("---")] for label, _checker in CHECKS]
        show(section("Kết quả kiểm tra dữ liệu", "Chưa có dữ liệu. Hãy dùng dữ liệu mẫu hoặc tải file."))
        show(grid([
            score_ring("---", 0, "#E2E8F0", "Chất lượng dữ liệu", "Chưa có dữ liệu"),
            data_table(["Loại dữ liệu", "Trạng thái", "Chi tiết"], rows, raw=True),
        ], columns=2))
        show(banner("Chưa có dữ liệu để chấm điểm chất lượng."))
        return
    color = "#10B981" if report.score >= 85 else ("#F59E0B" if report.score >= 65 else "#EF4444")
    rows = []
    missing_inventory = False
    for label, checker in CHECKS:
        ok, detail = checker(report, caps)
        if label.startswith("Dữ liệu tồn kho") and not ok:
            missing_inventory = True
        rows.append([
            esc(label),
            badge("OK" if ok else "Thiếu dữ liệu", "ok" if ok else "warn"),
            esc(detail),
        ])
    if missing_inventory:
        note = banner("Bổ sung dữ liệu tồn kho để cải thiện chất lượng mô phỏng và đề xuất nhập hàng.")
    elif report.warnings:
        note = banner(report.warnings[0], "warn")
    else:
        note = banner("Dữ liệu đã sẵn sàng để phân tích các bước tiếp theo.", "good")
    checked = ""
    if st.session_state.get("data_loaded_at"):
        checked = st.session_state["data_loaded_at"].strftime("%d/%m/%Y %H:%M")
    show(section("Kết quả kiểm tra dữ liệu", f"Điểm chất lượng {report.score_label}. Kiểm tra lúc {checked}."))
    show(grid([
        score_ring(
            f"{report.score}%",
            report.score,
            color,
            "Chất lượng dữ liệu",
            f"{report.n_days_span} ngày · {report.n_skus:,} SKU · {report.n_invalid_rows_dropped:,} dòng lỗi đã loại.",
        ),
        data_table(["Loại dữ liệu", "Trạng thái", "Chi tiết"], rows, raw=True),
    ], columns=2))
    show(note)
