import pandas as pd
import pytest

from src.data.loader import DataLoadError, load_raw_file


def test_load_csv_utf8sig():
    content = "Ngày,Mã sản phẩm,Số lượng,Doanh thu\n2026-01-01,SP01,2,50000\n".encode("utf-8-sig")
    df = load_raw_file(content, "test.csv")
    assert list(df.columns) == ["Ngày", "Mã sản phẩm", "Số lượng", "Doanh thu"]
    assert len(df) == 1


def test_load_csv_semicolon_separator():
    content = "Ngay;San_pham;So_luong;Doanh_thu\n2026-01-01;SP01;2;50000\n".encode("utf-8")
    df = load_raw_file(content, "test.csv")
    assert df.shape[1] == 4


def test_unsupported_extension_raises():
    with pytest.raises(DataLoadError):
        load_raw_file(b"abc", "data.txt")


def test_empty_csv_raises():
    with pytest.raises(DataLoadError):
        load_raw_file("col1,col2\n".encode("utf-8"), "empty.csv")


def test_load_xlsx(tmp_path):
    path = tmp_path / "data.xlsx"
    pd.DataFrame({"Ngày": ["2026-01-01"], "Số lượng": [1]}).to_excel(path, index=False)
    df = load_raw_file(path.read_bytes(), "data.xlsx")
    assert "Ngày" in df.columns
