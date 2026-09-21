"""Metric đánh giá và backtesting time-series (mục IX yêu cầu gốc).

[LITERATURE]: WAPE được ưu tiên làm metric chính vì ổn định hơn MAPE khi có nhiều
ngày sales thấp/bằng 0 (Hyndman, "WAPE: Weighted Absolute Percentage Error";
xem docs/nghien_cuu_nen_tang.md mục 1.8). MAPE chỉ hiển thị khi actual trung bình
đủ lớn để không bị chia cho số gần 0.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

MAPE_SAFE_MIN_MEAN = 1.0  # chỉ tính MAPE nếu giá trị trung bình actual > ngưỡng này


def compute_mae(actual: np.ndarray, pred: np.ndarray) -> float:
    return float(np.mean(np.abs(actual - pred)))


def compute_rmse(actual: np.ndarray, pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((actual - pred) ** 2)))


def compute_wape(actual: np.ndarray, pred: np.ndarray) -> float:
    denom = np.sum(np.abs(actual))
    if denom == 0:
        return float("inf") if np.sum(np.abs(pred)) > 0 else 0.0
    return float(np.sum(np.abs(actual - pred)) / denom)


def compute_mape_safe(actual: np.ndarray, pred: np.ndarray) -> float | None:
    if np.mean(np.abs(actual)) < MAPE_SAFE_MIN_MEAN:
        return None
    mask = actual != 0
    if mask.sum() == 0:
        return None
    return float(np.mean(np.abs((actual[mask] - pred[mask]) / actual[mask])))


@dataclass
class BacktestResult:
    model_name: str
    wape: float
    mae: float
    rmse: float
    mape: float | None
    residual_std: float
    n_folds: int


def rolling_backtest(y: pd.Series, model_factory, test_size: int, max_folds: int = 3) -> BacktestResult | None:
    """Time-series split kiểu rolling-origin: train tăng dần, test cố định `test_size` ngày mỗi fold.

    Trả về None nếu không đủ dữ liệu để backtest ít nhất 1 fold.
    """
    n = len(y)
    min_train = max(model_factory().min_obs, test_size * 2)
    if n < min_train + test_size:
        return None

    fold_errors = []
    fold_residuals = []
    n_possible_folds = (n - min_train) // test_size
    n_folds = max(1, min(max_folds, n_possible_folds))

    for fold in range(n_folds):
        test_end = n - fold * test_size
        test_start = test_end - test_size
        train_end = test_start
        if train_end < model_factory().min_obs:
            break

        train_y = y.iloc[:train_end]
        test_y = y.iloc[test_start:test_end]

        model = model_factory()
        try:
            model.fit(train_y)
            pred = model.forecast(len(test_y))
        except Exception:  # noqa: BLE001 - model lỗi trên fold này thì bỏ qua fold
            continue

        actual = test_y.values
        fold_errors.append(
            {
                "wape": compute_wape(actual, pred),
                "mae": compute_mae(actual, pred),
                "rmse": compute_rmse(actual, pred),
                "mape": compute_mape_safe(actual, pred),
            }
        )
        fold_residuals.extend((actual - pred).tolist())

    if not fold_errors:
        return None

    mapes = [e["mape"] for e in fold_errors if e["mape"] is not None]
    return BacktestResult(
        model_name=model_factory().name,
        wape=float(np.mean([e["wape"] for e in fold_errors])),
        mae=float(np.mean([e["mae"] for e in fold_errors])),
        rmse=float(np.mean([e["rmse"] for e in fold_errors])),
        mape=float(np.mean(mapes)) if mapes else None,
        residual_std=float(np.std(fold_residuals)) if fold_residuals else 0.0,
        n_folds=len(fold_errors),
    )


def confidence_label(wape: float) -> str:
    """[BUSINESS RULE tự thiết kế]: ngưỡng phân loại độ tin cậy dự báo theo WAPE."""
    if wape <= 0.10:
        return "Cao"
    if wape <= 0.25:
        return "Trung bình"
    return "Thấp"
