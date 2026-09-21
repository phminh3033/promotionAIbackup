"""Market Basket Analysis: FP-Growth + Association Rules (mục XIII yêu cầu gốc).

[LITERATURE]: FP-Growth nhanh hơn Apriori trên dataset vừa/lớn — xem
docs/nghien_cuu_nen_tang.md mục 1.5. Ngưỡng lift/confidence lọc kết quả là
[BUSINESS RULE] tự thiết kế cho MVP.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from mlxtend.frequent_patterns import association_rules, fpgrowth
from mlxtend.preprocessing import TransactionEncoder

MIN_LIFT = 1.0
MIN_CONFIDENCE = 0.3
MIN_TRANSACTIONS = 30


@dataclass
class BasketAnalysisResult:
    rules: pd.DataFrame
    n_transactions_used: int
    sufficient_data: bool
    message: str


def run_market_basket_analysis(
    df: pd.DataFrame,
    item_col: str = "product_id",
    min_support: float | None = None,
) -> BasketAnalysisResult:
    if "transaction_id" not in df.columns:
        return BasketAnalysisResult(
            rules=pd.DataFrame(),
            n_transactions_used=0,
            sufficient_data=False,
            message="Dữ liệu không có Mã giao dịch/hóa đơn nên không thể phân tích giỏ hàng.",
        )

    baskets = df.groupby("transaction_id")[item_col].apply(lambda s: sorted(set(s.dropna().astype(str)))).tolist()
    baskets = [b for b in baskets if len(b) >= 2]
    n_transactions = len(baskets)

    if n_transactions < MIN_TRANSACTIONS:
        return BasketAnalysisResult(
            rules=pd.DataFrame(),
            n_transactions_used=n_transactions,
            sufficient_data=False,
            message=(
                f"Chỉ có {n_transactions} giao dịch có từ 2 sản phẩm trở lên, "
                f"cần tối thiểu {MIN_TRANSACTIONS} để phân tích giỏ hàng đáng tin cậy."
            ),
        )

    encoder = TransactionEncoder()
    encoded = encoder.fit(baskets).transform(baskets)
    basket_df = pd.DataFrame(encoded, columns=encoder.columns_)

    if min_support is None:
        # [BUSINESS RULE]: support tối thiểu tự thích nghi theo cỡ dữ liệu, để không bỏ sót
        # cặp sản phẩm hiếm khi dataset nhỏ, nhưng không bùng nổ số luật khi dataset lớn.
        min_support = max(0.01, min(0.05, 20 / n_transactions))

    frequent_itemsets = fpgrowth(basket_df, min_support=min_support, use_colnames=True)
    if frequent_itemsets.empty:
        return BasketAnalysisResult(
            rules=pd.DataFrame(),
            n_transactions_used=n_transactions,
            sufficient_data=True,
            message="Không tìm thấy cặp sản phẩm nào được mua cùng nhau đủ thường xuyên với ngưỡng hiện tại.",
        )

    rules = association_rules(frequent_itemsets, metric="lift", min_threshold=MIN_LIFT, num_itemsets=len(basket_df))
    rules = rules[rules["confidence"] >= MIN_CONFIDENCE]
    rules = rules[rules["antecedents"].apply(len) == 1]
    rules = rules[rules["consequents"].apply(len) == 1]

    rules["antecedent"] = rules["antecedents"].apply(lambda s: next(iter(s)))
    rules["consequent"] = rules["consequents"].apply(lambda s: next(iter(s)))
    rules = rules[["antecedent", "consequent", "support", "confidence", "lift"]]
    rules = rules.sort_values("lift", ascending=False).reset_index(drop=True)

    return BasketAnalysisResult(
        rules=rules,
        n_transactions_used=n_transactions,
        sufficient_data=True,
        message=f"Phân tích {n_transactions} giao dịch, tìm được {len(rules)} luật kết hợp đáng chú ý.",
    )


def explain_rule(row: pd.Series) -> str:
    return (
        f"Khách mua **{row['antecedent']}** có xác suất mua thêm **{row['consequent']}** "
        f"là {row['confidence']:.0%} — cao gấp {row['lift']:.1f} lần so với mức bình thường."
    )
