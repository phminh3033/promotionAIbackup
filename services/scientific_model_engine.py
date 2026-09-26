"""Lớp bọc các mô hình khoa học đang có. Không viết lại công thức."""
from __future__ import annotations

import pandas as pd

from src.forecasting.selector import select_and_forecast
from src.inventory.planning import plan_inventory_for_all_skus, plan_sku_inventory
from src.optimization.objective import score_scenarios
from src.promotion.mechanics import estimate_historical_uplift
from src.promotion.rules import evaluate_sku_rules, max_allowed_depth
from src.promotion.simulator import simulate_scenarios
from src.recommendation.engine import build_recommendation_card
from src.segmentation.clustering import run_segmentation
from src.segmentation.rfm import compute_rfm


class ScientificModelEngine:
    def forecast(self, y: pd.Series, horizon: int, series_name: str):
        return select_and_forecast(y, horizon=horizon, series_name=series_name)

    def segment_customers(self, df: pd.DataFrame):
        scoped = df[df["customer_id"] != "KHACH_LE"] if "KHACH_LE" in set(df["customer_id"].astype(str)) else df
        rfm = compute_rfm(scoped)
        return rfm, run_segmentation(rfm)

    def inventory_plan(self, demand_by_sku, inventory_by_sku, lead_time_days, safety_stock_days):
        return plan_inventory_for_all_skus(demand_by_sku, inventory_by_sku, lead_time_days, safety_stock_days)

    def sku_inventory(self, product_id, avg_daily_demand, current_inventory, lead_time_days, safety_stock_days):
        return plan_sku_inventory(product_id, avg_daily_demand, current_inventory, lead_time_days, safety_stock_days)

    def historical_uplift(self, df):
        return estimate_historical_uplift(df)

    def rules(self, ctx, min_margin_pct, max_discount_pct):
        return evaluate_sku_rules(ctx, min_margin_pct, max_discount_pct)

    def depth(self, mechanic, unit_cost, price, min_margin_pct, max_discount_pct):
        return max_allowed_depth(mechanic, unit_cost, price, min_margin_pct, max_discount_pct)

    def simulate(
        self,
        baseline,
        historical_uplifts,
        gift_cost_per_unit,
        max_discount_overrides,
        scenarios=None,
        allowed_mechanics=None,
        max_discount_pct=0.3,
    ):
        return simulate_scenarios(
            baseline,
            historical_uplifts=historical_uplifts,
            scenarios=scenarios,
            gift_cost_per_unit=gift_cost_per_unit,
            max_discount_overrides=max_discount_overrides,
            allowed_mechanics=allowed_mechanics,
            max_discount_pct=max_discount_pct,
        )

    def score(self, table, objective, current_inventory=None):
        return score_scenarios(table, objective, current_inventory=current_inventory)

    def recommend(self, **kwargs):
        return build_recommendation_card(**kwargs)
