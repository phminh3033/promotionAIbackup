"""Prepare: tồn kho, ngân sách, margin — UI gate trước Simulate; logic planner giữ nguyên."""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd
import streamlit as st

from services.workflow import recent_demand, run_inventory, stock_status
from ui.components import (
    DASH,
    EMPTY,
    badge,
    esc,
    gap_cell,
    prepare_metric_card,
    product_readiness_table,
    readiness_issue_item,
    readiness_issue_list,
    readiness_score_card,
    show,
)
from ui.formatters import compact_vnd, format_int_commas, integer, parse_int_commas, pct
from ui.shell import continue_button, render_shell

STATUS_KIND = {"Đủ hàng": "ok", "Sắp thiếu": "warn", "Thiếu hàng": "bad"}


@dataclass
class PrepareViewModel:
    """UI adapter — chỉ gom output sẵn có; không chạy ML / không đổi công thức planner."""

    inventory_value: str = DASH
    inventory_support: str = EMPTY
    inventory_progress: float | None = None
    inventory_note: str = ""

    budget_value: str = DASH
    budget_support: str = EMPTY
    budget_progress: float | None = None

    margin_value: str = DASH
    margin_support: str = EMPTY
    margin_label: str = ""  # Healthy / Watch / Risk / ""
    margin_kind: str | None = None

    ops_value: str = DASH
    ops_support: str = EMPTY
    ops_kind: str = "muted"

    products: list[dict] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)

    readiness_label: str = DASH
    readiness_progress: float | None = None
    readiness_message: str = EMPTY
    readiness_tone: str = "muted"

    issues: list[dict] = field(default_factory=list)
    cta_note: str = "Cần dữ liệu trước khi mô phỏng."
    can_continue: bool = True  # workflow hiện tại cho phép override


def render() -> None:
    render_shell(
        "Prepare",
        "Đánh giá tồn kho, ngân sách, margin và năng lực vận hành trước khi mô phỏng.",
        stage=3,
    )
    from src.utils.state import has_data

    if not has_data():
        _render_empty()
        return

    profile = st.session_state["business_profile"]
    caps = st.session_state["capabilities"]
    lead, safety, budget, min_margin = _param_controls(profile)
    if lead is not None and int(lead) >= 1:
        profile.lead_time_days = int(lead)
    if safety is not None:
        profile.safety_stock_days = int(safety)
    if budget is not None:
        profile.promotion_budget = float(budget)
    if min_margin is not None:
        profile.min_margin_pct = float(min_margin)

    if not caps.has_inventory:
        st.warning("Chưa có cột tồn kho. Hệ thống chỉ hiện nhu cầu gần đây, không tính số lượng cần nhập.")
        demand = recent_demand(st.session_state["clean_df"])
        st.dataframe(demand.sort_values("avg_daily_demand", ascending=False), width="stretch", hide_index=True)
    else:
        if st.button("Tính mức sẵn sàng tồn kho", type="primary", key="run_inv"):
            if lead is None or safety is None:
                st.warning(
                    "Nhập Lead time và Safety stock, hoặc lưu Hồ sơ doanh nghiệp để tự điền trước khi tính."
                )
            else:
                with st.spinner("Đang lập kế hoạch tồn kho..."):
                    run_inventory(int(lead), int(safety))

    plan = st.session_state.get("inventory_plan")
    vm = build_prepare_view_model(plan, profile, caps)
    _render_view(vm)


def _render_empty() -> None:
    vm = PrepareViewModel(
        inventory_support="Chưa có dữ liệu tồn kho.",
        budget_support="Chưa thiết lập ngân sách chiến dịch.",
        margin_support="Chưa thể tính biên lợi nhuận dự kiến.",
        ops_support="Chưa đánh giá năng lực vận hành.",
        ops_value="Chưa đánh giá",
        readiness_message="Chưa sẵn sàng",
        cta_note="Cần tải dữ liệu trước khi tiếp tục.",
    )
    _render_view(vm, empty=True)


