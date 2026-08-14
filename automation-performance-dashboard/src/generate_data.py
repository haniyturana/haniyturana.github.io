from __future__ import annotations

import random
from datetime import datetime
from pathlib import Path

import polars as pl

CLIENTS = [
    ("C001", "Nusa F&B Group", "Food & Beverage"),
    ("C002", "Aster Retail", "Retail"),
    ("C003", "Meridian Business Services", "Professional Services"),
    ("C004", "Selera Outlet Holdings", "Food & Beverage"),
    ("C005", "Nova Distribution", "Distribution"),
]

PROCESSES = [
    "Supplier invoice processing",
    "Invoice matching",
    "Payment allocation",
    "Daily outlet sales reporting",
    "Purchase reconciliation",
    "Inventory synchronisation",
    "Management report preparation",
]

VALID_STATUSES = ["Success", "Failed", "Exception"]
AUTOMATION_IDS = {
    "Supplier invoice processing": "AUTO-INV-001",
    "Invoice matching": "AUTO-INV-002",
    "Payment allocation": "AUTO-INV-003",
    "Daily outlet sales reporting": "AUTO-REP-001",
    "Purchase reconciliation": "AUTO-REC-001",
    "Inventory synchronisation": "AUTO-INV-004",
    "Management report preparation": "AUTO-REP-002",
}

ERROR_CATEGORIES = [
    "Source data issue",
    "System timeout",
    "Validation rule failure",
    "API integration error",
    "Duplicate record",
    "Missing supplier ID",
    "No exception",
]


def add_months(date_value: datetime, months: int) -> datetime:
    month_index = (date_value.year * 12 + date_value.month - 1) + months
    year = month_index // 12
    month = (month_index % 12) + 1
    return datetime(year, month, 1)


def generate_automation_runs() -> pl.DataFrame:
    rng = random.Random(42)
    rows: list[dict] = []
    month_start = datetime(2025, 1, 1)

    for month_idx in range(24):
        month_date = add_months(month_start, month_idx)
        for client_id, client_name, industry in CLIENTS:
            for process_name in PROCESSES:
                runs_this_month = 12 if process_name == "Daily outlet sales reporting" else 9
                if month_idx in {10, 11}:
                    runs_this_month += 2

                for run_idx in range(runs_this_month):
                    process_bias = 0.96
                    if client_name == "Aster Retail" and month_idx > 6:
                        process_bias -= 0.04 + (month_idx - 6) * 0.006
                    if process_name == "Purchase reconciliation":
                        process_bias -= 0.03
                    if process_name == "Management report preparation":
                        process_bias -= 0.04

                    first_pass_success = rng.random() < max(0.82, min(0.97, process_bias))
                    retry_count = 0
                    if not first_pass_success:
                        retry_roll = rng.random()
                        if process_name == "Purchase reconciliation":
                            retry_count = 1 if retry_roll < 0.35 else 2 if retry_roll < 0.58 else 3
                        elif process_name == "Daily outlet sales reporting":
                            retry_count = 1 if retry_roll < 0.28 else 2 if retry_roll < 0.45 else 3
                        else:
                            retry_count = 1 if retry_roll < 0.18 else 2 if retry_roll < 0.30 else 0

                    success_probability = 0.97 if first_pass_success else 0.90
                    if process_name == "Purchase reconciliation":
                        success_probability -= 0.04
                    if client_name == "Aster Retail" and month_idx > 8:
                        success_probability -= 0.03

                    if rng.random() < success_probability:
                        final_status = "Success"
                    else:
                        final_status = "Failed" if rng.random() < 0.75 else "Exception"

                    records_processed = int(rng.uniform(150, 3500))
                    if process_name == "Daily outlet sales reporting":
                        records_processed = int(rng.uniform(500, 8000))

                    start_timestamp = datetime(
                        month_date.year,
                        month_date.month,
                        1,
                        rng.randint(7, 20),
                        rng.randint(0, 59),
                    )
                    duration_seconds = max(30, int(rng.uniform(80, 2400)))
                    if final_status == "Success" and first_pass_success:
                        duration_seconds = max(45, int(rng.uniform(120, 1800)))
                    if month_idx in {5, 6, 9, 10}:
                        duration_seconds = int(duration_seconds * 1.12)

                    end_timestamp = start_timestamp.timestamp() + duration_seconds
                    end_timestamp = datetime.fromtimestamp(end_timestamp)

                    sla_target_seconds = 1800 if process_name != "Supplier invoice processing" else 2400
                    if process_name == "Management report preparation":
                        sla_target_seconds = 3600
                    sla_met = duration_seconds <= sla_target_seconds
                    if client_name == "Aster Retail" and month_idx > 6:
                        sla_met = rng.random() < 0.78

                    manual_intervention_required = False
                    manual_minutes = 0
                    if process_name == "Management report preparation" and rng.random() < 0.32:
                        manual_intervention_required = True
                        manual_minutes = int(rng.uniform(20, 120))
                    elif process_name == "Daily outlet sales reporting" and rng.random() < 0.18:
                        manual_intervention_required = True
                        manual_minutes = int(rng.uniform(10, 55))

                    estimated_manual_minutes_without_automation = int(rng.uniform(75, 480))
                    if process_name == "Management report preparation":
                        estimated_manual_minutes_without_automation = int(rng.uniform(140, 700))

                    error_category = "No exception"
                    if final_status in {"Failed", "Exception"}:
                        error_category = rng.choice(ERROR_CATEGORIES[:-1])
                    if client_name == "Nova Distribution" and rng.random() < 0.18:
                        error_category = "Source data issue"

                    error_message = "" if final_status == "Success" else f"{error_category} during processing"

                    rows.append(
                        {
                            "run_id": f"RUN-{month_idx + 1:02d}-{client_id}-{process_name[:3].upper()}-{run_idx + 1:03d}",
                            "client_id": client_id,
                            "client_name": client_name,
                            "industry": industry,
                            "automation_id": AUTOMATION_IDS[process_name],
                            "process_name": process_name,
                            "run_date": month_date.strftime("%Y-%m-%d"),
                            "start_timestamp": start_timestamp,
                            "end_timestamp": end_timestamp,
                            "duration_seconds": duration_seconds,
                            "final_status": final_status,
                            "first_pass_success": first_pass_success,
                            "retry_count": retry_count,
                            "records_processed": records_processed,
                            "error_category": error_category,
                            "error_message": error_message,
                            "sla_target_seconds": sla_target_seconds,
                            "sla_met": sla_met,
                            "manual_intervention_required": manual_intervention_required,
                            "manual_minutes": manual_minutes,
                            "estimated_manual_minutes_without_automation": estimated_manual_minutes_without_automation,
                        }
                    )

    return pl.DataFrame(rows)


