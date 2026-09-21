"""Local Events connector (chưa triển khai — kiến trúc sẵn sàng, mục XXXIII).

Tương lai: kết nối nguồn sự kiện địa phương (lịch lễ hội, sự kiện thành phố...) để tự động gợi ý
vào Local Context thay vì người dùng phải tự nhớ nhập ("Sự kiện địa phương").
"""
from __future__ import annotations

from src.external_signals import SignalStatus


def get_status() -> SignalStatus:
    return SignalStatus(source_name="Sự kiện địa phương (Events)", connected=False)


def fetch_upcoming_events(latitude: float | None, longitude: float | None, days: int = 14) -> None:
    """Placeholder — chưa có nguồn dữ liệu thật. Trả về None thay vì bịa dữ liệu."""
    return None
