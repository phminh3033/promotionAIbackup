import pandas as pd

from src.execution.plan import generate_execution_plan, tasks_to_dataframe


def test_generate_execution_plan_spans_d7_before_to_d7_after():
    tasks = generate_execution_plan(
        campaign_start=pd.Timestamp("2026-12-20"),
        product_focus="Vitamin C",
        promotion_label="Combo -10%",
        recommended_stock=500,
        objective_vi="Tăng Doanh thu",
    )
    offsets = [t.day_offset for t in tasks]
    assert min(offsets) == -7
    assert max(offsets) == 7
    assert 0 in offsets


def test_execution_plan_due_dates_relative_to_campaign_start():
    start = pd.Timestamp("2026-12-20")
    tasks = generate_execution_plan(start, "SP01", "Discount 10%", 100, "Tăng Doanh thu")
    launch_task = next(t for t in tasks if t.day_offset == 0)
    assert launch_task.due_date == start

    d_minus_7 = next(t for t in tasks if t.day_offset == -7)
    assert d_minus_7.due_date == start - pd.Timedelta(days=7)


def test_tasks_to_dataframe_has_expected_columns():
    tasks = generate_execution_plan(pd.Timestamp("2026-12-20"), "SP01", "BOGO", 200, "Kéo Traffic")
    df = tasks_to_dataframe(tasks)
    assert list(df.columns) == ["Mốc", "Ngày", "Phòng ban", "Công việc", "Phụ trách", "Mức độ ưu tiên", "Trạng thái"]
    assert len(df) == len(tasks)


def test_all_tasks_reference_valid_teams():
    from src.execution.plan import TEAMS

    tasks = generate_execution_plan(pd.Timestamp("2026-12-20"), "SP01", "Gift", 300, "Tăng Lợi nhuận")
    for t in tasks:
        assert t.team in TEAMS
