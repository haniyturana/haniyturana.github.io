from __future__ import annotations

from pathlib import Path

import polars as pl
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from src.load_data import format_currency
from src.metrics import (
    final_success_rate,
    first_pass_success_rate,
    implementation_cost_total,
    retry_rate,
    roi_percentage,
)
from src.styles import get_app_css

st.set_page_config(page_title="Automation Performance Dashboard", page_icon="📈", layout="wide")
st.markdown(get_app_css(), unsafe_allow_html=True)
st.markdown("""
<style>
section[data-testid="stSidebar"], section[data-testid="stSidebar"] > div {
    background: white !important; background-color: white !important;
}
section[data-testid="stSidebar"] * { color: #102a43 !important; }
[data-testid="stSidebarNav"] li:first-child a > * { display: none !important; }
[data-testid="stSidebarNav"] li:first-child a { font-size: 0 !important; }
[data-testid="stSidebarNav"] li:first-child a::after { content: "Executive Summary"; font-size: 0.875rem; }
</style>
""", unsafe_allow_html=True)
st.title("Automation Performance & ROI Intelligence")

data_dir = Path(__file__).resolve().parent / "data"
runs = pl.read_parquet(data_dir / "automation_runs.parquet")
performance = pl.read_parquet(data_dir / "business_performance.parquet")

# Keep older in-memory demo data aligned with the current 2026 reporting period.
if runs["run_date"].str.slice(0, 4).min() == "2024":
    runs = runs.with_columns(pl.col("run_date").str.replace(r"^2024", "2026"))
if performance["month"].str.slice(0, 4).min() == "2024":
    performance = performance.with_columns(pl.col("month").str.replace(r"^2024", "2026"))


# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Global filters")

    date_min = runs["run_date"].str.to_date().min()
    date_max = runs["run_date"].str.to_date().max()
    start_date = st.date_input(
        "Date range start", value=date_min, min_value=date_min, max_value=date_max, key="date_start_2025_2026"
    )
    end_date = st.date_input(
        "Date range end", value=date_max, min_value=date_min, max_value=date_max, key="date_end_2025_2026"
    )

    industry_options = sorted(runs["industry"].unique().to_list())
    industry_choice = st.selectbox("Industry", ["All industries", *industry_options], key="global_industry_v2")
    industry_filter = industry_options if industry_choice == "All industries" else [industry_choice]

    filter_scope = runs.filter(pl.col("industry").is_in(industry_filter))
    client_options = sorted(filter_scope["client_name"].unique().to_list())
    client_choice = st.selectbox(
        "Client", ["All clients", *client_options], key=f"global_client_v2_{industry_choice}"
    )
    client_filter = client_options if client_choice == "All clients" else [client_choice]
    filter_scope = filter_scope.filter(pl.col("client_name").is_in(client_filter))

    process_options = sorted(filter_scope["process_name"].unique().to_list())
    process_choice = st.selectbox(
        "Business process", ["All processes", *process_options],
        key=f"global_process_v2_{industry_choice}_{client_choice}",
    )
    process_filter = process_options if process_choice == "All processes" else [process_choice]
    filter_scope = filter_scope.filter(pl.col("process_name").is_in(process_filter))

    automation_options = sorted(filter_scope["automation_id"].unique().to_list())
    automation_choice = st.selectbox(
        "Automation", ["All automations", *automation_options],
        key=f"global_automation_v2_{industry_choice}_{client_choice}_{process_choice}",
    )
    automation_filter = automation_options if automation_choice == "All automations" else [automation_choice]

    status_options = sorted(filter_scope["final_status"].unique().to_list())
    status_choice = st.selectbox("Final status", ["All statuses", *status_options], key="global_status_v2")
    status_filter = status_options if status_choice == "All statuses" else [status_choice]