def _param_controls(profile):
    """Tham số Prepare: mặc định trống; chỉ autofill khi đã lưu/tải Hồ sơ doanh nghiệp."""
    _restore_prepare_params()
    _sanitize_prep_lead_session()
    _seed_prep_from_business_profile(profile)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.text_input(
            "Lead time (ngày)",
            key="prep_lead_fmt",
            on_change=_sync_prep_lead,
            placeholder="",
        )
    with c2:
        st.text_input(
            "Safety stock (ngày)",
            key="prep_safety_fmt",
            on_change=_sync_prep_safety,
            placeholder="",
        )
    with c3:
        st.text_input(
            "Ngân sách khuyến mãi (VND)",
            key="prep_budget_fmt",
            on_change=_sync_prep_budget,
            placeholder="",
            help="Tự thêm dấu phẩy hàng nghìn. Đồng bộ từ Hồ sơ doanh nghiệp khi đã lưu/chỉnh sửa.",
        )
    with c4:
        st.text_input(
            "Margin tối thiểu",
            key="prep_margin_fmt",
            on_change=_sync_prep_margin,
            placeholder="",
            help="Tỷ lệ thập phân, vd 0.15 = 15%.",
        )
    _snapshot_prepare_params()
    return (
        st.session_state.get("prep_lead"),
        st.session_state.get("prep_safety"),
        st.session_state.get("prep_budget"),
        st.session_state.get("prep_margin"),
    )


def _snapshot_prepare_params() -> None:
    """Lưu bản sao không phải widget-key — Streamlit xóa widget state khi rời trang Prepare."""
    st.session_state["prepare_params"] = {
        "prep_lead": st.session_state.get("prep_lead"),
        "prep_lead_fmt": st.session_state.get("prep_lead_fmt", ""),
        "prep_safety": st.session_state.get("prep_safety"),
        "prep_safety_fmt": st.session_state.get("prep_safety_fmt", ""),
        "prep_budget": st.session_state.get("prep_budget"),
        "prep_budget_fmt": st.session_state.get("prep_budget_fmt", ""),
        "prep_margin": st.session_state.get("prep_margin"),
        "prep_margin_fmt": st.session_state.get("prep_margin_fmt", ""),
    }


def _restore_prepare_params() -> None:
    """Khôi phục giá trị đã nhập trước khi tạo lại widget trên trang Prepare."""
    saved = st.session_state.get("prepare_params")
    if not isinstance(saved, dict):
        return
    for key, value in saved.items():
        # Chỉ khôi phục khi widget key đã bị Streamlit xóa sau khi navigate.
        if key not in st.session_state:
            st.session_state[key] = value


def _sanitize_prep_lead_session() -> None:
    """Session cũ từ st.number_input(key=prep_lead, min_value=1) có thể còn giá trị 0 → crash.

    Xóa/chuẩn hóa trước mọi widget Prepare; lead hợp lệ phải ≥ 1 hoặc trống (None).
    """
    lead = st.session_state.get("prep_lead")
    if lead is not None:
        try:
            lead_i = int(lead)
        except (TypeError, ValueError):
            lead_i = 0
        if lead_i < 1:
            st.session_state["prep_lead"] = None
            st.session_state["prep_lead_fmt"] = ""


def _seed_prep_from_business_profile(profile) -> None:
    """Autofill Prepare từ hồ sơ đã Lưu/Tải; seed lại khi hồ sơ đổi."""
    from src.utils.state import apply_business_profile_to_prepare, prep_profile_fingerprint

    blank = {
        "prep_lead": None,
        "prep_lead_fmt": "",
        "prep_safety": None,
        "prep_safety_fmt": "",
        "prep_budget": None,
        "prep_budget_fmt": "",
        "prep_margin": None,
        "prep_margin_fmt": "",
    }
    if not st.session_state.get("prep_fields_initialized"):
        for key, value in blank.items():
            if key not in st.session_state:
                st.session_state[key] = value
        st.session_state["prep_fields_initialized"] = True

    if not st.session_state.get("bp_profile_committed"):
        return

    # User đang giữ chỉnh tay trên Prepare → không ghi đè.
    if st.session_state.get("params_authority") == "prep":
        return

    fp = prep_profile_fingerprint(profile)
    force = not st.session_state.get("prep_autofilled_from_bp")
    if not force and st.session_state.get("prep_autofill_fp") == fp:
        return

    apply_business_profile_to_prepare(profile)


def _mark_prep_authority() -> None:
    st.session_state["params_authority"] = "prep"


def _sync_prep_lead() -> None:
    raw = st.session_state.get("prep_lead_fmt")
    if not str(raw or "").strip():
        st.session_state["prep_lead"] = None
        st.session_state["prep_lead_fmt"] = ""
        _mark_prep_authority()
        _snapshot_prepare_params()
        return
    value = parse_int_commas(raw, default=0, minimum=0)
    st.session_state["prep_lead"] = value if value > 0 else None
    st.session_state["prep_lead_fmt"] = str(value) if value > 0 else ""
    _mark_prep_authority()
    _snapshot_prepare_params()


