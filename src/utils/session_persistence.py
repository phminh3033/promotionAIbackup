"""Lưu / khôi phục phiên làm việc TRONG TRÌNH DUYỆT của từng user (localStorage).

Nguyên tắc (bắt buộc trên Railway / multi-user):
- KHÔNG ghi snapshot vào đĩa/server chung (`config/session_workspace`, DB…).
- Mỗi trình duyệt chỉ đọc/ghi localStorage của chính nó → user mới không thấy data người khác.
- F5 trong cùng trình duyệt vẫn khôi phục được phiên (st.session_state mất khi reload WebSocket).

[ASSUMPTION cho MVP]: Demo dataset chỉ lưu cờ `data_ref=demo` (nạp lại từ file demo trên
server — đây là dữ liệu mẫu công khai, không phải data riêng của user). File upload lớn có thể
vượt hạn mức localStorage (~5MB) → bỏ DataFrame nặng, user phải tải lại file sau F5.
"""
from __future__ import annotations

import base64
import logging
import pickle
import zlib
from typing import Any

logger = logging.getLogger(__name__)

STORAGE_KEY = "pp_session_v1"
# Giới hạn an toàn dưới hạn mức localStorage phổ biến (~5MB).
MAX_BROWSER_BYTES = 3_500_000

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
    """Tạo dict có thể pickle từ mapping giống session_state."""
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
        logger.warning("Bỏ qua khóa không pickle được khi lưu phiên: %s", ", ".join(skipped))

    filename = str(session.get("raw_filename") or "")
    data_ref = None
    if filename in _DEMO_FILENAMES and session.get("clean_df") is not None:
        data_ref = "demo"
        for heavy in _HEAVY_DATA_KEYS:
            state.pop(heavy, None)

    return {
        "version": 2,
        "backend": "browser_localStorage",
        "data_ref": data_ref,
        "state": state,
    }


def apply_snapshot(snapshot: dict[str, Any], session: dict[str, Any]) -> None:
    """Ghi snapshot vào mapping session (in-place)."""
    state = dict(snapshot.get("state") or {})
    data_ref = snapshot.get("data_ref")
    if data_ref == "demo":
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
            logger.warning("Không nạp lại demo bundle khi hydrate: %s", exc)
    session.update(state)


def encode_snapshot(snapshot: dict[str, Any]) -> str:
    """pickle + zlib + base64 để đưa vào localStorage."""
    raw = pickle.dumps(snapshot, protocol=pickle.HIGHEST_PROTOCOL)
    compressed = zlib.compress(raw, level=6)
    return base64.b64encode(compressed).decode("ascii")


def decode_snapshot(blob: str) -> dict[str, Any] | None:
    try:
        raw = zlib.decompress(base64.b64decode(blob.encode("ascii")))
        data = pickle.loads(raw)
        if not isinstance(data, dict) or "state" not in data:
            return None
        return data
    except Exception as exc:  # noqa: BLE001
        logger.warning("Không giải mã snapshot localStorage: %s", exc)
        return None


