"""Sinh dữ liệu demo SME thực tế (mục XXVI yêu cầu gốc): data/demo_sme_sales.csv.

Dữ liệu được sinh có LOGIC (không random hoàn toàn):
- Seasonality: cao điểm Tết (giữa T1-đầu T2), back-to-school (T8-T9), cuối năm (T11-T12).
- Weekend effect: Thứ 6/7/CN cao hơn ngày thường.
- Xu hướng tăng trưởng nhẹ theo thời gian.
- ~14 đợt khuyến mãi thật (discount/bogo/bundle/gift) trên các SKU cụ thể, có uplift thực sự
  áp dụng vào dữ liệu để module "historical uplift" có tín hiệu thật để học.
- Khách hàng có 5 phân khúc hành vi khác nhau (mua thường xuyên, ít mua, mới, rời bỏ...).
- Tồn kho giảm dần theo bán hàng và được nhập bổ sung định kỳ (replenishment).
- Một số cặp SKU có "ái lực" mua cùng nhau cao hơn để Market Basket Analysis tìm được luật thật.

Chạy: python scripts/generate_demo_data.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

RNG = np.random.default_rng(42)

START_DATE = pd.Timestamp("2025-01-01")
END_DATE = pd.Timestamp("2026-09-19")
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "demo_sme_sales.csv"

STORES = ["CH01", "CH02"]
STORE_WEIGHTS = [0.68, 0.32]

CATEGORIES = {
    "Đồ uống": {"n_sku": 10, "price_range": (8_000, 35_000), "margin_range": (0.15, 0.28)},
    "Bánh kẹo": {"n_sku": 9, "price_range": (10_000, 45_000), "margin_range": (0.20, 0.35)},
    "Thực phẩm khô": {"n_sku": 9, "price_range": (15_000, 90_000), "margin_range": (0.18, 0.30)},
    "Hóa mỹ phẩm": {"n_sku": 9, "price_range": (25_000, 150_000), "margin_range": (0.25, 0.45)},
    "Đồ gia dụng": {"n_sku": 8, "price_range": (30_000, 250_000), "margin_range": (0.20, 0.40)},
    "Văn phòng phẩm": {"n_sku": 8, "price_range": (5_000, 60_000), "margin_range": (0.25, 0.40)},
    "Mẹ & bé": {"n_sku": 8, "price_range": (20_000, 220_000), "margin_range": (0.20, 0.38)},
    "Chăm sóc cá nhân": {"n_sku": 8, "price_range": (15_000, 180_000), "margin_range": (0.28, 0.48)},
}

N_CUSTOMERS = 2500
BASE_DAILY_TXN = 42

# [BUSINESS RULE demo]: hệ số theo thứ trong tuần
WEEKDAY_MULT = {0: 0.95, 1: 0.95, 2: 1.0, 3: 1.0, 4: 1.15, 5: 1.4, 6: 1.25}


def build_sku_catalog() -> pd.DataFrame:
    rows = []
    sku_counter = 1
    for cat, cfg in CATEGORIES.items():
        for i in range(cfg["n_sku"]):
            price = int(RNG.uniform(*cfg["price_range"]) / 500) * 500
            margin = RNG.uniform(*cfg["margin_range"])
            cost = round(price * (1 - margin))
            popularity = RNG.pareto(a=1.8) + 0.3  # phân phối lệch: vài SKU bán rất chạy
            rows.append(
                {
                    "product_id": f"SP{sku_counter:03d}",
                    "category": cat,
                    "price": price,
                    "cost": cost,
                    "popularity": popularity,
                }
            )
            sku_counter += 1
    catalog = pd.DataFrame(rows)
    catalog["popularity"] = catalog["popularity"] / catalog["popularity"].sum()
    return catalog


def build_affinity_pairs(catalog: pd.DataFrame, n_pairs: int = 12) -> dict[str, str]:
    """Một số SKU trong cùng category có xu hướng được mua cùng nhau cao hơn bình thường."""
    pairs: dict[str, str] = {}
    for cat, group in catalog.groupby("category"):
        skus = group["product_id"].tolist()
        if len(skus) < 2:
            continue
        a, b = RNG.choice(skus, size=2, replace=False)
        pairs[a] = b
    return pairs


def build_customers() -> pd.DataFrame:
    segment_probs = {"loyal": 0.08, "frequent": 0.17, "occasional": 0.50, "new": 0.15, "at_risk": 0.10}
    segments = RNG.choice(list(segment_probs.keys()), size=N_CUSTOMERS, p=list(segment_probs.values()))

    join_days = np.where(
        segments == "new",
        RNG.integers(int((END_DATE - START_DATE).days * 0.55), (END_DATE - START_DATE).days, size=N_CUSTOMERS),
        RNG.integers(0, int((END_DATE - START_DATE).days * 0.3), size=N_CUSTOMERS),
    )
    join_dates = START_DATE + pd.to_timedelta(join_days, unit="D")

    churn_days = np.where(
        segments == "at_risk",
        RNG.integers(int((END_DATE - START_DATE).days * 0.3), int((END_DATE - START_DATE).days * 0.75), size=N_CUSTOMERS),
        (END_DATE - START_DATE).days + 1,
    )
    churn_dates = START_DATE + pd.to_timedelta(churn_days, unit="D")

    activity_weight = {"loyal": 5.0, "frequent": 3.0, "occasional": 1.0, "new": 1.2, "at_risk": 0.8}
    weights = np.array([activity_weight[s] for s in segments])

    aov_mult = {"loyal": 1.3, "frequent": 1.1, "occasional": 0.9, "new": 0.85, "at_risk": 0.9}
    aov = np.array([aov_mult[s] * RNG.uniform(0.85, 1.15) for s in segments])

    return pd.DataFrame(
        {
            "customer_id": [f"KH{i:05d}" for i in range(1, N_CUSTOMERS + 1)],
            "segment": segments,
            "join_date": join_dates,
            "churn_date": churn_dates,
            "activity_weight": weights,
            "aov_mult": aov,
        }
    )


def seasonality_multiplier(date: pd.Timestamp) -> float:
    m, d = date.month, date.day
    mult = 1.0
    if (m == 1 and d >= 15) or (m == 2 and d <= 10):
        mult *= 1.75  # cao điểm Tết
    elif m in (8, 9):
        mult *= 1.15  # back to school
    elif m in (11, 12):
        mult *= 1.3  # cuối năm
    elif m in (6, 7):
        mult *= 0.9  # mùa thấp điểm
    return mult


def build_promotions(catalog: pd.DataFrame) -> pd.DataFrame:
    mechanics = ["discount_percent", "discount_percent", "bogo", "bundle", "gift"]
    discount_values = {"discount_percent": [0.05, 0.10, 0.15], "bogo": [0.5], "bundle": [0.12], "gift": [0.0]}
    n_promos = 16
    total_days = (END_DATE - START_DATE).days
    rows = []
    for i in range(n_promos):
        start_offset = int(RNG.uniform(10, total_days - 15))
        duration = int(RNG.integers(4, 10))
        start = START_DATE + pd.Timedelta(days=start_offset)
        end = start + pd.Timedelta(days=duration)
        mechanic = RNG.choice(mechanics)
        discount = RNG.choice(discount_values[mechanic])
        n_skus_in_promo = int(RNG.integers(1, 4))
        skus = RNG.choice(catalog["product_id"], size=n_skus_in_promo, replace=False)
        for sku in skus:
            rows.append(
                {
                    "promotion_id": f"KM{i+1:03d}",
                    "product_id": sku,
                    "promotion_type": mechanic,
                    "discount": discount,
                    "start": start,
                    "end": end,
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    from src.promotion.mechanics import default_unit_uplift

    catalog = build_sku_catalog()
    affinity = build_affinity_pairs(catalog)
    customers = build_customers()
    promotions = build_promotions(catalog)

    dates = pd.date_range(START_DATE, END_DATE, freq="D")
    total_days = len(dates)

    inventory = {row.product_id: int(RNG.uniform(150, 500)) for row in catalog.itertuples()}
    target_stock = {k: v for k, v in inventory.items()}
    days_since_restock = {k: 0 for k in inventory}

    promo_by_sku_active: dict[str, list[dict]] = {}
    for _, p in promotions.iterrows():
        promo_by_sku_active.setdefault(p["product_id"], []).append(p.to_dict())

    catalog_indexed = catalog.set_index("product_id")
    price_map = catalog_indexed["price"].to_dict()
    cost_map = catalog_indexed["cost"].to_dict()
    category_map = catalog_indexed["category"].to_dict()
    popularity_map = catalog_indexed["popularity"].to_dict()
    sku_list = catalog["product_id"].tolist()
    base_pop = np.array([popularity_map[s] for s in sku_list])

    customers_active_pool = customers.copy()

    rows = []
    txn_counter = 1

    for day_idx, day in enumerate(dates):
        weekday_mult = WEEKDAY_MULT[day.weekday()]
        season_mult = seasonality_multiplier(day)
        trend_mult = 1.0 + 0.25 * (day_idx / total_days)
        noise = RNG.lognormal(mean=0, sigma=0.12)
        lam = BASE_DAILY_TXN * weekday_mult * season_mult * trend_mult * noise
        n_txn_today = RNG.poisson(lam)

        active_promos_today = {
            sku: p for sku, plist in promo_by_sku_active.items() for p in plist if p["start"] <= day <= p["end"]
        }

        pop_today = base_pop.copy()
        for sku, promo in active_promos_today.items():
            idx = sku_list.index(sku)
            uplift = default_unit_uplift(promo["promotion_type"], promo["discount"])
            pop_today[idx] *= (1 + uplift) * RNG.uniform(0.85, 1.15)
        pop_today = pop_today / pop_today.sum()

        active_customers = customers_active_pool[
            (customers_active_pool["join_date"] <= day) & (customers_active_pool["churn_date"] >= day)
        ]
        if active_customers.empty:
            continue
        cust_weights = active_customers["activity_weight"].values
        cust_weights = cust_weights / cust_weights.sum()

        for _ in range(n_txn_today):
            store = RNG.choice(STORES, p=STORE_WEIGHTS)
            if RNG.random() < 0.93:
                cust_row = active_customers.iloc[RNG.choice(len(active_customers), p=cust_weights)]
                customer_id = cust_row["customer_id"]
                aov_mult = cust_row["aov_mult"]
            else:
                customer_id = "KHACH_LE"
                aov_mult = 1.0

            n_items = RNG.choice([1, 2, 3, 4], p=[0.55, 0.28, 0.12, 0.05])
            chosen_skus: list[str] = []
            first_sku = RNG.choice(sku_list, p=pop_today)
            chosen_skus.append(first_sku)
            if first_sku in affinity and n_items > 1 and RNG.random() < 0.55:
                chosen_skus.append(affinity[first_sku])
                n_items -= 1
            while len(chosen_skus) < n_items:
                candidate = RNG.choice(sku_list, p=pop_today)
                if candidate not in chosen_skus:
                    chosen_skus.append(candidate)

            txn_id = f"HD{txn_counter:07d}"
            txn_time = day + pd.Timedelta(
                hours=int(RNG.integers(8, 21)), minutes=int(RNG.integers(0, 60))
            )

            for sku in chosen_skus:
                qty = RNG.choice([1, 2, 3, 4, 5], p=[0.68, 0.17, 0.08, 0.05, 0.02])
                price = price_map[sku]
                cost = cost_map[sku]

                promo = active_promos_today.get(sku)
                if promo:
                    mech = promo["promotion_type"]
                    depth = promo["discount"]
                    if mech == "discount_percent":
                        eff_price = price * (1 - depth)
                    elif mech == "bogo":
                        eff_price = price * 0.5
                    elif mech == "bundle":
                        eff_price = price * (1 - depth)
                    else:
                        eff_price = price
                else:
                    eff_price = price

                revenue = round(qty * eff_price * aov_mult)
                inventory[sku] = max(0, inventory[sku] - qty)
                current_inv = inventory[sku]

                rows.append(
                    {
                        "Ngày": txn_time,
                        "Mã hóa đơn": txn_id,
                        "Mã khách hàng": customer_id,
                        "Mã cửa hàng": store,
                        "Mã sản phẩm": sku,
                        "Danh mục": category_map[sku],
                        "Số lượng": qty,
                        "Đơn giá": price,
                        "Giá vốn": cost,
                        "Doanh thu": revenue,
                        "Tồn kho": current_inv,
                        "Mã khuyến mãi": promo["promotion_id"] if promo else "",
                        "Loại khuyến mãi": promo["promotion_type"] if promo else "",
                        "Giảm giá": promo["discount"] if promo else "",
                        "Ngày bắt đầu khuyến mãi": promo["start"].date() if promo else "",
                        "Ngày kết thúc khuyến mãi": promo["end"].date() if promo else "",
                    }
                )
            txn_counter += 1

        for sku in sku_list:
            days_since_restock[sku] += 1
            if inventory[sku] < target_stock[sku] * 0.25 or days_since_restock[sku] > 21:
                inventory[sku] = target_stock[sku] + int(RNG.uniform(-30, 60))
                days_since_restock[sku] = 0

    df = pd.DataFrame(rows)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    print(f"Đã sinh {len(df):,} dòng, {df['Mã hóa đơn'].nunique():,} giao dịch, "
          f"{df['Mã sản phẩm'].nunique()} SKU, {df['Mã khách hàng'].nunique()} khách hàng.")
    print(f"Khoảng thời gian: {df['Ngày'].min()} -> {df['Ngày'].max()}")
    print(f"File lưu tại: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
