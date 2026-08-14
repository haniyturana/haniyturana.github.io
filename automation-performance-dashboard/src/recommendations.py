from __future__ import annotations

from typing import Any

import polars as pl


def generate_recommendations(runs: pl.DataFrame, quality: pl.DataFrame, performance: pl.DataFrame) -> list[dict[str, Any]]:
    """Apply a transparent, rule-based recommendation engine."""
    recommendations: list[dict[str, Any]] = []

    if runs.is_empty():
        return recommendations

    # First-pass success drop > 5 percentage points
    runs_by_client = runs.group_by(["client_name", "process_name"]).agg(
        pl.len().alias("total_runs"),
        pl.mean("first_pass_success").alias("first_pass_rate"),
        pl.mean((pl.col("retry_count") > 0).cast(pl.Float64)).alias("retry_rate"),
        pl.mean((pl.col("final_status") == "Success").cast(pl.Float64)).alias("final_success_rate"),
        pl.mean((pl.col("sla_met") == True).cast(pl.Float64)).alias("sla_compliance"),
        pl.mean((pl.col("manual_intervention_required") == True).cast(pl.Float64)).alias("manual_intervention_rate"),
    )

    for row in runs_by_client.to_dicts():
        if row["first_pass_rate"] is not None and row["first_pass_rate"] < 0.95:
            recommendations.append({
                "Finding": "First-pass automation quality has weakened.",
                "Supporting metric": f"{row['first_pass_rate'] * 100:.0f}% first-pass success",
                "Client": row["client_name"],
                "Process": row["process_name"],
                "Evidence period": "Rolling 12 months",
                "Severity": "High",
                "Recommended action": "Review exception handling, data quality and retry logic to improve first-attempt completion.",
            })

        if row["retry_rate"] is not None and row["retry_rate"] > 0.10:
            recommendations.append({
                "Finding": "Retry activity exceeds the acceptable threshold.",
                "Supporting metric": f"{row['retry_rate'] * 100:.0f}% retry rate",
                "Client": row["client_name"],
                "Process": row["process_name"],
                "Evidence period": "Rolling 12 months",
                "Severity": "High",
                "Recommended action": "Run root-cause analysis on retry triggers and monitor upstream data or integration health.",
            })

        if row["manual_intervention_rate"] is not None and row["manual_intervention_rate"] > 0.08:
            recommendations.append({
                "Finding": "Manual handling remains elevated for this process.",
                "Supporting metric": f"{row['manual_intervention_rate'] * 100:.0f}% manual intervention",
                "Client": row["client_name"],
                "Process": row["process_name"],
                "Evidence period": "Rolling 12 months",
                "Severity": "Medium",
                "Recommended action": "Review process exceptions and assess whether additional rules or workflow automation are required.",
            })

        if row["sla_compliance"] is not None and row["sla_compliance"] < 0.95:
            recommendations.append({
                "Finding": "SLA compliance is below the target threshold.",
                "Supporting metric": f"{row['sla_compliance'] * 100:.0f}% SLA compliance",
                "Client": row["client_name"],
                "Process": row["process_name"],
                "Evidence period": "Rolling 12 months",
                "Severity": "Warning",
                "Recommended action": "Prioritise performance tuning and source-data checks to restore service-level delivery.",
            })

    if not quality.is_empty():
        quality_summary = quality.group_by("client_name").agg(pl.mean("pass_rate").alias("average_pass_rate"))
        for row in quality_summary.to_dicts():
            if row["average_pass_rate"] is not None and row["average_pass_rate"] < 0.98:
                recommendations.append({
                    "Finding": "Data quality is below the reliability threshold.",
                    "Supporting metric": f"{row['average_pass_rate'] * 100:.0f}% average pass rate",
                    "Client": row["client_name"],
                    "Process": "All automation datasets",
                    "Evidence period": "Current review window",
                    "Severity": "High",
                    "Recommended action": "Treat related KPIs as provisional and resolve data-quality issues before making operational decisions.",
                })

    if not performance.is_empty():
        roi_months = performance.group_by(["client_name", "process_name", "month"]).agg(
            (pl.col("verified_cash_saving") + pl.col("avoided_hiring_cost") - pl.col("monthly_operating_cost") - pl.col("implementation_cost")).alias("net_benefit")
        )
        for client in sorted(performance["client_name"].unique().to_list()):
            client_rows = roi_months.filter(pl.col("client_name") == client)
            if client_rows.is_empty():
                continue
            negatives = client_rows.filter(pl.col("net_benefit") < 0)
            if negatives.height >= 3:
                recommendations.append({
                    "Finding": "ROI has remained negative across multiple months.",
                    "Supporting metric": f"{negatives.height} months with negative net benefit",
                    "Client": client,
                    "Process": "Portfolio-wide",
                    "Evidence period": "Rolling 12 months",
                    "Severity": "Critical",
                    "Recommended action": "Review automation costs, process suitability and expected benefit assumptions with the business sponsor.",
                })

    return recommendations
