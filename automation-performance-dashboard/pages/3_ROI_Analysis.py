from __future__ import annotations

import polars as pl
import plotly.express as px
import streamlit as st

from src.load_data import format_currency, load_business_performance
from src.metrics import implementation_cost_total, payback_period, roi_percentage
from src.styles import get_app_css

st.set_page_config(page_title="ROI Analysis | Automation Intelligence", page_icon="💼", layout="wide")
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
st.title("ROI Analysis")
st.caption("Validated financial outcomes and a transparent scenario model for management review.")


def formatted_currency_input(label: str, default: float, key: str) -> float:
    """Editable currency input with comma grouping and two decimal places."""
    if key not in st.session_state:
        st.session_state[key] = f"{default:,.0f}"

    def normalise() -> None:
        try:
            value = float(str(st.session_state[key]).replace(",", ""))
            st.session_state[key] = f"{max(value, 0.0):,.0f}"
        except ValueError:
            st.session_state[key] = f"{default:,.0f}"

    raw_value = st.text_input(label, key=key, on_change=normalise)
    try:
        return max(float(raw_value.replace(",", "")), 0.0)
    except ValueError:
        return default


with st.sidebar:
    st.header("Scenario assumptions")
    labour_cost = formatted_currency_input("Labour cost per hour (RM)", 32.0, "scenario_labour_cost_whole")
    implementation_cost = formatted_currency_input("Implementation cost (RM)", 25_000.0, "scenario_implementation_cost_whole")
    operating_cost = formatted_currency_input("Monthly operating cost (RM)", 3_500.0, "scenario_operating_cost_whole")
    realisable_percent = st.slider("Financially realisable saved hours", 0, 100, 40, format="%d%%")
    st.caption("Adjust assumptions to test a conservative or optimistic case.")

realisable_share = realisable_percent / 100
summary = performance.group_by("client_name").agg(
    pl.sum("baseline_processing_hours").alias("baseline_hours"),
    pl.sum("actual_processing_hours").alias("actual_hours"),
    pl.sum("verified_cash_saving").alias("verified_cash_saving"),
    pl.sum("avoided_hiring_cost").alias("avoided_hiring_cost"),
    pl.sum("monthly_operating_cost").alias("monthly_operating_cost"),
)
implementation_by_client = (
    performance.group_by(["client_name", "process_name"])
    .agg(pl.max("implementation_cost").alias("implementation_cost"))
    .group_by("client_name")
    .agg(pl.sum("implementation_cost"))
)
summary = summary.join(implementation_by_client, on="client_name", how="left").with_columns(
    (pl.col("baseline_hours") - pl.col("actual_hours")).alias("capacity_hours_released"),
    (
        pl.col("verified_cash_saving") + pl.col("avoided_hiring_cost")
        - pl.col("monthly_operating_cost") - pl.col("implementation_cost")
    ).alias("net_benefit"),
)

portfolio_capacity = float(summary["capacity_hours_released"].sum())
portfolio_cash = float(summary["verified_cash_saving"].sum())
portfolio_avoided = float(summary["avoided_hiring_cost"].sum())
portfolio_operating = float(summary["monthly_operating_cost"].sum())
portfolio_impl = implementation_cost_total(performance)
net_benefit = portfolio_cash + portfolio_avoided - portfolio_operating - portfolio_impl
roi = roi_percentage(net_benefit, portfolio_impl + portfolio_operating)
monthly_positive_benefit = max((portfolio_cash + portfolio_avoided - portfolio_operating) / performance["month"].n_unique(), 0.0)
payback = payback_period(portfolio_impl, monthly_positive_benefit)

st.markdown('<div class="concept-banner">Management principle: capacity released is not automatically a cash saving. Only finance-validated savings are included as verified cash savings.</div>', unsafe_allow_html=True)
st.markdown("### Portfolio financial summary")
top = st.columns(4)
top[0].metric("Net benefit", format_currency(net_benefit))
top[1].metric("ROI", f"{roi:.0f}%")
top[2].metric("Payback period", f"{payback:.0f} months" if payback else "Not achieved")
top[3].metric("Capacity released", f"{portfolio_capacity:,.0f} hours")

support = st.columns(4)
support[0].metric("Gross financial benefit", format_currency(portfolio_cash + portfolio_avoided))
support[1].metric("Verified cash saving", format_currency(portfolio_cash))
support[2].metric("Avoided hiring cost", format_currency(portfolio_avoided))
support[3].metric("Total automation cost", format_currency(portfolio_impl + portfolio_operating))

st.markdown("### Benefit by client")
benefit_chart = px.bar(
    summary.sort("net_benefit").to_pandas(), x="client_name", y="net_benefit",
    labels={"client_name": "Client", "net_benefit": "Net benefit (RM)"},
    color_discrete_sequence=["#0F766E"], text_auto=",.0f",
)
benefit_chart.update_layout(height=390, plot_bgcolor="white", paper_bgcolor="white", showlegend=False, margin={"l": 20, "r": 20, "t": 20, "b": 20})
benefit_chart.update_yaxes(gridcolor="#E2E8F0", zerolinecolor="#94A3B8")
st.plotly_chart(benefit_chart, width="stretch")

scenario_hours = portfolio_capacity * realisable_share
scenario_gross = scenario_hours * labour_cost
client_count = summary.height
scenario_implementation = implementation_cost * client_count
scenario_annual_operating = operating_cost * 12 * client_count
scenario_total_cost = scenario_implementation + scenario_annual_operating
scenario_net = scenario_gross - scenario_total_cost
scenario_roi = roi_percentage(scenario_net, scenario_total_cost)
scenario_monthly_benefit = (scenario_gross / 12) - (operating_cost * client_count)
scenario_payback = payback_period(scenario_implementation, scenario_monthly_benefit)

st.markdown("### Scenario result")
st.caption(
    f"Modelled across {client_count} clients using {realisable_percent}% realisable capacity at "
    f"{format_currency(labour_cost)} per hour. Operating cost is annualised."
)
scenario_top = st.columns(4)
scenario_top[0].metric("Modelled net benefit", format_currency(scenario_net))
scenario_top[1].metric("Modelled ROI", f"{scenario_roi:.0f}%")
scenario_top[2].metric("Modelled payback", f"{scenario_payback:.0f} months" if scenario_payback else "Not achieved")
scenario_top[3].metric("Realisable capacity", f"{scenario_hours:,.0f} hours")

with st.expander("View scenario calculation"):
    detail = pl.DataFrame({
        "Component": ["Realisable labour value", "Implementation cost", "Annual operating cost", "Net benefit"],
        "Amount (RM)": [
            format_currency(scenario_gross),
            format_currency(scenario_implementation),
            format_currency(scenario_annual_operating),
            format_currency(scenario_net),
        ],
    })
    st.dataframe(detail, width="stretch", hide_index=True)
