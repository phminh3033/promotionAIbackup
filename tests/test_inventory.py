from src.inventory.planning import plan_sku_inventory


def test_recommended_order_qty_formula():
    # avg_daily_demand=10, lead_time=5 -> expected_demand=50, safety_stock_days=7 -> safety=70
    # current=80, incoming=0 -> order = 50+70-80-0 = 40
    rec = plan_sku_inventory("SP01", avg_daily_demand=10, current_inventory=80, lead_time_days=5, safety_stock_days=7)
    assert rec.expected_demand_leadtime == 50.0
    assert rec.safety_stock == 70.0
    assert rec.recommended_order_qty == 40.0


def test_no_order_needed_when_inventory_sufficient():
    rec = plan_sku_inventory("SP01", avg_daily_demand=10, current_inventory=500, lead_time_days=5, safety_stock_days=7)
    assert rec.recommended_order_qty == 0.0
    assert rec.overstock_risk in ("MEDIUM", "HIGH")


def test_stockout_risk_high_when_inventory_below_leadtime_demand():
    rec = plan_sku_inventory("SP01", avg_daily_demand=10, current_inventory=20, lead_time_days=5, safety_stock_days=7)
    assert rec.stockout_risk == "HIGH"


def test_zero_demand_does_not_crash():
    rec = plan_sku_inventory("SP01", avg_daily_demand=0, current_inventory=50, lead_time_days=5, safety_stock_days=7)
    assert rec.recommended_order_qty == 0.0
    assert "không có nhu cầu" in rec.explanation


def test_incoming_inventory_reduces_order_qty():
    rec1 = plan_sku_inventory("SP01", avg_daily_demand=10, current_inventory=0, lead_time_days=5, safety_stock_days=0)
    rec2 = plan_sku_inventory(
        "SP01", avg_daily_demand=10, current_inventory=0, lead_time_days=5, safety_stock_days=0, incoming_inventory=20
    )
    assert rec2.recommended_order_qty == rec1.recommended_order_qty - 20
