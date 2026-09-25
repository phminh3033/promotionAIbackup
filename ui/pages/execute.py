"""Execute: Campaign Execution Workspace — UI/presentation only.

Dữ liệu lấy từ Decide / Forecast / Prepare / Simulate / execution plan hiện có.
Không rerun recommendation/simulation/ML. Không hard-code số liệu mockup.
"""
from __future__ import annotations

import io
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

from src.execution.plan import STATUS_LEVELS, TEAMS, generate_execution_plan
from src.learning.campaign_log import CampaignRecord, new_campaign_id, save_campaign_record
from src.recommendation.campaign import generate_campaign_plan, is_llm_enabled
from ui.components import (
    DASH,
    EMPTY,
    campaign_info_card,
    campaign_info_field,
    campaign_readiness_card,
    exec_panel_header,
    muted,
    prelaunch_checklist_card,
    show,
)
from ui.formatters import integer, vnd
from ui.nav import goto
from ui.shell import render_shell

# Chữ viết tắt từ tên phòng ban thật trong TEAMS — không invent person name.
TEAM_INITIALS = {
    "Demand Planning": "DP",
    "Marketing": "MK",
    "ERP / IT": "IT",
    "Supply Chain": "SC",
    "Retail / Store": "RT",
    "HR": "HR",
    "PSD / Trading": "TD",
}

CHECKLIST_VISIBLE = 6
# Chiều cao cố định 2 card hàng trên — task list scroll bên trong.
EXEC_TOP_CARD_HEIGHT = 540


@dataclass
class CampaignInfoVM:
    id: str = ""
    name: str = DASH
    period: str = EMPTY
    period_sub: str = ""
    scope: str = DASH
    scope_sub: str = ""
    budget: str = DASH
    budget_sub: str = ""
    mechanic: str = EMPTY
    mechanic_sub: str = ""
    segment: str = ""
    category: str = ""


@dataclass
class TaskVM:
    id: str
    name: str
    owner: str
    team: str
    due_date: date | None
    status: str
    priority: str = "Trung bình"
    is_new: bool = False


@dataclass
class ExecuteViewModel:
    campaign: CampaignInfoVM = field(default_factory=CampaignInfoVM)
    tasks: list[TaskVM] = field(default_factory=list)
    completed: int = 0
    total: int = 0
    percentage: int = 0
    readiness_message: str = EMPTY
    checklist: list[dict] = field(default_factory=list)
    ready_to_launch: bool = False
    launch_blockers: list[str] = field(default_factory=list)
    has_recommendation: bool = False
    show_all_checklist: bool = False


def render() -> None:
    render_shell(
        "Execute",
        "Cấu hình chiến dịch, phân công công việc và kiểm tra sẵn sàng trước khi khởi chạy.",
        stage=6,
    )
    rec = st.session_state.get("last_recommendation_card")
    if rec is None:
        _render_empty()
        return

    _ensure_execute_state(rec)
    vm = build_execute_view_model(rec)
    _render_view(vm, rec)


def build_execute_view_model(rec) -> ExecuteViewModel:
    """UI adapter — chỉ gom session / output sẵn có, không tính lại recommendation."""
    camp = st.session_state.get("execute_campaign") or {}
    tasks_raw = st.session_state.get("execute_tasks") or []
    new_ids = set(st.session_state.get("new_task_ids") or [])

    tasks: list[TaskVM] = []
    for t in tasks_raw:
        due = _parse_date(t.get("due_date"))
        tasks.append(
            TaskVM(
                id=str(t.get("id") or ""),
                name=str(t.get("name") or ""),
                owner=str(t.get("owner") or ""),
                team=str(t.get("team") or ""),
                due_date=due,
                status=str(t.get("status") or "Chưa bắt đầu"),
                priority=str(t.get("priority") or "Trung bình"),
                is_new=str(t.get("id")) in new_ids,
            )
        )

    completed = sum(1 for t in tasks if t.status == "Hoàn thành")
    total = len(tasks)
    percentage = int(round(100.0 * completed / total)) if total else 0

    if total == 0:
        message = "Chưa có công việc thực thi. Hệ thống sẽ tạo kế hoạch từ quy tắc D-7…D+7 khi có phương án đã chọn."
    elif percentage >= 100:
        message = "Chiến dịch đã đáp ứng các điều kiện triển khai theo checklist công việc hiện tại."
    else:
        message = "Hoàn thành các công việc còn lại để sẵn sàng khởi động chiến dịch."

    checklist = [
        {"label": t.name or f"Công việc {i + 1}", "checked": t.status == "Hoàn thành"}
        for i, t in enumerate(tasks)
    ]

    blockers: list[str] = []
    if total == 0:
        blockers.append("Chưa có kế hoạch thực thi.")
    name = str(camp.get("name") or "").strip()
    if not name:
        blockers.append("Thiếu tên chiến dịch.")
    start = _parse_date(camp.get("start"))
    end = _parse_date(camp.get("end"))
    if start and end and start > end:
        blockers.append("Thời gian triển khai không hợp lệ (ngày bắt đầu > ngày kết thúc).")
    budget = camp.get("budget")
    if budget is not None:
        try:
            if float(budget) < 0:
                blockers.append("Ngân sách không hợp lệ.")
        except (TypeError, ValueError):
            blockers.append("Ngân sách không hợp lệ.")

    # [BUSINESS RULE giữ nguyên]: chỉ bắt buộc có kế hoạch trước khi launch (logic Execute cũ).
    # Không tự thêm hard-blocker mới (vd. bắt buộc 100% task xong).
    ready = len(blockers) == 0

    return ExecuteViewModel(
        campaign=_campaign_vm(rec, camp),
        tasks=tasks,
        completed=completed,
        total=total,
        percentage=percentage,
        readiness_message=message,
        checklist=checklist,
        ready_to_launch=ready,
        launch_blockers=blockers,
        has_recommendation=True,
        show_all_checklist=bool(st.session_state.get("execute_show_all_checklist")),
    )


