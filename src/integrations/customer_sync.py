"""Đồng bộ dữ liệu khách hàng tự động với CRM/loyalty system (Level 2-3, chưa triển khai — mục XXXIV)."""
from __future__ import annotations

from src.integrations import IntegrationStatus


def get_status() -> IntegrationStatus:
    return IntegrationStatus(integration_name="Customer Sync (CRM/Loyalty)", level=2)


def sync_customers(store_id: str) -> None:
    """Placeholder — hiện tại dữ liệu khách hàng lấy từ cột CustomerID trong file upload."""
    return None
