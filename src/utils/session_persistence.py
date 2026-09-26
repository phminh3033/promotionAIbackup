"""Lưu / khôi phục phiên làm việc lên đĩa để sống sót qua reload trình duyệt.

Streamlit `st.session_state` gắn với WebSocket — F5 / reload tạo phiên mới và mất hết
trạng thái trong RAM. Module này ghi snapshot xuống `config/session_workspace/` và
nạp lại khi phiên mới khởi tạo.

[ASSUMPTION cho MVP]: Định danh workspace bằng cookie + query param `wid` (không dùng
DB multi-tenant). Demo dataset không pickle nguyên DataFrame — chỉ lưu cờ `data_ref=demo`
rồi nạp lại từ `_demo_bundle()` để tránh file hàng trăm MB.
"""
from __future__ import annotations

import pickle
import re
import tempfile
import uuid
from pathlib import Path
from typing import Any

WORKSPACE_DIR = Path(__file__).resolve().parent.parent.parent / "config" / "session_workspace"
COOKIE_NAME = "pp_wid"
QUERY_PARAM = "wid"
_SAFE_ID = re.compile(r"^[a-zA-Z0-9_-]{8,64}$")

# Khóa cần giữ qua reload (dữ liệu, input, kết quả mô hình). Không gồm khóa nội bộ Streamlit.
PERSIST_KEYS: tuple[str, ...] = (
    # Dữ liệu đã nạp
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
    # Hồ sơ / bối cảnh / mục tiêu
    "business_profile",
    "objective",
    "business_events",
    "local_context",
    "bp_form_snapshot",
    "bp_profile_committed",
    "bp_blank_defaults_v1",
    "bp_defaults_restored_v2",
    "demo_access_granted",
    # Kết quả phân tích / dự báo / mô phỏng
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
    # Tham số Prepare / Simulate đã nhập
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
    # Điều khiển UI các trang
    "ui_control_drafts",
    "fc_scope",
    "fc_horizon",
    "fc_cat",
    "fc_sku",
    "fc_param_fingerprint",
    # Local context widgets
    "lc_store",
    "lc_events",
    "lc_customers",
    "lc_stores",
    "lc_note",
    # Snapshot form hồ sơ (dialog có thể đóng)
    "bp_objective",
)

# Cột DataFrame nặng — với demo chỉ lưu tham chiếu, không pickle.
_HEAVY_DATA_KEYS = ("raw_df", "mapped_df", "clean_df", "pending_raw_df")
_DEMO_FILENAMES = frozenset({"pharmacity_demo.csv"})


def ensure_workspace_dir() -> Path:
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    return WORKSPACE_DIR


def sanitize_workspace_id(raw: str | None) -> str | None:
    if not raw:
        return None
    text = str(raw).strip()
    if _SAFE_ID.match(text):
        return text
    return None


def workspace_path(workspace_id: str) -> Path:
    safe = sanitize_workspace_id(workspace_id) or "default"
    return ensure_workspace_dir() / f"{safe}.pkl"