def generate_business_performance() -> pl.DataFrame:
    rng = random.Random(2024)
    implementation_rng = random.Random(2025)
    rows: list[dict] = []
    month_start = datetime(2025, 1, 1)
    implementation_cost_by_unit = {
        (client_id, process_name): implementation_rng.uniform(1800, 9000)
        for client_id, _, _ in CLIENTS
        for process_name in PROCESSES
    }

    for month_idx in range(24):
        month_date = add_months(month_start, month_idx)
        for client_id, client_name, industry in CLIENTS:
            for process_name in PROCESSES:
                baseline_hours = rng.uniform(90, 420)
                if process_name == "Daily outlet sales reporting":
                    baseline_hours = rng.uniform(160, 600)
                actual_hours = baseline_hours * rng.uniform(0.42, 0.78)
                baseline_error_count = int(rng.uniform(6, 65))
                actual_error_count = max(1, int(baseline_error_count * rng.uniform(0.25, 0.65)))
                baseline_turnaround = int(rng.uniform(220, 420))
                actual_turnaround = max(30, int(baseline_turnaround * rng.uniform(0.35, 0.72)))
                baseline_headcount = int(rng.uniform(2, 9))
                actual_headcount = max(1, int(baseline_headcount * rng.uniform(0.35, 0.7)))
                labour_cost = rng.uniform(18, 42)
                # One-time implementation cost repeated for lineage; ROI logic deduplicates it.
                implementation_cost = implementation_cost_by_unit[(client_id, process_name)]
                monthly_operating_cost = rng.uniform(450, 2200)
                transaction_volume = int(rng.uniform(3000, 30000))

                if month_idx in {10, 11, 12}:
                    transaction_volume = int(transaction_volume * 1.2)

                capacity_hours = max(0.0, baseline_hours - actual_hours)
                gross_labour_value = capacity_hours * labour_cost
                verified_cash_saving = max(0.0, gross_labour_value * rng.uniform(0.55, 0.9))
                avoided_hiring_cost = rng.uniform(1800, 18000) if process_name in {"Daily outlet sales reporting", "Management report preparation"} else rng.uniform(300, 6000)

                rows.append(
                    {
                        "month": month_date.strftime("%Y-%m"),
                        "client_id": client_id,
                        "client_name": client_name,
                        "industry": industry,
                        "process_name": process_name,
                        "transaction_volume": transaction_volume,
                        "baseline_processing_hours": round(baseline_hours, 2),
                        "actual_processing_hours": round(actual_hours, 2),
                        "baseline_error_count": baseline_error_count,
                        "actual_error_count": actual_error_count,
                        "baseline_turnaround_minutes": baseline_turnaround,
                        "actual_turnaround_minutes": actual_turnaround,
                        "baseline_required_headcount": baseline_headcount,
                        "actual_required_headcount": actual_headcount,
                        "labour_cost_per_hour": round(labour_cost, 2),
                        "implementation_cost": round(implementation_cost, 2),
                        "monthly_operating_cost": round(monthly_operating_cost, 2),
                        "verified_cash_saving": round(verified_cash_saving, 2),
                        "avoided_hiring_cost": round(avoided_hiring_cost, 2),
                    }
                )

    return pl.DataFrame(rows)


