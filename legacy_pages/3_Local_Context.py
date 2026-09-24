"""Trang Local Context (mục XI, XII spec PromotionPilot AI)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from src.context.local_context import BUSINESS_EVENTS, CUSTOMER_CONTEXTS, STORE_CONTEXTS, LocalContext
from src.optimization.objective import OBJECTIVE_LABELS_VI
from src.utils.state import init_session_state

init_session_state()

st.title("📍 Local Context — Bối cảnh địa phương")
st.write(
    "Dữ liệu bán hàng không thể hiện được mọi thứ đang diễn ra xung quanh cửa hàng. Hãy cho hệ "
    "thống biết thêm bối cảnh địa phương để đề xuất phù hợp hơn — đây là input **thủ công**, "
    "PromotionPilot AI chưa tự động thu thập dữ liệu bên ngoài (xem trạng thái ở cuối trang)."
)

ctx: LocalContext = st.session_state["local_context"]

col1, col2 = st.columns(2)
with col1:
    store_name = st.text_input("Tên cửa hàng / chi nhánh", value=ctx.store_name, placeholder="VD: Nhà thuốc ABC - Quận 7")
with col2:
    loc_col1, loc_col2 = st.columns(2)
    latitude = loc_col1.number_input("Vĩ độ (Latitude)", value=ctx.latitude or 0.0, format="%.6f")
    longitude = loc_col2.number_input("Kinh độ (Longitude)", value=ctx.longitude or 0.0, format="%.6f")

st.subheader("🗓️ Sự kiện kinh doanh (Business Event)")
business_events = st.multiselect(
    "Chọn 1 hoặc nhiều sự kiện đang/sắp diễn ra",
    BUSINESS_EVENTS,
    default=[e for e in ctx.business_events if e in BUSINESS_EVENTS],
)

st.subheader("👥 Đặc điểm khách hàng khu vực (Customer Context)")
customer_contexts = st.multiselect(
    "Khu vực xung quanh cửa hàng chủ yếu là nhóm khách hàng nào?",
    CUSTOMER_CONTEXTS,
    default=[c for c in ctx.customer_contexts if c in CUSTOMER_CONTEXTS],
)

st.subheader("🏪 Tình hình cửa hàng (Store Context)")
store_contexts = st.multiselect(
    "Cửa hàng hiện đang trong tình trạng nào?",
    STORE_CONTEXTS,
    default=[s for s in ctx.store_contexts if s in STORE_CONTEXTS],
)

free_text = st.text_area(
    "Mô tả thêm tình hình địa phương (tuỳ chọn)",
    value=ctx.free_text,
    placeholder="VD: Khu vực sắp có công trình sửa đường phía trước cửa hàng trong 2 tuần tới...",
)

if st.button("💾 Lưu bối cảnh địa phương", type="primary"):
    new_ctx = LocalContext(
        store_name=store_name,
        latitude=latitude if latitude != 0.0 else None,
        longitude=longitude if longitude != 0.0 else None,
        business_events=business_events,
        customer_contexts=customer_contexts,
        store_contexts=store_contexts,
        free_text=free_text,
    )
    st.session_state["local_context"] = new_ctx
    st.success("Đã lưu bối cảnh địa phương.")
    st.rerun()

if ctx.has_any_context():
    st.divider()
    st.subheader("📋 Tóm tắt bối cảnh hiện tại")
    st.info(ctx.summary_text())

    suggestion = ctx.suggested_objective()
    if suggestion:
        obj, reason = suggestion
        st.success(
            f"💡 Dựa trên sự kiện đã chọn, gợi ý mục tiêu kinh doanh: "
            f"**{OBJECTIVE_LABELS_VI[obj]}**. Lý do: {reason} "
            "Bạn có thể áp dụng gợi ý này ở trang **Mục tiêu kinh doanh**."
        )

st.divider()
st.subheader("🔌 Trạng thái nguồn dữ liệu bên ngoài (External Signals)")
st.caption(
    "Các nguồn dưới đây là kiến trúc chuẩn bị sẵn cho tương lai — MVP hiện tại CHƯA kết nối, "
    "không hiển thị số liệu giả."
)
from src.external_signals import competitor, events, google_trends, social_listener, weather  # noqa: E402

signal_cols = st.columns(5)
for col, module in zip(signal_cols, [social_listener, weather, competitor, google_trends, events]):
    status = module.get_status()
    with col:
        icon = "✅" if status.connected else "⛔"
        st.write(f"{icon} **{status.source_name}**")
        st.caption(status.message)