def build_snapshot(session: dict[str, Any]) -> dict[str, Any]:
    """Tạo dict có thể pickle từ mapping giống session_state (không phụ thuộc Streamlit)."""
    state: dict[str, Any] = {}
    for key in PERSIST_KEYS:
        if key in session:
            state[key] = session[key]

    filename = str(session.get("raw_filename") or "")
    data_ref = None
    if filename in _DEMO_FILENAMES and session.get("clean_df") is not None:
        data_ref = "demo"
        for heavy in _HEAVY_DATA_KEYS:
            state.pop(heavy, None)

    return {
        "version": 1,
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
        except Exception:  # noqa: BLE001 — không chặn app nếu demo file thiếu
            pass
    session.update(state)


def save_snapshot(workspace_id: str, snapshot: dict[str, Any]) -> Path:
    path = workspace_path(workspace_id)
    ensure_workspace_dir()
    # Ghi atomic để tránh file hỏng nếu process bị kill giữa chừng.
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    tmp_path = Path(tmp_name)
    try:
        with open(fd, "wb") as fh:
            pickle.dump(snapshot, fh, protocol=pickle.HIGHEST_PROTOCOL)
        tmp_path.replace(path)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise
    return path


def load_snapshot(workspace_id: str) -> dict[str, Any] | None:
    path = workspace_path(workspace_id)
    if not path.exists():
        return None
    try:
        with path.open("rb") as fh:
            data = pickle.load(fh)
        if not isinstance(data, dict) or "state" not in data:
            return None
        return data
    except Exception:  # noqa: BLE001 — file hỏng / phiên bản cũ → bỏ qua
        return None


def new_workspace_id() -> str:
    return uuid.uuid4().hex[:16]


# ── Streamlit glue ──────────────────────────────────────────────────────────


def resolve_workspace_id() -> str:
    """Lấy id workspace từ query param → cookie → tạo mới."""
    import streamlit as st

    existing = sanitize_workspace_id(st.session_state.get("_workspace_id"))
    if existing:
        return existing

    qp = None
    try:
        qp = sanitize_workspace_id(st.query_params.get(QUERY_PARAM))
    except Exception:  # noqa: BLE001
        qp = None
    if qp:
        st.session_state["_workspace_id"] = qp
        return qp

    cookie = None
    try:
        cookies = st.context.cookies
        if cookies is not None:
            cookie = sanitize_workspace_id(cookies.get(COOKIE_NAME))
    except Exception:  # noqa: BLE001
        cookie = None
    if cookie:
        st.session_state["_workspace_id"] = cookie
        try:
            if st.query_params.get(QUERY_PARAM) != cookie:
                st.query_params[QUERY_PARAM] = cookie
        except Exception:  # noqa: BLE001
            pass
        return cookie

    wid = new_workspace_id()
    st.session_state["_workspace_id"] = wid
    st.session_state["_need_set_wid_cookie"] = True
    try:
        st.query_params[QUERY_PARAM] = wid
    except Exception:  # noqa: BLE001
        pass
    return wid


def mark_session_dirty() -> None:
    import streamlit as st

    st.session_state["_session_dirty"] = True


def hydrate_session_state() -> bool:
    """Nạp snapshot đĩa vào session một lần mỗi phiên Streamlit. True nếu có dữ liệu."""
    import streamlit as st

    if st.session_state.get("_workspace_hydrated"):
        return bool(st.session_state.get("_workspace_restored"))
    st.session_state["_workspace_hydrated"] = True

    wid = resolve_workspace_id()
    snapshot = load_snapshot(wid)
    if not snapshot:
        st.session_state["_workspace_restored"] = False
        return False

    apply_snapshot(snapshot, st.session_state)  # type: ignore[arg-type]
    # Chuẩn hoá kho chiến dịch (dict thuần → CampaignRecord) sau pickle.
    try:
        from src.learning.campaign_log import SESSION_KEY, normalize_campaign_records_map

        st.session_state[SESSION_KEY] = normalize_campaign_records_map(
            st.session_state.get(SESSION_KEY)
        )
    except Exception:  # noqa: BLE001
        pass
    # Khôi phục lựa chọn UI từ bản nháp nếu khóa widget chưa có.
    drafts = st.session_state.get("ui_control_drafts") or {}
    if isinstance(drafts, dict):
        for key, value in drafts.items():
            if key not in st.session_state:
                st.session_state[key] = value
    st.session_state["_workspace_restored"] = True
    st.session_state["_session_dirty"] = False
    return True


def persist_session_to_disk(*, force: bool = False) -> Path | None:
    """Ghi session hiện tại ra đĩa nếu dirty (hoặc force)."""
    import streamlit as st

    if not force and not st.session_state.get("_session_dirty"):
        return None
    wid = resolve_workspace_id()
    # st.session_state hỗ trợ iteration kiểu dict
    session_map = {key: st.session_state[key] for key in PERSIST_KEYS if key in st.session_state}
    snapshot = build_snapshot(session_map)
    # Giữ raw_filename / mapping dù đã bỏ DF demo
    if snapshot.get("data_ref") == "demo":
        for key in ("raw_filename", "column_mapping", "capabilities", "quality_report", "data_loaded_at"):
            if key in st.session_state:
                snapshot["state"][key] = st.session_state[key]
    path = save_snapshot(wid, snapshot)
    st.session_state["_session_dirty"] = False
    return path


def inject_workspace_cookie() -> None:
    """Ghi cookie workspace id vào trình duyệt (một lần sau khi tạo id mới)."""
    import streamlit as st
    import streamlit.components.v1 as components

    wid = st.session_state.get("_workspace_id")
    if not wid or not st.session_state.get("_need_set_wid_cookie"):
        return
    safe = sanitize_workspace_id(str(wid))
    if not safe:
        return
    # max-age ~ 1 năm; SameSite=Lax đủ cho reload cùng site.
    components.html(
        f"""
<script>
(function() {{
  try {{
    document.cookie = "{COOKIE_NAME}={safe}; path=/; max-age=31536000; SameSite=Lax";
  }} catch (e) {{}}
}})();
</script>
""",
        height=0,
        width=0,
    )
    st.session_state["_need_set_wid_cookie"] = False
