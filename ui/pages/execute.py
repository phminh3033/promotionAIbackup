"""Execute: kế hoạch từ generate_execution_plan và khởi tạo campaign như luồng cũ."""
from __future__ import annotations

import io
from datetime import date

import pandas as pd
import streamlit as st

from src.execution.plan import generate_execution_plan, tasks_to_dataframe
from src.learning.campaign_log import CampaignRecord, new_campaign_id, save_campaign_record
from src.recommendation.campaign import generate_campaign_plan, is_llm_enabled
from ui.components import DASH, EMPTY, badge, bullets, card, defs, grid, kicker, kicker_raw, muted, placeholder_table, progress, show
from ui.formatters import integer, vnd
from ui.nav import goto
from ui.shell import render_shell


def render() -> None:
    render_shell("Execute", "Tạo kế hoạch thực thi và checklist công việc.", stage=6)
    card = st.session_state.get("last_recommendation_card")
    if card is None:
        left, right = st.columns([0.9, 1.3], gap="medium")
        with left:
            show(card(kicker("Thông tin chiến dịch") + defs([
                ("Tên chiến dịch", DASH),
                ("Thời gian triển khai", EMPTY),
                ("Phạm vi", DASH),
                ("Ngân sách dự kiến", DASH),
                ("Cơ chế ưu đãi", EMPTY),
            ])))
        with right:
            show(kicker("Danh sách công việc thực thi"))
            show(placeholder_table(["Công việc", "Phụ trách", "Hạn hoàn thành", "Trạng thái"]))
        show(grid([
            card(kicker("Mức độ sẵn sàng chiến dịch") + progress(0) + muted(DASH)),
            card(kicker("Checklist trước khi khởi động") + muted(EMPTY)),
        ], columns=2, style="margin-top:12px"))
        return
    profile = st.session_state["business_profile"]
    meta = st.session_state.get("last_scenario_meta") or {}
    left, right = st.columns([0.9, 1.3], gap="medium")
    with left:
        start = st.date_input("Ngày khởi chạy", value=date.today(), key="ex_start")
        show(card(
            kicker("Thông tin chiến dịch")
            + defs([
                ("Tên", card.promotion_label),
                ("Thời gian gợi ý", card.timing_text),
                ("Phạm vi", card.product_focus),
                ("Ngân sách hồ sơ", vnd(profile.promotion_budget)),
                ("Cơ chế", card.promotion_label),
            ])
            + muted(f"Mục tiêu: {card.objective_vi}. Tồn kho đề xuất {integer(card.recommended_stock)}.")
        ))
    with right:
        if st.button("Tạo kế hoạch từ phương án đã chọn", type="primary", key="build_plan"):
            tasks = generate_execution_plan(
                campaign_start=pd.Timestamp(start),
                product_focus=card.product_focus,
                promotion_label=card.promotion_label,
                recommended_stock=card.recommended_stock,
                objective_vi=card.objective_vi,
            )
            st.session_state["last_execution_plan"] = tasks_to_dataframe(tasks)
            st.session_state["last_campaign_plan"] = generate_campaign_plan(
                card,
                business_name=profile.business_name,
                service_capacity_per_staff_per_hour=profile.service_capacity_per_staff_per_hour,
            )
        plan_df = st.session_state.get("last_execution_plan")
        if plan_df is None:
            st.info("Bấm tạo kế hoạch để sinh checklist theo mốc D-7 đến D+7.")
        else:
            edited = st.data_editor(plan_df, width="stretch", hide_index=True, num_rows="fixed", key="exec_editor")
            st.session_state["execution_editor_df"] = edited
            _readiness(edited)
    _actions(card, profile, start, meta)


