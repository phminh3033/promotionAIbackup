"""POS API polling connector (Level 2, chưa triển khai — mục XXXIV)."""
from __future__ import annotations

from src.integrations import IntegrationStatus


def get_status() -> IntegrationStatus:
    return IntegrationStatus(integration_name="POS API Polling", level=2)


def poll_latest_transactions(store_id: str, since_timestamp: str | None = None) -> None:
    """Placeholder — chưa kết nối POS thật. Trả về None thay vì bịa dữ liệu giao dịch."""
    return None
