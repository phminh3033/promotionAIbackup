"""Test chuẩn hoá campaign records trong session."""
from __future__ import annotations

from src.learning.campaign_log import CampaignRecord, normalize_campaign_records_map


def test_normalize_campaign_records_from_plain_dicts():
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


def test_normalize_keeps_dataclass_records():
    record = CampaignRecord(
        campaign_id="CAMP_TEST_1",
        objective="REVENUE",
        product_focus="SKU-A",
        promotion_label="Giảm 10%",
    )
    out = normalize_campaign_records_map({"CAMP_TEST_1": record})
    assert out["CAMP_TEST_1"] is record
