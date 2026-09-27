"""Streamlit custom component: đọc/ghi localStorage của trình duyệt hiện tại."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit.components.v1 as components

_COMPONENT_DIR = Path(__file__).resolve().parent
_browser_storage = components.declare_component(
    "pp_browser_storage",
    path=str(_COMPONENT_DIR),
)


def browser_storage_get(storage_key: str, *, nonce: int = 0, component_key: str = "pp_ls_get") -> Any:
    """Đọc localStorage. Trả về dict {status, value} khi JS sẵn sàng; None ở frame đầu."""
    return _browser_storage(
        mode="get",
        storage_key=storage_key,
        nonce=int(nonce),
        default=None,
        key=component_key,
    )


def browser_storage_set(
    storage_key: str,
    value: str,
    *,
    nonce: int = 0,
    component_key: str = "pp_ls_set",
) -> Any:
    """Ghi localStorage. value = chuỗi đã encode (base64)."""
    return _browser_storage(
        mode="set",
        storage_key=storage_key,
        value=value,
        nonce=int(nonce),
        default=None,
        key=component_key,
    )


def browser_storage_clear(storage_key: str, *, nonce: int = 0, component_key: str = "pp_ls_clear") -> Any:
    return _browser_storage(
        mode="clear",
        storage_key=storage_key,
        nonce=int(nonce),
        default=None,
        key=component_key,
    )
