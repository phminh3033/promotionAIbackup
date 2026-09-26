"""Local Context module (mục XI, XII spec PromotionPilot AI).

MVP dùng input THỦ CÔNG (người dùng tự chọn/nhập) — không crawl social/API thật. Kiến trúc sẵn
sàng để `src/external_signals/` cắm thêm nguồn tự động (weather, Google Trends, social listening,
competitor price...) sau này mà không phải đổi cấu trúc LocalContext này.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.recommendation.timing import EVENT_TO_OBJECTIVE

BUSINESS_EVENTS = list(EVENT_TO_OBJECTIVE.keys())

CUSTOMER_CONTEXTS = [
    "Gia đình có trẻ nhỏ",
    "Học sinh / sinh viên",
    "Người cao tuổi",
    "Nhân viên văn phòng",
    "Công nhân / lao động phổ thông",
    "Khách du lịch / vãng lai",
    "Mẹ & bé",
]

STORE_CONTEXTS = [
    "Tồn kho cao",
    "Tồn kho thấp",
    "Thiếu nhân sự",
    "Traffic cuối tuần cao",
    "Traffic buổi tối cao",
    "Cửa hàng mới mở",
    "Khu vực cạnh tranh cao",
]


@dataclass
class LocalContext:
    store_name: str = ""
    latitude: float | None = None
    longitude: float | None = None
    business_events: list[str] = field(default_factory=list)
    customer_contexts: list[str] = field(default_factory=list)
    store_contexts: list[str] = field(default_factory=list)
    free_text: str = ""

    def suggested_objective(self) -> tuple[str, str] | None:
        """Gợi ý (objective, lý do) dựa trên business event đầu tiên khớp với bảng ánh xạ đã có."""
        for event in self.business_events:
            if event in EVENT_TO_OBJECTIVE:
                return EVENT_TO_OBJECTIVE[event]
        return None

    def has_any_context(self) -> bool:
        return bool(
            (self.store_name or "").strip()
            or self.business_events
            or self.customer_contexts
            or self.store_contexts
            or self.free_text.strip()
        )

    def summary_text(self) -> str:
        parts = []
        if (self.store_name or "").strip():
            parts.append("Cửa hàng/khu vực: " + self.store_name.strip())
        if self.business_events:
            parts.append("Sự kiện: " + ", ".join(self.business_events))
        if self.customer_contexts:
            parts.append("Khách hàng khu vực: " + ", ".join(self.customer_contexts))
        if self.store_contexts:
            parts.append("Tình hình cửa hàng: " + ", ".join(self.store_contexts))
        if self.free_text.strip():
            parts.append("Ghi chú thêm: " + self.free_text.strip())
        return " | ".join(parts) if parts else "Chưa có thông tin bối cảnh địa phương."

    def to_dict(self) -> dict:
        return {
            "store_name": self.store_name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "business_events": self.business_events,
            "customer_contexts": self.customer_contexts,
            "store_contexts": self.store_contexts,
            "free_text": self.free_text,
        }