def _sync_prep_safety() -> None:
    raw = st.session_state.get("prep_safety_fmt")
    if not str(raw or "").strip():
        st.session_state["prep_safety"] = None
        st.session_state["prep_safety_fmt"] = ""
        _mark_prep_authority()
        _snapshot_prepare_params()
        return
    value = parse_int_commas(raw, default=0, minimum=0)
    st.session_state["prep_safety"] = value
    st.session_state["prep_safety_fmt"] = str(value)
    _mark_prep_authority()
    _snapshot_prepare_params()


def _sync_prep_budget() -> None:
    raw = st.session_state.get("prep_budget_fmt")
    if not str(raw or "").strip():
        st.session_state["prep_budget"] = None
        st.session_state["prep_budget_fmt"] = ""
        _mark_prep_authority()
        _snapshot_prepare_params()
        return
    value = parse_int_commas(raw, default=0, minimum=0)
    st.session_state["prep_budget"] = float(value) if value > 0 else None
    st.session_state["prep_budget_fmt"] = format_int_commas(value) if value > 0 else ""
    _mark_prep_authority()
    _snapshot_prepare_params()


def _sync_prep_margin() -> None:
    raw = str(st.session_state.get("prep_margin_fmt") or "").strip().replace(",", ".")
    if not raw:
        st.session_state["prep_margin"] = None
        st.session_state["prep_margin_fmt"] = ""
        _mark_prep_authority()
        _snapshot_prepare_params()
        return
    try:
        value = min(0.9, max(0.0, float(raw)))
    except ValueError:
        st.session_state["prep_margin"] = None
        st.session_state["prep_margin_fmt"] = ""
        _mark_prep_authority()
        _snapshot_prepare_params()
        return
    st.session_state["prep_margin"] = value
    st.session_state["prep_margin_fmt"] = f"{value:.2f}"
    _mark_prep_authority()
    _snapshot_prepare_params()


