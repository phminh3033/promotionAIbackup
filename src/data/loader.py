"""Đọc file dữ liệu bán hàng (CSV/XLSX) do doanh nghiệp tải lên."""
from __future__ import annotations

import io

import pandas as pd


class DataLoadError(Exception):
    """Lỗi khi không đọc được file dữ liệu."""


def load_raw_file(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Đọc file CSV hoặc XLSX thành DataFrame thô (chưa mapping cột).

    Không raise crash khó hiểu cho người dùng cuối — mọi lỗi được bọc lại
    thành DataLoadError với thông điệp tiếng Việt.
    """
    name_lower = filename.lower()
    buffer = io.BytesIO(file_bytes)
    try:
        if name_lower.endswith(".csv"):
            df = _read_csv_with_fallback(buffer)
        elif name_lower.endswith((".xlsx", ".xls")):
            df = pd.read_excel(buffer)
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
                df = pd.read_csv(buffer, encoding=enc, sep=sep)
                if df.shape[1] > 1:
                    return df
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                continue
    if last_error:
        raise last_error
    raise DataLoadError("Không xác định được định dạng CSV.")