def _readiness(edited: pd.DataFrame) -> None:
    done = int((edited["Trạng thái"] == "Hoàn thành").sum()) if "Trạng thái" in edited.columns else 0
    total = max(len(edited), 1)
    ratio = done / total
    checks = [
        f"{'✓' if row['Trạng thái'] == 'Hoàn thành' else '○'} {row['Công việc']}"
        for _, row in edited.head(6).iterrows()
    ]
    show(card(
        kicker_raw(f"Mức độ sẵn sàng chiến dịch {badge(f'{done}/{total}', 'info')}")
        + progress(ratio)
        + bullets(checks)
        + muted("Đổi cột Trạng thái trong bảng rồi bấm lưu ở dưới. Đây là checklist nội bộ, chưa nối hệ thống ticket."),
        style="margin-top:12px",
    ))


def _actions(card, profile, start, meta) -> None:
    plan = st.session_state.get("last_campaign_plan")
    c1, c2 = st.columns(2)
    with c1:
        tasks_df = st.session_state.get("execution_editor_df")
        if tasks_df is None:
            tasks_df = st.session_state.get("last_execution_plan")
        if tasks_df is not None:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                tasks_df.to_excel(writer, sheet_name="Execution Plan", index=False)
                if plan is not None:
                    pd.DataFrame(
                        {"Kênh": ["Facebook", "Zalo", "SMS"], "Nội dung": [plan.fb_copy, plan.zalo_copy, plan.sms_copy]}
                    ).to_excel(writer, sheet_name="Noi dung", index=False)
            st.download_button(
                "Xuất kế hoạch",
                data=buffer.getvalue(),
                file_name="promotionpilot_execution_plan.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width="stretch",
            )
    with c2:
        if st.button("Bắt đầu chiến dịch", type="primary", key="start_campaign", width="stretch"):
            if st.session_state.get("last_execution_plan") is None:
                st.error("Hãy tạo kế hoạch trước khi khởi chạy.")
            else:
                _persist_campaign(card, start, meta)
    if plan is not None:
        note = "Nội dung marketing dùng template rule-based."
        if is_llm_enabled():
            note = "Đã thấy cấu hình LLM, nhưng bản này vẫn dùng template rule-based cho nội dung."
        with st.expander("Nội dung marketing (Facebook, Zalo, SMS)"):
            st.caption(note)
            st.text_area("Facebook", plan.fb_copy, height=120)
            st.text_area("Zalo", plan.zalo_copy, height=100)
            st.text_area("SMS", plan.sms_copy, height=70)


def _persist_campaign(card, start, meta) -> None:
    promo_days = meta.get("promo_days")
    scenario_table = st.session_state.get("last_scenario_table")
    no_promo_gp_per_day = None
    if scenario_table is not None and promo_days:
        no_promo_rows = scenario_table[scenario_table["mechanic"] == "no_promo"]
        if not no_promo_rows.empty:
            no_promo_gp_per_day = float(no_promo_rows.iloc[0]["loi_nhuan_gop"]) / promo_days
    record = CampaignRecord(
        campaign_id=new_campaign_id(),
        objective=card.objective_vi,
        product_focus=card.product_focus,
        promotion_label=card.promotion_label,
        forecast={
            "expected_revenue_range": list(card.expected_revenue_range),
            "expected_gp_range": list(card.expected_gp_range),
            "expected_customers_range": list(card.expected_customers_range),
            "expected_demand_range": list(card.expected_demand_range),
            "expected_roi_range": list(card.expected_roi_range) if card.expected_roi_range else None,
            "campaign_start": str(start),
            "promo_days": promo_days,
            "no_promo_gp_per_day": no_promo_gp_per_day,
        },
        roi_forecast=sum(card.expected_roi_range) / 2 if card.expected_roi_range else None,
    )
    save_campaign_record(record)
    st.session_state["active_campaign_id"] = record.campaign_id
    if st.session_state.get("execution_editor_df") is not None:
        st.session_state["last_execution_plan"] = st.session_state["execution_editor_df"]
    st.success(f"Đã khởi tạo {record.campaign_id}. Sang Monitor để nhập số thực tế.")
    goto("monitor")
