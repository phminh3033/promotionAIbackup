"""Trang Model & Độ tin cậy (mục XXVIII yêu cầu gốc)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st

from src.utils.state import init_session_state

init_session_state()

st.title("🧪 Model & Độ tin cậy")

st.markdown(
    """
PromoPilot AI **không dùng một mô hình dự báo cố định**. Với mỗi chuỗi dữ liệu (toàn công ty,
theo danh mục, hoặc theo SKU), hệ thống tự động:

1. Phân tích đặc điểm dữ liệu (xu hướng, mùa vụ theo tuần, dữ liệu ngắt quãng...).
2. Thử nhiều mô hình phù hợp: Naive, Seasonal Naive, Trung bình trượt, Exponential Smoothing,
   Holt-Winters, Random Forest, Gradient Boosting (và XGBoost nếu có cài đặt).
3. Kiểm tra từng mô hình bằng **backtesting** (dùng dữ liệu quá khứ để giả lập dự báo, so với
   thực tế đã biết) theo phương pháp time-series split (rolling-origin), không dùng ngẫu nhiên
   train/test như bài toán thông thường (tránh "nhìn thấy tương lai").
4. Chọn mô hình có sai số **WAPE** (Weighted Absolute Percentage Error) thấp nhất — WAPE được ưu
   tiên hơn MAPE vì ổn định hơn khi có nhiều ngày bán hàng thấp/bằng 0, phù hợp với dữ liệu bán lẻ SME.
"""
)

with st.expander("📖 Giải thích các chỉ số (bằng ngôn ngữ đơn giản)"):
    st.markdown(
        """
- **WAPE (sai số dự báo)**: trung bình sai lệch giữa dự báo và thực tế, tính theo tỷ lệ % trên
  tổng doanh số thực tế. WAPE = 10% nghĩa là dự báo lệch trung bình khoảng 10% so với thực tế.
- **Độ tin cậy Cao**: WAPE ≤ 10% — có thể dùng số liệu này để lên kế hoạch khá chắc chắn.
- **Độ tin cậy Trung bình**: WAPE 10–25% — dùng để tham khảo xu hướng, nên có phương án dự phòng.
- **Độ tin cậy Thấp**: WAPE > 25% — chỉ nên dùng để thấy xu hướng chung, không nên cam kết số liệu cứng.
- **Khoảng tin cậy (dải mờ trên biểu đồ)**: khoảng giá trị có khả năng xảy ra, rộng hơn nếu dữ liệu
  biến động nhiều hoặc dự báo càng xa trong tương lai.
"""
    )

st.divider()
st.subheader("📊 Các dự báo đã chạy trong phiên làm việc này")

cache = st.session_state.get("forecast_cache", {})
if not cache:
    st.info("Chưa chạy dự báo nào. Vào trang **3. Dự báo** để bắt đầu.")
else:
    rows = []
    for key, result in cache.items():
        rows.append(
            {
                "Chuỗi dữ liệu": result.series_name,
                "Mô hình được chọn": result.model_name,
                "WAPE": f"{result.wape:.1%}" if pd.notna(result.wape) else "N/A",
                "Độ tin cậy": result.confidence,
                "Đủ dữ liệu backtest?": "Có" if result.data_sufficient else "Không",
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

    st.subheader("Chi tiết từng dự báo")
    selected_key = st.selectbox("Chọn dự báo để xem chi tiết", list(cache.keys()))
    result = cache[selected_key]
    st.info(result.explanation)
    if not result.all_model_scores.empty:
        st.dataframe(result.all_model_scores, use_container_width=True)

st.divider()
st.caption(
    "Xem thêm cơ sở khoa học và các paper tham khảo cho phương pháp luận tại "
    "`docs/nghien_cuu_nen_tang.md` trong mã nguồn dự án."
)
