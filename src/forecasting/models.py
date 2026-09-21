"""Các mô hình dự báo chuỗi thời gian (mục IX yêu cầu gốc: không dùng 1 model duy nhất).

Mỗi model implement interface chung: fit(y: pd.Series có DatetimeIndex) -> self, forecast(horizon) -> np.ndarray.
Dự báo âm được clip về 0 vì nhu cầu/doanh số không thể âm.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from statsmodels.tsa.holtwinters import ExponentialSmoothing, SimpleExpSmoothing

from src.features.engineering import add_calendar_features, add_lag_rolling_features

try:
    from xgboost import XGBRegressor  # type: ignore

    _HAS_XGBOOST = True
except Exception:  # noqa: BLE001
    _HAS_XGBOOST = False

try:
    from lightgbm import LGBMRegressor  # type: ignore

    _HAS_LIGHTGBM = True
except Exception:  # noqa: BLE001
    _HAS_LIGHTGBM = False

try:
    from catboost import CatBoostRegressor  # type: ignore

    _HAS_CATBOOST = True
except Exception:  # noqa: BLE001
    _HAS_CATBOOST = False


class BaseForecastModel:
    name = "base"
    min_obs = 1

    def fit(self, y: pd.Series) -> "BaseForecastModel":
        raise NotImplementedError

    def forecast(self, horizon: int) -> np.ndarray:
        raise NotImplementedError

    @staticmethod
    def _clip_non_negative(arr: np.ndarray) -> np.ndarray:
        return np.clip(np.nan_to_num(arr, nan=0.0), a_min=0, a_max=None)


class NaiveModel(BaseForecastModel):
    name = "Naive (giữ nguyên giá trị gần nhất)"
    min_obs = 3

    def fit(self, y: pd.Series):
        self.last_value = float(y.iloc[-1])
        return self

    def forecast(self, horizon: int) -> np.ndarray:
        return self._clip_non_negative(np.full(horizon, self.last_value))


class SeasonalNaiveModel(BaseForecastModel):
    name = "Seasonal Naive (lặp lại tuần trước)"
    min_obs = 14

    def fit(self, y: pd.Series):
        self.last_week = y.iloc[-7:].values
        return self

    def forecast(self, horizon: int) -> np.ndarray:
        reps = int(np.ceil(horizon / 7))
        return self._clip_non_negative(np.tile(self.last_week, reps)[:horizon])


class MovingAverageModel(BaseForecastModel):
    name = "Trung bình trượt 7 ngày"
    min_obs = 7

    def __init__(self, window: int = 7):
        self.window = window

    def fit(self, y: pd.Series):
        self.avg = float(y.iloc[-self.window :].mean())
        return self

    def forecast(self, horizon: int) -> np.ndarray:
        return self._clip_non_negative(np.full(horizon, self.avg))


class ExpSmoothingModel(BaseForecastModel):
    name = "Exponential Smoothing"
    min_obs = 14

    def fit(self, y: pd.Series):
        self.model = SimpleExpSmoothing(y.values, initialization_method="estimated").fit()
        return self

    def forecast(self, horizon: int) -> np.ndarray:
        return self._clip_non_negative(np.asarray(self.model.forecast(horizon)))


class HoltWintersModel(BaseForecastModel):
    name = "Holt-Winters (xu hướng + mùa vụ tuần)"
    min_obs = 21

    def fit(self, y: pd.Series):
        seasonal_periods = 7
        use_seasonal = len(y) >= seasonal_periods * 2
        kwargs = dict(trend="add", initialization_method="estimated")
        if use_seasonal:
            kwargs.update(seasonal="add", seasonal_periods=seasonal_periods)
        try:
            self.model = ExponentialSmoothing(y.values, **kwargs).fit(optimized=True)
        except Exception:  # noqa: BLE001 - fallback nếu dữ liệu quá ít biến động
            self.model = ExponentialSmoothing(y.values, trend=None, initialization_method="estimated").fit()
        return self

    def forecast(self, horizon: int) -> np.ndarray:
        return self._clip_non_negative(np.asarray(self.model.forecast(horizon)))


class _MLRecursiveModel(BaseForecastModel):
    """Model ML dùng lag/rolling/calendar features, dự báo đệ quy (recursive multi-step)."""

    min_obs = 30
    estimator_cls: type = RandomForestRegressor
    estimator_kwargs: dict = {}

    def fit(self, y: pd.Series):
        df = pd.DataFrame({"day": pd.to_datetime(y.index), "value": y.values})
        df = add_calendar_features(df, date_col="day")
        df = add_lag_rolling_features(df, target_col="value")
        feature_cols = [c for c in df.columns if c not in ("day", "value")]
        train = df.dropna(subset=feature_cols)
        if len(train) < 5:
            train = df.fillna(0)
        self.feature_cols = feature_cols
        self.model = self.estimator_cls(**self.estimator_kwargs)
        self.model.fit(train[feature_cols], train["value"])
        self.history = df[["day", "value"]].copy()
        return self

    def forecast(self, horizon: int) -> np.ndarray:
        history = self.history.copy()
        preds = []
        last_day = history["day"].iloc[-1]
        for i in range(1, horizon + 1):
            next_day = last_day + pd.Timedelta(days=i)
            temp = pd.concat(
                [history, pd.DataFrame({"day": [next_day], "value": [np.nan]})], ignore_index=True
            )
            temp = add_calendar_features(temp, date_col="day")
            temp = add_lag_rolling_features(temp, target_col="value")
            row = temp.iloc[[-1]][self.feature_cols].fillna(0)
            pred = max(0.0, float(self.model.predict(row)[0]))
            preds.append(pred)
            history = pd.concat(
                [history, pd.DataFrame({"day": [next_day], "value": [pred]})], ignore_index=True
            )
        return np.array(preds)


class RandomForestModel(_MLRecursiveModel):
    name = "Random Forest"
    min_obs = 30
    estimator_cls = RandomForestRegressor
    estimator_kwargs = {"n_estimators": 200, "max_depth": 6, "random_state": 42}


class GradientBoostingModel(_MLRecursiveModel):
    name = "Gradient Boosting"
    min_obs = 30
    estimator_cls = GradientBoostingRegressor
    estimator_kwargs = {"n_estimators": 150, "max_depth": 3, "learning_rate": 0.08, "random_state": 42}


class XGBoostModel(_MLRecursiveModel):
    name = "XGBoost"
    min_obs = 30
    if _HAS_XGBOOST:
        estimator_cls = XGBRegressor
        estimator_kwargs = {
            "n_estimators": 200,
            "max_depth": 4,
            "learning_rate": 0.08,
            "random_state": 42,
            "verbosity": 0,
        }


class LightGBMModel(_MLRecursiveModel):
    name = "LightGBM"
    min_obs = 30
    if _HAS_LIGHTGBM:
        estimator_cls = LGBMRegressor
        estimator_kwargs = {
            "n_estimators": 200,
            "max_depth": 5,
            "learning_rate": 0.08,
            "random_state": 42,
            "verbosity": -1,
            "min_child_samples": 5,
        }


class CatBoostModel(_MLRecursiveModel):
    name = "CatBoost"
    min_obs = 30
    if _HAS_CATBOOST:
        estimator_cls = CatBoostRegressor
        estimator_kwargs = {
            "iterations": 200,
            "depth": 5,
            "learning_rate": 0.08,
            "random_state": 42,
            "verbose": False,
            "allow_writing_files": False,
        }


class EnsembleAverageModel(BaseForecastModel):
    """Kết hợp trung bình cộng dự báo của nhiều model con — thường ổn định hơn từng model riêng lẻ.

    [LITERATURE]: ensemble learning (trung bình/kết hợp nhiều model) cho kết quả dự báo retail
    tốt hơn model đơn lẻ trong nhiều trường hợp — xem docs/nghien_cuu_nen_tang.md mục 1.2
    (hybrid ensemble learning, Computing 2024). Đây là bản ensemble đơn giản nhất (simple average),
    không học trọng số — [ASSUMPTION cho MVP] trọng số bằng nhau giữa các model con, thay vì tối ưu
    hoá trọng số theo hiệu suất (stacking) vốn cần nhiều dữ liệu hơn để tránh overfit trên MVP.
    """

    name = "base_ensemble"
    min_obs = 30
    sub_model_classes: tuple[type, ...] = ()

    def fit(self, y: pd.Series):
        self.sub_models = [cls().fit(y) for cls in self.sub_model_classes]
        return self

    def forecast(self, horizon: int) -> np.ndarray:
        preds = np.array([m.forecast(horizon) for m in self.sub_models])
        return self._clip_non_negative(preds.mean(axis=0))


class EnsembleStatMLModel(EnsembleAverageModel):
    name = "Ensemble (Holt-Winters + Random Forest)"
    min_obs = max(HoltWintersModel.min_obs, RandomForestModel.min_obs)
    sub_model_classes = (HoltWintersModel, RandomForestModel)


def get_candidate_models(n_obs: int) -> list[BaseForecastModel]:
    """Trả về danh sách model khả thi với độ dài dữ liệu hiện có.

    [LITERATURE]: ý tưởng "không có model duy nhất tối ưu cho mọi chuỗi, cần thử nhiều model
    rồi chọn theo backtest" theo tinh thần paper hybrid ensemble (Computing, 2024) — xem
    docs/nghien_cuu_nen_tang.md mục 1.2.
    """
    candidates: list[BaseForecastModel] = [
        NaiveModel(),
        MovingAverageModel(),
    ]
    if n_obs >= SeasonalNaiveModel.min_obs:
        candidates.append(SeasonalNaiveModel())
    if n_obs >= ExpSmoothingModel.min_obs:
        candidates.append(ExpSmoothingModel())
    if n_obs >= HoltWintersModel.min_obs:
        candidates.append(HoltWintersModel())
    if n_obs >= RandomForestModel.min_obs:
        candidates.append(RandomForestModel())
    if n_obs >= GradientBoostingModel.min_obs:
        candidates.append(GradientBoostingModel())
    if _HAS_XGBOOST and n_obs >= XGBoostModel.min_obs:
        candidates.append(XGBoostModel())
    if _HAS_LIGHTGBM and n_obs >= LightGBMModel.min_obs:
        candidates.append(LightGBMModel())
    if _HAS_CATBOOST and n_obs >= CatBoostModel.min_obs:
        candidates.append(CatBoostModel())
    if n_obs >= EnsembleStatMLModel.min_obs:
        candidates.append(EnsembleStatMLModel())
    return candidates
