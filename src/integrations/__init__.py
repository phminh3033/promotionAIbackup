"""Realtime / POS Integrations (mục XXXIV spec PromotionPilot AI).

MVP chỉ hỗ trợ upload Excel/CSV thủ công (Level 1). Các module trong package này là kiến trúc
sẵn sàng cho Level 2-4 (xem README.md phần Deployment/Architecture Roadmap), CHƯA kết nối hệ thống
POS/ERP thật nào — không fake dữ liệu.

Level 1: Excel/CSV upload (đã có, đang dùng).
Level 2: POS API polling định kỳ.
Level 3: Webhook (POS đẩy sự kiện bán hàng theo thời gian thực).
Level 4: Enterprise Event Bus (Kafka/RabbitMQ...) cho hệ thống nhiều cửa hàng/nhiều nguồn.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class IntegrationStatus:
    integration_name: str
    level: int
    connected: bool = False
    message: str = "Chưa kết nối — hiện chỉ hỗ trợ upload Excel/CSV thủ công (Level 1)."
