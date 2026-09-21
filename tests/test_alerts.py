from src.alerts.engine import Alert, decide_action, evaluate_alerts


def test_no_alerts_when_all_within_normal_range():
    alerts = evaluate_alerts(
        cumulative_revenue_variance=0.02,
        current_margin_pct=0.25,
        min_margin_pct=0.15,
        days_of_inventory=10,
        cumulative_customers_variance=0.05,
        inventory_vs_forecast_ratio=1.0,
        actual_roi=0.30,
        min_roi_pct=0.20,
    )
    assert len(alerts) == 1
    assert alerts[0].code == "ON_TRACK"


def test_revenue_below_forecast_triggers_warning():
    alerts = evaluate_alerts(
        cumulative_revenue_variance=-0.25,  # doanh thu thấp hơn dự báo 25% -> dưới ngưỡng 20%
        current_margin_pct=0.25,
        min_margin_pct=0.15,
        days_of_inventory=10,
        cumulative_customers_variance=0.0,
        inventory_vs_forecast_ratio=1.0,
        actual_roi=0.30,
        min_roi_pct=0.20,
    )
    codes = [a.code for a in alerts]
    assert "REVENUE_BELOW_FORECAST" in codes


def test_margin_below_minimum_triggers_critical():
    alerts = evaluate_alerts(
        cumulative_revenue_variance=0.0,
        current_margin_pct=0.10,
        min_margin_pct=0.15,
        days_of_inventory=10,
        cumulative_customers_variance=0.0,
        inventory_vs_forecast_ratio=1.0,
        actual_roi=0.30,
        min_roi_pct=0.20,
    )
    margin_alert = next(a for a in alerts if a.code == "MARGIN_BELOW_MINIMUM")
    assert margin_alert.level == "critical"


def test_stockout_risk_triggers_critical():
    alerts = evaluate_alerts(
        cumulative_revenue_variance=0.0,
        current_margin_pct=0.25,
        min_margin_pct=0.15,
        days_of_inventory=1.5,
        cumulative_customers_variance=0.0,
        inventory_vs_forecast_ratio=1.0,
        actual_roi=0.30,
        min_roi_pct=0.20,
    )
    stockout_alert = next(a for a in alerts if a.code == "STOCKOUT_RISK")
    assert stockout_alert.level == "critical"


def test_staffing_alert_when_traffic_much_higher():
    alerts = evaluate_alerts(
        cumulative_revenue_variance=0.0,
        current_margin_pct=0.25,
        min_margin_pct=0.15,
        days_of_inventory=10,
        cumulative_customers_variance=0.40,
        inventory_vs_forecast_ratio=1.0,
        actual_roi=0.30,
        min_roi_pct=0.20,
    )
    codes = [a.code for a in alerts]
    assert "STAFFING_ALERT" in codes


def test_overstock_alert():
    alerts = evaluate_alerts(
        cumulative_revenue_variance=0.0,
        current_margin_pct=0.25,
        min_margin_pct=0.15,
        days_of_inventory=10,
        cumulative_customers_variance=0.0,
        inventory_vs_forecast_ratio=1.8,
        actual_roi=0.30,
        min_roi_pct=0.20,
    )
    codes = [a.code for a in alerts]
    assert "OVERSTOCK_ALERT" in codes


def test_decide_action_stop_when_two_critical_alerts():
    alerts = [
        Alert("critical", "MARGIN_BELOW_MINIMUM", "margin thấp"),
        Alert("critical", "STOCKOUT_RISK", "sắp hết hàng"),
    ]
    result = decide_action(alerts, cumulative_revenue_variance=-0.3, cumulative_customers_variance=0.0, actual_roi=0.05, min_roi_pct=0.20)
    assert result.action == "STOP"


def test_decide_action_scale_when_strong_positive_and_no_warnings():
    alerts = [Alert("info", "ON_TRACK", "ổn định")]
    result = decide_action(alerts, cumulative_revenue_variance=0.25, cumulative_customers_variance=0.20, actual_roi=0.30, min_roi_pct=0.20)
    assert result.action == "SCALE"


def test_decide_action_continue_when_nothing_unusual():
    alerts = [Alert("info", "ON_TRACK", "ổn định")]
    result = decide_action(alerts, cumulative_revenue_variance=0.02, cumulative_customers_variance=0.0, actual_roi=0.22, min_roi_pct=0.20)
    assert result.action == "CONTINUE"


def test_decide_action_adjust_when_warning_only():
    alerts = [Alert("warning", "REVENUE_BELOW_FORECAST", "doanh thu thấp hơn dự báo")]
    result = decide_action(alerts, cumulative_revenue_variance=-0.15, cumulative_customers_variance=0.0, actual_roi=0.18, min_roi_pct=0.20)
    assert result.action == "ADJUST"
