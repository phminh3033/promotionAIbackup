"""Reports: xuất Excel từ kết quả đã tính. PDF chưa có exporter nên không tạo file giả."""
from __future__ import annotations

import io

import pandas as pd
import streamlit as st

from services.workflow import kpi_snapshot, period_chip
from ui.components import DASH, EMPTY, card, grid, kicker, metric_mini, muted, show
from ui.formatters import compact_vnd, integer, pct, roi_label
from ui.shell import render_shell


def render() -> None:
    render_shell("Reports", "Xuất báo cáo từ các kết quả đã chạy trong phiên. Không điền số liệu minh hoạ.")
    from src.utils.state import has_data

    loaded = has_data()
    left, right = st.columns([1, 1], gap="large")
    with left:
        report_type = st.selectbox(
            "Loại báo cáo",
            ["Tổng hợp", "Hiệu quả chiến dịch", "Dự báo", "Mô phỏng khuyến mãi", "Khách hàng", "Tồn kho"],
            key="rep_type",
        )
        st.text_input("Kỳ dữ liệu", value=period_chip() if loaded else "---", disabled=True, key="rep_period")
        stores = ["Tất cả cửa hàng"]
        caps = st.session_state.get("capabilities")
        if loaded and caps is not None and caps.has_store:
            stores += sorted(st.session_state["clean_df"]["store_id"].dropna().astype(str).unique().tolist())
        store = st.selectbox("Cửa hàng / khu vực", stores, key="rep_store")
        fmt = st.radio("Định dạng", ["Excel", "PDF"], horizontal=True, key="rep_fmt")
        if fmt == "PDF":
            st.info("Bản này xuất Excel. PDF chưa có bộ kết xuất riêng nên không tạo file PDF giả.")
        if not loaded:
            st.button("Xuất báo cáo", type="primary", disabled=True, width="stretch")
            st.caption(EMPTY)
        else:
            buffer = _workbook(report_type, store)
            st.download_button(
                "Tải file Excel",
                data=buffer.getvalue(),
                file_name="promotionpilot_bao_cao.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width="stretch",
            )
    with right:
        if loaded:
            _preview(store)
        else:
            show(_preview_card(EMPTY, DASH, DASH, DASH, DASH, ""))


def _preview(store: str) -> None:
    df = _filtered(store)
    revenue = float(df["revenue"].sum()) if not df.empty else 0
    orders = int(df["transaction_id"].nunique()) if "transaction_id" in df.columns else len(df)
    margin = None
    if "gross_profit" in df.columns and revenue:
        margin = float(df["gross_profit"].sum()) / revenue
    snap = kpi_snapshot()
    show(_preview_card(
        f"{period_chip()} · {store}",
        compact_vnd(revenue),
        integer(orders),
        pct(margin, 1) if margin is not None else "—",
        roi_label(snap["roi"]) if snap else "—",
        "Phần dự báo, mô phỏng và đề xuất trong file là kết quả phiên làm việc, không tự chạy lại khi lọc cửa hàng.",
    ))


def _preview_card(subtitle: str, revenue: str, orders: str, margin: str, roi: str, note: str) -> str:
    note_html = muted(note) if note else ""
    return card(
        kicker("Xem trước báo cáo")
        + '<h2 style="margin:6px 0">PromotionPilot AI</h2>'
        + muted(subtitle)
        + grid([
            metric_mini("Doanh thu", revenue),
            metric_mini("Đơn / dòng", orders),
            metric_mini("Margin", margin),
            metric_mini("ROI mô phỏng", roi),
        ], columns=2)
        + note_html
    )


def _filtered(store: str) -> pd.DataFrame:
    df = st.session_state["clean_df"]
    if store != "Tất cả cửa hàng" and "store_id" in df.columns:
        return df[df["store_id"].astype(str) == store]
    return df


def _workbook(report_type: str, store: str) -> io.BytesIO:
    report = st.session_state["quality_report"]
    df = _filtered(store)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.DataFrame(
            [
                {"Chỉ số": "Cửa hàng", "Giá trị": store},
                {"Chỉ số": "Số dòng", "Giá trị": len(df)},
                {"Chỉ số": "Doanh thu", "Giá trị": float(df["revenue"].sum()) if not df.empty else 0},
                {"Chỉ số": "Điểm chất lượng", "Giá trị": f"{report.score}/100"},
                {"Chỉ số": "Kỳ", "Giá trị": period_chip()},
            ]
        ).to_excel(writer, sheet_name="Tong quan", index=False)
        if report_type in {"Tổng hợp", "Dự báo"} and st.session_state.get("forecast_cache"):
            rows = [
                {"Chuỗi": item.series_name, "Mô hình": item.model_name, "WAPE": item.wape, "Độ tin cậy": item.confidence}
                for item in st.session_state["forecast_cache"].values()
            ]
            pd.DataFrame(rows).to_excel(writer, sheet_name="Du bao", index=False)
        if report_type in {"Tổng hợp", "Mô phỏng khuyến mãi", "Hiệu quả chiến dịch"} and st.session_state.get("last_scenario_table") is not None:
            st.session_state["last_scenario_table"].to_excel(writer, sheet_name="Mo phong", index=False)
        card = st.session_state.get("last_recommendation_card")
        if report_type in {"Tổng hợp", "Hiệu quả chiến dịch"} and card is not None:
            pd.DataFrame(
                [
                    {"Mục": "Chương trình", "Giá trị": card.promotion_label},
                    {"Mục": "Sản phẩm", "Giá trị": card.product_focus},
                    {"Mục": "Rủi ro", "Giá trị": card.risk_label},
                    {"Mục": "Doanh thu dự kiến", "Giá trị": f"{card.expected_revenue_range[0]}-{card.expected_revenue_range[1]}"},
                ]
            ).to_excel(writer, sheet_name="De xuat", index=False)
        seg = st.session_state.get("segmentation_result")
        if report_type in {"Tổng hợp", "Khách hàng"} and seg is not None and seg.sufficient_data:
            seg.cluster_summary.to_excel(writer, sheet_name="Khach hang", index=False)
        plan = st.session_state.get("inventory_plan")
        if report_type in {"Tổng hợp", "Tồn kho"} and plan is not None:
            plan.to_excel(writer, sheet_name="Ton kho", index=False)
        if report_type in {"Tổng hợp", "Hiệu quả chiến dịch"} and st.session_state.get("last_execution_plan") is not None:
            st.session_state["last_execution_plan"].to_excel(writer, sheet_name="Ke hoach", index=False)
    return buffer
