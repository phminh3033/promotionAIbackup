"""Snapshot tham số «Thiết lập mô phỏng» sau khi chạy Simulate.

[BUSINESS RULE cho MVP] Execute chỉ lấy thông tin chiến dịch từ snapshot lần chạy
mô phỏng thành công gần nhất (`last_scenario_meta`), không lấy từ widget đang sửa
trên form (tránh lệch khi user đổi ô nhưng chưa chạy lại).
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any


def _as_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    try:
        return datetime.fromisoformat(str(value)[:10]).date()
    except Exception:
        return None


def campaign_window_from_meta(meta: dict | None, *, fallback_days: int = 7) -> tuple[date, date, int]:
    """Trả về (start, end, promo_days) ưu tiên campaign_start/end đã lưu khi chạy mô phỏng."""
    meta = meta or {}
    start = _as_date(meta.get("campaign_start"))
    end = _as_date(meta.get("campaign_end"))
    if start and end:
        if end < start:
            end = start
        days = max(1, (end - start).days + 1)
        return start, end, days

    days = int(meta.get("promo_days") or fallback_days or 7)
    days = max(1, days)
    start = date.today()
    end = start + timedelta(days=days - 1)
    return start, end, days


def budget_from_meta(meta: dict | None, fallback: float = 0.0) -> float:
    meta = meta or {}
    raw = meta.get("budget")
    if raw is None:
        return float(fallback or 0)
    try:
        return float(raw)
    except (TypeError, ValueError):
        return float(fallback or 0)


def scope_label_from_meta(meta: dict | None, store_name: str | None = None) -> str:
    """Nhãn phạm vi hiển thị trên Execute (Theo Danh mục · … / Theo SKU · …)."""
    meta = meta or {}
    scope = meta.get("scope")
    scope_value = meta.get("scope_value") or meta.get("product_focus_label")
    if scope in {"Một Danh mục", "Theo Danh mục"} and scope_value:
        return f"Theo Danh mục · {scope_value}"
    if scope in {"Một SKU cụ thể", "Theo SKU"} and scope_value:
        return f"Theo SKU · {scope_value}"
    if scope == "Toàn công ty":
        return "Toàn công ty"
    if scope and scope_value:
        return f"{scope} · {scope_value}"
    if scope_value:
        return str(scope_value)
    if scope:
        return str(scope)
    if store_name and str(store_name).strip():
        return str(store_name).strip()
    product = meta.get("product_focus_label")
    if product:
        return str(product)
    return "Toàn công ty"


def build_setup_snapshot(
    *,
    scope: str,
    scope_value: str,
    promo_days: int,
    gift_cost: float,
    campaign_start: date,
    campaign_end: date,
    budget: float,
    max_discount_pct: float,
    min_margin_pct: float,
) -> dict:
    """Phần meta gắn với form Thiết lập mô phỏng — lưu khi bấm «Chạy mô phỏng»."""
    start = campaign_start
    end = campaign_end if campaign_end >= campaign_start else campaign_start
    days = max(1, int(promo_days), (end - start).days + 1)
    return {
        "scope": scope,
        "scope_value": scope_value,
        "product_focus_label": scope_value,
        "promo_days": int(days),
        "gift_cost_per_unit": float(gift_cost),
        "campaign_start": start.isoformat(),
        "campaign_end": end.isoformat(),
        "budget": float(budget),
        "max_discount_pct": float(max_discount_pct),
        "min_margin_pct": float(min_margin_pct),
    }
