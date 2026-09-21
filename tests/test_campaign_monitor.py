import pandas as pd

from src.monitoring.campaign_monitor import build_daily_baseline, compare_actual_vs_forecast, cumulative_variance


def test_build_daily_baseline_divides_by_promo_days():
    baseline = build_daily_baseline(
        expected_revenue_range=(1_000_000, 2_000_000),
        expected_gp_range=(200_000, 400_000),
        expected_customers_range=(50, 100),
        expected_demand_range=(100, 200),
        promo_days=5,
    )
    assert baseline.revenue_per_day == 300_000  # mid=1.5tr / 5 ngày
    assert baseline.customers_per_day == 15  # mid=75 / 5 ngày


def test_compare_actual_vs_forecast_computes_variance_pct():
    baseline = build_daily_baseline((1_000_000, 1_000_000), (200_000, 200_000), (50, 50), (100, 100), promo_days=5)
    actual = pd.DataFrame(
        {
            "date": pd.date_range("2026-12-20", periods=3),
            "revenue": [180_000, 200_000, 220_000],  # baseline/day = 200_000
        }
    )
    result = compare_actual_vs_forecast(actual, baseline)
    assert result.loc[0, "revenue_forecast"] == 200_000
    assert abs(result.loc[0, "revenue_variance_pct"] - (-0.10)) < 1e-9
    assert abs(result.loc[2, "revenue_variance_pct"] - 0.10) < 1e-9


def test_cumulative_variance_sums_before_comparing():
    baseline = build_daily_baseline((1_000_000, 1_000_000), (200_000, 200_000), (50, 50), (100, 100), promo_days=2)
    actual = pd.DataFrame({"date": pd.date_range("2026-12-20", periods=2), "revenue": [400_000, 600_000]})
    compared = compare_actual_vs_forecast(actual, baseline)
    variance = cumulative_variance(compared, "revenue")
    # forecast/ngay = 500_000 -> tong forecast 1_000_000; actual tong = 1_000_000 -> variance = 0
    assert abs(variance - 0.0) < 1e-9


def test_cumulative_variance_none_when_metric_missing():
    baseline = build_daily_baseline((1_000_000, 1_000_000), (200_000, 200_000), (50, 50), (100, 100), promo_days=2)
    actual = pd.DataFrame({"date": pd.date_range("2026-12-20", periods=2), "revenue": [400_000, 600_000]})
    compared = compare_actual_vs_forecast(actual, baseline)
    assert cumulative_variance(compared, "gp") is None
