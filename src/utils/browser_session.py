"""Lưu / khôi phục phiên trong trình duyệt riêng của từng user.

Chỉ dùng localStorage + sessionStorage + cookies của browser — KHÔNG ghi đĩa/DB
chung trên Railway. Không thay đổi logic/flow nghiệp vụ; chỉ snapshot `st.session_state`.

[ASSUMPTION cho MVP]: Demo dataset lưu cờ `data_ref=demo` (file mẫu công khai trên
server). Upload lớn có thể vượt hạn mức localStorage → thu gọn DataFrame nặng.
"""
from __future__ import annotations

import base64
import logging
import pickle
import zlib
from typing import Any

logger = logging.getLogger(__name__)

STORAGE_KEY = "pp_session_v1"
COOKIE_KEY = "pp_meta"
MAX_BROWSER_BYTES = 3_500_000
# Cookie ~4KB — chỉ giữ cờ nhỏ, không nhét snapshot.
MAX_COOKIE_CHARS = 1200

PERSIST_KEYS: tuple[str, ...] = (
    "raw_df",
    "raw_filename",
    "column_mapping",
    "mapped_df",
    "capabilities",
    "clean_df",
    "quality_report",
    "data_loaded_at",
    "pending_raw_df",
    "pending_filename",
    "pending_mapping",
    "pending_file_token",
    "business_profile",
    "objective",
    "business_events",
    "local_context",
    "bp_form_snapshot",
    "bp_profile_committed",
    "bp_blank_defaults_v1",
    "bp_defaults_restored_v2",
    "demo_access_granted",
    "forecast_cache",
    "forecast_history",
    "rfm_result",
    "segmentation_result",
    "basket_result",
    "historical_uplifts",
    "inventory_plan",
    "last_scenario_table",
    "last_scenario_baseline",
    "last_scenario_meta",
    "last_rule_context",
    "last_rule_verdicts",
    "last_recommendation_card",
    "last_campaign_plan",
    "last_execution_plan",
    "selected_mechanic",
    "recommended_mechanic",
    "execute_campaign",
    "execute_tasks",
    "execute_checklist",
    "active_campaign_id",
    "campaign_records",
    "campaign_actual_data",
    "prepare_draft",
    "prepare_params",
    "decision_tradeoffs",
    "decision_objective_label",
    "_decision_for",
    "prep_lead",
    "prep_lead_fmt",
    "prep_safety",
    "prep_safety_fmt",
    "prep_budget",
    "prep_budget_fmt",
    "prep_margin",
    "prep_margin_fmt",
    "prep_autofill_fp",
    "prep_autofilled_from_bp",
    "prep_fields_initialized",
    "prep_search",
    "prep_cat",
    "params_authority",
    "sim_budget",
    "sim_budget_fmt",
    "sim_gift",
    "sim_gift_fmt",
    "sim_max_disc",
    "sim_min_margin",
    "sim_scope",
    "sim_cat",
    "sim_sku",
    "sim_period",
    "ui_control_drafts",
    "fc_scope",
    "fc_horizon",
    "fc_cat",
    "fc_sku",
    "fc_param_fingerprint",
    "lc_store",
    "lc_events",
    "lc_customers",
    "lc_stores",
    "lc_note",
    "bp_objective",
)

_HEAVY_DATA_KEYS = ("raw_df", "mapped_df", "clean_df", "pending_raw_df")
_DEMO_FILENAMES = frozenset({"pharmacity_demo.csv"})


def _is_pickleable(value: Any) -> bool:
    try:
        pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
        return True
    except Exception:  # noqa: BLE001
        return False


def build_snapshot(session: dict[str, Any]) -> dict[str, Any]:
    state: dict[str, Any] = {}
    skipped: list[str] = []
    for key in PERSIST_KEYS:
        if key not in session:
            continue
        value = session[key]
        if _is_pickleable(value):
            state[key] = value
        else:
            skipped.append(key)
    if skipped:
        logger.warning("Bỏ qua khóa không pickle được: %s", ", ".join(skipped))

    filename = str(session.get("raw_filename") or "")
    data_ref = None
    if filename in _DEMO_FILENAMES and session.get("clean_df") is not None:
        data_ref = "demo"
        for heavy in _HEAVY_DATA_KEYS:
            state.pop(heavy, None)

    return {
        "version": 3,
        "backend": "browser_only",
        "data_ref": data_ref,
        "state": state,
    }


def apply_snapshot(snapshot: dict[str, Any], session: dict[str, Any]) -> None:
    state = dict(snapshot.get("state") or {})
    if snapshot.get("data_ref") == "demo":
        try:
            from services.workflow import _demo_bundle

            bundle = _demo_bundle()
            state["raw_df"] = bundle["raw_df"]
            state["mapped_df"] = bundle["mapped_df"]
            state["clean_df"] = bundle["clean_df"]
            state.setdefault("raw_filename", bundle["filename"])
            state.setdefault("column_mapping", bundle["mapping"])
            state.setdefault("capabilities", bundle["caps"])
            state.setdefault("quality_report", bundle["report"])
        except Exception as exc:  # noqa: BLE001
            logger.warning("Không nạp demo bundle khi hydrate: %s", exc)
    session.update(state)


def encode_snapshot(snapshot: dict[str, Any]) -> str:
    raw = pickle.dumps(snapshot, protocol=pickle.HIGHEST_PROTOCOL)
    return base64.b64encode(zlib.compress(raw, level=6)).decode("ascii")


def decode_snapshot(blob: str) -> dict[str, Any] | None:
    try:
        data = pickle.loads(zlib.decompress(base64.b64decode(blob.encode("ascii"))))
        if not isinstance(data, dict) or "state" not in data:
            return None
        return data
    except Exception as exc:  # noqa: BLE001
        logger.warning("Không giải mã snapshot browser: %s", exc)
        return None


