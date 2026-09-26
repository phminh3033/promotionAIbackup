"""Kiểm tra nhanh toàn bộ pipeline end-to-end bằng dữ liệu demo (không phải pytest chính thức)."""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from src.data.loader import load_raw_file
from src.data.mapper import apply_mapping, detect_capabilities, suggest_mapping, validate_mapping
from src.data.quality import run_quality_check
from src.features.engineering import aggregate_daily
from src.forecasting.selector import select_and_forecast
from src.segmentation.rfm import compute_rfm
from src.segmentation.clustering import run_segmentation
from src.basket.market_basket import run_market_basket_analysis
from src.promotion.mechanics import BaselineMetrics, estimate_historical_uplift
from src.promotion.simulator import simulate_scenarios
from src.roi.calculator import compute_roi_breakdown
from src.optimization.objective import score_scenarios, pick_best_scenario
from src.inventory.planning import plan_sku_inventory

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "demo_sme_sales.csv"


def main():
    t0 = time.time()
    raw_bytes = DATA_PATH.read_bytes()
    raw_df = load_raw_file(raw_bytes, "demo_sme_sales.csv")
    print(f"[1] Load raw: {raw_df.shape}")

    mapping = suggest_mapping(list(raw_df.columns))
    errors = validate_mapping(mapping)
    assert not errors, f"Mapping lỗi: {errors}"
    print(f"[2] Mapping tự động OK: {mapping}")

    df = apply_mapping(raw_df, mapping)
    caps = detect_capabilities(df)
    print(f"[3] Capabilities: {caps}")

    clean_df, report = run_quality_check(df)
    print(f"[4] Quality score: {report.score} ({report.score_label}), rows clean={len(clean_df)}")

    daily = aggregate_daily(clean_df)
    y = daily.set_index("day")["revenue"]
    fr = select_and_forecast(y, horizon=14, series_name="Doanh thu toàn công ty")
    print(f"[5] Forecast model: {fr.model_name}, WAPE={fr.wape:.2%}, confidence={fr.confidence}")
    print(f"    Forecast 14 ngày đầu: {fr.yhat[:5].round(0)}")

    rfm = compute_rfm(clean_df)
    seg = run_segmentation(rfm)
    print(f"[6] Segmentation: k={seg.k}, silhouette={seg.silhouette:.2f}, msg={seg.message}")
    print(seg.cluster_summary)

    basket = run_market_basket_analysis(clean_df)
    print(f"[7] Basket rules: {len(basket.rules)} luật. {basket.message}")
    if not basket.rules.empty:
        print(basket.rules.head(5))

    hist_uplift = estimate_historical_uplift(clean_df)
    print(f"[8] Historical uplift estimates: {hist_uplift}")

    sample_sku = clean_df["product_id"].value_counts().idxmax()
    sku_df = clean_df[clean_df["product_id"] == sample_sku]
    avg_daily_units = sku_df.groupby(sku_df["date"].dt.normalize())["quantity"].sum().mean()
    baseline = BaselineMetrics(
        avg_daily_units=avg_daily_units,
        avg_price=sku_df["selling_price"].mean(),
        unit_cost=sku_df["cost"].mean(),
        promo_days=5,
        avg_daily_customers=sku_df.groupby(sku_df["date"].dt.normalize())["customer_id"].nunique().mean(),
    )
    sim = simulate_scenarios(
        baseline,
        historical_uplifts=hist_uplift,
        allowed_mechanics=["discount_percent", "bogo", "bundle", "gift"],
        max_discount_pct=0.15,
        max_discount_overrides={"discount_percent": 0.15, "bundle": 0.12},
    )
    roi_table = compute_roi_breakdown(sim.table, baseline)
    print(f"[9] Scenario simulation cho SKU {sample_sku}:")
    print(roi_table[["scenario", "san_luong", "doanh_thu", "loi_nhuan_gop", "roi"]])

    for obj in ["TRAFFIC", "REVENUE", "PROFIT", "CLEARANCE"]:
        best = pick_best_scenario(sim.table, obj, min_margin_pct=0.10)
        print(f"    Objective={obj} -> Best scenario = {best['scenario'] if best is not None else None}")

    current_inv = sku_df.sort_values("date")["inventory"].iloc[-1]
    inv_rec = plan_sku_inventory(sample_sku, avg_daily_units, current_inv, lead_time_days=5, safety_stock_days=7)
    print(f"[10] Inventory rec: {inv_rec}")

    print(f"\nTổng thời gian chạy: {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
