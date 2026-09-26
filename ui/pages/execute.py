"""Execute: Campaign Execution Workspace — UI/presentation only.

Thông tin chiến dịch lấy từ Simulate + Decide (read-only).
Không rerun recommendation/simulation/ML. Không hard-code số liệu mockup.
"""
from __future__ import annotations

import io
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

from src.execution.plan import generate_execution_plan
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
    task_list_card,
    task_name_cell,
    task_owner_badge,
    task_status_badge,
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

CHECKLIST_SCROLL_HEIGHT = 300


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


def render() -> None:
    render_shell(
        "Execute",
        "Xem thông tin chiến dịch từ Simulate/Decide, theo dõi công việc và kiểm tra sẵn sàng trước khi khởi chạy.",
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

    checks = _sync_checklist_checks(tasks)
    completed, total, percentage = checklist_progress(checks, [t.id for t in tasks])

    if total == 0:
        message = "Chưa có công việc thực thi. Hệ thống sẽ tạo kế hoạch từ quy tắc D-7…D+7 khi có phương án đã chọn."
    elif percentage >= 100:
        message = "Chiến dịch đã đáp ứng các điều kiện triển khai theo checklist hiện tại."
    else:
        message = "Hoàn thành các công việc còn lại để sẵn sàng khởi động chiến dịch."

    checklist = [
        {"id": t.id, "label": t.name or f"Công việc {i + 1}", "checked": bool(checks.get(t.id))}
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

    # [BUSINESS RULE]: phải tick hết checklist trước khi «Bắt đầu chiến dịch».
    if total > 0 and completed < total:
        blockers.append(
            f"Cần hoàn tất checklist trước khi khởi chạy ({completed}/{total} đã chọn)."
        )

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
    )


def checklist_progress(checks: dict, task_ids: list[str]) -> tuple[int, int, int]:
    """(completed, total, percentage) từ map id→checked."""
    total = len(task_ids)
    completed = sum(1 for tid in task_ids if checks.get(tid))
    percentage = int(round(100.0 * completed / total)) if total else 0
    return completed, total, percentage


def _sync_checklist_checks(tasks: list[TaskVM]) -> dict:
    """Đồng bộ execute_checklist với widget checkbox + danh sách task hiện tại."""
    checks = dict(st.session_state.get("execute_checklist") or {})
    valid_ids = {t.id for t in tasks if t.id}
    for tid in list(checks.keys()):
        if tid not in valid_ids:
            checks.pop(tid, None)
    for t in tasks:
        if not t.id:
            continue
        wkey = f"ex_chk_{t.id}"
        if wkey in st.session_state:
            checks[t.id] = bool(st.session_state[wkey])
        elif t.id not in checks:
            checks[t.id] = False
    st.session_state["execute_checklist"] = checks
    return checks


def _campaign_vm(rec, camp: dict) -> CampaignInfoVM:
    """Hiển thị read-only — mọi field lấy từ Simulate (meta/budget/period) + Decide (rec)."""
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

    scope = str(camp.get("scope") or "").strip() or _scope_label_from_simulate(meta, local_ctx)
    scope_sub = ""
    if local_ctx is not None and getattr(local_ctx, "store_name", "") and str(local_ctx.store_name).strip():
        store = str(local_ctx.store_name).strip()
        if store not in scope:
            scope_sub = f"Cửa hàng: {store}"
    scope_value = meta.get("scope_value") or meta.get("product_focus_label")
    if scope_value and str(scope_value) not in scope and (not scope_sub or str(scope_value) not in scope_sub):
        note = f"Phạm vi mô phỏng: {scope_value}"
        scope_sub = f"{scope_sub} · {note}" if scope_sub else note

    budget_val = camp.get("budget")
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
            campaign_info_field("Tên chiến dịch", DASH, EMPTY, "megaphone", "blue"),
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
            task_list_card(
                "",
                empty_html=muted("Chọn phương án ở Decide trước khi tạo kế hoạch thực thi."),
            )
        )
    b1, b2 = st.columns(2, gap="medium")
    with b1:
        show(campaign_readiness_card(0, 0, 0, "Chưa có dữ liệu chiến dịch từ Decide."))
    with b2:
        show(prelaunch_checklist_card([]))
    st.caption("Quay lại Decide để chọn phương án khuyến mãi trước khi triển khai.")


def _render_view(vm: ExecuteViewModel, rec) -> None:
    left, right = st.columns([0.42, 0.58], gap="medium")
    with left:
        show(_campaign_info_html(vm))
    with right:
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