def _campaign_vm(rec, camp: dict) -> CampaignInfoVM:
    profile = st.session_state.get("business_profile")
    meta = st.session_state.get("last_scenario_meta") or {}
    local_ctx = st.session_state.get("local_context")

    name = str(camp.get("name") or "").strip() or DASH
    camp_id = st.session_state.get("active_campaign_id") or camp.get("draft_id") or ""
    id_sub = camp_id if camp_id else "Chưa khởi tạo"

    start = _parse_date(camp.get("start"))
    end = _parse_date(camp.get("end"))
    if start and end:
        period = f"{_fmt_date(start)} - {_fmt_date(end)}"
    elif start:
        period = _fmt_date(start)
    else:
        period = EMPTY

    promo_days = camp.get("promo_days")
    if promo_days is None:
        promo_days = meta.get("promo_days")
    period_sub = f"Thời gian: {int(promo_days)} ngày" if promo_days else (rec.timing_text or "")

    scope = str(camp.get("scope") or "").strip()
    if not scope:
        scope = _default_scope(meta, local_ctx)
    scope_sub = ""
    # Chỉ thêm ghi chú phụ khi không trùng nội dung value (tránh lặp "Phạm vi mô phỏng").
    if local_ctx is not None and getattr(local_ctx, "store_name", "") and str(local_ctx.store_name).strip():
        store = str(local_ctx.store_name).strip()
        if store not in scope:
            scope_sub = f"Cửa hàng: {store}"
    scope_value = meta.get("scope_value")
    if scope_value and str(scope_value) not in scope and (not scope_sub or str(scope_value) not in scope_sub):
        note = f"Phạm vi mô phỏng: {scope_value}"
        scope_sub = f"{scope_sub} · {note}" if scope_sub else note

    budget_val = camp.get("budget")
    if budget_val is None and profile is not None:
        budget_val = profile.promotion_budget
    budget_text = vnd(float(budget_val)) if budget_val is not None else DASH
    budget_sub = ""
    if budget_val is not None and rec.expected_revenue_range:
        mid_rev = (float(rec.expected_revenue_range[0]) + float(rec.expected_revenue_range[1])) / 2
        if mid_rev > 0:
            pct = 100.0 * float(budget_val) / mid_rev
            budget_sub = f"~{pct:.1f}% doanh thu dự kiến (trung điểm khoảng dự báo)"

    mechanic = rec.promotion_label or EMPTY
    mechanic_sub = f"Mục tiêu: {rec.objective_vi}" if rec.objective_vi else ""
    if rec.recommended_stock is not None:
        stock_note = f"Tồn kho đề xuất {integer(rec.recommended_stock)}"
        mechanic_sub = f"{mechanic_sub}. {stock_note}" if mechanic_sub else stock_note

    return CampaignInfoVM(
        id=id_sub,
        name=name,
        period=period,
        period_sub=period_sub,
        scope=scope or DASH,
        scope_sub=scope_sub,
        budget=budget_text,
        budget_sub=budget_sub,
        mechanic=mechanic,
        mechanic_sub=mechanic_sub,
        segment=rec.target_segment or "",
        category=rec.product_focus or "",
    )


def _render_empty() -> None:
    fields = "".join(
        [
            campaign_info_field("Tên chiến dịch", DASH, EMPTY, "megaphone", "purple"),
            campaign_info_field("Thời gian triển khai", EMPTY, "", "calendar", "green"),
            campaign_info_field("Phạm vi áp dụng", DASH, "", "map-pin", "pink"),
            campaign_info_field("Ngân sách dự kiến", DASH, "", "wallet", "orange"),
            campaign_info_field("Cơ chế ưu đãi", EMPTY, "", "gift", "blue"),
        ]
    )
    left, right = st.columns([0.42, 0.58], gap="medium")
    with left:
        show(campaign_info_card(fields))
    with right:
        show(
            f'<div class="pp-exec-panel">{exec_panel_header("Danh sách công việc thực thi", "Các đầu việc cần hoàn thành để triển khai chiến dịch", "clipboard-check")}'
            f"{muted('Chọn phương án ở Decide trước khi tạo kế hoạch thực thi.')}</div>"
        )
    b1, b2 = st.columns(2, gap="medium")
    with b1:
        show(campaign_readiness_card(0, 0, 0, "Chưa có dữ liệu chiến dịch từ Decide."))
    with b2:
        show(prelaunch_checklist_card([]))
    st.caption("Quay lại Decide để chọn phương án khuyến mãi trước khi triển khai.")


