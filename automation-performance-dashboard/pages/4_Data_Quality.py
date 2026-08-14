from __future__ import annotations

import polars as pl
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.load_data import load_data_quality
from src.styles import get_app_css

st.set_page_config(page_title="Data Quality | Automation Intelligence", page_icon="✅", layout="wide")
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

quality = load_data_quality()
st.title("Data Quality")
st.caption("Reliability controls across completeness, uniqueness, validity, consistency and timeliness.")

if quality.is_empty():
    st.warning("No data-quality checks available.")
    st.stop()

summary = quality.group_by("quality_dimension").agg(pl.mean("pass_rate").alias("average_pass_rate")).sort("quality_dimension")
score = summary.to_dicts()
metric_columns = st.columns(len(score))
for column, row in zip(metric_columns, score):
    column.metric(row["quality_dimension"], f"{row['average_pass_rate']:.0%}")

left, right = st.columns(2)
with left:
    st.markdown("### Issues by severity")
    severity_order = ["Critical", "High", "Medium", "Low"]
    severity_counts = quality.group_by("severity").agg(pl.len().alias("Issues"))
    severity_counts = severity_counts.with_columns(
        pl.col("severity").replace_strict(severity_order, list(range(len(severity_order))), default=len(severity_order)).alias("order")
    ).sort("order")
    severity_fig = px.bar(
        severity_counts.to_pandas(), x="severity", y="Issues", color="severity", text_auto=True,
        category_orders={"severity": severity_order},
        color_discrete_map={"Critical": "#B91C1C", "High": "#D97706", "Medium": "#F59E0B", "Low": "#94A3B8"},
        labels={"severity": "Severity"},
    )
    severity_fig.update_layout(height=340, showlegend=False, plot_bgcolor="white", paper_bgcolor="white",
                               margin={"l": 15, "r": 15, "t": 15, "b": 15})
    severity_fig.update_yaxes(gridcolor="#E2E8F0", rangemode="tozero")
    st.plotly_chart(severity_fig, width="stretch")

with right:
    st.markdown("### Pass rate by quality dimension")
    dimension_data = summary.to_dict(as_series=False)
    dimension_fig = go.Figure()
    dimension_fig.add_bar(
        x=dimension_data["quality_dimension"], y=dimension_data["average_pass_rate"],
        marker_color="#0F766E", text=[f"{value:.0%}" for value in dimension_data["average_pass_rate"]],
        textposition="inside", textfont={"color": "white"}, name="Pass rate",
    )
    dimension_fig.add_hline(y=0.98, line_color="#D97706", line_dash="dash", line_width=2)
    dimension_fig.add_trace(go.Scatter(
        x=[None], y=[None], mode="lines", name="Target 98%",
        line={"color": "#D97706", "dash": "dash", "width": 2},
    ))
    dimension_fig.update_layout(height=340, showlegend=True, plot_bgcolor="white", paper_bgcolor="white",
                                yaxis_tickformat=".0%", yaxis_range=[0.94, 1.0],
                                legend={"orientation": "h", "y": 1.08, "x": 0},
                                margin={"l": 15, "r": 15, "t": 35, "b": 15})
    dimension_fig.update_yaxes(gridcolor="#E2E8F0")
    st.plotly_chart(dimension_fig, width="stretch")

st.markdown("### Client quality overview")
client_matrix = quality.group_by(["client_name", "quality_dimension"]).agg(
    pl.mean("pass_rate").alias("pass_rate")
).to_pandas().pivot(index="client_name", columns="quality_dimension", values="pass_rate")
heatmap = px.imshow(
    client_matrix, text_auto=".0%", aspect="auto", color_continuous_scale=["#FEE2E2", "#FEF3C7", "#CCFBF1"],
    zmin=0.94, zmax=1.0, labels={"x": "Quality dimension", "y": "Client", "color": "Pass rate"},
)
heatmap.update_layout(height=340, margin={"l": 15, "r": 15, "t": 15, "b": 15})
st.plotly_chart(heatmap, width="stretch")

with st.expander("View detailed quality checks"):
    display_quality = quality.with_columns(
        pl.col("check_date").str.to_date().dt.strftime("%d %b %Y")
    ).rename({
        "check_date": "Check date",
        "client_id": "Client ID",
        "client_name": "Client name",
        "dataset_name": "Dataset",
        "quality_rule": "Quality rule",
        "quality_dimension": "Quality dimension",
        "records_checked": "Records checked",
        "failed_records": "Failed records",
        "pass_rate": "Pass rate",
        "severity": "Severity",
        "status": "Status",
    })
    st.dataframe(
        display_quality,
        width="stretch",
        hide_index=True,
        column_config={"Pass rate": st.column_config.NumberColumn(format="percent")},
    )
