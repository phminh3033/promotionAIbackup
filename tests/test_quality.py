import numpy as np
import pandas as pd

from src.data.quality import run_quality_check


def _make_df(n_days=100):
    dates = pd.date_range("2025-01-01", periods=n_days, freq="D")
    return pd.DataFrame(
        {
            "date": dates,
            "product_id": ["SP01"] * n_days,
            "quantity": np.random.default_rng(0).integers(1, 10, n_days),
            "revenue": np.random.default_rng(0).integers(10_000, 100_000, n_days),
        }
    )


def test_quality_score_high_for_clean_data():
    df = _make_df()
    clean_df, report = run_quality_check(df)
    assert report.score >= 70
    assert len(clean_df) == len(df)


def test_quality_handles_missing_and_invalid_rows_without_crash():
    df = _make_df(30)
    df.loc[0, "date"] = pd.NaT
    df.loc[1, "quantity"] = np.nan
    df.loc[2, "revenue"] = -500
    clean_df, report = run_quality_check(df)
    assert report.n_invalid_rows_dropped >= 2
    assert report.n_negative_revenue >= 1
    assert len(clean_df) < len(df)


def test_quality_all_invalid_rows_does_not_crash():
    df = pd.DataFrame({"date": [pd.NaT], "product_id": [None], "quantity": [np.nan], "revenue": [np.nan]})
    clean_df, report = run_quality_check(df)
    assert clean_df.empty
    assert report.score == 0


def test_quality_short_history_gets_note():
    df = _make_df(20)
    _, report = run_quality_check(df)
    assert any("chưa đủ" in n for n in report.notes)