# ---------------------------------------------------------------------------
# Apply filters
# ---------------------------------------------------------------------------
filtered_runs = runs.filter(
    pl.col("run_date").str.to_date().is_between(start_date, end_date),
    pl.col("client_name").is_in(client_filter),
    pl.col("industry").is_in(industry_filter),
    pl.col("process_name").is_in(process_filter),
    pl.col("automation_id").is_in(automation_filter),
    pl.col("final_status").is_in(status_filter),
)

filtered_performance = performance.filter(
    pl.col("month").str.to_date("%Y-%m").is_between(start_date, end_date),
    pl.col("client_name").is_in(client_filter),
    pl.col("industry").is_in(industry_filter),
    pl.col("process_name").is_in(process_filter),
)

if automation_choice != "All automations":
    automation_processes = runs.filter(pl.col("automation_id") == automation_choice)["process_name"].unique().to_list()
    filtered_performance = filtered_performance.filter(pl.col("process_name").is_in(automation_processes))

if filtered_runs.is_empty() or filtered_performance.is_empty():
    st.warning("No data matches the current filters. Adjust the filters or clear selections to resume the dashboard.")
    st.stop()


# ---------------------------------------------------------------------------
# KPI metrics
# ---------------------------------------------------------------------------
def col_sum(df: pl.DataFrame, column: str) -> float:
    """Sum a column, treating nulls as zero."""
    return float(df.get_column(column).fill_null(0.0).sum())


first_pass = first_pass_success_rate(filtered_runs)
final_rate = final_success_rate(filtered_runs)
retry = retry_rate(filtered_runs)
sla = float(filtered_runs.get_column("sla_met").fill_null(False).mean())
manual_rate = float(filtered_runs.get_column("manual_intervention_required").fill_null(False).mean())
capacity_hours = (
    col_sum(filtered_runs, "estimated_manual_minutes_without_automation")
    - col_sum(filtered_runs, "manual_minutes")
) / 60
implementation_cost = implementation_cost_total(filtered_performance)

net_benefit = (
    col_sum(filtered_performance, "verified_cash_saving")
    + col_sum(filtered_performance, "avoided_hiring_cost")
    - col_sum(filtered_performance, "monthly_operating_cost")
    - implementation_cost
)
reo_cost = implementation_cost + col_sum(filtered_performance, "monthly_operating_cost")
roi = roi_percentage(net_benefit, reo_cost)

monthly_benefit = (
    filtered_performance.group_by("month")
    .agg(
        (
            pl.sum("verified_cash_saving")
            + pl.sum("avoided_hiring_cost")
            - pl.sum("monthly_operating_cost")
        ).alias("monthly_benefit")
    )
    .get_column("monthly_benefit")
)
positive_monthly_benefit = monthly_benefit.filter(monthly_benefit > 0)
average_positive_monthly_net_benefit = (
    float(positive_monthly_benefit.mean()) if not positive_monthly_benefit.is_empty() else 0.0
)
payback = (
    implementation_cost / average_positive_monthly_net_benefit
    if average_positive_monthly_net_benefit > 0
    else 0.0
)

kpis = [
    ("Total automation runs", f"{filtered_runs.height:,}", ""),
    ("First-pass success rate", f"{first_pass:.0%}", "positive"),
    ("Final success rate", f"{final_rate:.0%}", "positive"),
    ("SLA compliance", f"{sla:.0%}", "positive"),
    ("Manual intervention rate", f"{manual_rate:.0%}", "warning"),
    ("Hours of capacity released", f"{capacity_hours:,.0f}", "positive"),
    ("Net financial benefit", format_currency(net_benefit), "positive" if net_benefit >= 0 else "critical"),
    ("ROI", f"{roi:.0f}%", "positive" if roi >= 0 else "critical"),
    ("Estimated payback period", f"{payback:.0f} months", "positive"),
]

