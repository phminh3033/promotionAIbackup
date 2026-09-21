"""Phân cụm khách hàng dựa trên RFM bằng K-Means, tự chọn số cụm qua silhouette score.

[LITERATURE]: RFM + K-Means, xem docs/nghien_cuu_nen_tang.md mục 1.4.
[BUSINESS RULE]: ngưỡng số khách hàng tối thiểu (30) và logic đặt tên cụm theo rank
R/F/M là tự thiết kế cho MVP nhằm đảm bảo tính diễn giải được (interpretability) theo
yêu cầu gốc mục XII, không phải kết luận trực tiếp từ một paper cụ thể.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

MIN_CUSTOMERS_FOR_CLUSTERING = 30
CLUSTER_LABELS_PRIORITY = [
    "Khách giá trị cao",
    "Khách mua thường xuyên",
    "Khách có nguy cơ rời bỏ",
    "Khách mới",
    "Khách ít mua",
]


@dataclass
class SegmentationResult:
    rfm_labeled: pd.DataFrame
    cluster_summary: pd.DataFrame
    k: int
    silhouette: float
    sufficient_data: bool
    message: str


def run_segmentation(rfm: pd.DataFrame, k_range: range = range(2, 6)) -> SegmentationResult:
    n_customers = len(rfm)
    if n_customers < MIN_CUSTOMERS_FOR_CLUSTERING:
        return SegmentationResult(
            rfm_labeled=rfm.assign(cluster=-1, segment="Chưa đủ dữ liệu"),
            cluster_summary=pd.DataFrame(),
            k=0,
            silhouette=0.0,
            sufficient_data=False,
            message=(
                f"Chỉ có {n_customers} khách hàng, cần tối thiểu {MIN_CUSTOMERS_FOR_CLUSTERING} khách hàng "
                "để phân cụm có ý nghĩa thống kê. Hệ thống chưa đặt tên nhóm khách hàng."
            ),
        )

    features = rfm[["recency", "frequency", "monetary"]].copy()
    features_log = np.log1p(features.clip(lower=0))
    scaler = StandardScaler()
    X = scaler.fit_transform(features_log)

    best_k, best_score, best_labels = None, -1.0, None
    max_k = min(max(k_range), n_customers - 1)
    for k in [kk for kk in k_range if kk <= max_k]:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X)
        if len(set(labels)) < 2:
            continue
        score = silhouette_score(X, labels)
        if score > best_score:
            best_k, best_score, best_labels = k, score, labels

    if best_labels is None:
        best_k = 2
        km = KMeans(n_clusters=best_k, random_state=42, n_init=10)
        best_labels = km.fit_predict(X)
        best_score = silhouette_score(X, best_labels) if len(set(best_labels)) > 1 else 0.0

    rfm = rfm.copy()
    rfm["cluster"] = best_labels

    cluster_stats = rfm.groupby("cluster").agg(
        recency_mean=("recency", "mean"),
        frequency_mean=("frequency", "mean"),
        monetary_mean=("monetary", "mean"),
        n_customers=("cluster", "size"),
    ).reset_index()

    labels_map = _assign_cluster_labels(cluster_stats)
    rfm["segment"] = rfm["cluster"].map(labels_map)
    cluster_stats["segment"] = cluster_stats["cluster"].map(labels_map)

    return SegmentationResult(
        rfm_labeled=rfm,
        cluster_summary=cluster_stats.sort_values("monetary_mean", ascending=False).reset_index(drop=True),
        k=best_k,
        silhouette=float(best_score),
        sufficient_data=True,
        message=f"Phân {n_customers} khách hàng thành {best_k} nhóm (silhouette score = {best_score:.2f}).",
    )


def _assign_cluster_labels(cluster_stats: pd.DataFrame) -> dict[int, str]:
    stats = cluster_stats.copy()
    stats["recency_rank"] = stats["recency_mean"].rank(method="first")  # 1 = gần đây nhất (tốt)
    stats["frequency_rank"] = stats["frequency_mean"].rank(method="first", ascending=False)  # 1 = mua nhiều nhất
    stats["monetary_rank"] = stats["monetary_mean"].rank(method="first", ascending=False)  # 1 = chi nhiều nhất
    stats["overall_rank"] = stats["recency_rank"] + stats["frequency_rank"] + stats["monetary_rank"]

    labels_map: dict[int, str] = {}
    remaining = stats.copy()

    # 1) Khách giá trị cao: tổng rank tốt nhất (R, F, M đều tốt)
    best_row = remaining.sort_values("overall_rank").iloc[0]
    labels_map[int(best_row["cluster"])] = "Khách giá trị cao"
    remaining = remaining[remaining["cluster"] != best_row["cluster"]]

    # 2) Khách mua thường xuyên: frequency_rank tốt nhất trong số còn lại
    if not remaining.empty:
        row = remaining.sort_values("frequency_rank").iloc[0]
        labels_map[int(row["cluster"])] = "Khách mua thường xuyên"
        remaining = remaining[remaining["cluster"] != row["cluster"]]

    # 3) Khách có nguy cơ rời bỏ: recency_rank tệ nhất (lâu không quay lại) trong số còn lại
    if not remaining.empty:
        row = remaining.sort_values("recency_rank", ascending=False).iloc[0]
        labels_map[int(row["cluster"])] = "Khách có nguy cơ rời bỏ"
        remaining = remaining[remaining["cluster"] != row["cluster"]]

    # 4) Khách mới: recency tốt (mới mua gần đây) nhưng frequency thấp
    if not remaining.empty:
        remaining = remaining.copy()
        remaining["newness_score"] = remaining["recency_rank"] + (remaining["frequency_rank"] * -1)
        row = remaining.sort_values("recency_rank").iloc[0]
        labels_map[int(row["cluster"])] = "Khách mới"
        remaining = remaining[remaining["cluster"] != row["cluster"]]

    # 5) Còn lại: Khách ít mua
    for _, row in remaining.iterrows():
        labels_map[int(row["cluster"])] = "Khách ít mua"

    return labels_map
