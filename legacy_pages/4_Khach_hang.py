"""Trang Phân tích Khách hàng: RFM + K-Means Segmentation (mục XII yêu cầu gốc)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import plotly.express as px
import streamlit as st

from src.segmentation.clustering import run_segmentation
from src.segmentation.rfm import compute_rfm
from src.utils.state import init_session_state, require_data_warning

init_session_state()

st.title("👥 Phân tích Khách hàng (RFM)")

if require_data_warning():
    st.stop()

caps = st.session_state["capabilities"]
if not caps.has_customer:
    st.warning(
        "⛔ Dữ liệu không có cột **Mã khách hàng** nên không thể phân tích khách hàng. "
        "Nếu doanh nghiệp có hệ thống thành viên/CRM, hãy bổ sung cột này ở lần tải dữ liệu sau."
    )
    st.stop()

df = st.session_state["clean_df"]

if st.button("🔍 Phân tích RFM & Phân khúc khách hàng", type="primary") or st.session_state.get("segmentation_result"):
    if st.session_state.get("rfm_result") is None:
        rfm = compute_rfm(df[df["customer_id"] != "KHACH_LE"] if "KHACH_LE" in df["customer_id"].values else df)
        st.session_state["rfm_result"] = rfm
        st.session_state["segmentation_result"] = run_segmentation(rfm)

    rfm = st.session_state["rfm_result"]
    seg = st.session_state["segmentation_result"]

    st.info(seg.message)

    if seg.sufficient_data:
        st.subheader("Tổng quan các nhóm khách hàng")
        summary = seg.cluster_summary.copy()
        summary["% khách hàng"] = (summary["n_customers"] / summary["n_customers"].sum() * 100).round(1)
        summary_display = summary.rename(
            columns={
                "segment": "Nhóm khách hàng",
                "recency_mean": "Recency TB (ngày)",
                "frequency_mean": "Frequency TB (lần)",
                "monetary_mean": "Monetary TB (VNĐ)",
                "n_customers": "Số khách hàng",
            }
        )[["Nhóm khách hàng", "Số khách hàng", "% khách hàng", "Recency TB (ngày)", "Frequency TB (lần)", "Monetary TB (VNĐ)"]]
        st.dataframe(summary_display.style.format({"Recency TB (ngày)": "{:.0f}", "Frequency TB (lần)": "{:.1f}", "Monetary TB (VNĐ)": "{:,.0f}"}), use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            fig_pie = px.pie(summary, names="segment", values="n_customers", title="Tỷ trọng số lượng khách hàng theo nhóm")
            st.plotly_chart(fig_pie, use_container_width=True)
        with col2:
            fig_bar = px.bar(
                summary.sort_values("monetary_mean", ascending=False),
                x="segment",
                y="monetary_mean",
                title="Doanh thu trung bình/khách theo nhóm",
                labels={"segment": "Nhóm khách hàng", "monetary_mean": "Doanh thu TB (VNĐ)"},
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        fig_scatter = px.scatter(
            rfm.merge(seg.rfm_labeled[["customer_id", "segment"]], on="customer_id"),
            x="recency",
            y="monetary",
            size="frequency",
            color="segment",
            title="Bản đồ khách hàng: Recency vs Monetary (kích thước = Frequency)",
            labels={"recency": "Recency (ngày từ lần mua cuối)", "monetary": "Monetary (Tổng chi tiêu)"},
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

        st.subheader("💡 Ý nghĩa từng nhóm khách hàng")
        explain_map = {
            "Khách giá trị cao": "Chi tiêu nhiều, mua thường xuyên, mới mua gần đây — nhóm quan trọng nhất, nên ưu tiên giữ chân bằng ưu đãi thành viên/quà tặng thay vì giảm giá đại trà.",
            "Khách mua thường xuyên": "Mua lặp lại nhiều nhưng chi tiêu/lần thấp hơn nhóm giá trị cao — phù hợp với BOGO/Mua nhiều giảm nhiều để tăng giá trị đơn hàng.",
            "Khách có nguy cơ rời bỏ": "Đã lâu không quay lại mua — cần chương trình win-back (ưu đãi đặc biệt để kéo họ quay lại) trước khi mất hẳn.",
            "Khách mới": "Mới mua gần đây, chưa đủ dữ liệu để đánh giá lòng trung thành — nên tập trung trải nghiệm lần mua tiếp theo.",
            "Khách ít mua": "Tần suất và giá trị mua thấp — cân nhắc chi phí marketing hợp lý, không nên đầu tư ưu đãi sâu cho nhóm này.",
        }
        for seg_name in summary["segment"]:
            if seg_name in explain_map:
                st.markdown(f"**{seg_name}**: {explain_map[seg_name]}")

        with st.expander("Xem dữ liệu RFM chi tiết theo từng khách hàng"):
            st.dataframe(seg.rfm_labeled, use_container_width=True)
    else:
        st.dataframe(rfm, use_container_width=True)