cols = st.columns(3)
for index, (label, value, tone) in enumerate(kpis):
    with cols[index % 3]:
        st.markdown(
            f'<div class="kpi-card"><div class="metric-label">{label}</div>'
            f'<div class="metric-value {tone}">{value}</div></div>',
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
st.subheader("Monthly automation volume and success-rate trend")
monthly = (
    filtered_runs.group_by("run_date")
    .agg(
        pl.len().alias("runs"),
        pl.col("final_status").eq("Success").sum().alias("success_count"),
    )
    .with_columns((pl.col("success_count") / pl.col("runs")).alias("success_rate"))
    .sort("run_date")
)
monthly_data = monthly.to_pandas()
trend_chart = make_subplots(specs=[[{"secondary_y": True}]])
trend_chart.add_trace(
    go.Bar(
        x=monthly_data["run_date"], y=monthly_data["runs"], name="Runs", marker_color="#B8D8D3",
        hovertemplate="%{x}<br>Runs: %{y:,.0f}<extra></extra>",
    ),
    secondary_y=False,
)
trend_chart.add_trace(
    go.Scatter(x=monthly_data["run_date"], y=monthly_data["success_rate"], name="Success rate",
               mode="lines+markers", line={"color": "#0F766E", "width": 3},
               hovertemplate="%{x}<br>Success rate: %{y:.0%}<extra></extra>"),
    secondary_y=True,
)
trend_chart.update_yaxes(
    title_text="Runs", secondary_y=False, rangemode="tozero", gridcolor="#E2E8F0", tickformat=",.0f"
)
trend_chart.update_yaxes(title_text="Success rate", secondary_y=True, tickformat=".0%", range=[0.8, 1.01])
trend_chart.update_layout(
    plot_bgcolor="white", paper_bgcolor="white", height=410, hovermode="x unified",
    legend={"orientation": "h", "y": 1.1}, margin={"l": 20, "r": 20, "t": 35, "b": 20},
)
st.plotly_chart(trend_chart, width="stretch")

client_capacity = filtered_runs.group_by("client_name").agg(
    (
        (pl.sum("estimated_manual_minutes_without_automation") - pl.sum("manual_minutes")) / 60
    ).alias("hours_released"),
)
client_financials = filtered_performance.group_by("client_name").agg(
    pl.sum("verified_cash_saving").alias("cash_saving"),
    pl.sum("avoided_hiring_cost").alias("hiring_cost_avoided"),
    pl.sum("monthly_operating_cost").alias("operating_cost"),
)
client_implementation_cost = (
    filtered_performance.group_by(["client_name", "process_name"])
    .agg(pl.max("implementation_cost").alias("implementation_cost"))
    .group_by("client_name")
    .agg(pl.sum("implementation_cost"))
)
client_benefit = client_financials.join(client_implementation_cost, on="client_name", how="left").with_columns(
    (pl.col("cash_saving") + pl.col("hiring_cost_avoided") - pl.col("operating_cost") - pl.col("implementation_cost"))
    .alias("net_benefit")
)

capacity_chart = px.bar(
    client_capacity.sort("hours_released").to_pandas(), x="client_name", y="hours_released",
    labels={"client_name": "Client", "hours_released": "Hours"}, text_auto=",.0f",
    color_discrete_sequence=["#0F766E"],
)
capacity_chart.update_layout(height=340, showlegend=False, plot_bgcolor="white", paper_bgcolor="white",
                             margin={"l": 15, "r": 15, "t": 15, "b": 15})
capacity_chart.update_traces(hovertemplate="%{x}<br>Hours: %{y:,.0f}<extra></extra>")
capacity_chart.update_yaxes(gridcolor="#E2E8F0", tickformat=",.0f")

benefit_data = client_benefit.sort("net_benefit").to_pandas()
benefit_chart = px.bar(
    benefit_data, x="client_name", y="net_benefit",
    labels={"client_name": "Client", "net_benefit": "Net benefit (RM)"}, text_auto=",.0f",
    color_discrete_sequence=["#0F766E"],
)
benefit_chart.update_traces(
    marker_color=["#0F766E" if value >= 0 else "#B91C1C" for value in benefit_data["net_benefit"]],
    hovertemplate="%{x}<br>Net benefit: RM %{y:,.0f}<extra></extra>",
)
benefit_chart.update_layout(height=340, showlegend=False, plot_bgcolor="white", paper_bgcolor="white",
                            margin={"l": 15, "r": 15, "t": 15, "b": 15})
benefit_chart.update_yaxes(gridcolor="#E2E8F0", zerolinecolor="#94A3B8", tickformat=",.0f")

left_chart, right_chart = st.columns(2)
with left_chart:
    st.markdown("### Capacity released by client")
    st.plotly_chart(capacity_chart, width="stretch")
with right_chart:
    st.markdown("### Net benefit by client")
    st.plotly_chart(benefit_chart, width="stretch")

error_counts = (
    filtered_runs.filter(pl.col("final_status") != "Success")
    .group_by("error_category")
    .agg(pl.len().alias("fault_count"))
)
performance_summary = filtered_performance.group_by("process_name").agg(
    pl.mean("baseline_processing_hours").alias("baseline_hours"),
    pl.mean("actual_processing_hours").alias("actual_hours"),
    pl.mean("baseline_turnaround_minutes").alias("baseline_turnaround"),
    pl.mean("actual_turnaround_minutes").alias("actual_turnaround"),
).sort("actual_hours")

detail_left, detail_right = st.columns(2)
with detail_left:
    st.markdown("### Failure mix")
    if error_counts.is_empty():
        st.info("No failures in the current selection.")
    else:
        failure_chart = px.pie(
            error_counts.to_pandas(), names="error_category", values="fault_count", hole=0.58,
            color_discrete_sequence=px.colors.qualitative.Safe,
        )
        failure_chart.update_layout(height=360, margin={"l": 10, "r": 10, "t": 15, "b": 15},
                                    legend={"orientation": "h", "y": -0.08})
        st.plotly_chart(failure_chart, width="stretch")
with detail_right:
    st.markdown("### Processing hours: baseline vs actual")
    performance_chart = px.bar(
        performance_summary.to_pandas(), y="process_name", x=["baseline_hours", "actual_hours"],
        barmode="group", orientation="h",
        labels={"process_name": "", "value": "Average hours", "variable": "Measure"},
        color_discrete_map={"baseline_hours": "#94A3B8", "actual_hours": "#0F766E"},
    )
    performance_chart.for_each_trace(lambda trace: trace.update(name="Baseline" if trace.name == "baseline_hours" else "Actual"))
    performance_chart.update_layout(height=360, plot_bgcolor="white", paper_bgcolor="white",
                                    legend={"orientation": "h", "y": 1.08}, margin={"l": 15, "r": 15, "t": 15, "b": 15})
    performance_chart.update_xaxes(gridcolor="#E2E8F0")
    st.plotly_chart(performance_chart, width="stretch")


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------
st.subheader("Rule-based management recommendations and alerts")

alert_rules = [
    (first_pass < 0.95, f"First-pass success is {first_pass:.0%}; exception handling needs attention."),
    (retry > 0.10, f"Retry rate is {retry:.0%}; run a root-cause review for the affected automation."),
    (manual_rate > 0.08, f"Manual intervention sits at {manual_rate:.0%}; review process design and exception routing."),
    (sla < 0.95, f"SLA compliance is {sla:.0%}; service performance is below the management target."),
    (net_benefit < 0, "Net benefit is negative for the current selection; validate cost assumptions and process suitability."),
]
alerts = [message for condition, message in alert_rules if condition]

if not alerts:
    st.success("No critical automation alerts for the current selection.")
for alert in alerts:
    st.warning(alert)

st.markdown(
    "> Time saved does not automatically represent salary reduction. It may represent additional operating "
    "capacity, faster processing or avoidance of future hiring. Actual cash savings should be validated by "
    "the client's finance team."
)
