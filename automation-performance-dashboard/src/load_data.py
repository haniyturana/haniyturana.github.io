from __future__ import annotations

from pathlib import Path

import polars as pl

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"


def load_automation_runs() -> pl.DataFrame:
    path = DATA_DIR / "automation_runs.parquet"
    return pl.read_parquet(path)


def load_business_performance() -> pl.DataFrame:
    path = DATA_DIR / "business_performance.parquet"
    return pl.read_parquet(path)


def load_data_quality() -> pl.DataFrame:
    path = DATA_DIR / "data_quality_results.parquet"
    return pl.read_parquet(path)


def format_currency(value: float) -> str:
    return f"RM {value:,.0f}"


def format_percent(value: float) -> str:
    return f"{value * 100:.0f}%" if value <= 1 else f"{value:.0f}%"


def as_month_label(value):
    if value is None:
        return "Unknown"
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m")
    return str(value)
