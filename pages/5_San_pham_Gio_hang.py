"""Trang Sản phẩm & Giỏ hàng: xếp hạng sản phẩm + Market Basket Analysis (mục XIII)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import plotly.express as px
import streamlit as st

from src.basket.market_basket import explain_rule, run_market_basket_analysis
from src.utils.state import init_session_state, require_data_warning

init_session_state()

st.title("🛒 Sản phẩm & Phân tích Giỏ hàng")

if require_data_warning():
    st.stop()

df = st.session_state["clean_df"]
caps = st.session_state["capabilities"]

st.subheader("📦 Xếp hạng sản phẩm")
product_stats = df.groupby("product_id").agg(
    doanh_thu=("revenue", "sum"), san_luong=("quantity", "sum")
).reset_index().sort_values("doanh_thu", ascending=False)

col1, col2 = st.columns(2)
with col1:
    top_n = st.slider("Số sản phẩm hiển thị", 5, 30, 15)
    fig = px.bar(
        product_stats.head(top_n),
        x="doanh_thu",
        y="product_id",
        orientation="h",
        title=f"Top {top_n} sản phẩm theo doanh thu",
        labels={"doanh_thu": "Doanh thu (VNĐ)", "product_id": "Sản phẩm"},
    )
    fig.update_yaxes(categoryorder="total ascending")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    if caps.has_category:
        cat_stats = df.groupby("category")["revenue"].sum().reset_index().sort_values("revenue", ascending=False)
        fig2 = px.pie(cat_stats, names="category", values="revenue", title="Tỷ trọng doanh thu theo danh mục")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.dataframe(product_stats.head(top_n), use_container_width=True)

st.divider()
st.subheader("🔗 Phân tích giỏ hàng (Market Basket Analysis)")

if not caps.has_transaction:
    st.warning("⛔ Dữ liệu không có Mã giao dịch/hóa đơn nên không thể phân tích sản phẩm mua cùng nhau.")
else:
    if st.session_state.get("basket_result") is None:
        with st.spinner("Đang phân tích luật kết hợp (FP-Growth)..."):
            st.session_state["basket_result"] = run_market_basket_analysis(df)

    basket = st.session_state["basket_result"]
    st.info(basket.message)

    if basket.sufficient_data and not basket.rules.empty:
        rules_display = basket.rules.copy()
        rules_display["support"] = rules_display["support"].map(lambda v: f"{v:.1%}")
        rules_display["confidence"] = rules_display["confidence"].map(lambda v: f"{v:.1%}")
        rules_display["lift"] = rules_display["lift"].map(lambda v: f"{v:.2f}")
        rules_display = rules_display.rename(
            columns={
                "antecedent": "Mua sản phẩm",
                "consequent": "Có xu hướng mua thêm",
                "support": "Support",
                "confidence": "Confidence",
                "lift": "Lift",
            }
        )
        st.dataframe(rules_display, use_container_width=True)

        st.subheader("💡 Diễn giải luật kết hợp hàng đầu")
        for _, row in basket.rules.head(5).iterrows():
            st.markdown(f"- {explain_rule(row)}")

        st.caption(
            "Gợi ý: các cặp sản phẩm có **lift > 1** và **confidence cao** là ứng viên tốt cho "
            "chương trình Bundle/Combo — xem thêm ở trang **8. Kịch bản Promotion**."
        )
    elif basket.sufficient_data:
        st.write("Không tìm được luật kết hợp nào đủ mạnh với ngưỡng hiện tại.")