def generate_data_quality_results() -> pl.DataFrame:
    rows: list[dict] = []
    # Quality checks represent the latest fully completed reporting month.
    quality_check_date = "2026-07-31"
    quality_checks = [
        ("automation_runs.parquet", "run_id", "Uniqueness", "run_id must be unique", 500, 2, 0.996, "High", "Warning"),
        ("automation_runs.parquet", "client_id", "Completeness", "client_id cannot be missing", 500, 3, 0.994, "High", "Warning"),
        ("automation_runs.parquet", "end_timestamp", "Validity", "end_timestamp must be later than start_timestamp", 500, 4, 0.992, "High", "Warning"),
        ("automation_runs.parquet", "duration_seconds", "Validity", "duration_seconds cannot be negative", 500, 1, 0.998, "Medium", "Pass"),
        ("automation_runs.parquet", "final_status", "Consistency", "final_status must use an accepted value", 500, 2, 0.996, "High", "Warning"),
        ("business_performance.parquet", "baseline_processing_hours", "Completeness", "financial baselines must be available before ROI is reported", 420, 5, 0.988, "High", "Warning"),
        ("automation_runs.parquet", "records_processed", "Validity", "records_processed cannot be negative", 500, 1, 0.998, "Medium", "Pass"),
        ("automation_runs.parquet", "pass_rate", "Timeliness", "delayed source-data refresh", 500, 7, 0.986, "Critical", "Fail"),
    ]

    for client_id, client_name, industry in CLIENTS:
        for dataset_name, quality_rule, quality_dimension, rule_name, records_checked, failed_records, pass_rate, severity, status in quality_checks:
            if client_name == "Nova Distribution" and quality_dimension == "Timeliness":
                failed_records = 15
                pass_rate = 0.970
                status = "Fail"
                severity = "Critical"

            if client_name == "Aster Retail" and quality_dimension == "Completeness":
                failed_records = 11
                pass_rate = 0.975
                status = "Warning"

            rows.append(
                {
                    "check_date": quality_check_date,
                    "client_id": client_id,
                    "client_name": client_name,
                    "dataset_name": dataset_name,
                    "quality_rule": rule_name,
                    "quality_dimension": quality_dimension,
                    "records_checked": records_checked,
                    "failed_records": failed_records,
                    "pass_rate": round(pass_rate, 4),
                    "severity": severity,
                    "status": status,
                }
            )

    # Add a direct issue for missing supplier IDs and duplicate runs.
    rows.extend(
        [
            {
                "check_date": quality_check_date,
                "client_id": "C004",
                "client_name": "Selera Outlet Holdings",
                "dataset_name": "supplier_master.parquet",
                "quality_rule": "Missing supplier IDs",
                "quality_dimension": "Completeness",
                "records_checked": 220,
                "failed_records": 9,
                "pass_rate": 0.959,
                "severity": "High",
                "status": "Warning",
            },
            {
                "check_date": quality_check_date,
                "client_id": "C001",
                "client_name": "Nusa F&B Group",
                "dataset_name": "automation_runs.parquet",
                "quality_rule": "Duplicate run IDs",
                "quality_dimension": "Uniqueness",
                "records_checked": 300,
                "failed_records": 4,
                "pass_rate": 0.987,
                "severity": "Medium",
                "status": "Warning",
            },
        ]
    )

    return pl.DataFrame(rows)


def main() -> None:
    output_dir = Path(__file__).resolve().parents[1] / "data"
    output_dir.mkdir(parents=True, exist_ok=True)

    automation_runs = generate_automation_runs()
    business_performance = generate_business_performance()
    quality_results = generate_data_quality_results()

    automation_runs.write_parquet(output_dir / "automation_runs.parquet")
    business_performance.write_parquet(output_dir / "business_performance.parquet")
    quality_results.write_parquet(output_dir / "data_quality_results.parquet")

    print(f"Generated: {len(automation_runs)} automation runs")
    print(f"Generated: {len(business_performance)} business performance records")
    print(f"Generated: {len(quality_results)} data quality checks")


if __name__ == "__main__":
    main()
