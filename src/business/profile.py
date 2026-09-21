"""Business Onboarding Profile (mục VII yêu cầu gốc). Lưu local bằng JSON — không cần Cloud/DB."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

PROFILE_DIR = Path(__file__).resolve().parent.parent.parent / "config" / "business_profiles"


@dataclass
class BusinessProfile:
    business_name: str = "Doanh nghiệp demo"
    industry: str = "Bán lẻ tổng hợp"
    b2b_or_b2c: str = "B2C"
    n_stores: int = 1
    sku_range: str = "30-100"
    typical_purchase_cycle_days: int = 14
    target_margin_pct: float = 0.30
    min_margin_pct: float = 0.15
    max_discount_pct: float = 0.30
    safety_stock_days: int = 7
    lead_time_days: int = 5
    allowed_mechanics: list[str] = field(
        default_factory=lambda: [
            "discount_percent",
            "discount_fixed",
            "bogo",
            "buy_x_get_y",
            "bundle",
            "gift",
            "member_price",
            "coupon",
            "buy_more_save_more",
        ]
    )
    promotion_budget: float = 20_000_000.0
    service_capacity_per_staff_per_hour: float = 8.0
    primary_objective: str = "REVENUE"
    has_seasonality: bool = True

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "BusinessProfile":
        valid_keys = BusinessProfile.__dataclass_fields__.keys()
        filtered = {k: v for k, v in d.items() if k in valid_keys}
        return BusinessProfile(**filtered)


def save_profile(profile: BusinessProfile, name: str = "default") -> Path:
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    path = PROFILE_DIR / f"{name}.json"
    path.write_text(json.dumps(profile.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_profile(name: str = "default") -> BusinessProfile | None:
    path = PROFILE_DIR / f"{name}.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return BusinessProfile.from_dict(data)


def list_profiles() -> list[str]:
    if not PROFILE_DIR.exists():
        return []
    return sorted(p.stem for p in PROFILE_DIR.glob("*.json"))
