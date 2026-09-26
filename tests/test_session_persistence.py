"""Kiểm thử lưu/khôi phục phiên làm việc (sống sót qua reload)."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from src.business.profile import BusinessProfile
from src.context.local_context import LocalContext
from src.data.schema import DatasetCapabilities
from src.utils.session_persistence import (
    apply_snapshot,
    build_snapshot,
    load_snapshot,
    new_workspace_id,
    sanitize_workspace_id,
    save_snapshot,
    workspace_path,
)


def test_sanitize_workspace_id():
    assert sanitize_workspace_id("abc12345") == "abc12345"
    assert sanitize_workspace_id("../etc/passwd") is None
    assert sanitize_workspace_id("short") is None
    assert sanitize_workspace_id(None) is None


def test_build_and_apply_snapshot_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "src.utils.session_persistence.WORKSPACE_DIR",
        tmp_path / "session_workspace",
    )
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
    assert snapshot["data_ref"] is None  # không phải demo → giữ DataFrame
    assert "clean_df" in snapshot["state"]
    assert snapshot["state"]["business_profile"].business_name == "Cửa hàng Test"

    wid = new_workspace_id()
    path = save_snapshot(wid, snapshot)
    assert path.exists()
    assert path == workspace_path(wid)

    loaded = load_snapshot(wid)
    assert loaded is not None
    restored: dict = {}
    apply_snapshot(loaded, restored)
    assert restored["objective"] == "TRAFFIC"
    assert restored["prep_lead"] == 5
    assert restored["sim_budget"] == 1_000_000.0
    assert restored["demo_access_granted"] is True
    assert isinstance(restored["clean_df"], pd.DataFrame)
    assert len(restored["clean_df"]) == 2
    assert restored["local_context"].store_name == "Chi nhánh 1"
    assert restored["ui_control_drafts"]["fc_horizon"] == 14


def test_demo_snapshot_omits_heavy_frames():
    df = pd.DataFrame({"a": [1, 2, 3]})
    session = {
        "raw_filename": "pharmacity_demo.csv",
        "clean_df": df,
        "mapped_df": df,
        "raw_df": df,
        "objective": "REVENUE",
    }
    snapshot = build_snapshot(session)
    assert snapshot["data_ref"] == "demo"
    assert "clean_df" not in snapshot["state"]
    assert "raw_df" not in snapshot["state"]
    assert snapshot["state"]["raw_filename"] == "pharmacity_demo.csv"


def test_load_missing_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "src.utils.session_persistence.WORKSPACE_DIR",
        tmp_path / "empty_ws",
    )
    assert load_snapshot("nonexistentid12") is None


def test_campaign_records_survive_snapshot_roundtrip(tmp_path, monkeypatch):
    """Chiến dịch đã triển khai phải còn sau pickle → hydrate (F5)."""
    from src.learning.campaign_log import (
        CampaignRecord,
        normalize_campaign_records_map,
    )

    monkeypatch.setattr(
        "src.utils.session_persistence.WORKSPACE_DIR",
        tmp_path / "ws_camp",
    )
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
    wid = "camppersist01ab"
    save_snapshot(wid, build_snapshot(session))

    loaded = load_snapshot(wid)
    assert loaded is not None
    restored: dict = {}
    apply_snapshot(loaded, restored)
    restored["campaign_records"] = normalize_campaign_records_map(
        restored.get("campaign_records")
    )

    assert restored["active_campaign_id"] == "CAMP202609270001"
    camps = restored["campaign_records"]
    assert "CAMP202609270001" in camps
    got = camps["CAMP202609270001"]
    assert isinstance(got, CampaignRecord)
    assert got.product_focus == "Vitamin C"
    assert got.forecast["revenue"] == 12_000_000
    assert got.outcome_note == "launched"


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
