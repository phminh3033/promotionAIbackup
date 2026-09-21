"""Webhook receiver cho sự kiện bán hàng thời gian thực (Level 3, chưa triển khai — mục XXXIV)."""
from __future__ import annotations

from src.integrations import IntegrationStatus


def get_status() -> IntegrationStatus:
    return IntegrationStatus(integration_name="Webhook (Realtime Sales Event)", level=3)


def handle_incoming_webhook(payload: dict) -> None:
    """Placeholder — chưa có endpoint webhook thật được triển khai."""
    raise NotImplementedError("Webhook receiver chưa được triển khai trong MVP.")
