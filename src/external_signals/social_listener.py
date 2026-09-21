"""Social Listening connector (chưa triển khai — kiến trúc sẵn sàng, mục XXXIII).

Tương lai: kết nối API mạng xã hội (Facebook Graph API, TikTok, Google Reviews...) để đo lường
sentiment/thảo luận về thương hiệu/đối thủ tại khu vực cửa hàng, làm input bổ sung cho Local Context.
"""
from __future__ import annotations

from src.external_signals import SignalStatus


def get_status() -> SignalStatus:
    return SignalStatus(source_name="Social Listening", connected=False)


def fetch_local_sentiment(store_name: str, latitude: float | None, longitude: float | None) -> None:
    """Placeholder — chưa có API key/kết nối thật. Trả về None thay vì bịa dữ liệu."""
    return None