def _render_view(vm: ExecuteViewModel, rec) -> None:
    if st.session_state.get("simulation_stale"):
        st.warning(
            "Một số thay đổi trên Execute (ngân sách / thời gian / phạm vi) có thể làm kết quả "
            "mô phỏng hiện tại không còn phù hợp. Không tự chạy lại mô hình — hãy xem lại Simulate nếu cần."
        )

    left, right = st.columns([0.42, 0.58], gap="medium")
    with left:
        with st.container(border=True, height=EXEC_TOP_CARD_HEIGHT):
            _render_campaign_info(vm)
    with right:
        with st.container(border=True, height=EXEC_TOP_CARD_HEIGHT):
            _render_task_list(vm)

    b1, b2 = st.columns(2, gap="medium")
    with b1:
        show(
            campaign_readiness_card(
                vm.completed,
                vm.total,
                vm.percentage,
                vm.readiness_message,
            )
        )
    with b2:
        _render_checklist(vm)

    _render_actions(vm, rec)

    plan = st.session_state.get("last_campaign_plan")
    if plan is not None:
        note = "Nội dung marketing dùng template rule-based."
        if is_llm_enabled():
            note = "Đã thấy cấu hình LLM, nhưng bản này vẫn dùng template rule-based cho nội dung."
        with st.expander("Nội dung marketing (Facebook, Zalo, SMS)"):
            st.caption(note)
            st.text_area("Facebook", plan.fb_copy, height=120, key="ex_fb_copy")
            st.text_area("Zalo", plan.zalo_copy, height=100, key="ex_zalo_copy")
            st.text_area("SMS", plan.sms_copy, height=70, key="ex_sms_copy")


def _render_campaign_info(vm: ExecuteViewModel) -> None:
    head_l, head_r = st.columns([3.2, 1.0])
    with head_l:
        show(exec_panel_header("Thông tin chiến dịch", "Tóm tắt các thông tin chính của chiến dịch", "rocket"))
    with head_r:
        if st.button("Chỉnh sửa", type="secondary", key="ex_edit_campaign", width="stretch"):
            _campaign_edit_dialog()

    fields = [
        campaign_info_field(
            "Tên chiến dịch",
            vm.campaign.name,
            f"Mã chiến dịch: {vm.campaign.id}"
            if vm.campaign.id and vm.campaign.id != "Chưa khởi tạo"
            else (vm.campaign.id or ""),
            "megaphone",
            "purple",
        ),
        campaign_info_field(
            "Thời gian triển khai", vm.campaign.period, vm.campaign.period_sub, "calendar", "green"
        ),
        campaign_info_field("Phạm vi áp dụng", vm.campaign.scope, vm.campaign.scope_sub, "map-pin", "pink"),
        campaign_info_field("Ngân sách dự kiến", vm.campaign.budget, vm.campaign.budget_sub, "wallet", "orange"),
        campaign_info_field("Cơ chế ưu đãi", vm.campaign.mechanic, vm.campaign.mechanic_sub, "gift", "blue"),
    ]
    if vm.campaign.category:
        fields.append(
            campaign_info_field("Sản phẩm / nhóm mục tiêu", vm.campaign.category, "", "package", "blue")
        )
    if vm.campaign.segment:
        fields.append(
            campaign_info_field("Phân khúc khách hàng", vm.campaign.segment, "", "users", "purple")
        )
    show(f'<div class="pp-exec-fields">{"".join(fields)}</div>')


