"""Campaign Learning Loop (mục XXXII spec PromotionPilot AI).

Kho chiến dịch trong `st.session_state["campaign_records"]`, đồng bộ ra workspace đĩa
qua `save_workspace_now()` để sống sót F5/reload trình duyệt (cùng cơ chế session_persistence).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime

SESSION_KEY = "campaign_records"

# Fallback khi gọi ngoài Streamlit (script/test) — không ghi file.
_MEMORY_FALLBACK: dict[str, "CampaignRecord"] = {}


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


def _store() -> dict[str, CampaignRecord]:
    """Kho chiến dịch gắn session Streamlit; ngoài Streamlit dùng dict tạm trong process."""
    try:
        import streamlit as st

        if SESSION_KEY not in st.session_state or not isinstance(st.session_state[SESSION_KEY], dict):
            st.session_state[SESSION_KEY] = {}
        return st.session_state[SESSION_KEY]
    except Exception:  # noqa: BLE001 — script/test không có runtime Streamlit
        return _MEMORY_FALLBACK


def _as_record(value) -> CampaignRecord | None:
    if isinstance(value, CampaignRecord):
        return value
    if isinstance(value, dict):
        try:
            return CampaignRecord(**value)
        except TypeError:
            return None
    return None


def normalize_campaign_records_map(raw) -> dict[str, CampaignRecord]:
    """Chuẩn hoá map id→CampaignRecord sau hydrate/pickle (dict thuần → dataclass)."""
    if not isinstance(raw, dict):
        return {}
    out: dict[str, CampaignRecord] = {}
    for key, value in raw.items():
        record = _as_record(value)
        if record is None:
            continue
        out[str(record.campaign_id or key)] = record
    return out


def save_campaign_record(record: CampaignRecord) -> str:
    """Ghi/ghi đè record trong session + ép snapshot đĩa (giữ qua reload)."""
    store = _store()
    store[record.campaign_id] = record
    try:
        from src.utils.state import save_workspace_now

        save_workspace_now()
    except Exception:  # noqa: BLE001 — không chặn UI nếu persistence lỗi
        pass
    return record.campaign_id


def load_campaign_record(campaign_id: str) -> CampaignRecord | None:
    return _as_record(_store().get(campaign_id))


def list_campaign_records() -> list[CampaignRecord]:
    store = _store()
    normalized = normalize_campaign_records_map(store)
    # Ghi lại map đã chuẩn hoá nếu snapshot mang dict thuần / lẫn type.
    if any(not isinstance(v, CampaignRecord) for v in store.values()) or len(normalized) != len(store):
        try:
            import streamlit as st

            st.session_state[SESSION_KEY] = normalized
        except Exception:  # noqa: BLE001
            store.clear()
            store.update(normalized)

    records = list(normalized.values())
    records.sort(key=lambda item: item.created_at or "", reverse=True)
    return records


def new_campaign_id() -> str:
    return f"CAMP{datetime.now().strftime('%Y%m%d%H%M%S')}"
