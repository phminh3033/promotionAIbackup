"""Data Mapping Wizard: gợi ý và áp dụng ánh xạ cột dữ liệu doanh nghiệp -> schema chuẩn.

Doanh nghiệp không cần đặt tên cột đúng chuẩn. Wizard sẽ:
1. Tự gợi ý cột nào tương ứng với trường nào (dựa trên tên cột + kiểu dữ liệu).
2. Cho phép người dùng xác nhận/sửa lại trong UI.
3. Áp dụng mapping để tạo DataFrame chuẩn hoá.
"""
from __future__ import annotations

import re
import unicodedata
import warnings

import pandas as pd

from src.data.schema import ALL_CANONICAL_FIELDS, REQUIRED_FIELDS, DatasetCapabilities

# Từ khóa gợi ý (đã bỏ dấu, viết thường) cho từng trường chuẩn, ưu tiên xuất hiện trước = match trước
_SUGGESTION_KEYWORDS: dict[str, list[str]] = {
    "date": ["ngay", "date", "thoi gian", "time", "hoa don ngay", "created", "order date"],
    "product_id": ["ma san pham", "product_id", "sku", "ma hang", "productid", "item id", "ma sp"],
    "quantity": ["so luong", "quantity", "qty", "sl"],
    "revenue": ["doanh thu", "revenue", "thanh tien", "tong tien", "amount", "sales"],
    "transaction_id": ["ma giao dich", "transaction_id", "ma hoa don", "invoice", "order id", "bill"],
    "customer_id": ["ma khach hang", "customer_id", "customerid", "khach hang id", "member id"],
    "store_id": ["ma cua hang", "store_id", "chi nhanh", "branch", "shop id"],
    "category": ["danh muc", "category", "nhom hang", "phan loai"],
    "selling_price": ["don gia", "selling_price", "gia ban", "unit price", "price"],
    "cost": ["gia von", "cost", "cogs"],
    "gross_profit": ["loi nhuan gop", "gross_profit", "gross profit", "lai gop"],
    "inventory": ["ton kho", "inventory", "stock", "so luong ton"],
    "promotion_id": ["ma khuyen mai", "promotion_id", "ma cttm", "campaign id"],
    "promotion_type": ["loai khuyen mai", "promotion_type", "hinh thuc khuyen mai", "promo type"],
    "discount": ["giam gia", "discount", "% giam"],
    "promotion_start": ["ngay bat dau khuyen mai", "promotion_start", "start date"],
    "promotion_end": ["ngay ket thuc khuyen mai", "promotion_end", "end date"],
}


_ISO_DATE_RE = re.compile(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}")


def _parse_date_column(series: pd.Series) -> pd.Series:
    """Phát hiện định dạng ngày trước khi parse để tránh lỗi hoán đổi ngày/tháng.

    QUAN TRỌNG: pandas.to_datetime(..., dayfirst=True) có thể ÂM THẦM đọc sai một số giá trị
    (không chỉ báo lỗi) khi cột thực ra đã ở định dạng ISO không mơ hồ (YYYY-MM-DD) — với những
    ngày <= 12, dayfirst=True có thể hoán đổi nhầm tháng/ngày. Do đó: nếu cột trông giống ISO
    (bắt đầu bằng năm 4 chữ số), parse KHÔNG dùng dayfirst; ngược lại (định dạng dd/mm/yyyy phổ
    biến ở file Excel/POS Việt Nam) mới dùng dayfirst=True.
    """
    sample = series.dropna().astype(str).head(30)
    looks_iso = True
    if len(sample) > 0:
        looks_iso = (sample.str.match(_ISO_DATE_RE)).mean() > 0.5

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        if looks_iso:
            return pd.to_datetime(series, errors="coerce")
        return pd.to_datetime(series, errors="coerce", dayfirst=True)