@st.dialog("Chỉnh sửa thông tin chiến dịch", width="large")
def _campaign_edit_dialog() -> None:
    camp = dict(st.session_state.get("execute_campaign") or {})
    rec = st.session_state.get("last_recommendation_card")
    profile = st.session_state["business_profile"]

    start_default = _parse_date(camp.get("start")) or date.today()
    end_default = _parse_date(camp.get("end")) or start_default
    budget_default = float(camp.get("budget") if camp.get("budget") is not None else profile.promotion_budget)

    scope_options = _forecast_scope_options()
    current_scope = str(camp.get("scope") or "").strip()
    if current_scope and current_scope not in scope_options:
        # Giữ lựa chọn đang lưu nếu chưa có trong danh sách Forecast (không invent option mới).
        scope_options = [current_scope] + scope_options
    if not scope_options:
        st.warning("Chưa có dữ liệu Forecast để chọn phạm vi. Hãy tải dữ liệu và mở trang Forecast trước.")
        if st.button("Đóng", key="ex_dlg_close_no_scope"):
            st.rerun()
        return

    scope_index = scope_options.index(current_scope) if current_scope in scope_options else 0

    with st.form("ex_campaign_edit_form"):
        name = st.text_input("Tên chiến dịch", value=str(camp.get("name") or ""))
        description = st.text_area("Mô tả (tuỳ chọn)", value=str(camp.get("description") or ""), height=80)
        c1, c2 = st.columns(2)
        with c1:
            start = st.date_input("Ngày bắt đầu", value=start_default)
        with c2:
            end = st.date_input("Ngày kết thúc", value=end_default)
        scope = st.selectbox(
            "Phạm vi áp dụng",
            scope_options,
            index=scope_index,
            help="Danh sách lấy từ cùng nguồn tùy chọn Phạm vi trên trang Forecast (Toàn công ty / Danh mục / SKU).",
        )
        budget = st.number_input(
            "Ngân sách dự kiến (đ)",
            min_value=0.0,
            value=float(budget_default),
            step=1_000_000.0,
        )
        st.caption(
            "Cơ chế ưu đãi lấy từ phương án đã chọn ở Decide và không chỉnh tại đây "
            f"(hiện tại: {rec.promotion_label if rec else DASH}). "
            "Muốn đổi cơ chế, hãy quay lại Decide."
        )
        st.info(
            "Đổi ngân sách, thời gian hoặc phạm vi có thể làm giả định mô phỏng không còn phù hợp. "
            "Hệ thống sẽ đánh dấu kết quả phụ thuộc là stale — không tự chạy lại mô hình."
        )
        save = st.form_submit_button("Lưu thay đổi", type="primary", width="stretch")

    if st.button("Hủy", type="secondary", key="ex_dlg_cancel", width="stretch"):
        st.rerun()

    if save:
        err = _validate_campaign(name, start, end, budget, scope)
        if err:
            st.error(err)
            st.stop()
        old = dict(st.session_state.get("execute_campaign") or {})
        sensitive_changed = (
            float(old.get("budget") or 0) != float(budget)
            or str(old.get("start")) != str(start)
            or str(old.get("end")) != str(end)
            or str(old.get("scope") or "") != str(scope).strip()
        )
        camp["name"] = name.strip()
        camp["description"] = description.strip()
        camp["start"] = start.isoformat()
        camp["end"] = end.isoformat()
        camp["scope"] = str(scope).strip()
        camp["budget"] = float(budget)
        camp["promo_days"] = max(1, (end - start).days + 1)
        st.session_state["execute_campaign"] = camp
        profile.promotion_budget = float(budget)
        if sensitive_changed:
            st.session_state["simulation_stale"] = True
        _sync_plan_dataframe()
        st.rerun()


def _validate_campaign(name: str, start: date, end: date, budget: float, scope: str) -> str | None:
    if not str(name).strip():
        return "Tên chiến dịch là bắt buộc."
    if start > end:
        return "Ngày bắt đầu phải trước hoặc bằng ngày kết thúc."
    if budget is None or float(budget) < 0:
        return "Ngân sách phải ≥ 0."
    if not str(scope).strip():
        return "Phạm vi áp dụng là bắt buộc."
    return None


def _render_task_list(vm: ExecuteViewModel) -> None:
    head_l, head_r = st.columns([3.0, 1.2])
    with head_l:
        show(
            exec_panel_header(
                "Danh sách công việc thực thi",
                "Các đầu việc cần hoàn thành để triển khai chiến dịch",
                "clipboard-check",
            )
        )
    with head_r:
        if st.button("+ Thêm công việc", type="secondary", key="ex_add_task", width="stretch"):
            _add_task()

    if not vm.tasks:
        show(muted("Chưa có công việc. Bấm «+ Thêm công việc» hoặc tạo từ quy tắc D-7…D+7."))
        if st.button("Tạo kế hoạch từ quy tắc hiện có", type="primary", key="ex_gen_plan"):
            _generate_plan_from_rules()
            st.rerun()
        return

    # Header bảng
    show(
        '<div class="pp-exec-grid-head">'
        "<div>#</div><div>Công việc</div><div>Phụ trách</div>"
        "<div>Hạn hoàn thành</div><div>Trạng thái</div><div></div>"
        "</div>"
    )
    for idx, task in enumerate(vm.tasks, start=1):
        _render_task_row(task, idx)

    # Neo cuộn xuống cuối khi vừa thêm công việc
    show('<div id="pp-exec-task-end"></div>')
    _maybe_scroll_tasks_to_end()


def _editing_cell() -> tuple[str, str] | None:
    raw = st.session_state.get("editing_cell")
    if not raw or not isinstance(raw, (list, tuple)) or len(raw) != 2:
        return None
    return str(raw[0]), str(raw[1])


def _set_editing_cell(task_id: str | None, field: str | None = None) -> None:
    if task_id and field:
        st.session_state["editing_cell"] = (task_id, field)
    else:
        st.session_state["editing_cell"] = None


def _render_task_row(task: TaskVM, index: int) -> None:
    editing = _editing_cell()
    # Viền rõ từng hàng (Streamlit container border)
    with st.container(border=True):
        if task.is_new:
            st.caption("Mới")
        c0, c1, c2, c3, c4, c5 = st.columns([0.35, 2.4, 1.45, 1.05, 1.25, 0.65])
        with c0:
            st.markdown(f"**{index}**")
        with c1:
            _cell_name(task, editing)
        with c2:
            _cell_team(task, editing)
        with c3:
            _cell_due(task, editing)
        with c4:
            _cell_status(task, editing)
        with c5:
            st.markdown('<div class="pp-exec-del-btn">', unsafe_allow_html=True)
            if st.button("Xóa", key=f"ex_del_{task.id}", help="Xóa công việc", width="stretch"):
                _delete_task(task.id)
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)


