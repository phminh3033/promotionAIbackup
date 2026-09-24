"""Warmup trước buổi demo: nạp demo + 1 forecast để nạp cache model."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.data.loader import load_raw_file
from src.data.mapper import apply_mapping, suggest_mapping, validate_mapping
from src.data.quality import run_quality_check
from src.features.engineering import aggregate_daily
from src.forecasting.selector import select_and_forecast


def main() -> None:
    demo = ROOT / "data" / "pharmacity_demo.csv"
    if not demo.exists():
        raise SystemExit(f"Thiếu {demo} — chạy scripts/generate_pharmacity_demo.py")
    print("[1] Đọc demo...")
    raw = load_raw_file(demo.read_bytes(), demo.name)
    mapping = suggest_mapping(list(raw.columns))
    err = validate_mapping(mapping)
    if err:
        raise SystemExit("; ".join(err))
    mapped = apply_mapping(raw, mapping)
    clean, report = run_quality_check(mapped)
    print(f"[2] Clean {len(clean):,} dòng, score={report.score}")
    daily = aggregate_daily(clean)
    y = daily.set_index("day")["revenue"].astype(float)
    print("[3] Forecast doanh thu horizon=14...")
    result = select_and_forecast(y, horizon=14, series_name="Doanh thu")
    print(f"[4] Model={result.model_name} WAPE={result.wape:.2%} — warmup OK")


if __name__ == "__main__":
    main()
