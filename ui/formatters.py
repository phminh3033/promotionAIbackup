"""Định dạng hiển thị. Không tính lại công thức nghiệp vụ."""
from __future__ import annotations

import math
import re
from datetime import datetime


def _finite(value) -> bool:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(number)


def vnd(value) -> str:
    if not _finite(value):
        return "—"
    formatted = f"{float(value):,.0f}".replace(",", ".")
    return f"{formatted} đ"


def compact_vnd(value) -> str:
    if not _finite(value):
        return "—"
    number = float(value)
    sign = "-" if number < 0 else ""
    number = abs(number)
    if number >= 1_000_000_000:
        return f"{sign}{number / 1_000_000_000:.2f} tỷ đ"
    if number >= 1_000_000:
        return f"{sign}{number / 1_000_000:.1f} triệu đ"
    return vnd(number if sign == "" else -number)


def integer(value) -> str:
    if not _finite(value):
        return "—"
    return f"{float(value):,.0f}".replace(",", ".")


def integer_comma(value) -> str:
    """Số nguyên với dấu phẩy phân tách hàng nghìn (vd: 43,489)."""
    if not _finite(value):
        return "—"
    return f"{float(value):,.0f}"


def format_int_commas(value, *, default: int = 0) -> str:
    """Chuỗi số nguyên có dấu phẩy — dùng cho ô nhập liệu."""
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        number = default
    return f"{number:,}"


def parse_int_commas(text, *, default: int = 0, minimum: int | None = None) -> int:
    """Parse chuỗi có dấu phẩy/ký tự thừa → số nguyên."""
    cleaned = str(text or "").strip().replace(",", "").replace(" ", "")
    if re.fullmatch(r"\d+\.\d+", cleaned):
        # vd: 8.00 / 8.5 → lấy phần nguyên (không gộp thành 800)
        value = int(float(cleaned))
    else:
        digits = "".join(ch for ch in cleaned if ch.isdigit())
        value = int(digits) if digits else default
    if minimum is not None:
        value = max(minimum, value)
    return value


def pct(value, digits: int = 1) -> str:
    if not _finite(value):
        return "—"
    return f"{float(value):.{digits}%}"


def signed_pct(value, digits: int = 1) -> str:
    if not _finite(value):
        return "—"
    number = float(value)
    sign = "+" if number > 0 else ""
    return f"{sign}{number:.{digits}%}"


def roi_label(value) -> str:
    """ROI theo đúng định nghĩa calculator: (LN gộp tăng thêm) / chi phí KM."""
    if not _finite(value):
        return "—"
    return f"{float(value):.0%}"


def delta_class(value) -> str:
    if not _finite(value) or abs(float(value)) < 1e-9:
        return "flat"
    return "up" if float(value) > 0 else "down"


def relative_time(stamp: datetime | None) -> str:
    if stamp is None:
        return "Chưa cập nhật"
    seconds = (datetime.now() - stamp).total_seconds()
    if seconds < 60:
        return "Vừa xong"
    if seconds < 3600:
        return f"{int(seconds // 60)} phút trước"
    if seconds < 86400:
        return f"{int(seconds // 3600)} giờ trước"
    return stamp.strftime("%d/%m/%Y %H:%M")


def sparkline(values: list[float], color: str = "#2563EB") -> str:
    clean = [float(v) for v in values if _finite(v)]
    if len(clean) < 2:
        return ""
    low, high = min(clean), max(clean)
    span = high - low or 1.0
    width, height = 88, 32
    points = []
    last = len(clean) - 1
    for index, value in enumerate(clean):
        x = 2 + (index / last) * (width - 4)
        y = height - 3 - ((value - low) / span) * (height - 8)
        points.append(f"{x:.1f},{y:.1f}")
    return (
        f'<svg class="pp-spark" viewBox="0 0 {width} {height}" aria-hidden="true">'
        f'<polyline fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" '
        f'stroke-linejoin="round" points="{" ".join(points)}"/></svg>'
    )
