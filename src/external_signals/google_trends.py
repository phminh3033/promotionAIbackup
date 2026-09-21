"""Google Trends connector (chưa triển khai — kiến trúc sẵn sàng, mục XXXIII).

Tương lai: dùng pytrends hoặc Google Trends API để đo mức độ quan tâm tìm kiếm theo từ khoá sản
phẩm/danh mục theo khu vực, làm tín hiệu bổ sung cho forecast demand.
"""
from __future__ import annotations

from src.external_signals import SignalStatus


def get_status() -> SignalStatus:
    return SignalStatus(source_name="Google Trends", connected=False)


def fetch_trend_score(keyword: str, region: str = "VN") -> None:
    """Placeholder — chưa có kết nối thật. Trả về None thay vì bịa dữ liệu."""
    return None
