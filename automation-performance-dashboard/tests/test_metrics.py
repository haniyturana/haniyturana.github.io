import polars as pl

from src.metrics import (
    capacity_hours_released,
    detect_duplicate_run_ids,
    detect_invalid_status,
    final_success_rate,
    first_pass_success_rate,
    implementation_cost_total,
    net_financial_benefit,
    payback_period,
    retry_rate,
    roi_percentage,
)


def test_first_pass_success_rate():
    df = pl.DataFrame(
        {
            "first_pass_success": [True, True, False, False, True, False],
            "final_status": ["Success", "Success", "Success", "Failed", "Success", "Exception"],
        }
    )
    assert first_pass_success_rate(df) == 0.5


def test_final_success_rate():
    df = pl.DataFrame({"final_status": ["Success", "Success", "Failed", "Exception", "Success"]})
    assert final_success_rate(df) == 0.6


def test_retry_rate():
    df = pl.DataFrame({"retry_count": [0, 1, 2, 0, 3]})
    assert retry_rate(df) == 0.6


def test_capacity_hours_released():
    df = pl.DataFrame(
        {
            "baseline_processing_hours": [100, 80, 45],
            "actual_processing_hours": [60, 50, 40],
        }
    )
    assert capacity_hours_released(df) == 75.0


def test_net_financial_benefit():
    df = pl.DataFrame(
        {
            "client_id": ["C001", "C001"],
            "process_name": ["Reporting", "Reporting"],
            "verified_cash_saving": [5000, 3000],
            "avoided_hiring_cost": [2000, 0],
            "monthly_operating_cost": [1500, 1000],
            "implementation_cost": [1200, 1200],
        }
    )
    assert implementation_cost_total(df) == 1200.0
    assert net_financial_benefit(df) == 6300.0


def test_roi_percentage():
    assert roi_percentage(2500, 10000) == 25.0
    assert roi_percentage(-500, 10000) == -5.0
    assert roi_percentage(0, 0) == 0.0


def test_payback_period():
    assert payback_period(5000, 2000) == 2.5
    assert payback_period(0, 0) == 0.0
    assert payback_period(5000, -100) == 0.0


def test_division_by_zero_handling():
    assert roi_percentage(100, 0) == 0.0
    assert payback_period(0, 0) == 0.0


def test_invalid_status_detection():
    df = pl.DataFrame({"final_status": ["Success", "Retried", "Exception", "Unknown"]})
    assert detect_invalid_status(df) == ["Retried", "Unknown"]


def test_duplicate_run_id_detection():
    df = pl.DataFrame({"run_id": ["A1", "A2", "A1", "A3"]})
    assert detect_duplicate_run_ids(df) == ["A1"]
