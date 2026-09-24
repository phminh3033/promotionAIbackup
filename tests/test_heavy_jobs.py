"""Kiểm tra giới hạn job nặng cho buổi demo đồng thời."""
from __future__ import annotations

import threading
import time

from src.utils.heavy_jobs import heavy_job_slots, run_heavy_job


def test_heavy_job_runs():
    result, err = run_heavy_job(lambda: 42)
    assert err is None
    assert result == 42


def test_heavy_job_slots_positive():
    assert heavy_job_slots() >= 1


def test_heavy_job_timeout_message():
    """Khi mọi slot bị giữ, acquire timeout trả về thông báo tiếng Việt."""
    from src.utils import heavy_jobs as hj

    # Giữ hết slot
    held = []
    for _ in range(hj.heavy_job_slots()):
        assert hj._SEM.acquire(blocking=False)
        held.append(True)

    try:
        result, err = run_heavy_job(lambda: 1, wait_timeout_sec=0.2)
        assert result is None
        assert err is not None
        assert "bận" in err.lower() or "Hệ thống" in err
    finally:
        for _ in held:
            hj._SEM.release()
