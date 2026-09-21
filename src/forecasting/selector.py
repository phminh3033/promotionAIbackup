"""Auto Model Selection: thử nhiều model, backtest, chọn model tốt nhất (mục IX yêu cầu gốc)."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.features.engineering import analyze_series_characteristics
from src.forecasting.backtest import BacktestResult, confidence_label, rolling_backtest
from src.forecasting.models import get_candidate_models

Z_80 = 1.2816  # z-score cho khoảng tin cậy ~80%


@dataclass
class ForecastResult:
    series_name: str
    model_name: str
    wape: float
    mape: float | None
    confidence: str
    dates: list[pd.Timestamp]
    yhat: np.ndarray
    yhat_lower: np.ndarray
    yhat_upper: np.ndarray
    explanation: str
    all_model_scores: pd.DataFrame
    data_sufficient: bool


def _pick_test_size(n_obs: int) -> int:
    if n_obs >= 90:
        return 14
    if n_obs >= 45:
        return 7
    return max(3, n_obs // 6)


def _explain_choice(model_name: str, characteristics: dict, wape: float) -> str:
    reasons = []
    if "Holt-Winters" in model_name:
        if characteristics.get("has_weekly_seasonality"):
            reasons.append("dữ liệu có mùa vụ theo tuần rõ ràng (doanh số các ngày trong tuần lệch nhau đáng kể)")
        if characteristics.get("has_trend"):
            reasons.append("dữ liệu có xu hướng tăng/giảm rõ ràng theo thời gian")
    elif "Ensemble" in model_name:
        reasons.append("kết hợp trung bình nhiều mô hình (thống kê + máy học) cho kết quả ổn định hơn dùng riêng lẻ từng mô hình")
    elif any(m in model_name for m in ("Random Forest", "Gradient Boosting", "XGBoost", "LightGBM", "CatBoost")):
        reasons.append("mối quan hệ giữa các yếu tố (thứ trong tuần, lag, trung bình trượt) phức tạp, mô hình máy học nắm bắt tốt hơn mô hình thống kê đơn giản")
    elif "Seasonal Naive" in model_name:
        reasons.append("dữ liệu lặp lại theo tuần khá ổn định nên lặp lại tuần trước cho kết quả tốt")
    elif "Naive" in model_name or "Trung bình trượt" in model_name:
        reasons.append("dữ liệu còn ít hoặc biến động không rõ quy luật, mô hình đơn giản giúp tránh dự báo sai lệch do overfitting")
    else:
        reasons.append("mô hình này cho sai số thấp nhất khi kiểm tra trên dữ liệu quá khứ (backtesting)")

    reason_text = "; ".join(reasons)
    confidence = confidence_label(wape)
    return (
        f"Hệ thống chọn mô hình **{model_name}** vì {reason_text}. "
        f"Sai số backtest (WAPE) là {wape:.1%}, tương ứng độ tin cậy **{confidence}**."
    )


def select_and_forecast(
    y: pd.Series,
    horizon: int,
    series_name: str = "Chuỗi thời gian",
) -> ForecastResult:
    """Chạy toàn bộ pipeline: phân tích chuỗi -> thử model -> backtest -> chọn tốt nhất -> forecast."""
    y = y.astype(float)
    n_obs = len(y)
    characteristics = analyze_series_characteristics(y)
    test_size = _pick_test_size(n_obs)

    candidates = get_candidate_models(n_obs)
    scores: list[BacktestResult] = []
    for model in candidates:
        model_cls = type(model)
        init_kwargs = getattr(model, "estimator_kwargs", None)

        def factory(cls=model_cls):
            return cls()

        result = rolling_backtest(y, factory, test_size=test_size, max_folds=3)
        if result is not None:
            scores.append(result)

    data_sufficient = len(scores) > 0 and n_obs >= 14

    if not scores:
        # Dữ liệu quá ít để backtest nghiêm túc -> dùng Naive nhưng cảnh báo rõ ràng
        from src.forecasting.models import NaiveModel

        model = NaiveModel().fit(y)
        yhat = model.forecast(horizon)
        dates = [y.index[-1] + pd.Timedelta(days=i) for i in range(1, horizon + 1)]
        return ForecastResult(
            series_name=series_name,
            model_name="Naive (dữ liệu quá ít để backtest)",
            wape=float("nan"),
            mape=None,
            confidence="Thấp",
            dates=dates,
            yhat=yhat,
            yhat_lower=yhat * 0.5,
            yhat_upper=yhat * 1.5,
            explanation=(
                f"Dữ liệu chỉ có {n_obs} ngày, chưa đủ để backtest đáng tin cậy. "
                "Hệ thống tạm dùng giá trị gần nhất làm dự báo và khuyến nghị thu thập thêm dữ liệu."
            ),
            all_model_scores=pd.DataFrame(),
            data_sufficient=False,
        )

    scores_df = pd.DataFrame(
        [
            {
                "model": s.model_name,
                "WAPE": s.wape,
                "MAE": s.mae,
                "RMSE": s.rmse,
                "MAPE": s.mape,
                "n_folds": s.n_folds,
            }
            for s in scores
        ]
    ).sort_values("WAPE")

    best = scores_df.iloc[0]
    best_model_name = best["model"]
    best_result = next(s for s in scores if s.model_name == best_model_name)

    best_model_cls = next(type(m) for m in candidates if m.name == best_model_name)
    final_model = best_model_cls()
    final_model.fit(y)
    yhat = final_model.forecast(horizon)

    dates = [y.index[-1] + pd.Timedelta(days=i) for i in range(1, horizon + 1)]
    growth = np.sqrt(np.arange(1, horizon + 1))
    margin = Z_80 * best_result.residual_std * growth
    yhat_lower = np.clip(yhat - margin, a_min=0, a_max=None)
    yhat_upper = yhat + margin

    explanation = _explain_choice(best_model_name, characteristics, best_result.wape)

    return ForecastResult(
        series_name=series_name,
        model_name=best_model_name,
        wape=best_result.wape,
        mape=best_result.mape,
        confidence=confidence_label(best_result.wape),
        dates=dates,
        yhat=yhat,
        yhat_lower=yhat_lower,
        yhat_upper=yhat_upper,
        explanation=explanation,
        all_model_scores=scores_df.reset_index(drop=True),
        data_sufficient=data_sufficient,
    )
