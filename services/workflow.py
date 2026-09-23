"""Điều phối UI gọi đúng hàm src/ hiện có. Không đổi công thức, không bịa số liệu."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from services.recommendation_engine import RecommendationEngine
from services.scientific_model_engine import ScientificModelEngine
from src.business.profile import BusinessProfile
from src.data.loader import load_raw_file
from src.data.mapper import apply_mapping, detect_capabilities, suggest_mapping, validate_mapping
from src.data.quality import run_quality_check
from src.explainability.explainer import explain_trend
from src.features.engineering import aggregate_daily
from src.optimization.objective import OBJECTIVE_LABELS_VI, score_scenarios
from src.promotion.mechanics import MECHANIC_LABELS_VI, BaselineMetrics
from src.promotion.rules import SkuRuleContext
from src.promotion.simulator import DISCLAIMER_VI
from src.recommendation.engine import CONFIDENCE_PCT_BY_LABEL, _assess_risk
from src.recommendation.timing import analyze_best_timing
from src.roi.calculator import compute_roi_breakdown

ROOT = Path(__file__).resolve().parent.parent
DEMO_PATH = ROOT / "data" / "pharmacity_demo.csv"
TEMPLATE_PATH = ROOT / "data" / "mau_du_lieu_promotionpilot.xlsx"
ENGINE = ScientificModelEngine()
RECOMMENDER = RecommendationEngine()

DOWNSTREAM_KEYS = [
    "rfm_result",
    "segmentation_result",
    "basket_result",
    "historical_uplifts",
    "inventory_plan",
    "last_scenario_table",
    "last_scenario_baseline",
    "last_scenario_meta",
    "last_rule_context",
    "last_rule_verdicts",
    "last_recommendation_card",
    "last_campaign_plan",
    "last_execution_plan",
    "selected_mechanic",
]


def reset_downstream() -> None:
    for key in DOWNSTREAM_KEYS:
        st.session_state[key] = None
    st.session_state["forecast_cache"] = {}
    st.session_state["forecast_history"] = {}


def commit_dataset(raw_df, filename: str, mapping: dict) -> tuple[bool, str]:
    errors = validate_mapping(mapping)
    if errors:
        return False, "; ".join(errors)
    mapped_df = apply_mapping(raw_df, mapping)
    clean_df, report = run_quality_check(mapped_df)
    caps = detect_capabilities(mapped_df)
    st.session_state["raw_df"] = raw_df
    st.session_state["raw_filename"] = filename
    st.session_state["column_mapping"] = mapping
    st.session_state["mapped_df"] = mapped_df
    st.session_state["capabilities"] = caps
    st.session_state["clean_df"] = clean_df
    st.session_state["quality_report"] = report
    st.session_state["data_loaded_at"] = datetime.now()
    reset_downstream()
    return True, f"Đã xử lý {len(clean_df):,} dòng hợp lệ. Điểm chất lượng {report.score}/100."


def load_demo_dataset() -> tuple[bool, str]:
    if not DEMO_PATH.exists():
        return False, "Không tìm thấy file dữ liệu demo. Chạy python scripts/generate_pharmacity_demo.py trước."
    raw_df = load_raw_file(DEMO_PATH.read_bytes(), DEMO_PATH.name)
    mapping = suggest_mapping(list(raw_df.columns))
    ok, message = commit_dataset(raw_df, DEMO_PATH.name, mapping)
    if ok:
        st.session_state["business_profile"] = BusinessProfile.with_yaml_defaults(
            business_name="Nhà thuốc Demo (Pharmacity-style)",
            industry="Dược phẩm / Nhà thuốc",
        )
    return ok, message


def dataset_chip() -> str:
    filename = str(st.session_state.get("raw_filename") or "")
    if not filename:
        return "Chưa tải"
    if "pharmacity" in filename.lower():
        return "Demo Retail"
    return Path(filename).stem


def period_chip() -> str:
    report = st.session_state.get("quality_report")
    if report is None or report.date_min is None:
        return "—"
    return f"{report.date_min.strftime('%d/%m/%Y')} – {report.date_max.strftime('%d/%m/%Y')}"


def _month_frame(df: pd.DataFrame) -> pd.DataFrame:
    work = df.dropna(subset=["date"]).copy()
    work["month"] = work["date"].dt.to_period("M").dt.to_timestamp()
    agg = {"revenue": ("revenue", "sum"), "quantity": ("quantity", "sum")}
    grouped = work.groupby("month").agg(**agg)
    if "transaction_id" in work.columns:
        grouped["orders"] = work.groupby("month")["transaction_id"].nunique()
    else:
        grouped["orders"] = work.groupby("month").size()
    if "gross_profit" in work.columns:
        grouped["gross_profit"] = work.groupby("month")["gross_profit"].sum()
    return grouped.sort_index()


def _delta(series: pd.Series):
    if series is None or len(series.dropna()) < 2:
        return None
    previous, current = float(series.iloc[-2]), float(series.iloc[-1])
    if previous == 0:
        return None
    return (current - previous) / previous


def kpi_snapshot() -> dict | None:
    df = st.session_state.get("clean_df")
    if df is None or df.empty:
        return None
    caps = st.session_state["capabilities"]
    monthly = _month_frame(df)
    revenue = float(df["revenue"].sum())
    orders = int(df["transaction_id"].nunique()) if caps.has_transaction else int(len(df))
    margin = None
    if "gross_profit" in df.columns and revenue:
        margin = float(df["gross_profit"].sum()) / revenue
    roi = None
    card = st.session_state.get("last_recommendation_card")
    if card and card.expected_roi_range:
        roi = sum(card.expected_roi_range) / 2
    table = st.session_state.get("last_scenario_table")
    if roi is None and table is not None and "roi" in table.columns:
        eligible = table[table["mechanic"] != "no_promo"]
        if "bi_tu_choi" in eligible.columns:
            eligible = eligible[~eligible["bi_tu_choi"]]
        if not eligible.empty and pd.notna(eligible.iloc[0]["roi"]):
            roi = float(eligible.iloc[0]["roi"])
    margin_series = None
    if "gross_profit" in monthly.columns:
        margin_series = (monthly["gross_profit"] / monthly["revenue"].replace(0, pd.NA)).dropna()
    return {
        "revenue": revenue,
        "orders": orders,
        "margin": margin,
        "roi": roi,
        "revenue_delta": _delta(monthly["revenue"]),
        "orders_delta": _delta(monthly["orders"]),
        "margin_delta": _delta(margin_series) if margin_series is not None else None,
        "revenue_spark": monthly["revenue"].tail(12).tolist(),
        "orders_spark": monthly["orders"].tail(12).tolist(),
        "margin_spark": margin_series.tail(12).tolist() if margin_series is not None else [],
        "monthly": monthly,
        "roi_note": "ROI kịch bản mô phỏng" if roi is not None else "Chưa có mô phỏng",
    }


def revenue_by_grain(grain: str) -> pd.DataFrame:
    df = st.session_state["clean_df"]
    work = df.dropna(subset=["date"]).copy()
    if grain == "Năm":
        work["bucket"] = work["date"].dt.to_period("Y").dt.to_timestamp()
    elif grain == "Quý":
        work["bucket"] = work["date"].dt.to_period("Q").dt.to_timestamp()
    else:
        work["bucket"] = work["date"].dt.to_period("M").dt.to_timestamp()
    return work.groupby("bucket", as_index=False)["revenue"].sum().sort_values("bucket")


def company_revenue_forecast():
    cache = st.session_state.get("forecast_cache") or {}
    for key, result in cache.items():
        parts = key.split("|")
        if len(parts) >= 3 and parts[0] == "Toàn công ty" and parts[2] == "revenue":
            return result
    return None


def opportunity_cards() -> list[dict]:
    df = st.session_state.get("clean_df")
    if df is None or df.empty:
        return []
    cards: list[dict] = []
    cutoff = df["date"].max() - pd.Timedelta(days=30)
    recent = df[df["date"] >= cutoff]
    prior = df[(df["date"] < cutoff) & (df["date"] >= cutoff - pd.Timedelta(days=30))]
    group_col = "category" if "category" in df.columns and df["category"].notna().any() else "product_id"
    if not prior.empty and not recent.empty:
        rec = recent.groupby(group_col)["quantity"].sum()
        old = prior.groupby(group_col)["quantity"].sum()
        change = ((rec - old) / old.replace(0, pd.NA)).dropna().sort_values(ascending=False)
        if not change.empty and float(change.iloc[0]) > 0.05:
            name = str(change.index[0])
            impact = float(recent[recent[group_col] == name]["revenue"].sum() - prior[prior[group_col] == name]["revenue"].sum())
            cards.append(
                {
                    "title": f"Nhu cầu {name} đang tăng",
                    "body": explain_trend(float(change.iloc[0])),
                    "impact": impact,
                    "tone": "info",
                    "priority": "Ưu tiên theo dữ liệu 30 ngày",
                }
            )
    seg = st.session_state.get("segmentation_result")
    if seg is not None and seg.sufficient_data and "segment" in seg.rfm_labeled.columns:
        lapsed = seg.rfm_labeled[seg.rfm_labeled["segment"] == "Khách có nguy cơ rời bỏ"]
        if len(lapsed):
            cards.append(
                {
                    "title": "Kích hoạt lại khách hàng",
                    "body": f"{len(lapsed):,} khách đang ở nhóm có nguy cơ rời bỏ theo phân cụm RFM.",
                    "impact": None,
                    "tone": "purple",
                    "priority": "Cần chương trình giữ chân",
                }
            )
    try:
        daily = aggregate_daily(df)
        timing = analyze_best_timing(daily)
        cards.append(
            {
                "title": "Thời điểm traffic thuận lợi",
                "body": timing.best_weekdays_reason,
                "impact": None,
                "tone": "ok",
                "priority": ", ".join(timing.best_weekdays),
            }
        )
    except Exception:
        pass
    return cards[:3]


def scoped_frame(df: pd.DataFrame, scope: str, scope_value):
    if scope == "Theo Danh mục":
        return df[df["category"] == scope_value]
    if scope == "Theo SKU":
        return df[df["product_id"] == scope_value]
    return df


def run_forecast(scope: str, scope_value, metric_col: str, metric_label: str, horizon: int):
    df = st.session_state["clean_df"]
    scoped = scoped_frame(df, scope, scope_value)
    daily = aggregate_daily(scoped)
    if metric_col not in daily.columns:
        raise ValueError("Dữ liệu không có chỉ số này.")
    y = daily.set_index("day")[metric_col].astype(float)
    result = ENGINE.forecast(y, horizon=horizon, series_name=metric_label)
    cache_key = f"{scope}|{scope_value}|{metric_col}|{horizon}"
    st.session_state["forecast_cache"][cache_key] = result
    st.session_state["forecast_history"][cache_key] = y.tail(90)
    return cache_key, result, y.tail(90)


def recent_demand(df: pd.DataFrame, days: int = 30) -> pd.DataFrame:
    cutoff = df["date"].max() - pd.Timedelta(days=days)
    recent = df[df["date"] >= cutoff]
    avg = recent.groupby("product_id")["quantity"].sum().reset_index().rename(columns={"quantity": "total_qty"})
    avg["avg_daily_demand"] = avg["total_qty"] / days
    return avg


def run_inventory(lead_time: int, safety_days: int) -> pd.DataFrame:
    df = st.session_state["clean_df"]
    demand = recent_demand(df)
    latest = df.sort_values("date").groupby("product_id")["inventory"].last().reset_index()
    plan = ENGINE.inventory_plan(demand[["product_id", "avg_daily_demand"]], latest, lead_time, safety_days)
    if "category" in df.columns:
        cats = df.groupby("product_id")["category"].agg(lambda s: s.dropna().iloc[-1] if s.dropna().size else "")
        plan = plan.merge(cats.rename("category"), left_on="product_id", right_index=True, how="left")
    st.session_state["inventory_plan"] = plan
    profile = st.session_state["business_profile"]
    profile.lead_time_days = int(lead_time)
    profile.safety_stock_days = int(safety_days)
    return plan


def stock_status(row) -> str:
    if row["stockout_risk"] == "HIGH":
        return "Thiếu hàng"
    if row["stockout_risk"] == "MEDIUM":
        return "Sắp thiếu"
    return "Đủ hàng"


def _current_inventory(scoped: pd.DataFrame, caps, scope: str):
    if caps.has_inventory and scope == "Một SKU cụ thể" and "inventory" in scoped.columns and not scoped.empty:
        return float(scoped.sort_values("date")["inventory"].iloc[-1])
    return None


def run_simulation(scope: str, scope_value: str, promo_days: int, gift_cost: float) -> tuple[bool, str]:
    df = st.session_state["clean_df"]
    caps = st.session_state["capabilities"]
    profile = st.session_state["business_profile"]
    objective = st.session_state["objective"]
    if scope == "Một Danh mục":
        scoped = df[df["category"] == scope_value]
    else:
        scoped = df[df["product_id"] == scope_value]
    recent_days = 60
    cutoff = df["date"].max() - pd.Timedelta(days=recent_days)
    recent = scoped[scoped["date"] >= cutoff]
    if recent.empty or recent["quantity"].sum() == 0:
        return False, "Không đủ dữ liệu gần đây cho lựa chọn này để mô phỏng."
    n_days = (recent["date"].max() - recent["date"].min()).days + 1
    avg_daily_units = recent["quantity"].sum() / max(n_days, 1)
    avg_price = recent["selling_price"].mean() if caps.has_price else (recent["revenue"].sum() / max(recent["quantity"].sum(), 1))
    unit_cost = recent["cost"].mean() if caps.has_cost else avg_price * (1 - profile.target_margin_pct)
    avg_daily_customers = (
        recent.groupby(recent["date"].dt.normalize())["customer_id"].nunique().mean() if caps.has_customer else None
    )
    current_margin = (avg_price - unit_cost) / avg_price if avg_price > 0 else 0
    baseline = BaselineMetrics(
        avg_daily_units=float(avg_daily_units),
        avg_price=float(avg_price),
        unit_cost=float(unit_cost),
        promo_days=int(promo_days),
        avg_daily_customers=None if avg_daily_customers is None or pd.isna(avg_daily_customers) else float(avg_daily_customers),
    )
    older = scoped[(scoped["date"] < cutoff) & (scoped["date"] >= cutoff - pd.Timedelta(days=recent_days))]
    velocity_change = (recent["quantity"].sum() - older["quantity"].sum()) / max(older["quantity"].sum(), 1) if not older.empty else 0.0
    basket_result = st.session_state.get("basket_result")
    has_partner, partner_id = False, None
    if basket_result is not None and not basket_result.rules.empty and scope == "Một SKU cụ thể":
        match = basket_result.rules[basket_result.rules["antecedent"] == scope_value]
        if not match.empty:
            has_partner = True
            partner_id = match.iloc[0]["consequent"]
    seg_result = st.session_state.get("segmentation_result")
    repeat_rate, high_value_share = None, None
    if seg_result is not None and seg_result.sufficient_data:
        labeled = seg_result.rfm_labeled
        repeat_rate = float((labeled["frequency"] > 1).mean())
        hv_customers = labeled[labeled["segment"] == "Khách giá trị cao"]["customer_id"]
        if caps.has_customer and len(hv_customers) > 0:
            scope_revenue = scoped["revenue"].sum()
            hv_revenue = scoped[scoped["customer_id"].isin(hv_customers)]["revenue"].sum()
            high_value_share = float(hv_revenue / scope_revenue) if scope_revenue > 0 else 0.0
    current_inventory = _current_inventory(scoped, caps, scope)
    days_of_inventory = float("inf")
    if current_inventory is not None and avg_daily_units > 0:
        days_of_inventory = current_inventory / avg_daily_units
    ctx = SkuRuleContext(
        product_id=scope_value,
        days_of_inventory=days_of_inventory,
        sales_velocity_change_pct=float(velocity_change),
        margin_pct=float(current_margin),
        has_basket_partner=has_partner,
        basket_partner_id=partner_id,
        repeat_rate=repeat_rate,
        high_value_customer_share=high_value_share,
        lead_time_days=profile.lead_time_days,
    )
    verdicts = ENGINE.rules(ctx, profile.min_margin_pct, profile.max_discount_pct)
    rejected = {v.mechanic for v in verdicts if v.verdict == "rejected"}
    max_overrides = {
        "discount_percent": ENGINE.depth("discount_percent", unit_cost, avg_price, profile.min_margin_pct, profile.max_discount_pct),
        "bundle": ENGINE.depth("bundle", unit_cost, avg_price, profile.min_margin_pct, profile.max_discount_pct),
    }
    hist = ENGINE.historical_uplift(scoped) if caps.has_promotion else {}
    sim = ENGINE.simulate(baseline, hist, gift_cost, max_overrides)
    roi_table = compute_roi_breakdown(sim.table, baseline)
    scored = score_scenarios(roi_table, objective, current_inventory=None)
    scored["bi_tu_choi"] = scored["mechanic"].isin(rejected) & (scored["mechanic"] != "no_promo")
    st.session_state["last_rule_context"] = ctx
    st.session_state["last_rule_verdicts"] = verdicts
    st.session_state["last_scenario_table"] = scored
    st.session_state["last_scenario_baseline"] = baseline
    st.session_state["last_scenario_meta"] = {
        "scope": scope,
        "scope_value": scope_value,
        "product_focus_label": scope_value,
        "promo_days": int(promo_days),
        "gift_cost_per_unit": float(gift_cost),
        "hist_uplift": hist,
        "objective": objective,
        "current_inventory": current_inventory,
        "current_margin": float(current_margin),
        "velocity_change": float(velocity_change),
    }
    st.session_state["selected_mechanic"] = None
    st.session_state["last_recommendation_card"] = None
    return True, DISCLAIMER_VI


def ensure_scores():
    table = st.session_state.get("last_scenario_table")
    meta = st.session_state.get("last_scenario_meta")
    objective = st.session_state.get("objective")
    if table is None or meta is None or meta.get("objective") == objective:
        return table
    scored = score_scenarios(table, objective, current_inventory=None)
    if "bi_tu_choi" in table.columns and "bi_tu_choi" not in scored.columns:
        scored["bi_tu_choi"] = table["bi_tu_choi"].values
    meta = dict(meta)
    meta["objective"] = objective
    st.session_state["last_scenario_table"] = scored
    st.session_state["last_scenario_meta"] = meta
    return scored


def default_choice(table: pd.DataFrame, profile):
    candidates = table[table["mechanic"] != "no_promo"]
    if "bi_tu_choi" in candidates.columns:
        candidates = candidates[~candidates["bi_tu_choi"]]
    with_margin = candidates[candidates["margin"] >= profile.min_margin_pct]
    if not with_margin.empty:
        candidates = with_margin
    if candidates.empty:
        candidates = table[table["mechanic"] == "no_promo"]
    return candidates.iloc[0]


def chosen_row(table: pd.DataFrame, profile):
    selected = st.session_state.get("selected_mechanic")
    if selected:
        hit = table[table["mechanic"] == selected]
        if not hit.empty and not bool(hit.iloc[0].get("bi_tu_choi", False)):
            return hit.iloc[0]
    return default_choice(table, profile)


def scenario_views(table: pd.DataFrame, profile, meta) -> list[dict]:
    base = table[table["mechanic"] == "no_promo"]
    base_rev = float(base.iloc[0]["doanh_thu"]) if not base.empty else None
    base_gp = float(base.iloc[0]["loi_nhuan_gop"]) if not base.empty else None
    stockout = None
    views = []
    for _, row in table.iterrows():
        rev_lift = (float(row["doanh_thu_tang_them"]) / base_rev) if base_rev else None
        gp_lift = (float(row["loi_nhuan_gop_tang_them"]) / base_gp) if base_gp else None
        risk = _assess_risk(str(row["nguon_uplift"]).split(" ")[0] if "historical" in str(row["nguon_uplift"]) else str(row["nguon_uplift"]), float(row["margin"]), profile.min_margin_pct, stockout)
        if str(row["nguon_uplift"]).startswith("historical"):
            risk = _assess_risk("historical", float(row["margin"]), profile.min_margin_pct, stockout)
        else:
            risk = _assess_risk("assumption", float(row["margin"]), profile.min_margin_pct, stockout)
        if bool(row.get("bi_tu_choi", False)):
            risk = "Cao"
        views.append(
            {
                "mechanic": row["mechanic"],
                "label": MECHANIC_LABELS_VI.get(row["mechanic"], row["scenario"]),
                "scenario": row["scenario"],
                "revenue_lift": rev_lift,
                "profit_lift": gp_lift,
                "profit": float(row["loi_nhuan_gop"]),
                "revenue": float(row["doanh_thu"]),
                "roi": None if pd.isna(row["roi"]) else float(row["roi"]),
                "units": float(row["san_luong"]),
                "risk": risk,
                "rejected": bool(row.get("bi_tu_choi", False)),
                "confidence": _forecast_confidence_band(),
                "inventory_gap": None
                if meta.get("current_inventory") is None
                else max(0.0, float(row["san_luong"]) - float(meta["current_inventory"])),
            }
        )
    return views


def _forecast_confidence_band():
    cache = st.session_state.get("forecast_cache") or {}
    for result in cache.values():
        return result.confidence, CONFIDENCE_PCT_BY_LABEL.get(result.confidence)
    return None, None


def build_decision(mechanic: str | None = None):
    table = ensure_scores()
    baseline = st.session_state.get("last_scenario_baseline")
    meta = st.session_state.get("last_scenario_meta")
    if table is None or baseline is None or meta is None:
        return None
    if mechanic:
        st.session_state["selected_mechanic"] = mechanic
    df = st.session_state["clean_df"]
    caps = st.session_state["capabilities"]
    profile = st.session_state["business_profile"]
    objective = st.session_state["objective"]
    chosen = chosen_row(table, profile)
    st.session_state["selected_mechanic"] = str(chosen["mechanic"])
    ctx = st.session_state.get("last_rule_context")
    verdicts = st.session_state.get("last_rule_verdicts") or []
    target_segment = "Khách hàng nói chung"
    if ctx:
        if ctx.high_value_customer_share and ctx.high_value_customer_share >= 0.3:
            target_segment = "Khách giá trị cao"
        elif ctx.repeat_rate and ctx.repeat_rate >= 0.35:
            target_segment = "Khách mua lặp lại"
    timing = analyze_best_timing(aggregate_daily(df))
    stockout_risk = None
    recommended_stock = float(chosen["san_luong"])
    if caps.has_inventory and meta["scope"] == "Một SKU cụ thể":
        scoped = df[df["product_id"] == meta["scope_value"]]
        current_inv = float(scoped.sort_values("date")["inventory"].iloc[-1])
        inv_rec = ENGINE.sku_inventory(
            meta["scope_value"], baseline.avg_daily_units, current_inv, profile.lead_time_days, profile.safety_stock_days
        )
        recommended_stock = max(float(chosen["san_luong"]), inv_rec.expected_demand_leadtime + inv_rec.safety_stock)
        stockout_risk = inv_rec.stockout_risk
    why = []
    for verdict in verdicts:
        if verdict.mechanic == chosen["mechanic"] and verdict.reasons:
            why.extend(verdict.reasons)
    if not why:
        why.append(
            f"Kịch bản này có điểm phù hợp mục tiêu cao nhất trong số các kịch bản đã mô phỏng "
            f"(điểm {chosen['diem_muc_tieu']:.2f}/1.0)."
        )
    why.append(f"Margin dự kiến sau khuyến mãi: {chosen['margin']:.0%}.")
    why.append(timing.best_weekdays_reason)
    if timing.seasonal_note:
        why.append(timing.seasonal_note)
    confidence = "Trung bình"
    for result in (st.session_state.get("forecast_cache") or {}).values():
        confidence = result.confidence
        break
    caveats = []
    if str(chosen["nguon_uplift"]) == "assumption":
        caveats.append("Uplift dùng giả định elasticity mặc định vì chưa có đủ lịch sử khuyến mãi cho cơ chế này.")
    tradeoffs = list(caveats)
    for verdict in verdicts:
        if verdict.verdict in {"caution", "rejected"} and verdict.reasons:
            tradeoffs.extend(verdict.reasons)
    card = RECOMMENDER.build_card(
        objective=objective,
        chosen_scenario=chosen,
        baseline=baseline,
        business_profile=profile,
        product_focus=meta["product_focus_label"],
        target_segment=target_segment,
        timing=timing,
        recommended_stock=recommended_stock,
        confidence_label_forecast=confidence,
        why_bullets=why,
        stockout_risk=stockout_risk,
        data_caveats=caveats,
    )
    st.session_state["last_recommendation_card"] = card
    st.session_state["decision_tradeoffs"] = tradeoffs
    st.session_state["decision_objective_label"] = OBJECTIVE_LABELS_VI[objective]
    return card


def top_alternatives(table: pd.DataFrame, chosen_mechanic: str, limit: int = 3) -> pd.DataFrame:
    others = table[table["mechanic"] != chosen_mechanic]
    if "bi_tu_choi" in others.columns:
        others = others[~others["bi_tu_choi"]]
    return others.head(limit)
