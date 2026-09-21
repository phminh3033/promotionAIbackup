from src.business.profile import BusinessProfile


def test_with_yaml_defaults_returns_correct_types():
    """Regression test: YAML tự suy luận int cho số nguyên (vd '8' -> int 8), gây lỗi
    StreamlitMixedNumericTypesError khi UI dùng min_value dạng float. Phải luôn là float/int đúng."""
    profile = BusinessProfile.with_yaml_defaults()
    assert isinstance(profile.service_capacity_per_staff_per_hour, float)
    assert isinstance(profile.min_margin_pct, float)
    assert isinstance(profile.max_discount_pct, float)
    assert isinstance(profile.min_roi_pct, float)
    assert isinstance(profile.promotion_budget, float)
    assert isinstance(profile.safety_stock_days, int)
    assert isinstance(profile.lead_time_days, int)
    assert isinstance(profile.max_campaign_duration_days, int)


def test_with_yaml_defaults_overrides_work():
    profile = BusinessProfile.with_yaml_defaults(business_name="Test Co")
    assert profile.business_name == "Test Co"
