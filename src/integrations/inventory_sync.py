"""Đồng bộ tồn kho tự động với hệ thống kho/ERP (Level 2-3, chưa triển khai — mục XXXIV)."""
from __future__ import annotations

from src.integrations import IntegrationStatus


def get_status() -> IntegrationStatus:
    return IntegrationStatus(integration_name="Inventory Sync", level=2)


def sync_inventory(store_id: str) -> None:
    """Placeholder — hiện tại tồn kho lấy từ cột Inventory_Onhand trong file upload."""
    return None