def build_prepare_view_model(plan, profile, caps) -> PrepareViewModel:
    """Gom session/output hiện có thành view model cho UI.

    [UI ADAPTER — không đổi business rule]
    - Inventory readiness % = tỷ lệ SKU stockout_risk == LOW (logic Prepare cũ).
    - Supporting totals = tổng current_inventory / tổng expected_demand_leadtime.
    - Gap hiển thị = current_inventory - expected_demand_leadtime (map Stock vs Demand).
    - Status vẫn qua stock_status() hiện có.
    - Budget allocated chỉ lấy từ last_scenario_table nếu đã mô phỏng; không bịa.
    - Margin từ gross_profit/revenue nếu có, không thì target_margin_pct hồ sơ.
    - Ops = Sẵn sàng khi không còn HIGH stockout (logic Prepare cũ).
    - Overall readiness = trung bình các điểm 0–1 có sẵn (inventory, budget, margin, ops).
    """
    vm = PrepareViewModel()

    # —— Inventory ——
    if plan is None or (isinstance(plan, pd.DataFrame) and plan.empty):
        vm.inventory_value = "Chưa tính"
        vm.inventory_support = (
            "Bấm «Tính mức sẵn sàng tồn kho» khi đã có cột tồn kho."
            if caps.has_inventory
            else "Không thể đánh giá tồn kho vì chưa có dữ liệu tồn kho."
        )
        inv_score = None
    else:
        enough = int((plan["stockout_risk"] == "LOW").sum())
        ready_ratio = enough / max(len(plan), 1)
        inv_score = ready_ratio
        vm.inventory_value = pct(ready_ratio, 0)
        vm.inventory_progress = ready_ratio
        total_stock = float(plan["current_inventory"].sum())
        total_demand = float(plan["expected_demand_leadtime"].sum())
        vm.inventory_support = (
            f"{integer(total_stock)} / {integer(total_demand)} sản phẩm · "
            f"{enough}/{len(plan)} SKU đủ hàng theo lead time & safety stock."
        )

        # Product rows
        frame = plan.copy()
        frame["status"] = frame.apply(stock_status, axis=1)
        frame["gap"] = frame["current_inventory"] - frame["expected_demand_leadtime"]
        cats = []
        if "category" in frame.columns:
            cats = sorted({str(c) for c in frame["category"].dropna().unique() if str(c).strip()})
        vm.categories = cats
        products = []
        for _, row in frame.sort_values("recommended_order_qty", ascending=False).iterrows():
            products.append(
                {
                    "product_id": str(row["product_id"]),
                    "category": (
                        str(row["category"])
                        if "category" in frame.columns and pd.notna(row.get("category")) and str(row.get("category")).strip()
                        else "—"
                    ),
                    "stock": float(row["current_inventory"]),
                    "demand": float(row["expected_demand_leadtime"]),
                    "gap": float(row["gap"]),
                    "status": row["status"],
                    "order_qty": float(row["recommended_order_qty"]),
                    "risk": row["stockout_risk"],
                    "explanation": str(row.get("explanation") or ""),
                }
            )
        vm.products = products

    # —— Budget ——
    # Ưu tiên ô Prepare; chưa lưu hồ sơ / chưa nhập → coi như chưa thiết lập (không lấy default YAML).
    if st.session_state.get("prep_budget") is not None:
        budget = float(st.session_state["prep_budget"])
    elif st.session_state.get("bp_profile_committed"):
        budget = float(profile.promotion_budget or 0)
    else:
        budget = 0.0
    allocated = _allocated_promo_cost()
    if budget <= 0:
        vm.budget_value = "Chưa thiết lập"
        vm.budget_support = "Chưa thiết lập ngân sách chiến dịch."
        budget_score = None
    elif allocated is None:
        vm.budget_value = compact_vnd(budget)
        vm.budget_support = "Chưa phân bổ — chưa có chi phí từ kịch bản Simulate."
        vm.budget_progress = None
        budget_score = 1.0  # ngân sách đã có, chưa vượt
    else:
        used_ratio = allocated / budget if budget else 0.0
        vm.budget_value = f"{compact_vnd(allocated)} / {compact_vnd(budget)}"
        vm.budget_support = f"Đã phân bổ {pct(min(used_ratio, 9.99), 0)}" if used_ratio <= 1 else "Vượt ngân sách hồ sơ"
        vm.budget_progress = min(used_ratio, 1.0)
        budget_score = 1.0 if allocated <= budget else 0.0

    # —— Margin ——
    margin_pct, margin_source = _actual_or_target_margin(profile, caps)
    vm.margin_label, vm.margin_kind = _margin_status(margin_pct, profile)
    if margin_pct is None:
        vm.margin_value = DASH
        vm.margin_support = "Chưa thể tính biên lợi nhuận dự kiến."
        margin_score = None
    else:
        # Chỉ hiện % — không ghép nhãn Healthy/Watch/Risk vào giá trị card.
        vm.margin_value = pct(margin_pct, 1)
        vm.margin_support = margin_source
        if margin_pct >= float(profile.target_margin_pct):
            margin_score = 1.0
        elif margin_pct >= float(profile.min_margin_pct):
            margin_score = 0.5
        else:
            margin_score = 0.0

    # —— Operational (logic cũ: không còn HIGH) ——
    if plan is None or (isinstance(plan, pd.DataFrame) and plan.empty):
        vm.ops_value = "Chưa đánh giá"
        vm.ops_support = "Chưa đánh giá năng lực vận hành."
        vm.ops_kind = "muted"
        ops_score = None
    else:
        high = int((plan["stockout_risk"] == "HIGH").sum())
        if high == 0:
            vm.ops_value = "Sẵn sàng"
            vm.ops_support = "Đáp ứng kế hoạch chiến dịch theo rủi ro hết hàng hiện tại."
            vm.ops_kind = "ok"
            ops_score = 1.0
        else:
            vm.ops_value = "Cần chú ý"
            vm.ops_support = f"{high} SKU rủi ro hết hàng cao — rà soát kho vận trước khi mô phỏng."
            vm.ops_kind = "warn"
            ops_score = 0.0

    # —— Issues (derive, không hard-code SKU) ——
    issues: list[dict] = []
    for item in vm.products:
        if item["risk"] == "HIGH":
            short = max(0.0, -item["gap"])
            issues.append(
                {
                    "title": f"{item['product_id']} thiếu {integer(short)} đơn vị",
                    "description": item["explanation"]
                    or "Tồn kho hiện tại không đáp ứng nhu cầu dự báo trong lead time.",
                    "severity": "critical",
                    "priority": 1,
                }
            )
        elif item["risk"] == "MEDIUM":
            issues.append(
                {
                    "title": f"{item['product_id']} sắp thiếu hàng",
                    "description": item["explanation"]
                    or "Ngày tồn kho nằm giữa lead time và safety stock.",
                    "severity": "warn",
                    "priority": 2,
                }
            )
    if margin_score == 0.0 and margin_pct is not None:
        issues.append(
            {
                "title": f"Biên lợi nhuận {pct(margin_pct, 1)} dưới mức tối thiểu",
                "description": f"Ngưỡng tối thiểu hồ sơ: {pct(profile.min_margin_pct, 0)}.",
                "severity": "critical",
                "priority": 0,
            }
        )
    if budget_score == 0.0 and allocated is not None:
        issues.append(
            {
                "title": "Chi phí khuyến mãi vượt ngân sách hồ sơ",
                "description": f"{compact_vnd(allocated)} so với ngân sách {compact_vnd(budget)}.",
                "severity": "critical",
                "priority": 0,
            }
        )
    issues.sort(key=lambda x: (x["priority"], x["title"]))
    # Giới hạn hiển thị, ưu tiên critical rồi warn
    critical = [i for i in issues if i["severity"] == "critical"]
    warn = [i for i in issues if i["severity"] == "warn"]
    vm.issues = (critical + warn)[:6]

    # —— Overall readiness [UI ADAPTER] ——
    scores = [s for s in (inv_score, budget_score, margin_score, ops_score) if s is not None]
    if not scores:
        vm.readiness_label = DASH
        vm.readiness_message = "Chưa đủ dữ liệu đánh giá"
        vm.readiness_tone = "muted"
        vm.cta_note = "Cần xử lý dữ liệu trước khi tiếp tục."
    else:
        overall = sum(scores) / len(scores)
        passed = sum(1 for s in scores if s >= 0.99)
        vm.readiness_progress = overall
        vm.readiness_label = pct(overall, 0)
        # Mapping UI nếu chưa có rule aggregate riêng: >=80 ready, 60–79 attention, <60 not ready
        if overall >= 0.80:
            vm.readiness_message = "Đã sẵn sàng cho giai đoạn mô phỏng"
            vm.readiness_tone = "ok"
            vm.cta_note = "Đã sẵn sàng? Cùng mô phỏng kịch bản!"
        elif overall >= 0.60:
            vm.readiness_message = "Vẫn còn vấn đề cần xử lý"
            vm.readiness_tone = "warn"
            vm.cta_note = "Còn một số vấn đề cần chú ý trước khi mô phỏng."
        else:
            vm.readiness_message = "Chưa sẵn sàng"
            vm.readiness_tone = "bad"
            vm.cta_note = "Cần xử lý các điều kiện bắt buộc trước khi tiếp tục."
        vm.inventory_note = f"{passed}/{len(scores)} kiểm tra đạt"

    # Workflow hiện tại luôn cho phép sang Simulate (override) — chỉ cảnh báo.
    vm.can_continue = True
    return vm