def _campaign_info_html(vm: ExecuteViewModel) -> str:
    """Card HTML đồng bộ pp-card — không cho chỉnh sửa; nguồn Simulate + Decide."""
    fields = [
        campaign_info_field(
            "Tên chiến dịch",
            vm.campaign.name,
            f"Mã chiến dịch: {vm.campaign.id}"
            if vm.campaign.id and vm.campaign.id != "Chưa khởi tạo"
            else (vm.campaign.id or ""),
            "megaphone",
            "blue",
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
    return campaign_info_card("".join(fields))


def _render_task_list(vm: ExecuteViewModel) -> None:
    """Bảng công việc tạm khóa chỉnh sửa — chỉ hiển thị HTML gọn."""
    if not vm.tasks:
        show(
            task_list_card(
                "",
                empty_html=muted("Chưa có công việc. Hệ thống sẽ tạo kế hoạch từ quy tắc D-7…D+7 khi có phương án."),
            )
        )
        if st.button("Tạo kế hoạch từ quy tắc hiện có", type="primary", key="ex_gen_plan"):
            _generate_plan_from_rules()
            st.rerun()
        return

    rows: list[str] = []
    for idx, task in enumerate(vm.tasks, start=1):
        initials = TEAM_INITIALS.get(task.team) or _initials_from_label(task.team or task.owner)
        owner_label = task.team or task.owner or DASH
        due_text = _fmt_date(task.due_date) if task.due_date else DASH
        row_cls = "pp-exec-grid-row is-new" if task.is_new else "pp-exec-grid-row"
        rows.append(
            f'<div class="{row_cls}">'
            f'<div class="pp-exec-idx">{idx}</div>'
            f"<div>{task_name_cell(task.name, is_new=task.is_new)}</div>"
            f"<div>{task_owner_badge(initials, owner_label)}</div>"
            f'<div class="pp-exec-due">{due_text}</div>'
            f"<div>{task_status_badge(task.status)}</div>"
            f"</div>"
        )
    show(task_list_card("".join(rows)))
    st.caption("Danh sách công việc tạm thời chỉ xem — chỉnh sửa sẽ mở lại ở phiên sau.")


def _render_checklist(vm: ExecuteViewModel) -> None:
    """Checklist đầy đủ trong vùng cuộn — không còn nút Xem tất cả / Thu gọn."""
    with st.container(border=True):
        show(
            exec_panel_header(
                "Checklist trước khi khởi động",
                "Các hạng mục bắt buộc cần hoàn tất",
                "clipboard-check",
                "is-blue",
            )
        )
        if not vm.tasks:
            show(muted(EMPTY))
        else:
            with st.container(height=CHECKLIST_SCROLL_HEIGHT, border=False):
                for task in vm.tasks:
                    _checklist_checkbox(task)

    st.caption("Đánh dấu từng hạng mục khi hoàn tất. Phải chọn hết checklist mới bắt đầu chiến dịch.")


def _checklist_checkbox(task: TaskVM) -> None:
    """Checkbox với nhãn đầy đủ; CSS panel tắt ellipsis của Streamlit."""
    checks = dict(st.session_state.get("execute_checklist") or {})
    key = f"ex_chk_{task.id}"
    if key not in st.session_state:
        st.session_state[key] = bool(checks.get(task.id, False))
    label = (task.name or "").strip() or "Công việc"
    st.checkbox(label, key=key)


def _render_actions(vm: ExecuteViewModel, rec) -> None:
    st.write("")
    left, right = st.columns([2.2, 1.6])
    with left:
        if vm.launch_blockers:
            for b in vm.launch_blockers:
                st.caption(f"• {b}")
        elif vm.ready_to_launch:
            st.caption("Đã hoàn tất checklist — có thể bắt đầu chiến dịch.")
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
    """Đồng bộ execute_campaign từ Simulate + Decide mỗi lần vào trang (read-only)."""
    camp = _campaign_dict_from_sources(rec)
    st.session_state["execute_campaign"] = camp

    if "new_task_ids" not in st.session_state:
        st.session_state["new_task_ids"] = []
    if "execute_checklist" not in st.session_state:
        st.session_state["execute_checklist"] = {}

    plan_sig = f"{rec.promotion_label}|{rec.product_focus}|{camp.get('start')}|{camp.get('promo_days')}"
    prev_sig = st.session_state.get("_execute_plan_sig")
    tasks = st.session_state.get("execute_tasks")

    if tasks is None:
        plan_df = st.session_state.get("last_execution_plan")
        if plan_df is not None and isinstance(plan_df, pd.DataFrame) and not plan_df.empty:
            st.session_state["execute_tasks"] = _tasks_from_dataframe(plan_df)
        else:
            _generate_plan_from_rules(silent=True)
    elif prev_sig is not None and prev_sig != plan_sig:
        # Phương án Decide / thời gian Simulate đổi → tạo lại kế hoạch theo quy tắc.
        _generate_plan_from_rules(silent=True)
        _reset_checklist_state()

    st.session_state["_execute_plan_sig"] = plan_sig


def _reset_checklist_state() -> None:
    """Xóa lựa chọn checklist + widget keys khi kế hoạch thực thi đổi."""
    old = dict(st.session_state.get("execute_checklist") or {})
    st.session_state["execute_checklist"] = {}
    st.session_state.pop("execute_show_all_checklist", None)
    for tid in old:
        st.session_state.pop(f"ex_chk_{tid}", None)


def _campaign_dict_from_sources(rec) -> dict:
    """Gom field chiến dịch từ snapshot Simulate (last_scenario_meta) + Decide (rec).

    Ưu tiên meta đã lưu khi «Chạy mô phỏng» — không đọc widget form đang sửa.
    """
    from src.promotion.sim_setup import budget_from_meta, campaign_window_from_meta, scope_label_from_meta

    profile = st.session_state["business_profile"]
    meta = st.session_state.get("last_scenario_meta") or {}
    local_ctx = st.session_state.get("local_context")
    existing = st.session_state.get("execute_campaign") or {}

    start, end, promo_days = campaign_window_from_meta(
        meta, fallback_days=int(profile.max_campaign_duration_days or 14)
    )
    budget = budget_from_meta(meta, fallback=float(profile.promotion_budget or 0))
    store = getattr(local_ctx, "store_name", None) if local_ctx is not None else None

    default_name = f"{rec.promotion_label} — {rec.product_focus}".strip(" —")
    return {
        "name": default_name,
        "description": "",
        "start": start.isoformat(),
        "end": end.isoformat(),
        "scope": scope_label_from_meta(meta, store_name=store),
        "budget": budget,
        "promo_days": int(promo_days),
        "draft_id": existing.get("draft_id") or "",
    }


def _period_from_simulate(meta: dict, profile) -> tuple[date, date, int]:
    """Thời gian chiến dịch từ snapshot Simulate (campaign_start/end), không từ widget live."""
    from src.promotion.sim_setup import campaign_window_from_meta

    return campaign_window_from_meta(
        meta, fallback_days=int(getattr(profile, "max_campaign_duration_days", None) or 14)
    )


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
    _reset_checklist_state()
    _sync_plan_dataframe()

    if st.session_state.get("last_campaign_plan") is None:
        st.session_state["last_campaign_plan"] = generate_campaign_plan(
            rec,
            business_name=profile.business_name,
            service_capacity_per_staff_per_hour=profile.service_capacity_per_staff_per_hour,
        )
    if not silent:
        st.toast("Đã tạo kế hoạch thực thi từ quy tắc D-7…D+7.")


def _scope_label_from_simulate(meta: dict, local_ctx) -> str:
    """Nhãn phạm vi từ snapshot Simulate — ủy thác helper dùng chung."""
    from src.promotion.sim_setup import scope_label_from_meta

    store = None
    if local_ctx is not None and getattr(local_ctx, "store_name", ""):
        store = str(local_ctx.store_name).strip() or None
    return scope_label_from_meta(meta, store_name=store)


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
    expected_promo_cost = None
    if scenario_table is not None and promo_days:
        no_promo_rows = scenario_table[scenario_table["mechanic"] == "no_promo"]
        if not no_promo_rows.empty:
            no_promo_gp_per_day = float(no_promo_rows.iloc[0]["loi_nhuan_gop"]) / promo_days
        # Chi phí KM của cơ chế đã chọn (Decide) — fallback khi Monitor chưa nhập cost.
        selected = st.session_state.get("selected_mechanic")
        chosen = scenario_table
        if selected:
            hit = scenario_table[scenario_table["mechanic"] == selected]
            if not hit.empty:
                chosen = hit
        else:
            chosen = scenario_table[scenario_table["mechanic"] != "no_promo"]
        if not chosen.empty and "chi_phi_khuyen_mai" in chosen.columns:
            try:
                cost_val = float(chosen.iloc[0]["chi_phi_khuyen_mai"])
                if cost_val > 0:
                    expected_promo_cost = cost_val
            except (TypeError, ValueError):
                expected_promo_cost = None

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
            "expected_promo_cost": expected_promo_cost,
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
