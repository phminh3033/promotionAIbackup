"""Model Info: mô tả đúng phương pháp đang có trong source, không điền thông số giả."""
from __future__ import annotations

import streamlit as st

from src.forecasting.models import get_candidate_models
from src.promotion.mechanics import MECHANIC_LABELS_VI
from ui.components import badge
from ui.shell import render_shell


def render() -> None:
    render_shell(
        "Model Information",
        "Phương pháp, dữ liệu đầu vào và độ tin cậy của các mô hình đang chạy trong PromotionPilot AI.",
    )
    names = [model.name for model in get_candidate_models(120)]
    forecast_note = "Chưa chạy trong phiên này."
    cache = st.session_state.get("forecast_cache") or {}
    if cache:
        latest = next(iter(cache.values()))
        wape = f"{latest.wape:.1%}" if latest.wape == latest.wape else "—"
        forecast_note = f"Lần gần nhất chọn {latest.model_name}, WAPE {wape}, độ tin cậy {latest.confidence}."
    seg = st.session_state.get("segmentation_result")
    if seg and seg.sufficient_data:
        seg_note = f"k = {seg.k}, silhouette {seg.silhouette:.2f}."
    elif seg:
        seg_note = seg.message
    else:
        seg_note = "Chưa chạy phân cụm trong phiên này."
    sim = st.session_state.get("last_scenario_table")
    sim_note = f"{len(sim)} kịch bản đang lưu." if sim is not None else "Chưa chạy mô phỏng trong phiên này."
    cards = [
        (
            "Demand Forecasting",
            "Dự báo nhu cầu và doanh thu",
            "Auto model selection: backtest rolling-origin, chọn mô hình WAPE thấp nhất.",
            ", ".join(names),
            "Doanh thu, sản lượng, lịch bán theo ngày. Có thể thêm số giao dịch hoặc số khách nếu dữ liệu có cột.",
            forecast_note,
            "Giải thích rule-based theo đặc điểm chuỗi và bảng WAPE. Không dùng SHAP.",
        ),
        (
            "Customer Segmentation",
            "Phân khúc khách hàng",
            "RFM + K-Means, số cụm chọn bằng silhouette.",
            "RFM, K-Means",
            "Lịch sử mua: ngày, mã khách, doanh thu, số lần mua.",
            seg_note,
            "Tên cụm diễn giải theo hạng R/F/M. Cần tối thiểu 30 khách hàng.",
        ),
        (
            "Promotion Simulation",
            "Mô phỏng khuyến mãi",
            "Cơ chế khuyến mãi + uplift lịch sử nếu đủ ngày khuyến mãi, nếu không thì elasticity giả định đã ghi trong code. Chấm điểm theo mục tiêu kinh doanh.",
            ", ".join(MECHANIC_LABELS_VI.values()),
            "Giá, giá vốn hoặc margin hồ sơ, nhu cầu 60 ngày, luật tồn kho và giỏ hàng nếu đã chạy.",
            sim_note,
            "Không phải Monte Carlo và không phải causal uplift. Kết quả để so sánh kịch bản.",
        ),
        (
            "Recommendation Engine",
            "Đề xuất phương án",
            "Tổng hợp kịch bản đã chấm điểm, luật kinh doanh, thời điểm bán và tồn kho thành một thẻ đề xuất.",
            "Mô hình khoa học hiện có",
            "Bảng mô phỏng, hồ sơ doanh nghiệp, dự báo nếu đã chạy.",
            "Luôn dùng mô hình khoa học hiện có.",
            "Không có trợ lý hội thoại. Đề xuất chỉ tổng hợp từ mô hình đã triển khai.",
        ),
    ]
    blocks = []
    for title, subtitle, method, catalog, inputs, status, explain in cards:
        blocks.append(
            f"""
<div class="pp-card">
  <div class="pp-kicker">{title}</div>
  <div class="pp-opp-title">{subtitle}</div>
  <p class="pp-muted"><b>Phương pháp.</b> {method}</p>
  <p class="pp-muted"><b>Thành phần.</b> {catalog}</p>
  <p class="pp-muted"><b>Đầu vào.</b> {inputs}</p>
  <p class="pp-muted"><b>Trạng thái phiên.</b> {status}</p>
  <p class="pp-muted"><b>Diễn giải.</b> {explain}</p>
  <div style="margin-top:8px">{badge("Đang dùng trong source", "info")}</div>
</div>
"""
        )
    st.markdown(f'<div class="pp-grid-2">{"".join(blocks)}</div>', unsafe_allow_html=True)
    st.markdown(
        '<p class="pp-foot">Prophet, SHAP và Monte Carlo không nằm trong mã nguồn hiện tại nên không được ghi trên trang này.</p>',
        unsafe_allow_html=True,
    )
