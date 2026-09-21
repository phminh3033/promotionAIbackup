"""External Signals (mục XXXIII spec PromotionPilot AI).

Kiến trúc sẵn sàng để tích hợp các nguồn dữ liệu bên ngoài (social listening, thời tiết, đối thủ,
Google Trends, sự kiện địa phương) trong tương lai. MVP KHÔNG fake dữ liệu — mỗi module trả về
trạng thái "Chưa kết nối" rõ ràng thay vì số liệu giả, đúng nguyên tắc "không claim dữ liệu không
có thật" xuyên suốt hệ thống.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SignalStatus:
    source_name: str
    connected: bool = False
    message: str = "Chưa kết nối nguồn dữ liệu ngoài."
    data: dict | None = None
