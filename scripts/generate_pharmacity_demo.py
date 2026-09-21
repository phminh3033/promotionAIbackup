"""Sinh dữ liệu demo cho use case Pharmacity (mục II, VII, VIII, XXXVIII của spec PromotionPilot AI).

Tạo 2 file:
1. data/pharmacity_demo.csv — bộ dữ liệu demo LỚN dùng cho nút "Dùng dữ liệu Pharmacity mẫu"
   (one-click demo). Dùng CSV thay vì XLSX để tải nhanh trong app — đọc XLSX hàng trăm nghìn dòng
   trong Streamlit chậm hơn CSV đáng kể.
2. data/mau_du_lieu_promotionpilot.xlsx — file mẫu XLSX NHỎ, có 3 sheet (Sales_Data,
   Promotion_Master, Business_Config), người dùng tải về, tự điền dữ liệu thật của họ rồi upload lại.

[BUSINESS RULE — điều chỉnh so với spec gốc]: Spec gốc yêu cầu 24 tháng dữ liệu (~500 giao dịch/ngày
x 3.4 sản phẩm/giao dịch ≈ 1.2 triệu dòng). Con số này vượt xa mức "vài trăm nghìn giao dịch" mà
chính spec yêu cầu ở mục XLV (Performance) — và sẽ khiến việc load demo trên Streamlit Community
Cloud (free tier, ~1GB RAM) chậm/dễ timeout, ảnh hưởng trải nghiệm demo trực tiếp với khách hàng.
Quyết định: giảm còn 6 tháng (~180 ngày) dữ liệu, giữ nguyên tần suất ~500 giao dịch/ngày và
~3.4 sản phẩm/giao dịch → ~300.000 dòng — vẫn đủ dài để forecast nhận diện seasonality theo tuần/
tháng, và nằm gọn trong ngưỡng hiệu năng mục XLV. Ghi rõ trong README/docs, không giấu diếm.

Chạy: python scripts/generate_pharmacity_demo.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

RNG = np.random.default_rng(2026)

N_DAYS = 180  # [BUSINESS RULE] 6 tháng thay vì 24 tháng — xem giải thích ở docstring trên
END_DATE = pd.Timestamp("2026-09-20")
START_DATE = END_DATE - pd.Timedelta(days=N_DAYS - 1)

TARGET_TXN_PER_DAY = 500
TARGET_ITEMS_PER_TXN = 3.4
TARGET_AOV = 500_000  # đồng/giao dịch
MISSING_CUSTOMER_PCT = 0.30

OUTPUT_CSV = Path(__file__).resolve().parent.parent / "data" / "pharmacity_demo.csv"
OUTPUT_TEMPLATE_XLSX = Path(__file__).resolve().parent.parent / "data" / "mau_du_lieu_promotionpilot.xlsx"

# 43 SKU thuộc các nhóm ngành hàng nhà thuốc phổ biến
CATEGORIES = {
    "Vitamin & Thực phẩm chức năng": 8,
    "Thuốc không kê đơn (OTC)": 7,
    "Chăm sóc cá nhân": 6,
    "Mẹ & bé": 6,
    "Thiết bị y tế": 5,
    "Dược mỹ phẩm": 6,
    "Khẩu trang & Vệ sinh": 5,
}
assert sum(CATEGORIES.values()) == 43

PRICE_RANGE_BY_CATEGORY = {
    "Vitamin & Thực phẩm chức năng": (80_000, 450_000),
    "Thuốc không kê đơn (OTC)": (25_000, 180_000),
    "Chăm sóc cá nhân": (40_000, 220_000),
    "Mẹ & bé": (60_000, 380_000),
    "Thiết bị y tế": (100_000, 900_000),
    "Dược mỹ phẩm": (120_000, 650_000),
    "Khẩu trang & Vệ sinh": (15_000, 90_000),
}
MARGIN_RANGE_BY_CATEGORY = {
    "Vitamin & Thực phẩm chức năng": (0.25, 0.40),
    "Thuốc không kê đơn (OTC)": (0.18, 0.30),
    "Chăm sóc cá nhân": (0.28, 0.45),
    "Mẹ & bé": (0.22, 0.35),
    "Thiết bị y tế": (0.20, 0.32),
    "Dược mỹ phẩm": (0.30, 0.48),
    "Khẩu trang & Vệ sinh": (0.20, 0.35),
}

N_CUSTOMERS = 6000
WEEKDAY_MULT = {0: 0.92, 1: 0.92, 2: 0.95, 3: 0.98, 4: 1.08, 5: 1.35, 6: 1.25}


def build_sku_catalog() -> pd.DataFrame:
    rows = []
    sku_counter = 1
    for cat, n_sku in CATEGORIES.items():
        price_lo, price_hi = PRICE_RANGE_BY_CATEGORY[cat]
        margin_lo, margin_hi = MARGIN_RANGE_BY_CATEGORY[cat]
        for _ in range(n_sku):
            price = int(RNG.uniform(price_lo, price_hi) / 1000) * 1000
            margin_pct = RNG.uniform(margin_lo, margin_hi)
            cogs = round(price * (1 - margin_pct))
            popularity = RNG.pareto(a=1.6) + 0.3
            rows.append(
                {
                    "SKU_ID": f"PHA{sku_counter:03d}",
                    "Category": cat,
                    "Price_per_unit": price,
                    "COGS": cogs,
                    "Margin": round(margin_pct, 4),
                    "popularity": popularity,
                }
            )
            sku_counter += 1
    catalog = pd.DataFrame(rows)
    catalog["popularity"] = catalog["popularity"] / catalog["popularity"].sum()
    return catalog


def build_affinity_pairs(catalog: pd.DataFrame) -> dict[str, str]:
    pairs: dict[str, str] = {}
    for cat, group in catalog.groupby("Category"):
        skus = group["SKU_ID"].tolist()
        if len(skus) < 2:
            continue
        a, b = RNG.choice(skus, size=2, replace=False)
        pairs[a] = b
    return pairs


def build_customers() -> pd.DataFrame:
    segment_probs = {"loyal": 0.07, "frequent": 0.15, "occasional": 0.48, "new": 0.18, "at_risk": 0.12}
    segments = RNG.choice(list(segment_probs.keys()), size=N_CUSTOMERS, p=list(segment_probs.values()))
    activity_weight = {"loyal": 5.0, "frequent": 3.0, "occasional": 1.0, "new": 1.2, "at_risk": 0.7}
    weights = np.array([activity_weight[s] for s in segments])
    return pd.DataFrame({"customer_id": [f"KH{i:06d}" for i in range(1, N_CUSTOMERS + 1)], "activity_weight": weights})


def seasonality_multiplier(date: pd.Timestamp) -> float:
    m, d = date.month, date.day
    mult = 1.0
    if (m == 1 and d >= 15) or (m == 2 and d <= 10):
        mult *= 1.4  # mùa cúm/Tết — nhu cầu thuốc & vitamin tăng
    elif m in (9, 10):
        mult *= 1.15  # giao mùa, cảm cúm tăng
    return mult


def build_promotions(catalog: pd.DataFrame) -> pd.DataFrame:
    mechanics = ["Discount_Pct", "Discount_Pct", "B1G1", "Bundle", "Member_Price"]
    discount_values = {"Discount_Pct": [0.05, 0.10, 0.15], "B1G1": [0.5], "Bundle": [0.12], "Member_Price": [0.08]}
    n_promos = max(6, N_DAYS // 12)
    rows = []
    for i in range(n_promos):
        start_offset = int(RNG.uniform(5, N_DAYS - 10))
        duration = int(RNG.integers(4, 9))
        start = START_DATE + pd.Timedelta(days=start_offset)
        end = start + pd.Timedelta(days=duration)
        mechanic = RNG.choice(mechanics)
        discount = RNG.choice(discount_values[mechanic])
        n_skus_in_promo = int(RNG.integers(1, 4))
        skus = RNG.choice(catalog["SKU_ID"], size=n_skus_in_promo, replace=False)
        for sku in skus:
            rows.append(
                {
                    "PromotionID": f"KM{i+1:03d}",
                    "SKU_ID": sku,
                    "Scheme_Promotion": mechanic,
                    "Discount_Pct": discount,
                    "Start_Date_Promotion": start,
                    "End_Date_Promotion": end,
                }
            )
    return pd.DataFrame(rows)


def _uplift_for_mechanic(mechanic: str, depth: float) -> float:
    if mechanic == "Discount_Pct":
        return min(0.5, depth * 2.2)
    if mechanic == "B1G1":
        return min(0.75, 0.35 + depth * 1.4)
    if mechanic == "Bundle":
        return min(0.45, 0.25 + depth)
    if mechanic == "Member_Price":
        return min(0.35, depth * 1.8)
    return 0.1


def main() -> None:
    catalog = build_sku_catalog()
    affinity = build_affinity_pairs(catalog)
    customers = build_customers()
    promotions = build_promotions(catalog)

    dates = pd.date_range(START_DATE, END_DATE, freq="D")
    total_days = len(dates)

    promo_by_sku_active: dict[str, list[dict]] = {}
    for _, p in promotions.iterrows():
        promo_by_sku_active.setdefault(p["SKU_ID"], []).append(p.to_dict())

    catalog_indexed = catalog.set_index("SKU_ID")
    price_map = catalog_indexed["Price_per_unit"].to_dict()
    cogs_map = catalog_indexed["COGS"].to_dict()
    margin_map = catalog_indexed["Margin"].to_dict()
    category_map = catalog_indexed["Category"].to_dict()
    popularity_map = catalog_indexed["popularity"].to_dict()
    sku_list = catalog["SKU_ID"].tolist()
    base_pop = np.array([popularity_map[s] for s in sku_list])

    # [BUSINESS RULE] Tồn kho ban đầu/mục tiêu tái nhập PHẢI tỷ lệ với độ phổ biến (popularity)
    # của SKU — nếu không, các SKU bán chạy nhất (Pareto-distributed popularity) sẽ luôn cạn hàng
    # phi thực tế trong khi SKU ít bán tồn dư, vì tốc độ bán không tỷ lệ với mức tồn kho cố định.
    # Hệ số nhân theo độ phổ biến được clip [0.5, 8] để tránh giá trị cực đoan từ đuôi Pareto.
    mean_pop = float(base_pop.mean())
    pop_multiplier = {s: float(np.clip(popularity_map[s] / mean_pop, 0.6, 6.0)) for s in sku_list}
    inventory = {s: int(RNG.uniform(500, 900) * pop_multiplier[s]) for s in sku_list}
    target_stock = dict(inventory)
    days_since_restock = {k: 0 for k in inventory}

    # Hiệu chỉnh giá trung bình để AOV tổng thể ~500.000đ/giao dịch với ~3.4 sản phẩm/giao dịch
    avg_price_weighted = float((base_pop * np.array([price_map[s] for s in sku_list])).sum())
    aov_scale = TARGET_AOV / max(avg_price_weighted * TARGET_ITEMS_PER_TXN, 1)
    # [BUSINESS RULE] hệ số hiệu chỉnh thực nghiệm: chạy thử cho thấy AOV thực tế cao hơn mục tiêu
    # ~35% (do phân phối số lượng qty>1 kéo trung bình lên) — nhân thêm 0.74 để AOV cuối ra sát
    # TARGET_AOV hơn. Đây là hiệu chỉnh dữ liệu demo, không phải kết luận khoa học.
    aov_scale *= 0.74

    rows = []
    txn_counter = 1

    for day_idx, day in enumerate(dates):
        weekday_mult = WEEKDAY_MULT[day.weekday()]
        season_mult = seasonality_multiplier(day)
        trend_mult = 1.0 + 0.15 * (day_idx / total_days)
        noise = RNG.lognormal(mean=0, sigma=0.1)
        lam = TARGET_TXN_PER_DAY * weekday_mult * season_mult * trend_mult * noise
        n_txn_today = RNG.poisson(lam)

        active_promos_today = {
            sku: p for sku, plist in promo_by_sku_active.items() for p in plist
            if p["Start_Date_Promotion"] <= day <= p["End_Date_Promotion"]
        }

        pop_today = base_pop.copy()
        for sku, promo in active_promos_today.items():
            idx = sku_list.index(sku)
            uplift = _uplift_for_mechanic(promo["Scheme_Promotion"], promo["Discount_Pct"])
            pop_today[idx] *= (1 + uplift) * RNG.uniform(0.85, 1.15)
        pop_today = pop_today / pop_today.sum()

        cust_weights = customers["activity_weight"].values
        cust_weights = cust_weights / cust_weights.sum()

        for _ in range(n_txn_today):
            if RNG.random() < (1 - MISSING_CUSTOMER_PCT):
                customer_id = customers["customer_id"].iloc[RNG.choice(len(customers), p=cust_weights)]
            else:
                customer_id = None

            n_items = max(1, int(round(RNG.normal(TARGET_ITEMS_PER_TXN, 1.1))))
            n_items = min(n_items, 8)
            chosen_skus: list[str] = []
            first_sku = RNG.choice(sku_list, p=pop_today)
            chosen_skus.append(first_sku)
            if first_sku in affinity and n_items > 1 and RNG.random() < 0.5:
                chosen_skus.append(affinity[first_sku])
            while len(chosen_skus) < n_items:
                candidate = RNG.choice(sku_list, p=pop_today)
                if candidate not in chosen_skus:
                    chosen_skus.append(candidate)

            txn_id = f"TXN{txn_counter:07d}"
            txn_time = day + pd.Timedelta(hours=int(RNG.integers(7, 22)), minutes=int(RNG.integers(0, 60)))

            for sku in chosen_skus:
                qty = RNG.choice([1, 2, 3], p=[0.75, 0.18, 0.07])
                price = price_map[sku] * aov_scale
                cogs = cogs_map[sku] * aov_scale
                price = round(price / 500) * 500
                cogs = round(cogs / 500) * 500

                promo = active_promos_today.get(sku)
                if promo:
                    mech = promo["Scheme_Promotion"]
                    depth = promo["Discount_Pct"]
                    if mech in ("Discount_Pct", "Bundle", "Member_Price"):
                        eff_price = price * (1 - depth)
                    elif mech == "B1G1":
                        eff_price = price * 0.5
                    else:
                        eff_price = price
                else:
                    eff_price = price

                revenue = round(qty * eff_price)
                inventory[sku] = max(0, inventory[sku] - qty)

                rows.append(
                    {
                        "Date": txn_time,
                        "TransactionID": txn_id,
                        "CustomerID": customer_id,
                        "SKU_ID": sku,
                        "Category": category_map[sku],
                        "Quantity": qty,
                        "Price_per_unit": price,
                        "COGS": cogs,
                        "Margin": margin_map[sku],
                        "Revenue": revenue,
                        "Inventory_Onhand": inventory[sku],
                        "PromotionID": promo["PromotionID"] if promo else None,
                        "Scheme_Promotion": promo["Scheme_Promotion"] if promo else None,
                        "Discount_Pct": promo["Discount_Pct"] if promo else None,
                        "Start_Date_Promotion": promo["Start_Date_Promotion"].date() if promo else None,
                        "End_Date_Promotion": promo["End_Date_Promotion"].date() if promo else None,
                    }
                )
            txn_counter += 1

        for sku in sku_list:
            days_since_restock[sku] += 1
            # [BUSINESS RULE] tái nhập khi tồn kho xuống dưới 40% mục tiêu HOẶC quá 10 ngày chưa
            # nhập — chu kỳ chặt hơn trước (từng là 25%/18 ngày) để tránh SKU bán nhanh cạn hàng
            # phi thực tế trước khi kịp tái nhập, đặc biệt các SKU có sức bán cao.
            if inventory[sku] < target_stock[sku] * 0.40 or days_since_restock[sku] > 10:
                inventory[sku] = target_stock[sku] + int(RNG.uniform(-50, 100))
                days_since_restock[sku] = 0

    df = pd.DataFrame(rows)
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    print(
        f"[pharmacity_demo.csv] {len(df):,} dòng, {df['TransactionID'].nunique():,} giao dịch, "
        f"{df['SKU_ID'].nunique()} SKU, {df['CustomerID'].nunique()} khách hàng "
        f"({df['CustomerID'].isna().mean():.0%} thiếu CustomerID)."
    )
    print(f"AOV trung bình: {df.groupby('TransactionID')['Revenue'].sum().mean():,.0f}đ")
    print(f"Items/giao dịch trung bình: {df.groupby('TransactionID').size().mean():.2f}")
    print(f"Khoảng thời gian: {df['Date'].min()} -> {df['Date'].max()}")
    print(f"File: {OUTPUT_CSV}")

    build_template_xlsx(catalog, promotions)


def build_template_xlsx(catalog: pd.DataFrame, promotions: pd.DataFrame) -> None:
    """Sinh file mẫu XLSX nhỏ (mục VIII): 3 sheet, có header đúng chuẩn + vài dòng ví dụ để user
    hiểu cấu trúc, tự điền dữ liệu thật rồi upload lại."""
    example_dates = pd.date_range(END_DATE - pd.Timedelta(days=9), END_DATE, freq="D")
    sample_skus = catalog["SKU_ID"].head(5).tolist()
    sample_rows = []
    txn_i = 1
    for d in example_dates[:6]:
        for sku in RNG.choice(sample_skus, size=2, replace=False):
            row = catalog[catalog["SKU_ID"] == sku].iloc[0]
            qty = int(RNG.integers(1, 3))
            sample_rows.append(
                {
                    "Date": d.date(),
                    "TransactionID": f"TXN{txn_i:04d}",
                    "CustomerID": f"KH{txn_i:04d}" if txn_i % 3 else "",
                    "SKU_ID": sku,
                    "Category": row["Category"],
                    "Quantity": qty,
                    "Price_per_unit": row["Price_per_unit"],
                    "COGS": row["COGS"],
                    "Margin": row["Margin"],
                    "Revenue": qty * row["Price_per_unit"],
                    "Inventory_Onhand": int(RNG.integers(50, 500)),
                    "PromotionID": "",
                    "Scheme_Promotion": "",
                    "Discount_Pct": "",
                    "Start_Date_Promotion": "",
                    "End_Date_Promotion": "",
                }
            )
        txn_i += 1
    sales_template = pd.DataFrame(sample_rows)

    promo_master = promotions.drop_duplicates(subset=["PromotionID"]).head(10)[
        ["PromotionID", "Scheme_Promotion", "Discount_Pct", "Start_Date_Promotion", "End_Date_Promotion"]
    ]

    business_config = pd.DataFrame(
        [
            {"Tham_so": "Ten_doanh_nghiep", "Gia_tri": "Nhà thuốc Demo", "Ghi_chu": "Tên hiển thị trong báo cáo"},
            {"Tham_so": "Nganh_hang", "Gia_tri": "Dược phẩm / Nhà thuốc", "Ghi_chu": ""},
            {"Tham_so": "Bien_loi_nhuan_toi_thieu_pct", "Gia_tri": 0.15, "Ghi_chu": "Margin tối thiểu chấp nhận được"},
            {"Tham_so": "Giam_gia_toi_da_pct", "Gia_tri": 0.30, "Ghi_chu": "Mức giảm giá tối đa cho phép"},
            {"Tham_so": "ROI_toi_thieu_pct", "Gia_tri": 0.20, "Ghi_chu": "ROI tối thiểu chấp nhận khi chạy khuyến mãi"},
            {"Tham_so": "Safety_stock_days", "Gia_tri": 7, "Ghi_chu": "Số ngày tồn kho dự phòng"},
            {"Tham_so": "Lead_time_days", "Gia_tri": 5, "Ghi_chu": "Thời gian chờ nhập hàng"},
            {"Tham_so": "Thoi_gian_campaign_toi_da_days", "Gia_tri": 14, "Ghi_chu": "Số ngày chạy 1 chương trình tối đa"},
        ]
    )

    with pd.ExcelWriter(OUTPUT_TEMPLATE_XLSX, engine="openpyxl") as writer:
        sales_template.to_excel(writer, sheet_name="Sales_Data", index=False)
        promo_master.to_excel(writer, sheet_name="Promotion_Master", index=False)
        business_config.to_excel(writer, sheet_name="Business_Config", index=False)

    print(f"File mẫu Excel: {OUTPUT_TEMPLATE_XLSX}")


if __name__ == "__main__":
    main()