def _normalize(text: str) -> str:
    text = str(text).replace("đ", "d").replace("Đ", "D")
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = text.lower().strip()
    text = re.sub(r"[_\-]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def suggest_mapping(columns: list[str]) -> dict[str, str | None]:
    """Trả về {canonical_field: tên_cột_gợi_ý hoặc None nếu không đoán được}."""
    normalized_cols = {col: _normalize(col) for col in columns}
    suggestion: dict[str, str | None] = {field: None for field in ALL_CANONICAL_FIELDS}
    used_columns: set[str] = set()

    for field, keywords in _SUGGESTION_KEYWORDS.items():
        best_match = None
        for col, norm_col in normalized_cols.items():
            if col in used_columns:
                continue
            for kw in keywords:
                if kw in norm_col or norm_col in kw:
                    best_match = col
                    break
            if best_match:
                break
        if best_match:
            suggestion[field] = best_match
            used_columns.add(best_match)

    return suggestion


def validate_mapping(mapping: dict[str, str | None]) -> list[str]:
    """Kiểm tra mapping có đủ các trường bắt buộc chưa. Trả về danh sách lỗi (rỗng nếu OK)."""
    errors = []
    for field in REQUIRED_FIELDS:
        if not mapping.get(field):
            from src.data.schema import FIELD_LABELS_VI

            errors.append(f"Thiếu ánh xạ cho trường bắt buộc: {FIELD_LABELS_VI[field]}")

    chosen = [v for v in mapping.values() if v]
    duplicates = {c for c in chosen if chosen.count(c) > 1}
    if duplicates:
        errors.append(f"Một cột không thể ánh xạ cho nhiều trường cùng lúc: {', '.join(duplicates)}")

    return errors


def apply_mapping(raw_df: pd.DataFrame, mapping: dict[str, str | None]) -> pd.DataFrame:
    """Tạo DataFrame chuẩn hoá theo canonical schema từ mapping đã xác nhận."""
    rename_map = {src_col: field for field, src_col in mapping.items() if src_col}
    df = raw_df[[c for c in rename_map]].rename(columns=rename_map).copy()

    df["date"] = _parse_date_column(df["date"])
    for opt_col in ["promotion_start", "promotion_end"]:
        if opt_col in df.columns:
            df[opt_col] = _parse_date_column(df[opt_col])

    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce")
    df["product_id"] = df["product_id"].astype(str).str.strip()

    for opt_col in ["selling_price", "cost", "gross_profit", "inventory", "discount"]:
        if opt_col in df.columns:
            df[opt_col] = pd.to_numeric(df[opt_col], errors="coerce")

    for opt_col in ["transaction_id", "customer_id", "store_id", "category", "promotion_id", "promotion_type"]:
        if opt_col in df.columns:
            # Chuẩn hoá: ô rỗng / "nan" (do NaN bị ép kiểu chuỗi) đều phải thành NaN thật,
            # tránh việc "không có khuyến mãi" bị hiểu nhầm thành 1 giá trị chuỗi hợp lệ.
            cleaned = df[opt_col].astype(str).str.strip()
            df[opt_col] = cleaned.replace({"": None, "nan": None, "None": None, "NaT": None})

    if "gross_profit" not in df.columns and "cost" in df.columns:
        df["gross_profit"] = df["revenue"] - (df["cost"] * df["quantity"])

    return df


def detect_capabilities(df: pd.DataFrame) -> DatasetCapabilities:
    """Xác định module nào có thể bật dựa trên các cột hiện có sau khi mapping."""
    has_intraday_time = False
    if "date" in df.columns and df["date"].notna().any():
        sample = df["date"].dropna()
        has_intraday_time = bool((sample.dt.hour != 0).any() or (sample.dt.minute != 0).any())

    return DatasetCapabilities(
        has_transaction="transaction_id" in df.columns,
        has_customer="customer_id" in df.columns,
        has_store="store_id" in df.columns,
        has_category="category" in df.columns,
        has_price="selling_price" in df.columns,
        has_cost="cost" in df.columns,
        has_gross_profit="gross_profit" in df.columns,
        has_inventory="inventory" in df.columns,
        has_promotion=("promotion_id" in df.columns) or ("promotion_type" in df.columns),
        has_intraday_time=has_intraday_time,
        missing_optional=[f for f in ALL_CANONICAL_FIELDS if f not in df.columns],
    )