def _shrink_for_browser_quota(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Nếu quá lớn, bỏ DataFrame nặng / cache dự báo để vẫn lưu được phần còn lại."""
    encoded = encode_snapshot(snapshot)
    if len(encoded.encode("ascii")) <= MAX_BROWSER_BYTES:
        return snapshot

    slim = {
        "version": snapshot.get("version", 2),
        "backend": "browser_localStorage",
        "data_ref": snapshot.get("data_ref"),
        "state": dict(snapshot.get("state") or {}),
        "quota_shrunk": True,
    }
    for heavy in _HEAVY_DATA_KEYS:
        slim["state"].pop(heavy, None)
    # forecast_history / cache có thể rất lớn
    for key in ("forecast_history", "pending_raw_df"):
        slim["state"].pop(key, None)

    encoded = encode_snapshot(slim)
    if len(encoded.encode("ascii")) <= MAX_BROWSER_BYTES:
        logger.warning("Snapshot localStorage đã thu gọn (bỏ DataFrame/history) do vượt hạn mức.")
        return slim

    # Thu gọn thêm: bỏ forecast_cache
    slim["state"].pop("forecast_cache", None)
    logger.warning("Snapshot localStorage thu gọn thêm (bỏ forecast_cache).")
    return slim


def mark_session_dirty() -> None:
    import streamlit as st

    st.session_state["_session_dirty"] = True


def hydrate_session_state() -> bool | None:
    """Nạp snapshot từ localStorage trình duyệt hiện tại.

    Returns:
        True  — đã hydrate có dữ liệu
        False — localStorage trống / không có snapshot
        None  — đang chờ component JS đọc xong (caller nên st.stop() hoặc đợi rerun)
    """
    import streamlit as st

    if st.session_state.get("_workspace_hydrated"):
        return bool(st.session_state.get("_workspace_restored"))

    from ui.browser_storage import browser_storage_get

    result = browser_storage_get(STORAGE_KEY, nonce=0, component_key="pp_ls_hydrate")
    if not isinstance(result, dict) or result.get("status") != "ready":
        # Frame đầu: JS chưa trả về — chưa đánh dấu hydrated.
        return None

    st.session_state["_workspace_hydrated"] = True
    blob = result.get("value")
    if not blob or not isinstance(blob, str):
        st.session_state["_workspace_restored"] = False
        logger.info("localStorage trống — phiên mới (không dùng dữ liệu server chung).")
        return False

    snapshot = decode_snapshot(blob)
    if not snapshot:
        st.session_state["_workspace_restored"] = False
        return False

    apply_snapshot(snapshot, st.session_state)  # type: ignore[arg-type]
    try:
        from src.learning.campaign_log import SESSION_KEY, normalize_campaign_records_map

        st.session_state[SESSION_KEY] = normalize_campaign_records_map(
            st.session_state.get(SESSION_KEY)
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Không chuẩn hoá campaign_records khi hydrate: %s", exc)

    drafts = st.session_state.get("ui_control_drafts") or {}
    if isinstance(drafts, dict):
        for key, value in drafts.items():
            if key not in st.session_state:
                st.session_state[key] = value

    st.session_state["_workspace_restored"] = True
    st.session_state["_session_dirty"] = False
    logger.info(
        "Đã hydrate từ localStorage (clean_df=%s, forecast=%s)",
        st.session_state.get("clean_df") is not None,
        bool(st.session_state.get("forecast_cache")),
    )
    return True


def persist_session_to_browser(*, force: bool = False) -> bool:
    """Ghi session hiện tại vào localStorage của trình duyệt hiện tại (không ghi server)."""
    import streamlit as st

    if not force and not st.session_state.get("_session_dirty"):
        return False
    # Chưa hydrate xong thì chưa ghi (tránh ghi đè snapshot cũ bằng state mặc định trống).
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
            logger.error("Snapshot vẫn vượt hạn mức localStorage sau khi thu gọn — bỏ qua ghi.")
            st.session_state["_session_dirty"] = False
            return False

        from ui.browser_storage import browser_storage_set

        nonce = int(st.session_state.get("_ls_save_nonce") or 0) + 1
        st.session_state["_ls_save_nonce"] = nonce
        browser_storage_set(STORAGE_KEY, blob, nonce=nonce, component_key="pp_ls_persist")
        st.session_state["_session_dirty"] = False
        logger.info("Đã lưu phiên vào localStorage trình duyệt (%s KB).", round(len(blob) / 1024, 1))
        return True
    except Exception as exc:  # noqa: BLE001
        logger.exception("Lỗi lưu phiên vào localStorage: %s", exc)
        return False


# Alias giữ tương thích call-site cũ (workflow/state) — KHÔNG ghi đĩa nữa.
def persist_session_to_disk(*, force: bool = False) -> bool:
    return persist_session_to_browser(force=force)


def clear_browser_session() -> None:
    """Xoá snapshot trong localStorage (khi user muốn bắt đầu lại)."""
    import streamlit as st
    from ui.browser_storage import browser_storage_clear

    nonce = int(st.session_state.get("_ls_clear_nonce") or 0) + 1
    st.session_state["_ls_clear_nonce"] = nonce
    browser_storage_clear(STORAGE_KEY, nonce=nonce, component_key="pp_ls_clear")


def purge_legacy_shared_workspace() -> None:
    """Xoá snapshot đĩa chung cũ (config/session_workspace/*.pkl) — không còn dùng.

    Tránh user mới vô tình bị ảnh hưởng nếu code cũ / file còn sót trên Railway.
    Chỉ chạy một lần mỗi process.
    """
    import streamlit as st
    from pathlib import Path

    if st.session_state.get("_legacy_workspace_purged"):
        return
    st.session_state["_legacy_workspace_purged"] = True
    legacy = Path(__file__).resolve().parent.parent.parent / "config" / "session_workspace"
    if not legacy.exists():
        return
    removed = 0
    for path in legacy.glob("*.pkl"):
        try:
            path.unlink()
            removed += 1
        except Exception as exc:  # noqa: BLE001
            logger.warning("Không xoá được snapshot đĩa cũ %s: %s", path, exc)
    for path in legacy.glob("*.tmp"):
        try:
            path.unlink()
        except Exception:  # noqa: BLE001
            pass
    if removed:
        logger.info("Đã xoá %s file snapshot đĩa chung cũ tại %s", removed, legacy)
