"""Streamlit component: localStorage + sessionStorage + cookie của trình duyệt hiện tại."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit.components.v1 as components

_COMPONENT_DIR = Path(__file__).resolve().parent
_browser_storage = components.declare_component(
    "pp_browser_storage",
    path=str(_COMPONENT_DIR),
)


def browser_storage_get(
    storage_key: str,
    *,
    cookie_key: str = "pp_meta",
    nonce: int = 0,
    component_key: str = "pp_bs_get",
) -> Any:
    return _browser_storage(
        mode="get",
        storage_key=storage_key,
        cookie_key=cookie_key,
        nonce=int(nonce),
        default=None,
        key=component_key,
    )


def browser_storage_set(
    storage_key: str,
    value: str,
    *,
    cookie_key: str = "pp_meta",
    cookie_value: str | None = None,
    cookie_max_age: int = 31536000,
    nonce: int = 0,
    component_key: str = "pp_bs_set",
) -> Any:
    return _browser_storage(
        mode="set",
        storage_key=storage_key,
        value=value,
        cookie_key=cookie_key,
        cookie_value=cookie_value,
        cookie_max_age=int(cookie_max_age),
        nonce=int(nonce),
        default=None,
        key=component_key,
    )


def browser_storage_clear(
    storage_key: str,
    *,
    cookie_key: str = "pp_meta",
    nonce: int = 0,
    component_key: str = "pp_bs_clear",
) -> Any:
    return _browser_storage(
        mode="clear",
        storage_key=storage_key,
        cookie_key=cookie_key,
        nonce=int(nonce),
        default=None,
        key=component_key,
    )
