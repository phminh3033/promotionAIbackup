"""Giới hạn số job nặng (forecast / basket) chạy song song — tránh OOM khi nhiều user demo."""
from __future__ import annotations

import os
import threading
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")

_MAX = max(1, int(os.getenv("DEMO_MAX_HEAVY_JOBS", "4")))
_SEM = threading.Semaphore(_MAX)
_ACTIVE = 0
_ACTIVE_LOCK = threading.Lock()


def heavy_job_slots() -> int:
    return _MAX


def active_heavy_jobs() -> int:
    with _ACTIVE_LOCK:
        return _ACTIVE


def run_heavy_job(fn: Callable[[], T], *, wait_timeout_sec: float = 180.0) -> tuple[T | None, str | None]:
    """
    Chạy fn trong slot có giới hạn.
    Trả về (result, None) nếu OK; (None, message_vi) nếu không lấy được slot kịp.
    """
    global _ACTIVE
    got = _SEM.acquire(blocking=False)
    if not got:
        got = _SEM.acquire(blocking=True, timeout=wait_timeout_sec)
        if not got:
            return None, (
                f"Hệ thống đang bận ({_MAX} phép tính nặng cùng lúc). "
                "Vui lòng đợi khoảng 1–2 phút rồi thử lại."
            )
    with _ACTIVE_LOCK:
        _ACTIVE += 1
    try:
        return fn(), None
    finally:
        with _ACTIVE_LOCK:
            _ACTIVE = max(0, _ACTIVE - 1)
        _SEM.release()