def _cell_name(task: TaskVM, editing: tuple[str, str] | None) -> None:
    if editing == (task.id, "name"):
        key = f"ex_cell_name_{task.id}"
        if key not in st.session_state:
            st.session_state[key] = task.name or ""

        def _save() -> None:
            val = str(st.session_state.get(key, "")).strip()
            if not val:
                st.session_state["ex_cell_error"] = "Tên công việc không được để trống."
                return
            _patch_task(task.id, name=val)
            _set_editing_cell(None)
            st.session_state.pop("ex_cell_error", None)

        st.text_input(
            "Tên công việc",
            key=key,
            label_visibility="collapsed",
            placeholder="Nhập tên công việc…",
            on_change=_save,
        )
        if st.session_state.get("ex_cell_error"):
            st.caption(st.session_state["ex_cell_error"])
        st.caption("Nhấn Enter để lưu")
        return

    label = task.name.strip() if task.name and task.name.strip() else "Nhập tên công việc…"
    st.markdown('<div class="pp-exec-cell-btn">', unsafe_allow_html=True)
    if st.button(label, key=f"ex_clk_name_{task.id}", width="stretch"):
        _set_editing_cell(task.id, "name")
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def _cell_team(task: TaskVM, editing: tuple[str, str] | None) -> None:
    initials = TEAM_INITIALS.get(task.team) or _initials_from_label(task.team or task.owner)
    owner_label = task.team or task.owner or "Chọn phòng ban…"

    if editing == (task.id, "team"):
        key = f"ex_cell_team_{task.id}"
        options = list(TEAMS)
        if key not in st.session_state:
            st.session_state[key] = task.team if task.team in options else (options[0] if options else "")

        def _save() -> None:
            team = st.session_state.get(key) or ""
            _patch_task(task.id, team=team, owner=f"Phụ trách {team}" if team else "")
            _set_editing_cell(None)

        st.selectbox("Phòng ban", options, key=key, label_visibility="collapsed", on_change=_save)
        return

    btn_label = f"{initials} · {owner_label}" if initials else owner_label
    st.markdown('<div class="pp-exec-cell-btn">', unsafe_allow_html=True)
    if st.button(btn_label, key=f"ex_clk_team_{task.id}", width="stretch"):
        _set_editing_cell(task.id, "team")
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def _cell_due(task: TaskVM, editing: tuple[str, str] | None) -> None:
    due_text = _fmt_date(task.due_date) if task.due_date else "Chọn ngày…"

    if editing == (task.id, "due"):
        key = f"ex_cell_due_{task.id}"
        if key not in st.session_state:
            st.session_state[key] = task.due_date or date.today()

        def _save() -> None:
            due = st.session_state.get(key)
            _patch_task(task.id, due_date=due.isoformat() if due else None)
            _set_editing_cell(None)

        st.date_input("Hạn", key=key, label_visibility="collapsed", on_change=_save)
        return

    st.markdown('<div class="pp-exec-cell-btn">', unsafe_allow_html=True)
    if st.button(due_text, key=f"ex_clk_due_{task.id}", width="stretch"):
        _set_editing_cell(task.id, "due")
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def _cell_status(task: TaskVM, editing: tuple[str, str] | None) -> None:
    if editing == (task.id, "status"):
        key = f"ex_cell_status_{task.id}"
        options = list(STATUS_LEVELS)
        if key not in st.session_state:
            st.session_state[key] = task.status if task.status in options else options[0]

        def _save() -> None:
            status = st.session_state.get(key) or options[0]
            _patch_task(task.id, status=status)
            _set_editing_cell(None)

        st.selectbox("Trạng thái", options, key=key, label_visibility="collapsed", on_change=_save)
        return

    kind_map = {
        "Hoàn thành": "ok",
        "Đang thực hiện": "warn",
        "Chưa bắt đầu": "info",
        "Trễ hạn": "bad",
    }
    kind = kind_map.get(task.status, "muted")
    st.markdown(f'<div class="pp-exec-cell-btn pp-exec-status-btn is-{kind}">', unsafe_allow_html=True)
    if st.button(task.status or "—", key=f"ex_clk_status_{task.id}", width="stretch"):
        _set_editing_cell(task.id, "status")
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def _maybe_scroll_tasks_to_end() -> None:
    if not st.session_state.pop("ex_scroll_tasks_end", False):
        return
    import streamlit.components.v1 as components

    components.html(
        """
        <script>
        (function () {
          const doc = window.parent.document;
          const anchor = doc.getElementById('pp-exec-task-end');
          if (anchor) {
            anchor.scrollIntoView({behavior: 'smooth', block: 'end'});
            return;
          }
          const wrappers = doc.querySelectorAll('[data-testid="stVerticalBlockBorderWrapper"]');
          const last = wrappers[wrappers.length - 1];
          if (last) {
            const scrollable = last.querySelector('[data-testid="stVerticalBlock"]') || last;
            scrollable.scrollTop = scrollable.scrollHeight;
          }
        })();
        </script>
        """,
        height=0,
    )


