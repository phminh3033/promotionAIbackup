import numpy as np
import pandas as pd

from src.forecasting.backtest import compute_mae, compute_mape_safe, compute_rmse, compute_wape
from src.forecasting.selector import select_and_forecast


def test_wape_perfect_prediction_is_zero():
    actual = np.array([10, 20, 30])
    pred = np.array([10, 20, 30])
    assert compute_wape(actual, pred) == 0.0


def test_wape_known_value():
    actual = np.array([100, 100])
    pred = np.array([90, 100])
    assert compute_wape(actual, pred) == 0.05


def test_mae_rmse_basic():
    actual = np.array([1, 2, 3])
    pred = np.array([1, 2, 5])
    assert compute_mae(actual, pred) == (0 + 0 + 2) / 3
    assert compute_rmse(actual, pred) == np.sqrt((0 + 0 + 4) / 3)


def test_mape_none_when_actual_near_zero():
    actual = np.array([0.0, 0.1, 0.2])
    pred = np.array([1.0, 1.0, 1.0])
    assert compute_mape_safe(actual, pred) is None


def test_select_and_forecast_short_series_uses_naive_fallback():
    y = pd.Series([100, 110, 105], index=pd.date_range("2026-01-01", periods=3))
    result = select_and_forecast(y, horizon=3)
    assert result.data_sufficient is False
    assert len(result.yhat) == 3
    assert all(v >= 0 for v in result.yhat)


def test_select_and_forecast_seasonal_series_picks_reasonable_model():
    rng = np.random.default_rng(42)
    days = pd.date_range("2025-01-01", periods=200, freq="D")
    weekday_effect = np.where(pd.Series(days.weekday).isin([5, 6]), 1.5, 1.0)
    values = 1000 * weekday_effect + rng.normal(0, 20, len(days))
    y = pd.Series(values, index=days)

    result = select_and_forecast(y, horizon=14)
    assert result.data_sufficient is True
    assert len(result.yhat) == 14
    assert len(result.yhat_lower) == 14
    assert all(result.yhat_lower <= result.yhat_upper)
    assert result.confidence in ("Cao", "Trung bình", "Thấp")
    assert not result.all_model_scores.empty


def test_forecast_never_negative():
    y = pd.Series([5, 0, 0, 3, 0, 0, 2] * 5, index=pd.date_range("2025-01-01", periods=35))
    result = select_and_forecast(y, horizon=7)
    assert all(v >= 0 for v in result.yhat)
