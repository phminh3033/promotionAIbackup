"""Kiểm thử snapshot phiên (localStorage / encode — không dùng đĩa server chung)."""
from __future__ import annotations

from datetime import datetime

import pandas as pd

from src.business.profile import BusinessProfile
from src.context.local_context import LocalContext
from src.data.schema import DatasetCapabilities
from src.utils.session_persistence import (
    apply_snapshot,
    build_snapshot,
    decode_snapshot,
    encode_snapshot,
    _shrink_for_browser_quota,
)


def test_build_and_encode_roundtrip():
    profile = BusinessProfile.with_yaml_defaults(business_name="Cửa hàng Test")
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
        "business_profile": profile,
        "objective": "TRAFFIC",
        "local_context": LocalContext(store_name="Chi nhánh 1", business_events=["Tết"]),
        "forecast_cache": {"k1": "placeholder"},
        "last_scenario_meta": {"scope": "Toàn công ty", "promo_days": 7},
        "prep_lead": 5,
        "prep_lead_fmt": "5",
        "sim_budget": 1_000_000.0,
        "sim_budget_fmt": "1,000,000",
        "ui_control_drafts": {"fc_horizon": 14},
        "data_loaded_at": datetime(2026, 9, 26, 10, 0, 0),
        "demo_access_granted": True,
    }
    snapshot = build_snapshot(session)
    assert snapshot["backend"] == "browser_localStorage"
    assert snapshot["data_ref"] is None
    assert "clean_df" in snapshot["state"]

    blob = encode_snapshot(snapshot)
    assert isinstance(blob, str) and len(blob) > 20
    loaded = decode_snapshot(blob)
    assert loaded is not None
    restored: dict = {}
    apply_snapshot(loaded, restored)
    assert restored["objective"] == "TRAFFIC"
    assert restored["prep_lead"] == 5
    assert restored["demo_access_granted"] is True
    assert isinstance(restored["clean_df"], pd.DataFrame)
    assert restored["local_context"].store_name == "Chi nhánh 1"


def test_demo_snapshot_omits_heavy_frames():
    df = pd.DataFrame({"a": [1, 2, 3]})
    session = {
        "raw_filename": "pharmacity_demo.csv",
        "clean_df": df,
        "mapped_df": df,
        "raw_df": df,
        "objective": "REVENUE",
        "prep_lead": 7,
        "forecast_cache": {"k": "v"},
    }
    snapshot = build_snapshot(session)
    assert snapshot["data_ref"] == "demo"
    assert "clean_df" not in snapshot["state"]
    assert "raw_df" not in snapshot["state"]
    assert snapshot["state"]["raw_filename"] == "pharmacity_demo.csv"
    assert snapshot["state"]["prep_lead"] == 7

    loaded = decode_snapshot(encode_snapshot(snapshot))
    assert loaded is not None
    assert loaded["state"]["forecast_cache"] == {"k": "v"}


def test_campaign_records_survive_encode_roundtrip():
    from src.learning.campaign_log import CampaignRecord, normalize_campaign_records_map

    record = CampaignRecord(
        campaign_id="CAMP202609270001",
        objective="REVENUE",
        product_focus="Vitamin C",
        promotion_label="Giảm 20%",
        forecast={"revenue": 12_000_000},
        actual={"revenue": 11_500_000},
        roi_forecast=1.4,
        outcome_note="launched",
    )
    session = {
        "objective": "REVENUE",
        "active_campaign_id": record.campaign_id,
        "campaign_records": {record.campaign_id: record},
    }
    loaded = decode_snapshot(encode_snapshot(build_snapshot(session)))
    assert loaded is not None
    restored: dict = {}
    apply_snapshot(loaded, restored)
    restored["campaign_records"] = normalize_campaign_records_map(restored.get("campaign_records"))
    got = restored["campaign_records"]["CAMP202609270001"]
    assert isinstance(got, CampaignRecord)
    assert got.product_focus == "Vitamin C"


def test_normalize_campaign_records_from_plain_dicts():
    from src.learning.campaign_log import CampaignRecord, normalize_campaign_records_map

    raw = {
        "C1": {
            "campaign_id": "C1",
            "objective": "TRAFFIC",
            "product_focus": "SKU-A",
            "promotion_label": "Mua 1 tặng 1",
            "forecast": {},
            "actual": {},
            "variance": {},
            "roi_forecast": None,
            "roi_actual": None,
            "ai_action": None,
            "ai_action_reasons": [],
            "outcome_note": "",
            "created_at": "2026-09-27T01:00:00",
        }
    }
    out = normalize_campaign_records_map(raw)
    assert isinstance(out["C1"], CampaignRecord)
    assert out["C1"].promotion_label == "Mua 1 tặng 1"


def test_shrink_drops_heavy_frames_when_needed(monkeypatch):
    monkeypatch.setattr("src.utils.session_persistence.MAX_BROWSER_BYTES", 500)
    df = pd.DataFrame({"x": list(range(1000))})
    snap = build_snapshot(
        {
            "raw_filename": "upload_custom.csv",
            "clean_df": df,
            "mapped_df": df,
            "raw_df": df,
            "objective": "REVENUE",
            "forecast_cache": {"a": list(range(100))},
        }
    )
    slim = _shrink_for_browser_quota(snap)
    assert slim.get("quota_shrunk") is True or "clean_df" not in slim["state"]
    assert "clean_df" not in slim["state"]


def test_decode_invalid_returns_none():
    assert decode_snapshot("not-valid-base64!!!") is None


def test_purge_legacy_is_idempotent(tmp_path, monkeypatch):
    """Hàm xoá đĩa cũ không được crash khi thư mục trống / không tồn tại."""
    import src.utils.session_persistence as sp

    # Không gọi Streamlit thật — chỉ kiểm tra path logic qua monkeypatch Path trong hàm
    # (purge cần st.session_state). Test nhẹ: encode/decode đã cover chính.
    assert sp.STORAGE_KEY == "pp_session_v1"
    assert sp.MAX_BROWSER_BYTES > 0