def _patch_task(task_id: str, **fields) -> None:
    tasks = list(st.session_state.get("execute_tasks") or [])
    for t in tasks:
        if t.get("id") == task_id:
            for k, v in fields.items():
                t[k] = v
            break
    st.session_state["execute_tasks"] = tasks
    if "name" in fields and str(fields.get("name") or "").strip():
        st.session_state["new_task_ids"] = [
            i for i in (st.session_state.get("new_task_ids") or []) if i != task_id
        ]
    _sync_plan_dataframe()


def _delete_task(task_id: str) -> None:
    tasks = [t for t in (st.session_state.get("execute_tasks") or []) if t.get("id") != task_id]
    st.session_state["execute_tasks"] = tasks
    st.session_state["new_task_ids"] = [i for i in (st.session_state.get("new_task_ids") or []) if i != task_id]
    editing = _editing_cell()
    if editing and editing[0] == task_id:
        _set_editing_cell(None)
    for suffix in ("name", "team", "due", "status"):
        st.session_state.pop(f"ex_cell_{suffix}_{task_id}", None)
    _sync_plan_dataframe()


def _render_checklist(vm: ExecuteViewModel) -> None:
    show_all = vm.show_all_checklist
    head_extra = ""
    total = len(vm.checklist)
    if total > CHECKLIST_VISIBLE and not show_all:
        head_extra = "toggle"

    show(
        prelaunch_checklist_card(
            vm.checklist,
            visible_count=CHECKLIST_VISIBLE,
            show_all=show_all,
        )
    )
    if head_extra:
        if st.button(f"Xem tất cả ({total}) →", key="ex_checklist_all", type="secondary"):
            st.session_state["execute_show_all_checklist"] = True
            st.rerun()
    elif show_all and total > CHECKLIST_VISIBLE:
        if st.button("Thu gọn", key="ex_checklist_less", type="secondary"):
            st.session_state["execute_show_all_checklist"] = False
            st.rerun()
    st.caption("Checklist suy ra từ trạng thái công việc (read-only).")


def _render_actions(vm: ExecuteViewModel, rec) -> None:
    st.write("")
    left, right = st.columns([2.2, 1.6])
    with left:
        if vm.launch_blockers:
            for b in vm.launch_blockers:
                st.caption(f"• {b}")
        elif vm.percentage < 100 and vm.total:
            st.caption("Một số công việc chưa hoàn thành — có thể khởi chạy nhưng nên rà soát checklist.")
    with right:
        c1, c2 = st.columns(2)
        with c1:
            tasks_df = _tasks_dataframe()
            if tasks_df is not None and not tasks_df.empty:
                buffer = io.BytesIO()
                plan = st.session_state.get("last_campaign_plan")
                with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                    tasks_df.to_excel(writer, sheet_name="Execution Plan", index=False)
                    if plan is not None:
                        pd.DataFrame(
                            {
                                "Kênh": ["Facebook", "Zalo", "SMS"],
                                "Nội dung": [plan.fb_copy, plan.zalo_copy, plan.sms_copy],
                            }
                        ).to_excel(writer, sheet_name="Noi dung", index=False)
                st.download_button(
                    "Xuất kế hoạch",
                    data=buffer.getvalue(),
                    file_name="promotionpilot_execution_plan.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    width="stretch",
                )
            else:
                st.button("Xuất kế hoạch", disabled=True, width="stretch", key="ex_export_disabled")
        with c2:
            disabled = not vm.ready_to_launch
            if st.button(
                "Bắt đầu chiến dịch →",
                type="primary",
                key="start_campaign",
                width="stretch",
                disabled=disabled,
            ):
                _persist_campaign(rec)


# —— State / mutations ——


def _ensure_execute_state(rec) -> None:
    profile = st.session_state["business_profile"]
    meta = st.session_state.get("last_scenario_meta") or {}
    local_ctx = st.session_state.get("local_context")

    if "execute_campaign" not in st.session_state or not st.session_state["execute_campaign"]:
        start = date.today()
        promo_days = int(meta.get("promo_days") or profile.max_campaign_duration_days or 14)
        end = start + timedelta(days=max(promo_days, 1) - 1)
        default_name = f"{rec.promotion_label} — {rec.product_focus}".strip(" —")
        st.session_state["execute_campaign"] = {
            "name": default_name,
            "description": "",
            "start": start.isoformat(),
            "end": end.isoformat(),
            "scope": _default_scope(meta, local_ctx),
            "budget": float(profile.promotion_budget),
            "promo_days": promo_days,
            "draft_id": "",
        }

    if "new_task_ids" not in st.session_state:
        st.session_state["new_task_ids"] = []
    if "editing_cell" not in st.session_state:
        st.session_state["editing_cell"] = None

    if "execute_tasks" not in st.session_state or st.session_state["execute_tasks"] is None:
        # Ưu tiên DataFrame kế hoạch đã có (từ phiên cũ / data_editor).
        plan_df = st.session_state.get("last_execution_plan")
        if plan_df is not None and isinstance(plan_df, pd.DataFrame) and not plan_df.empty:
            st.session_state["execute_tasks"] = _tasks_from_dataframe(plan_df)
        else:
            # Sinh theo quy tắc deterministic hiện có (D-7…D+7) — không invent task giả.
            _generate_plan_from_rules(silent=True)


