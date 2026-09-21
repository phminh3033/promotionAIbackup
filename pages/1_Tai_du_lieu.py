"""Trang Tải dữ liệu: upload CSV/XLSX + Data Mapping Wizard (mục V yêu cầu gốc)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from src.data.loader import DataLoadError, load_raw_file
from src.data.mapper import apply_mapping, detect_capabilities, suggest_mapping, validate_mapping
from src.data.quality import run_quality_check
from src.data.schema import ALL_CANONICAL_FIELDS, FIELD_HINTS_VI, FIELD_LABELS_VI, REQUIRED_FIELDS
from src.utils.state import init_session_state

init_session_state()

st.title("📤 Tải dữ liệu bán hàng")
st.write(
    "Tải lên file CSV hoặc Excel (XLSX) xuất từ hệ thống POS/bán hàng của bạn. "
    "Không cần đặt đúng tên cột — hệ thống sẽ giúp bạn ánh xạ (mapping) ở bước tiếp theo."
)

uploaded_file = st.file_uploader("Chọn file dữ liệu", type=["csv", "xlsx", "xls"])

if uploaded_file is not None:
    try:
        raw_df = load_raw_file(uploaded_file.read(), uploaded_file.name)
    except DataLoadError as e:
        st.error(str(e))
        st.stop()

    st.session_state["raw_df"] = raw_df
    st.session_state["raw_filename"] = uploaded_file.name
    st.success(f"Đã đọc file **{uploaded_file.name}**: {raw_df.shape[0]:,} dòng, {raw_df.shape[1]} cột.")
    st.dataframe(raw_df.head(10), use_container_width=True)

if st.session_state.get("raw_df") is not None:
    raw_df = st.session_state["raw_df"]
    st.divider()
    st.subheader("🧭 Data Mapping Wizard — Ánh xạ cột dữ liệu")
    st.write(
        "Hãy xác nhận (hoặc chỉnh sửa) cột nào trong file của bạn tương ứng với từng trường dữ liệu bên dưới. "
        "Các trường có dấu **(*)** là bắt buộc."
    )

    columns = list(raw_df.columns)
    options = ["-- Không có --"] + columns

    if st.session_state.get("column_mapping") is None or st.button("🔄 Gợi ý lại tự động"):
        st.session_state["column_mapping"] = suggest_mapping(columns)

    suggested = st.session_state["column_mapping"]
    new_mapping: dict[str, str | None] = {}

    col_left, col_right = st.columns(2)
    for i, field in enumerate(ALL_CANONICAL_FIELDS):
        target_col = col_left if i % 2 == 0 else col_right
        is_required = field in REQUIRED_FIELDS
        label = FIELD_LABELS_VI[field] + (" (*)" if is_required else " (tuỳ chọn)")
        current = suggested.get(field)
        default_idx = options.index(current) if current in options else 0
        with target_col:
            chosen = st.selectbox(
                label,
                options,
                index=default_idx,
                help=FIELD_HINTS_VI[field],
                key=f"map_{field}",
            )
            new_mapping[field] = None if chosen == "-- Không có --" else chosen

    st.session_state["column_mapping"] = new_mapping
    errors = validate_mapping(new_mapping)

    if errors:
        for e in errors:
            st.error(e)
    else:
        st.success("Mapping hợp lệ — đủ các trường bắt buộc.")
        if st.button("✅ Áp dụng Mapping & Kiểm tra chất lượng dữ liệu", type="primary"):
            mapped_df = apply_mapping(raw_df, new_mapping)
            clean_df, report = run_quality_check(mapped_df)
            caps = detect_capabilities(mapped_df)

            st.session_state["mapped_df"] = mapped_df
            st.session_state["clean_df"] = clean_df
            st.session_state["quality_report"] = report
            st.session_state["capabilities"] = caps
            # reset các kết quả phân tích cũ vì dữ liệu đã đổi
            for k in ["rfm_result", "segmentation_result", "basket_result", "historical_uplifts", "forecast_cache"]:
                st.session_state[k] = None if k != "forecast_cache" else {}

            st.success(
                f"Đã xử lý xong! {len(clean_df):,} dòng dữ liệu hợp lệ. "
                "Hãy sang trang **2. Chất lượng dữ liệu** để xem báo cáo chi tiết."
            )
else:
    st.info("Chưa có file nào được tải lên.")
