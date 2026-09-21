import pandas as pd

from src.data.mapper import apply_mapping, detect_capabilities, suggest_mapping, validate_mapping


def test_suggest_mapping_vietnamese_with_dd_char():
    """Cột có chữ 'Đ/đ' (không phải ký tự kết hợp Unicode) phải vẫn được nhận diện đúng."""
    columns = ["Ngày", "Mã hóa đơn", "Mã sản phẩm", "Số lượng", "Doanh thu", "Ngày bắt đầu khuyến mãi"]
    mapping = suggest_mapping(columns)
    assert mapping["date"] == "Ngày"
    assert mapping["transaction_id"] == "Mã hóa đơn"
    assert mapping["product_id"] == "Mã sản phẩm"
    assert mapping["quantity"] == "Số lượng"
    assert mapping["revenue"] == "Doanh thu"
    assert mapping["promotion_start"] == "Ngày bắt đầu khuyến mãi"


def test_suggest_mapping_english_columns():
    columns = ["Order Date", "Item Code", "Qty", "Total Amount"]
    mapping = suggest_mapping(columns)
    assert mapping["date"] == "Order Date"
    assert mapping["quantity"] == "Qty"
    assert mapping["revenue"] == "Total Amount"
    assert mapping["product_id"] is None  # "Item Code" không đủ khớp -> cần map thủ công


def test_validate_mapping_missing_required():
    mapping = {"date": "A", "product_id": None, "quantity": "B", "revenue": "C"}
    errors = validate_mapping(mapping)
    assert any("Mã sản phẩm" in e for e in errors)


def test_validate_mapping_duplicate_column():
    mapping = {"date": "A", "product_id": "A", "quantity": "B", "revenue": "C"}
    errors = validate_mapping(mapping)
    assert any("nhiều trường" in e for e in errors)


def test_apply_mapping_parses_iso_dates_correctly():
    """Regression test: pandas dayfirst=True có thể đọc sai ngày ISO (vd hoán đổi tháng/ngày)."""
    raw = pd.DataFrame(
        {
            "Ngày": ["2025-01-01 08:00:00", "2025-01-10 09:00:00", "2025-01-12 10:00:00"],
            "SP": ["A", "A", "A"],
            "SL": [1, 2, 3],
            "DT": [1000, 2000, 3000],
        }
    )
    mapping = {"date": "Ngày", "product_id": "SP", "quantity": "SL", "revenue": "DT"}
    df = apply_mapping(raw, mapping)
    assert df["date"].max() == pd.Timestamp("2025-01-12 10:00:00")
    assert df["date"].min() == pd.Timestamp("2025-01-01 08:00:00")


def test_apply_mapping_empty_string_promotion_becomes_nan():
    raw = pd.DataFrame(
        {
            "Ngày": ["2025-01-01"],
            "SP": ["A"],
            "SL": [1],
            "DT": [1000],
            "LoaiKM": [""],
        }
    )
    mapping = {"date": "Ngày", "product_id": "SP", "quantity": "SL", "revenue": "DT", "promotion_type": "LoaiKM"}
    df = apply_mapping(raw, mapping)
    assert df["promotion_type"].isna().all()


def test_detect_capabilities_missing_optional_fields_no_crash():
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2025-01-01"]),
            "product_id": ["A"],
            "quantity": [1],
            "revenue": [1000],
        }
    )
    caps = detect_capabilities(df)
    assert caps.has_customer is False
    assert caps.has_inventory is False
    assert "customer_id" in caps.missing_optional
