"""Competitor Price connector (chưa triển khai — kiến trúc sẵn sàng, mục XXXIII).

Tương lai: crawl/API giá đối thủ theo SKU tương đương để đưa vào Promotion Simulator như một ràng
buộc/tín hiệu bổ sung (hiện tại doanh nghiệp nhập thủ công qua Local Context: "Đối thủ giảm giá").
"""
from __future__ import annotations

from src.external_signals import SignalStatus


def get_status() -> SignalStatus:
    return SignalStatus(source_name="Giá đối thủ (Competitor)", connected=False)


def fetch_competitor_prices(sku_ids: list[str]) -> None:
    """Placeholder — chưa có nguồn dữ liệu thật. Trả về None thay vì bịa dữ liệu."""
    return None