def _allocated_promo_cost() -> float | None:
    table = st.session_state.get("last_scenario_table")
    if table is None or "chi_phi_khuyen_mai" not in getattr(table, "columns", []):
        return None
    try:
        return float(table["chi_phi_khuyen_mai"].max())
    except (TypeError, ValueError):
        return None


def _actual_or_target_margin(profile, caps) -> tuple[float | None, str]:
    if caps.has_cost or caps.has_gross_profit:
        df = st.session_state.get("clean_df")
        if df is not None and not df.empty and "revenue" in df.columns:
            revenue = float(df["revenue"].sum())
            if "gross_profit" in df.columns and revenue:
                return float(df["gross_profit"].sum()) / revenue, "Biên từ dữ liệu bán (lợi nhuận gộp / doanh thu)."
    return float(profile.target_margin_pct), f"Margin mục tiêu hồ sơ (min {pct(profile.min_margin_pct, 0)})."


def _margin_status(margin_pct: float | None, profile) -> tuple[str, str | None]:
    if margin_pct is None:
        return "", None
    if margin_pct >= float(profile.target_margin_pct):
        return "Healthy", "ok"
    if margin_pct >= float(profile.min_margin_pct):
        return "Watch", "warn"
    return "At Risk", "bad"


def _render_view(vm: PrepareViewModel, empty: bool = False) -> None:
    # ROW 1 — KPI cards
    cards = [
        prepare_metric_card(
            "Tồn kho",
            "Sẵn sàng đáp ứng nhu cầu",
            vm.inventory_value,
            "boxes",
            supporting=vm.inventory_support,
            accent="green",
            progress=vm.inventory_progress,
        ),
        prepare_metric_card(
            "Ngân sách",
            "Ngân sách chiến dịch",
            vm.budget_value,
            "wallet",
            supporting=vm.budget_support,
            accent="purple",
            progress=vm.budget_progress,
        ),
        prepare_metric_card(
            "Biên lợi nhuận",
            "Dự kiến sau khuyến mãi",
            vm.margin_value,
            "percent",
            supporting=vm.margin_support,
            accent="pink",
        ),
        prepare_metric_card(
            "Năng lực vận hành",
            "Đội ngũ, kho vận, hệ thống",
            vm.ops_value,
            "settings",
            supporting=vm.ops_support,
            accent="orange",
        ),
    ]
    show(f'<div class="pp-prep-kpi-grid">{"".join(cards)}</div>')

    # ROW 2 — table (scroll) + summary; cột cân tỷ lệ ~3:1
    main, side = st.columns([2.4, 1], gap="medium")
    with main:
        _product_panel(vm, empty=empty)
    with side:
        show(
            readiness_score_card(
                "Mức độ sẵn sàng tổng thể",
                vm.readiness_label,
                vm.readiness_progress,
                vm.readiness_message,
                tone=vm.readiness_tone,
            )
        )
        st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)
        n = len(vm.issues)
        items_html = "".join(
            readiness_issue_item(i + 1, issue["title"], issue["description"], issue["severity"])
            for i, issue in enumerate(vm.issues)
        )
        if not vm.issues and not empty and vm.products:
            items_html = (
                '<div class="pp-issue-item severity-info">'
                '<div class="pp-issue-rank">✓</div>'
                "<div><div class=\"pp-issue-title\">Không có vấn đề nghiêm trọng</div>"
                "<div class=\"pp-issue-desc\">Không có SKU rủi ro hết hàng cao với tham số hiện tại.</div></div></div>"
            )
            subtitle = "Chưa phát hiện blocker với tham số hiện tại."
        else:
            subtitle = (
                f"{n} vấn đề cần được giải quyết trước khi tiếp tục"
                if n
                else EMPTY
            )
        show(readiness_issue_list("Vấn đề cần xử lý", subtitle, items_html))

    # ROW 3 — actions
    st.markdown(f'<p class="pp-prep-cta-note">{esc(vm.cta_note)}</p>', unsafe_allow_html=True)
    continue_button(
        "Tiếp tục đến Bước 4: Simulate →",
        "simulate",
        key="prep_next" if not empty else "prep_next_empty",
    )