def build_cookie_meta(session: dict[str, Any]) -> str:
    """Cờ nhỏ cho cookie (không chứa DataFrame / kết quả mô hình)."""
    granted = "1" if session.get("demo_access_granted") else "0"
    has_data = "1" if session.get("clean_df") is not None else "0"
    objective = str(session.get("objective") or "REVENUE")[:32]
    meta = f"v3|a={granted}|d={has_data}|o={objective}"
    return meta[:MAX_COOKIE_CHARS]


def parse_cookie_meta(raw: str | None) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if not raw or not isinstance(raw, str):
        return out
    for part in raw.split("|"):
        if part.startswith("a="):
            out["demo_access_granted"] = part[2:] == "1"
        elif part.startswith("o=") and part[2:]:
            out["objective"] = part[2:]
    return out


def _shrink_for_browser_quota(snapshot: dict[str, Any]) -> dict[str, Any]:
    if len(encode_snapshot(snapshot).encode("ascii")) <= MAX_BROWSER_BYTES:
        return snapshot
    slim = {
        "version": snapshot.get("version", 3),
        "backend": "browser_only",
        "data_ref": snapshot.get("data_ref"),
        "state": dict(snapshot.get("state") or {}),
        "quota_shrunk": True,
    }
    for heavy in _HEAVY_DATA_KEYS:
        slim["state"].pop(heavy, None)
    for key in ("forecast_history", "pending_raw_df"):
        slim["state"].pop(key, None)
    if len(encode_snapshot(slim).encode("ascii")) <= MAX_BROWSER_BYTES:
        return slim
    slim["state"].pop("forecast_cache", None)
    return slim


def mark_session_dirty() -> None:
    import streamlit as st

    st.session_state["_session_dirty"] = True


def hydrate_session_state() -> bool | None:
    """Nạp từ browser storage. None = đang chờ JS; True/False = đã xử lý."""
    import streamlit as st

    if st.session_state.get("_workspace_hydrated"):
        return bool(st.session_state.get("_workspace_restored"))

    from ui.browser_storage import browser_storage_get

    result = browser_storage_get(
        STORAGE_KEY,
        cookie_key=COOKIE_KEY,
        nonce=0,
        component_key="pp_bs_hydrate",
    )
    if not isinstance(result, dict) or result.get("status") != "ready":
        return None

    st.session_state["_workspace_hydrated"] = True
    blob = result.get("value")
    cookie_meta = parse_cookie_meta(result.get("cookie") if isinstance(result.get("cookie"), str) else None)

    if blob and isinstance(blob, str):
        snapshot = decode_snapshot(blob)
        if snapshot:
            apply_snapshot(snapshot, st.session_state)  # type: ignore[arg-type]
            try:
                from src.learning.campaign_log import SESSION_KEY, normalize_campaign_records_map

                st.session_state[SESSION_KEY] = normalize_campaign_records_map(
                    st.session_state.get(SESSION_KEY)
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Không chuẩn hoá campaign_records: %s", exc)
            drafts = st.session_state.get("ui_control_drafts") or {}
            if isinstance(drafts, dict):
                for key, value in drafts.items():
                    if key not in st.session_state:
                        st.session_state[key] = value
            st.session_state["_workspace_restored"] = True
            st.session_state["_session_dirty"] = False
            logger.info("Đã hydrate từ browser storage (localStorage/sessionStorage).")
            return True

    # Không có snapshot đầy đủ — chỉ khôi phục cờ nhỏ từ cookie (không đụng logic nghiệp vụ).
    if cookie_meta.get("demo_access_granted"):
        st.session_state["demo_access_granted"] = True

    st.session_state["_workspace_restored"] = False
    st.session_state["_session_dirty"] = False
    logger.info("Browser storage trống — phiên mới (không dùng DB chung Railway).")
    return False


def persist_session_to_browser(*, force: bool = False) -> bool:
    """Ghi snapshot vào localStorage + sessionStorage + cookie meta (browser hiện tại)."""
    import streamlit as st

    if not force and not st.session_state.get("_session_dirty"):
        return False
    if not st.session_state.get("_workspace_hydrated"):
        return False

    session_map = {key: st.session_state[key] for key in PERSIST_KEYS if key in st.session_state}
    try:
        snapshot = build_snapshot(session_map)
        if snapshot.get("data_ref") == "demo":
            for key in ("raw_filename", "column_mapping", "capabilities", "quality_report", "data_loaded_at"):
                if key in st.session_state and _is_pickleable(st.session_state[key]):
                    snapshot["state"][key] = st.session_state[key]
        snapshot = _shrink_for_browser_quota(snapshot)
        blob = encode_snapshot(snapshot)
        if len(blob.encode("ascii")) > MAX_BROWSER_BYTES:
            logger.error("Snapshot vượt hạn mức browser storage — bỏ qua ghi.")
            st.session_state["_session_dirty"] = False
            return False

        cookie_value = build_cookie_meta(session_map)
        from ui.browser_storage import browser_storage_set

        nonce = int(st.session_state.get("_bs_save_nonce") or 0) + 1
        st.session_state["_bs_save_nonce"] = nonce
        browser_storage_set(
            STORAGE_KEY,
            blob,
            cookie_key=COOKIE_KEY,
            cookie_value=cookie_value,
            nonce=nonce,
            component_key="pp_bs_persist",
        )
        st.session_state["_session_dirty"] = False
        logger.info("Đã lưu phiên vào browser storage (%s KB).", round(len(blob) / 1024, 1))
        return True
    except Exception as exc:  # noqa: BLE001
        logger.exception("Lỗi lưu browser storage: %s", exc)
        return False
