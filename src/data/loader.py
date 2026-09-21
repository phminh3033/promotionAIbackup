"""Đọc file dữ liệu bán hàng (CSV/XLSX) do doanh nghiệp tải lên."""
from __future__ import annotations

import io

import pandas as pd


class DataLoadError(Exception):
    """Lỗi khi không đọc được file dữ liệu."""


def list_excel_sheets(file_bytes: bytes) -> list[str]:
    """Liệt kê tên các sheet trong file Excel (dùng để cho người dùng chọn sheet dữ liệu bán hàng
    khi file có nhiều sheet, ví dụ Sales_Data / Promotion_Master / Business_Config)."""
    try:
        buffer = io.BytesIO(file_bytes)
        xls = pd.ExcelFile(buffer)
        return list(xls.sheet_names)
    except Exception:  # noqa: BLE001
        return []


# Tên sheet ưu tiên tự động chọn làm dữ liệu bán hàng chính khi không có chỉ định của người dùng.
_PREFERRED_SALES_SHEET_NAMES = ["sales_data", "sales data", "sale_data", "data", "sales"]


def load_raw_file(file_bytes: bytes, filename: str, sheet_name: str | None = None) -> pd.DataFrame:
    """Đọc file CSV hoặc XLSX thành DataFrame thô (chưa mapping cột).

    Với file Excel nhiều sheet (ví dụ mẫu PromotionPilot AI có Sales_Data/Promotion_Master/
    Business_Config), nếu không chỉ định `sheet_name`, tự động ưu tiên sheet tên giống
    "Sales_Data"; nếu không tìm thấy, dùng sheet đầu tiên.

    Không raise crash khó hiểu cho người dùng cuối — mọi lỗi được bọc lại
    thành DataLoadError với thông điệp tiếng Việt.
    """
    name_lower = filename.lower()
    buffer = io.BytesIO(file_bytes)
    try:
        if name_lower.endswith(".csv"):
            df = _read_csv_with_fallback(buffer)
        elif name_lower.endswith((".xlsx", ".xls")):
            if sheet_name is None:
                sheets = list_excel_sheets(file_bytes)
                sheet_name = next(
                    (s for s in sheets if s.strip().lower() in _PREFERRED_SALES_SHEET_NAMES),
                    sheets[0] if sheets else 0,
                )
            df = pd.read_excel(buffer, sheet_name=sheet_name)
        else:
            raise DataLoadError(
                "Định dạng file không được hỗ trợ. Vui lòng tải lên file .csv hoặc .xlsx."
            )
    except DataLoadError:
        raise
    except Exception as exc:  # noqa: BLE001 - cố ý bắt rộng để không crash UI
        raise DataLoadError(
            f"Không thể đọc file '{filename}'. Vui lòng kiểm tra định dạng file. "
            f"Chi tiết kỹ thuật: {exc}"
        ) from exc

    if df.empty:
        raise DataLoadError("File dữ liệu rỗng, không có dòng nào để phân tích.")

    df.columns = [str(c).strip() for c in df.columns]
    return df


def _read_csv_with_fallback(buffer: io.BytesIO) -> pd.DataFrame:
    """Thử nhiều encoding/separator phổ biến tại Việt Nam (POS thường xuất UTF-8-SIG hoặc CP1258/Windows-1252)."""
    encodings = ["utf-8-sig", "utf-8", "cp1258", "windows-1252"]
    separators = [",", ";", "\t"]
    last_error: Exception | None = None
    for enc in encodings:
        for sep in separators:
            try:
                buffer.seek(0)
                df = pd.read_csv(buffer, encoding=enc, sep=sep, low_memory=False)
                if df.shape[1] > 1:
                    return df
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                continue
    if last_error:
        raise last_error
    raise DataLoadError("Không xác định được định dạng CSV.")