def _generate_plan_from_rules(*, silent: bool = False) -> None:
    rec = st.session_state.get("last_recommendation_card")
    if rec is None:
        return
    camp = st.session_state.get("execute_campaign") or {}
    start = _parse_date(camp.get("start")) or date.today()
    profile = st.session_state["business_profile"]
    tasks = generate_execution_plan(
        campaign_start=pd.Timestamp(start),
        product_focus=rec.product_focus,
        promotion_label=rec.promotion_label,
        recommended_stock=rec.recommended_stock,
        objective_vi=rec.objective_vi,
    )
    rows = []
    for t in tasks:
        rows.append(
            {
                "id": str(uuid.uuid4()),
                "name": t.task,
                "owner": t.owner,
                "team": t.team,
                "due_date": t.due_date.date().isoformat() if hasattr(t.due_date, "date") else str(t.due_date),
                "status": t.status,
                "priority": t.priority,
                "day_offset": t.day_offset,
            }
        )
    st.session_state["execute_tasks"] = rows
    st.session_state["new_task_ids"] = []
    st.session_state["editing_cell"] = None
    _sync_plan_dataframe()

    if st.session_state.get("last_campaign_plan") is None:
        st.session_state["last_campaign_plan"] = generate_campaign_plan(
            rec,
            business_name=profile.business_name,
            service_capacity_per_staff_per_hour=profile.service_capacity_per_staff_per_hour,
        )
    if not silent:
        st.toast("Đã tạo kế hoạch thực thi từ quy tắc D-7…D+7.")


def _forecast_scope_options() -> list[str]:
    """Options Phạm vi — cùng nguồn với trang Forecast (Toàn công ty / Danh mục / SKU)."""
    options: list[str] = ["Toàn công ty"]
    df = st.session_state.get("clean_df")
    caps = st.session_state.get("capabilities")
    if df is None or getattr(df, "empty", True):
        # Vẫn ưu tiên lựa chọn gần nhất trên Forecast nếu còn trong session widget state.
        last = _forecast_scope_from_session()
        return [last] if last and last not in options else options

    if caps is not None and getattr(caps, "has_category", False) and "category" in df.columns:
        for cat in sorted(df["category"].dropna().unique()):
            label = f"Theo Danh mục · {cat}"
            if label not in options:
                options.append(label)

    if "product_id" in df.columns and "revenue" in df.columns:
        top = df.groupby("product_id")["revenue"].sum().sort_values(ascending=False).index.tolist()
        for sku in top[:50]:  # giới hạn UI; cùng logic top-revenue như Forecast
            label = f"Theo SKU · {sku}"
            if label not in options:
                options.append(label)
    elif "product_id" in df.columns:
        for sku in sorted(df["product_id"].dropna().unique().tolist())[:50]:
            label = f"Theo SKU · {sku}"
            if label not in options:
                options.append(label)

    last = _forecast_scope_from_session()
    if last and last not in options:
        options.insert(1, last)
    return options


def _forecast_scope_from_session() -> str | None:
    """Lấy phạm vi đang chọn trên Forecast (widget keys fc_scope / fc_cat / fc_sku) nếu có."""
    scope = st.session_state.get("fc_scope")
    if not scope:
        return None
    if scope == "Toàn công ty":
        return "Toàn công ty"
    if scope == "Theo Danh mục":
        cat = st.session_state.get("fc_cat")
        return f"Theo Danh mục · {cat}" if cat is not None and str(cat).strip() else "Theo Danh mục"
    if scope == "Theo SKU":
        sku = st.session_state.get("fc_sku")
        return f"Theo SKU · {sku}" if sku is not None and str(sku).strip() else "Theo SKU"
    return str(scope)


def _default_scope(meta: dict, local_ctx) -> str:
    # Ưu tiên phạm vi đang chọn trên Forecast (cùng nguồn dropdown chỉnh sửa).
    forecast_scope = _forecast_scope_from_session()
    if forecast_scope:
        return forecast_scope
    options = _forecast_scope_options()
    if options:
        return options[0]
    if local_ctx is not None and getattr(local_ctx, "store_name", "") and str(local_ctx.store_name).strip():
        return str(local_ctx.store_name).strip()
    scope = meta.get("scope")
    scope_value = meta.get("scope_value")
    parts = [p for p in [scope, scope_value] if p]
    if parts:
        return " · ".join(str(p) for p in parts)
    product = meta.get("product_focus_label")
    if product:
        return str(product)
    return "Toàn công ty"


