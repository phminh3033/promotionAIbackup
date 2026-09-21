"""Feature engineering cho các chuỗi thời gian tổng hợp theo ngày (mục IX yêu cầu gốc)."""
from __future__ import annotations

import numpy as np
import pandas as pd

# Ngày lễ Việt Nam phổ biến (dương lịch, cố định) — dùng như feature đơn giản.
# [BUSINESS RULE]: danh sách rút gọn cho MVP, không đầy đủ âm lịch (Tết biến động theo năm).
FIXED_VN_HOLIDAYS_MMDD = {
    "01-01": "Tết Dương lịch",
    "04-30": "Giải phóng miền Nam",
    "05-01": "Quốc tế Lao động",
    "09-02": "Quốc khánh",
    "12-24": "Giáng sinh (Eve)",
    "12-25": "Giáng sinh",
}


def aggregate_daily(df: pd.DataFrame, group_cols: list[str] | None = None) -> pd.DataFrame:
    """Tổng hợp dữ liệu giao dịch thành chuỗi thời gian theo ngày (và group_cols nếu có).

    group_cols vd: ["product_id"] hoặc ["category"] hoặc None (tổng toàn công ty).
    """
    df = df.copy()
    df["day"] = df["date"].dt.normalize()
    group_cols = group_cols or []
    keys = ["day"] + group_cols

    agg_dict = {"quantity": "sum", "revenue": "sum"}
    if "transaction_id" in df.columns:
        agg_dict["transaction_id"] = "nunique"
    if "customer_id" in df.columns:
        agg_dict["customer_id"] = "nunique"
    if "gross_profit" in df.columns:
        agg_dict["gross_profit"] = "sum"

    daily = df.groupby(keys, as_index=False).agg(agg_dict)
    rename = {"transaction_id": "n_transactions", "customer_id": "n_customers"}
    daily = daily.rename(columns=rename)

    if group_cols:
        full_index = pd.MultiIndex.from_product(
            [pd.date_range(df["day"].min(), df["day"].max(), freq="D")]
            + [daily[c].unique() for c in group_cols],
            names=keys,
        )
        daily = daily.set_index(keys).reindex(full_index, fill_value=0).reset_index()
    else:
        full_days = pd.date_range(df["day"].min(), df["day"].max(), freq="D")
        daily = daily.set_index("day").reindex(full_days, fill_value=0)
        daily.index.name = "day"
        daily = daily.reset_index()

    return daily.sort_values(keys).reset_index(drop=True)


def add_calendar_features(daily: pd.DataFrame, date_col: str = "day") -> pd.DataFrame:
    """Thêm đặc trưng lịch: weekday, weekend, tháng, ngày trong tháng, holiday."""
    daily = daily.copy()
    dt = daily[date_col]
    daily["weekday"] = dt.dt.weekday  # 0=Thứ 2
    daily["is_weekend"] = daily["weekday"].isin([5, 6]).astype(int)
    daily["month"] = dt.dt.month
    daily["day_of_month"] = dt.dt.day
    daily["week_of_year"] = dt.dt.isocalendar().week.astype(int)
    daily["is_month_start"] = dt.dt.is_month_start.astype(int)
    daily["is_month_end"] = dt.dt.is_month_end.astype(int)
    mmdd = dt.dt.strftime("%m-%d")
    daily["is_holiday"] = mmdd.isin(FIXED_VN_HOLIDAYS_MMDD.keys()).astype(int)
    return daily


def add_lag_rolling_features(
    daily: pd.DataFrame, target_col: str, lags: list[int] | None = None, windows: list[int] | None = None
) -> pd.DataFrame:
    """Thêm lag features và rolling mean/std cho target_col (vd: quantity, revenue)."""
    daily = daily.copy()
    lags = lags or [1, 7, 14]
    windows = windows or [7, 14, 28]

    for lag in lags:
        daily[f"{target_col}_lag_{lag}"] = daily[target_col].shift(lag)

    for w in windows:
        daily[f"{target_col}_roll_mean_{w}"] = daily[target_col].shift(1).rolling(w, min_periods=max(2, w // 3)).mean()
        daily[f"{target_col}_roll_std_{w}"] = daily[target_col].shift(1).rolling(w, min_periods=max(2, w // 3)).std()

    return daily


def analyze_series_characteristics(series: pd.Series) -> dict:
    """Phân tích đặc điểm chuỗi thời gian: trend, seasonality (tuần), intermittent, volatility.

    [BUSINESS RULE / heuristic đơn giản cho MVP] — không dùng statistical test phức tạp (STL, ADF)
    để giữ tốc độ và dễ giải thích, nhưng vẫn dựa trên các chỉ số thống kê cơ bản chuẩn.
    """
    s = series.astype(float).fillna(0)
    n = len(s)
    result = {
        "n_obs": n,
        "mean": float(s.mean()),
        "std": float(s.std()),
        "cv": float(s.std() / s.mean()) if s.mean() > 0 else np.inf,
        "pct_zero": float((s == 0).mean()),
        "is_intermittent": bool((s == 0).mean() > 0.3),
    }

    if n >= 14:
        x = np.arange(n)
        slope = np.polyfit(x, s.values, 1)[0]
        result["trend_slope"] = float(slope)
        result["has_trend"] = bool(abs(slope) > 0.01 * (s.mean() + 1e-6))
    else:
        result["trend_slope"] = 0.0
        result["has_trend"] = False

    if n >= 21:
        weekday_means = s.groupby(np.arange(n) % 7).mean()
        weekly_variation = weekday_means.std() / (s.mean() + 1e-6)
        result["weekly_seasonality_strength"] = float(weekly_variation)
        result["has_weekly_seasonality"] = bool(weekly_variation > 0.15)
    else:
        result["weekly_seasonality_strength"] = 0.0
        result["has_weekly_seasonality"] = False

    result["has_yearly_data"] = bool(n >= 350)

    return result
