"""Enterprise Event Bus consumer (Level 4, chưa triển khai — mục XXXIV)."""
from __future__ import annotations

from src.integrations import IntegrationStatus


def get_status() -> IntegrationStatus:
    return IntegrationStatus(integration_name="Enterprise Event Bus (Kafka/RabbitMQ...)", level=4)


def consume_events(topic: str) -> None:
    """Placeholder — chưa kết nối event bus thật."""
    raise NotImplementedError("Event stream consumer chưa được triển khai trong MVP.")
