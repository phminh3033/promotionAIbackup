from src.promotion.rules import SkuRuleContext, evaluate_sku_rules, max_allowed_depth


def _ctx(**overrides):
    base = dict(
        product_id="SP01",
        days_of_inventory=20,
        sales_velocity_change_pct=0.0,
        margin_pct=0.30,
        has_basket_partner=False,
        basket_partner_id=None,
        repeat_rate=0.10,
        high_value_customer_share=0.10,
        lead_time_days=5,
    )
    base.update(overrides)
    return SkuRuleContext(**base)


def test_insufficient_stock_rejects_all_mechanics():
    ctx = _ctx(days_of_inventory=2, lead_time_days=10)
    verdicts = evaluate_sku_rules(ctx, min_margin_pct=0.15, max_discount_pct=0.30)
    assert all(v.verdict == "rejected" for v in verdicts)


def test_high_inventory_low_velocity_sufficient_margin_recommends_discount():
    ctx = _ctx(days_of_inventory=60, sales_velocity_change_pct=-0.3, margin_pct=0.40)
    verdicts = evaluate_sku_rules(ctx, min_margin_pct=0.15, max_discount_pct=0.30)
    mechanics_recommended = {v.mechanic for v in verdicts if v.verdict == "recommended"}
    assert "discount_percent" in mechanics_recommended
    assert "bundle" in mechanics_recommended


def test_basket_partner_recommends_bundle():
    ctx = _ctx(has_basket_partner=True, basket_partner_id="SP02")
    verdicts = evaluate_sku_rules(ctx, min_margin_pct=0.15, max_discount_pct=0.30)
    bundle_verdict = next(v for v in verdicts if v.mechanic == "bundle")
    assert bundle_verdict.verdict == "recommended"


def test_high_repeat_rate_recommends_bogo():
    ctx = _ctx(repeat_rate=0.5)
    verdicts = evaluate_sku_rules(ctx, min_margin_pct=0.15, max_discount_pct=0.30)
    bogo_verdict = next(v for v in verdicts if v.mechanic == "bogo")
    assert bogo_verdict.verdict == "recommended"


def test_low_margin_cautions_deep_discount():
    ctx = _ctx(margin_pct=0.16)
    verdicts = evaluate_sku_rules(ctx, min_margin_pct=0.15, max_discount_pct=0.30)
    discount_verdict = next(v for v in verdicts if v.mechanic == "discount_percent")
    assert discount_verdict.verdict == "caution"


def test_max_allowed_depth_respects_min_margin():
    # price=100, cost=70 -> margin gốc 30%. min_margin=20% -> depth tối đa = 1 - 70/(100*0.8) = 0.125
    depth = max_allowed_depth("discount_percent", unit_cost=70, price=100, min_margin_pct=0.20, max_discount_pct=0.5)
    assert abs(depth - 0.125) < 1e-6


def test_max_allowed_depth_capped_by_business_max():
    depth = max_allowed_depth("discount_percent", unit_cost=10, price=100, min_margin_pct=0.10, max_discount_pct=0.2)
    assert depth == 0.2


def test_gift_mechanic_not_limited_by_margin_depth():
    depth = max_allowed_depth("gift", unit_cost=70, price=100, min_margin_pct=0.20, max_discount_pct=0.3)
    assert depth == 0.3
