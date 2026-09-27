"""Test encode/decode snapshot browser (không đụng logic nghiệp vụ)."""
from __future__ import annotations

from datetime import datetime

import pandas as pd

from src.business.profile import BusinessProfile
from src.context.local_context import LocalContext
from src.data.schema import DatasetCapabilities
from src.utils.browser_session import (
    apply_snapshot,
    build_cookie_meta,
    build_snapshot,
    decode_snapshot,
    encode_snapshot,
    parse_cookie_meta,
    _shrink_for_browser_quota,
)


def test_encode_roundtrip_preserves_inputs_and_results():
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-01-02"]),
            "product_id": ["A", "B"],
            "quantity": [1, 2],
            "revenue": [10.0, 20.0],
        }
    )
    session = {
        "raw_filename": "upload_custom.csv",
        "column_mapping": {"date": "date"},
        "clean_df": df,
        "mapped_df": df.copy(),
        "raw_df": df.copy(),
        "capabilities": DatasetCapabilities(has_category=True),
        "business_profile": BusinessProfile.with_yaml_defaults(business_name="Shop A"),
        "objective": "TRAFFIC",
        "local_context": LocalContext(store_name="CN1"),
        "forecast_cache": {"k": "v"},
        "prep_lead": 5,
        "demo_access_granted": True,
        "data_loaded_at": datetime(2026, 9, 27, 12, 0, 0),
    }
    snap = build_snapshot(session)
    assert snap["backend"] == "browser_only"
    restored: dict = {}
    apply_snapshot(decode_snapshot(encode_snapshot(snap)), restored)
    assert restored["objective"] == "TRAFFIC"
    assert restored["prep_lead"] == 5
    assert restored["demo_access_granted"] is True
    assert len(restored["clean_df"]) == 2


def test_demo_uses_data_ref_not_heavy_frames():
    df = pd.DataFrame({"a": [1, 2, 3]})
    snap = build_snapshot(
        {
            "raw_filename": "pharmacity_demo.csv",
            "clean_df": df,
            "mapped_df": df,
            "raw_df": df,
            "objective": "REVENUE",
        }
    )
    assert snap["data_ref"] == "demo"
    assert "clean_df" not in snap["state"]


def test_cookie_meta_is_small_and_roundtrips():
    meta = build_cookie_meta({"demo_access_granted": True, "clean_df": object(), "objective": "PROFIT"})
    assert len(meta) < 200
    parsed = parse_cookie_meta(meta)
    assert parsed["demo_access_granted"] is True


def test_shrink_when_over_quota(monkeypatch):
    monkeypatch.setattr("src.utils.browser_session.MAX_BROWSER_BYTES", 400)
    df = pd.DataFrame({"x": list(range(2000))})
    snap = build_snapshot(
        {
            "raw_filename": "upload_custom.csv",
            "clean_df": df,
            "mapped_df": df,
            "raw_df": df,
            "objective": "REVENUE",
            "forecast_cache": {"a": list(range(200))},
        }
    )
    slim = _shrink_for_browser_quota(snap)
    assert "clean_df" not in slim["state"]


def test_decode_invalid_returns_none():
    assert decode_snapshot("%%%invalid%%%") is None
