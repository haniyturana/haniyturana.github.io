from __future__ import annotations

import polars as pl
import plotly.graph_objects as go
import streamlit as st

from src.load_data import load_business_performance
from src.styles import get_app_css

st.set_page_config(page_title="Business Impact | Automation Intelligence", page_icon="📊", layout="wide")
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
performance = load_business_performance()

st.title("Business Impact")
st.caption("Post-automation results measured against defined management targets.")

clients = sorted(performance["client_name"].unique().to_list())
processes = sorted(performance["process_name"].unique().to_list())
with st.sidebar:
    st.header("Filters")
    client_choice = st.selectbox("Client", ["All clients", *clients])
    process_choice = st.selectbox("Business process", ["All processes", *processes])

filtered = performance
if client_choice != "All clients":
    filtered = filtered.filter(pl.col("client_name") == client_choice)
if process_choice != "All processes":
    filtered = filtered.filter(pl.col("process_name") == process_choice)
if filtered.is_empty():
    st.warning("No business-impact data matches the selected filters.")
    st.stop()

summary = filtered.group_by("process_name").agg(
    pl.mean("baseline_processing_hours").alias("baseline_hours"),
    pl.mean("actual_processing_hours").alias("actual_hours"),
    pl.mean("baseline_turnaround_minutes").alias("baseline_turnaround"),
    pl.mean("actual_turnaround_minutes").alias("actual_turnaround"),
    pl.mean("baseline_error_count").alias("baseline_errors"),
    pl.mean("actual_error_count").alias("actual_errors"),
).sort("process_name")

baseline_hours = float(filtered["baseline_processing_hours"].sum())
actual_hours = float(filtered["actual_processing_hours"].sum())
baseline_errors = float(filtered["baseline_error_count"].sum())
actual_errors = float(filtered["actual_error_count"].sum())
hours_reduction = (baseline_hours - actual_hours) / baseline_hours if baseline_hours else 0.0
error_reduction = (baseline_errors - actual_errors) / baseline_errors if baseline_errors else 0.0
baseline_turnaround = float(filtered["baseline_turnaround_minutes"].mean())
turnaround_reduction = 1 - float(filtered["actual_turnaround_minutes"].mean()) / baseline_turnaround if baseline_turnaround else 0.0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Hours released", f"{baseline_hours - actual_hours:,.0f}")
k2.metric("Processing time reduction · Target 40%", f"{hours_reduction:.0%}")
k3.metric("Turnaround improvement · Target 45%", f"{turnaround_reduction:.0%}")
k4.metric("Error reduction · Target 55%", f"{error_reduction:.0%}")

st.markdown("### Target performance")
st.caption("Bars show the actual percentage improvement from baseline. Orange dashed markers show the management target; higher is better.")


def target_chart(actual: str, baseline: str, target_reduction: float, title: str) -> go.Figure:
    data = summary.to_dict(as_series=False)
    improvements = [
        (baseline_value - actual_value) / baseline_value if baseline_value else 0.0
        for baseline_value, actual_value in zip(data[baseline], data[actual])
    ]
    targets = [target_reduction] * len(improvements)
    figure = go.Figure()
    figure.add_bar(
        x=data["process_name"], y=improvements, name="Actual improvement",
        marker_color="#1769AA",
        text=[f"{value:.0%}" for value in improvements], textposition="inside",
        insidetextanchor="middle", textfont={"color": "white", "size": 12},
        customdata=targets,
        hovertemplate="%{x}<br>Actual improvement: %{y:.0%}<br>Target: %{customdata:.0%}<extra></extra>",
    )
    for index, target in enumerate(targets):
        figure.add_shape(
            type="line", x0=index - 0.38, x1=index + 0.38, y0=target, y1=target,
            line={"color": "#F59E0B", "width": 3, "dash": "dash"},
        )
    figure.add_scatter(
        x=[None], y=[None], name=f"Target {target_reduction:.0%}", mode="lines",
        line={"color": "#F59E0B", "width": 3, "dash": "dash"},
    )
    figure.update_layout(
        title={"text": title, "font": {"size": 17}}, yaxis_title="Improvement", xaxis_title="",
        margin={"l": 20, "r": 20, "t": 65, "b": 25}, height=420,
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0},
        plot_bgcolor="white", paper_bgcolor="white", bargap=0.38,
    )
    figure.update_yaxes(gridcolor="#E2E8F0", rangemode="tozero", tickformat=".0%")
    figure.update_xaxes(tickangle=-20)
    return figure


left, right = st.columns(2)
with left:
    st.plotly_chart(target_chart("actual_hours", "baseline_hours", 0.40, "Processing-time reduction"), width="stretch")
with right:
    st.plotly_chart(target_chart("actual_turnaround", "baseline_turnaround", 0.45, "Turnaround-time improvement"), width="stretch")
st.plotly_chart(target_chart("actual_errors", "baseline_errors", 0.55, "Error reduction"), width="stretch")

with st.expander("Target methodology and process detail"):
    st.markdown("Targets are defined as reductions from each process baseline: **40% processing time**, **45% turnaround time**, and **55% errors**.")
    st.dataframe(summary, width="stretch", hide_index=True)
