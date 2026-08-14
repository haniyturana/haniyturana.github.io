from __future__ import annotations

import polars as pl
import plotly.express as px
import streamlit as st

from src.load_data import load_automation_runs
from src.metrics import final_success_rate, first_pass_success_rate, retry_rate
from src.styles import get_app_css

st.set_page_config(page_title="Automation Health | Automation Intelligence", page_icon="⚙️", layout="wide")
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

runs = load_automation_runs()

st.title("Automation Health")
st.caption("Operational reliability, retry behaviour and SLA performance across the automation portfolio.")

if runs.is_empty():
    st.warning("No automation data available.")
    st.stop()

clients = sorted(runs["client_name"].unique().to_list())
processes = sorted(runs["process_name"].unique().to_list())
with st.sidebar:
    st.header("Filters")
    client_choice = st.selectbox("Client", ["All clients", *clients])
    process_choice = st.selectbox("Business process", ["All processes", *processes])
filtered = runs
if client_choice != "All clients":
    filtered = filtered.filter(pl.col("client_name") == client_choice)
if process_choice != "All processes":
    filtered = filtered.filter(pl.col("process_name") == process_choice)

kpi_cols = st.columns(4)
with kpi_cols[0]:
    st.metric("Total runs", f"{filtered.height:,}")
with kpi_cols[1]:
    st.metric("First-pass success", f"{first_pass_success_rate(filtered):.0%}")
with kpi_cols[2]:
    st.metric("Final success", f"{final_success_rate(filtered):.0%}")
with kpi_cols[3]:
    st.metric("Retry rate", f"{retry_rate(filtered):.0%}")

col1, col2 = st.columns(2)
with col1:
    monthly_failures = filtered.group_by("run_date").agg(
        pl.len().alias("runs"),
        (pl.col("final_status") != "Success").sum().alias("failures"),
    ).with_columns((pl.col("failures") / pl.col("runs")).alias("failure_rate")).sort("run_date")
    monthly_failure_data = monthly_failures.to_pandas()
    fig = px.line(
        monthly_failure_data, x="run_date", y="failure_rate", markers=True,
        title="Monthly failure-rate trend", labels={"run_date": "Month", "failure_rate": "Failure rate"},
    )
    fig.update_traces(
        mode="lines+markers",
        line={"color": "#1769AA", "width": 2},
        marker={
            "color": "#1769AA", "size": 3,
            "line": {"width": 0},
        },
        hovertemplate="%{x}<br>Failure rate: %{y:.0%}<extra></extra>",
    )
    for row in monthly_failure_data.itertuples(index=False):
        fig.add_annotation(
            x=row.run_date,
            y=row.failure_rate,
            text=f"{row.failure_rate:.0%}",
            showarrow=False,
            bgcolor="rgba(255,255,255,0.92)",
            borderpad=1,
            font={"size": 10, "color": "#1769AA", "family": "Arial"},
        )
    fig.update_yaxes(tickformat=".0%", rangemode="tozero", gridcolor="#E2E8F0")
    fig.update_xaxes(gridcolor="#F1F5F9")
    fig.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        margin={"l": 15, "r": 20, "t": 55, "b": 15},
    )
    st.plotly_chart(fig, width="stretch")
with col2:
    error_counts = filtered.filter(pl.col("final_status") != "Success").group_by("error_category").agg(pl.len().alias("count"))
    total_errors = error_counts["count"].sum()
    error_counts = error_counts.with_columns(
        (pl.col("count") / total_errors if total_errors else pl.lit(0.0)).alias("error_share")
    ).sort("error_share", descending=True)
    fig2 = px.bar(
        error_counts.to_pandas(), x="error_category", y="error_share", title="Error-category share",
        labels={"error_category": "Error category", "error_share": "Share of failures"},
        text=[f"{value:.0%}" for value in error_counts["error_share"]],
        color_discrete_sequence=["#1769AA"],
    )
    fig2.update_traces(textposition="inside", textfont={"color": "white"},
                       hovertemplate="%{x}<br>Share: %{y:.0%}<extra></extra>")
    fig2.update_yaxes(tickformat=".0%", rangemode="tozero")
    st.plotly_chart(fig2, width="stretch")

performance = filtered.group_by("automation_id").agg(
    [
        pl.len().alias("runs"),
        (pl.col("final_status") == "Success").cast(pl.Int64).sum().alias("success_count"),
        (pl.col("retry_count") > 0).cast(pl.Int64).sum().alias("retry_count_total"),
        pl.col("manual_intervention_required").fill_null(False).cast(pl.Int64).sum().alias("manual_count"),
        pl.col("sla_met").fill_null(False).cast(pl.Int64).sum().alias("sla_met_count"),
    ]
).with_columns(
    (pl.col("success_count") / pl.col("runs")).alias("final_success"),
    (pl.col("retry_count_total") / pl.col("runs")).alias("retry_rate"),
    (pl.col("manual_count") / pl.col("runs")).alias("manual_rate"),
    (pl.col("sla_met_count") / pl.col("runs")).alias("sla_compliance")
)

st.subheader("Performance comparison by automation")
performance_display = performance.with_columns(
    (pl.col("final_success") * 100).alias("final_success_pct"),
    (pl.col("retry_rate") * 100).alias("retry_rate_pct"),
    (pl.col("manual_rate") * 100).alias("manual_rate_pct"),
    (pl.col("sla_compliance") * 100).alias("sla_compliance_pct"),
).select(
    "automation_id", "runs", "success_count", "retry_count_total", "manual_count", "sla_met_count",
    "final_success_pct", "retry_rate_pct", "manual_rate_pct", "sla_compliance_pct",
).rename({
    "automation_id": "Automation", "runs": "Runs", "success_count": "Successful runs",
    "retry_count_total": "Runs with retry", "manual_count": "Manual interventions",
    "sla_met_count": "SLA met", "final_success_pct": "Final success",
    "retry_rate_pct": "Retry rate", "manual_rate_pct": "Manual rate",
    "sla_compliance_pct": "SLA compliance",
})
st.dataframe(
    performance_display, width="stretch", hide_index=True,
    column_config={
        "Runs": st.column_config.NumberColumn(format="%d"),
        "Successful runs": st.column_config.NumberColumn(format="%d"),
        "Runs with retry": st.column_config.NumberColumn(format="%d"),
        "Manual interventions": st.column_config.NumberColumn(format="%d"),
        "SLA met": st.column_config.NumberColumn(format="%d"),
        "Final success": st.column_config.NumberColumn(format="%.0f%%"),
        "Retry rate": st.column_config.NumberColumn(format="%.0f%%"),
        "Manual rate": st.column_config.NumberColumn(format="%.0f%%"),
        "SLA compliance": st.column_config.NumberColumn(format="%.0f%%"),
    },
)

st.subheader("Detailed failed-run table")
failed = filtered.filter(pl.col("final_status") != "Success").select([
    "run_id",
    "client_name",
    "process_name",
    "run_date",
    "final_status",
    "retry_count",
    "manual_intervention_required",
    "sla_met",
    "error_category",
    "error_message",
])
st.dataframe(failed, width="stretch")
