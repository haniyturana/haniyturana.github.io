from __future__ import annotations

from typing import Iterable

import polars as pl

VALID_STATUSES = {"Success", "Failed", "Exception"}


def _safe_ratio(numerator: float, denominator: float) -> float:
    if denominator in (None, 0):
        return 0.0
    return float(numerator / denominator)


def first_pass_success_rate(df: pl.DataFrame) -> float:
    """Percentage of runs that succeeded without retry."""
    if df.is_empty():
        return 0.0
    values = df.get_column("first_pass_success").fill_null(False).cast(pl.Boolean)
    return _safe_ratio(values.sum(), len(values))


def final_success_rate(df: pl.DataFrame) -> float:
    """Percentage of runs that ended in a successful final status."""
    if df.is_empty():
        return 0.0
    status = df.get_column("final_status").fill_null("")
    success_count = status.eq("Success").sum()
    return _safe_ratio(success_count, len(status))


def retry_rate(df: pl.DataFrame) -> float:
    """Percentage of runs where retry_count is greater than zero."""
    if df.is_empty():
        return 0.0
    retries = df.get_column("retry_count").fill_null(0)
    retry_count = (retries > 0).sum()
    return _safe_ratio(retry_count, len(retries))


def capacity_hours_released(df: pl.DataFrame) -> float:
    """Total hours freed by automation versus baseline processing time."""
    if df.is_empty():
        return 0.0
    baseline = df.get_column("baseline_processing_hours").fill_null(0.0)
    actual = df.get_column("actual_processing_hours").fill_null(0.0)
    return float((baseline - actual).sum())


def implementation_cost_total(df: pl.DataFrame) -> float:
    """Return one implementation cost per client-process implementation unit."""
    if df.is_empty() or "implementation_cost" not in df.columns:
        return 0.0
    grain = [column for column in ("client_id", "client_name", "process_name") if column in df.columns]
    if not grain:
        return float(df.get_column("implementation_cost").fill_null(0.0).max() or 0.0)
    return float(
        df.group_by(grain)
        .agg(pl.col("implementation_cost").fill_null(0.0).max().alias("implementation_cost"))
        .get_column("implementation_cost")
        .sum()
    )


def net_financial_benefit(df: pl.DataFrame) -> float:
    """Net financial benefit after cost deductions."""
    if df.is_empty():
        return 0.0
    recurring_net_benefit = (
        df.get_column("verified_cash_saving").fill_null(0.0)
        + df.get_column("avoided_hiring_cost").fill_null(0.0)
        - df.get_column("monthly_operating_cost").fill_null(0.0)
    ).sum()
    return float(recurring_net_benefit - implementation_cost_total(df))


def roi_percentage(benefit: float, total_cost: float) -> float:
    """Return ROI as a percentage, safely handling zero denominators."""
    if total_cost in (None, 0):
        return 0.0
    return float((benefit / total_cost) * 100)


def payback_period(implementation_cost: float, average_monthly_positive_net_benefit: float) -> float:
    """Months to recover the implementation cost based on average monthly net benefit."""
    if implementation_cost in (None, 0) or average_monthly_positive_net_benefit in (None, 0):
        return 0.0
    if average_monthly_positive_net_benefit <= 0:
        return 0.0
    return float(implementation_cost / average_monthly_positive_net_benefit)


def detect_invalid_status(df: pl.DataFrame) -> list[str]:
    """Return unique invalid statuses in the data set while preserving input order."""
    if df.is_empty() or "final_status" not in df.columns:
        return []
    statuses = df.get_column("final_status").fill_null("").cast(pl.String)
    invalid: list[str] = []
    seen: set[str] = set()
    for value in statuses.to_list():
        text = str(value)
        if text and text not in VALID_STATUSES and text not in seen:
            invalid.append(text)
            seen.add(text)
    return invalid


def detect_duplicate_run_ids(df: pl.DataFrame) -> list[str]:
    """Return duplicate run IDs that would compromise lineage accuracy."""
    if df.is_empty() or "run_id" not in df.columns:
        return []
    run_ids = df.get_column("run_id").cast(pl.String).fill_null("")
    duplicates = run_ids.filter(run_ids.is_duplicated())
    return sorted({str(value) for value in duplicates.unique().to_list() if value})


def financial_benefit_components(df: pl.DataFrame) -> dict[str, float]:
    """Return a dictionary of core financial metrics from business performance data."""
    return {
        "capacity_hours_released": float(capacity_hours_released(df)),
        "gross_labour_value": float(
            (
                (df.get_column("baseline_processing_hours").fill_null(0.0)
                 - df.get_column("actual_processing_hours").fill_null(0.0))
                * df.get_column("labour_cost_per_hour").fill_null(0.0)
            ).sum()
        ),
        "net_financial_benefit": float(net_financial_benefit(df)),
    }


def safe_mean(values: Iterable[float]) -> float:
    """Calculate mean safely, returning 0.0 for empty inputs."""
    values = list(values)
    if not values:
        return 0.0
    return float(sum(values) / len(values))