def _add_task() -> None:
    # Đóng cell đang edit (nếu có)
    _set_editing_cell(None)

    task_id = str(uuid.uuid4())
    tasks = list(st.session_state.get("execute_tasks") or [])
    tasks.append(
        {
            "id": task_id,
            "name": "",
            "owner": "",
            "team": TEAMS[0] if TEAMS else "",
            "due_date": None,
            "status": "Chưa bắt đầu",
            "priority": "Trung bình",
        }
    )
    st.session_state["execute_tasks"] = tasks
    new_ids = list(st.session_state.get("new_task_ids") or [])
    new_ids.append(task_id)
    st.session_state["new_task_ids"] = new_ids
    # Mở ô tên trống để nhập ngay + cuộn xuống cuối
    _set_editing_cell(task_id, "name")
    st.session_state["ex_scroll_tasks_end"] = True
    _sync_plan_dataframe()
    st.rerun()


def _tasks_from_dataframe(df: pd.DataFrame) -> list[dict]:
    rows = []
    for _, row in df.iterrows():
        due = row.get("Ngày") or row.get("due_date") or row.get("Hạn hoàn thành")
        due_s = None
        if due is not None and not (isinstance(due, float) and pd.isna(due)):
            try:
                due_s = pd.Timestamp(due).date().isoformat()
            except Exception:
                due_s = str(due)
        rows.append(
            {
                "id": str(row["id"]) if "id" in df.columns and pd.notna(row.get("id")) else str(uuid.uuid4()),
                "name": str(row.get("Công việc") or row.get("name") or ""),
                "owner": str(row.get("Phụ trách") or row.get("owner") or ""),
                "team": str(row.get("Phòng ban") or row.get("team") or ""),
                "due_date": due_s,
                "status": str(row.get("Trạng thái") or row.get("status") or "Chưa bắt đầu"),
                "priority": str(row.get("Mức độ ưu tiên") or row.get("priority") or "Trung bình"),
            }
        )
    return rows


def _tasks_dataframe() -> pd.DataFrame | None:
    tasks = st.session_state.get("execute_tasks")
    if not tasks:
        return st.session_state.get("last_execution_plan")
    rows = []
    for t in tasks:
        due = _parse_date(t.get("due_date"))
        day_offset = t.get("day_offset")
        if day_offset is None:
            mốc = ""
        elif int(day_offset) == 0:
            mốc = "D0 (Ngày khởi chạy)"
        else:
            sign = "+" if int(day_offset) > 0 else ""
            mốc = f"D{sign}{int(day_offset)}"
        rows.append(
            {
                "Mốc": mốc,
                "Ngày": due,
                "Phòng ban": t.get("team") or "",
                "Công việc": t.get("name") or "",
                "Phụ trách": t.get("owner") or "",
                "Mức độ ưu tiên": t.get("priority") or "Trung bình",
                "Trạng thái": t.get("status") or "Chưa bắt đầu",
            }
        )
    return pd.DataFrame(rows)


def _sync_plan_dataframe() -> None:
    df = _tasks_dataframe()
    if df is not None:
        st.session_state["last_execution_plan"] = df
        st.session_state["execution_editor_df"] = df


def _persist_campaign(rec) -> None:
    camp = st.session_state.get("execute_campaign") or {}
    start = _parse_date(camp.get("start")) or date.today()
    meta = st.session_state.get("last_scenario_meta") or {}
    promo_days = camp.get("promo_days") or meta.get("promo_days")
    scenario_table = st.session_state.get("last_scenario_table")
    no_promo_gp_per_day = None
    if scenario_table is not None and promo_days:
        no_promo_rows = scenario_table[scenario_table["mechanic"] == "no_promo"]
        if not no_promo_rows.empty:
            no_promo_gp_per_day = float(no_promo_rows.iloc[0]["loi_nhuan_gop"]) / promo_days

    _sync_plan_dataframe()
    record = CampaignRecord(
        campaign_id=new_campaign_id(),
        objective=rec.objective_vi,
        product_focus=rec.product_focus,
        promotion_label=camp.get("name") or rec.promotion_label,
        forecast={
            "expected_revenue_range": list(rec.expected_revenue_range),
            "expected_gp_range": list(rec.expected_gp_range),
            "expected_customers_range": list(rec.expected_customers_range),
            "expected_demand_range": list(rec.expected_demand_range),
            "expected_roi_range": list(rec.expected_roi_range) if rec.expected_roi_range else None,
            "campaign_start": str(start),
            "campaign_end": str(camp.get("end") or ""),
            "promo_days": promo_days,
            "scope": camp.get("scope"),
            "budget": camp.get("budget"),
            "no_promo_gp_per_day": no_promo_gp_per_day,
        },
        roi_forecast=sum(rec.expected_roi_range) / 2 if rec.expected_roi_range else None,
    )
    save_campaign_record(record)
    st.session_state["active_campaign_id"] = record.campaign_id
    if st.session_state.get("execute_campaign"):
        st.session_state["execute_campaign"]["draft_id"] = record.campaign_id
    st.success(f"Đã khởi tạo {record.campaign_id}. Sang Monitor để nhập số thực tế.")
    goto("monitor")


def _parse_date(value) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    try:
        return pd.Timestamp(value).date()
    except Exception:
        return None


def _fmt_date(value: date | None) -> str:
    if value is None:
        return DASH
    return value.strftime("%d/%m/%Y")


def _initials_from_label(label: str) -> str:
    parts = [p for p in str(label).replace("/", " ").split() if p]
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[1][0]).upper()