def _product_panel(vm: PrepareViewModel, empty: bool = False) -> None:
    """Bảng trọng tâm: filter cố định phía trên, bảng scroll trong card (không khung đôi)."""
    if empty or not vm.products:
        show(
            product_readiness_table(
                ["Sản phẩm", "Danh mục", "Tồn kho hiện tại", "Nhu cầu dự báo", "Chênh lệch", "Trạng thái"],
                [],
                "Sản phẩm trọng tâm",
                "Kiểm tra tồn kho và mức độ sẵn sàng cho chiến dịch khuyến mãi",
            )
        )
        if not empty:
            st.caption("Chưa có kế hoạch tồn kho — bấm tính mức sẵn sàng ở trên.")
        return

    f1, f2 = st.columns([2, 1], gap="small")
    with f1:
        query = st.text_input(
            "Tìm kiếm sản phẩm",
            key="prep_search",
            label_visibility="collapsed",
            placeholder="Tìm kiếm sản phẩm...",
        )
    with f2:
        options = ["Tất cả danh mục", *vm.categories]
        cat = st.selectbox("Danh mục", options, key="prep_cat", label_visibility="collapsed")

    rows_data = vm.products
    if query:
        q = query.strip().lower()
        rows_data = [
            r for r in rows_data if q in r["product_id"].lower() or q in r["category"].lower()
        ]
    if cat and cat != "Tất cả danh mục":
        rows_data = [r for r in rows_data if r["category"] == cat]

    rows = []
    for item in rows_data[:40]:
        status = item["status"]
        rows.append(
            [
                esc_product(item["product_id"]),
                esc_product(item["category"]),
                esc_product(integer(item["stock"])),
                esc_product(integer(item["demand"])),
                gap_cell(item["gap"]),
                badge(status, STATUS_KIND.get(status, "muted")),
            ]
        )
    show(
        product_readiness_table(
            ["Sản phẩm", "Danh mục", "Tồn kho hiện tại", "Nhu cầu dự báo", "Chênh lệch", "Trạng thái"],
            rows,
            "Sản phẩm trọng tâm",
            "Kiểm tra tồn kho và mức độ sẵn sàng cho chiến dịch khuyến mãi",
        )
    )


def esc_product(value) -> str:
    return esc(value)
