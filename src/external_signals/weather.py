"""Weather connector (chưa triển khai — kiến trúc sẵn sàng, mục XXXIII).

Tương lai: kết nối API thời tiết (OpenWeatherMap, WeatherAPI...) — thời tiết ảnh hưởng nhu cầu một
số ngành hàng (nước giải khát, thuốc cảm cúm, đồ mưa...).
"""
from __future__ import annotations

from src.external_signals import SignalStatus


def get_status() -> SignalStatus:
    return SignalStatus(source_name="Thời tiết (Weather)", connected=False)


def fetch_forecast_weather(latitude: float | None, longitude: float | None, days: int = 7) -> None:
    """Placeholder — chưa có API key/kết nối thật. Trả về None thay vì bịa dữ liệu."""
    return None
