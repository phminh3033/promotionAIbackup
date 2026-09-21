"""Campaign Learning Loop (mục XXXII spec PromotionPilot AI).

Lưu lại từng campaign đã chạy (objective, scenario, forecast, actual, variance, ROI, AI
recommendation, outcome) để campaign sau có thể tham chiếu lại — nền tảng cho việc dần dần thay
giả định elasticity mặc định bằng dữ liệu lịch sử thật (xem src/promotion/mechanics.py::
estimate_historical_uplift và docs/backlog_tinh_nang.md).

MVP dùng file JSON local (giống src/business/profile.py) — không cần SQLite/Supabase để giữ đơn
giản; có thể nâng cấp sau nếu cần nhiều người dùng cùng lúc.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent.parent / "config" / "campaign_log"


@dataclass
class CampaignRecord:
    campaign_id: str
    objective: str
    product_focus: str
    promotion_label: str
    forecast: dict = field(default_factory=dict)
    actual: dict = field(default_factory=dict)
    variance: dict = field(default_factory=dict)
    roi_forecast: float | None = None
    roi_actual: float | None = None
    ai_action: str | None = None
    ai_action_reasons: list[str] = field(default_factory=list)
    outcome_note: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    def to_dict(self) -> dict:
        return asdict(self)


def save_campaign_record(record: CampaignRecord) -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    path = LOG_DIR / f"{record.campaign_id}.json"
    path.write_text(json.dumps(record.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_campaign_record(campaign_id: str) -> CampaignRecord | None:
    path = LOG_DIR / f"{campaign_id}.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return CampaignRecord(**data)


def list_campaign_records() -> list[CampaignRecord]:
    if not LOG_DIR.exists():
        return []
    records = []
    for p in sorted(LOG_DIR.glob("*.json"), reverse=True):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            records.append(CampaignRecord(**data))
        except Exception:  # noqa: BLE001 - file lỗi thì bỏ qua, không crash trang Monitor
            continue
    return records


def new_campaign_id() -> str:
    return f"CAMP{datetime.now().strftime('%Y%m%d%H%M%S')}"
