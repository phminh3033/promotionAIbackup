"""Business Onboarding Profile (mục VII yêu cầu gốc). Lưu local bằng JSON — không cần Cloud/DB."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import yaml

PROFILE_DIR = Path(__file__).resolve().parent.parent.parent / "config" / "business_profiles"
BUSINESS_RULES_YAML = Path(__file__).resolve().parent.parent.parent / "config" / "business_rules.yaml"


def load_business_rules_defaults() -> dict:
    """Đọc config/business_rules.yaml (mục XL) làm giá trị khởi tạo mặc định.

    Nếu file không tồn tại/lỗi, trả về {} — BusinessProfile() vẫn dùng default trong dataclass,
    không crash.
    """
    try:
        data = yaml.safe_load(BUSINESS_RULES_YAML.read_text(encoding="utf-8"))
        return data or {}
    except Exception:  # noqa: BLE001
        return {}


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
    min_roi_pct: float = 0.20
    max_campaign_duration_days: int = 14
    mask_customer_id: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "BusinessProfile":
        valid_keys = BusinessProfile.__dataclass_fields__.keys()
        filtered = {k: v for k, v in d.items() if k in valid_keys}
        return BusinessProfile(**filtered)

    @staticmethod
    def with_yaml_defaults(**overrides) -> "BusinessProfile":
        """Tạo BusinessProfile mới, khởi tạo constraint từ config/business_rules.yaml (mục XL)."""
        rules = load_business_rules_defaults()
        # Ép kiểu tường minh: YAML tự suy luận int/float theo cách viết số trong file (vd "8" ->
        # int, "8.0" -> float), có thể không khớp kiểu Streamlit widget yêu cầu — không phụ thuộc
        # vào việc người sửa file .yaml có viết đúng định dạng số thập phân hay không.
        kwargs = {
            "min_margin_pct": float(rules.get("minimum_margin", 0.15)),
            "max_discount_pct": float(rules.get("maximum_discount", 0.30)),
            "min_roi_pct": float(rules.get("minimum_roi", 0.20)),
            "safety_stock_days": int(rules.get("safety_stock_days", 7)),
            "lead_time_days": int(rules.get("lead_time_days", 5)),
            "max_campaign_duration_days": int(rules.get("campaign_duration_days", 14)),
            "promotion_budget": float(rules.get("promotion_budget_vnd", 20_000_000.0)),
            "service_capacity_per_staff_per_hour": float(rules.get("service_capacity_per_staff_per_hour", 8.0)),
        }
        kwargs.update(overrides)
        return BusinessProfile(**kwargs)


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
