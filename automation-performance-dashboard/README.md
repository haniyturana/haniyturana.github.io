# Automation Performance & ROI Intelligence Dashboard

## Project objective
This synthetic, client-facing dashboard concept turns automation telemetry into operational and financial insight. It helps executives assess whether automated workflows are reliable, efficient and economically justified without overstating benefits.

## Business problem
Operations leaders often have fragmented automation data spread across logs, spreadsheets and finance reports. This makes it difficult to understand whether automations are stable, whether staff capacity has improved, how much cost has been avoided, and whether the investment is producing a measurable return.

## Intended users
- Operations leaders
- Finance and transformation sponsors
- Process owners
- Automation champions
- Senior executives reviewing investment quality

## Dashboard pages
1. Executive Overview
2. Automation Health
3. Business Impact
4. ROI Analysis
5. Data Quality

## Data model and grain
The project uses synthetic data stored as Parquet files.

- automation_runs.parquet: one row per automation execution
- business_performance.parquet: one row per client, process and month
- data_quality_results.parquet: one row per quality check or issue record

## KPI definitions
- First-pass success rate: percentage of runs completed successfully without any retry
- Final success rate: percentage of runs ending in a successful status after all permitted retries
- Retry rate: runs with retry_count > 0 divided by total runs
- SLA compliance: percentage of runs completed within the agreed service window
- Manual intervention rate: fraction of runs requiring human intervention
- Capacity released: estimated manual time without automation minus remaining manual intervention time
- Net financial benefit: verified cash saving + avoided hiring cost - operating cost - implementation cost
- ROI: net financial benefit divided by total automation cost, expressed as a percentage
- Payback period: months required to recover the initial implementation cost

Implementation cost is treated as a one-time cost per client-process implementation unit. Repeated monthly values are deduplicated before portfolio ROI is calculated.

## ROI methodology
The ROI model separates time saved from financial savings. Time saved does not automatically equal salary reduction. The dashboard distinguishes:

- Capacity released: operating hours freed from the process
- Gross labour value: capacity released multiplied by labour cost per hour
- Cost avoided: reduced headcount or avoided future hiring cost
- Verified cash saving: actual cash reduction validated by finance

The project uses a conservative approach and evaluates automation value using a combination of realised and avoided cost components.

## Difference between time saved, capacity released, cost avoided and cash saving
- Time saved: minutes or hours recovered from the process
- Capacity released: time saved that becomes available for other work or growth
- Cost avoided: value associated with not hiring or delaying recruitment
- Cash saving: confirmed reduction in spend that can be validated by financial records

These are not interchangeable and must not be treated as equal without finance validation.

## Data limitations
- Synthetic data is for demonstration only
- Data quality issues are intentionally included to illustrate governance checks
- Financial outcomes are directional, not a formal client accounting statement
- Dashboard values are based on generated assumptions and should be validated with real operating records

## How to install
```bash
pip install -r requirements.txt
```

## How to run
```bash
python src/generate_data.py
streamlit run app.py
```

## How to deploy using Streamlit Community Cloud
1. Push the project to a GitHub repository.
2. Open Streamlit Community Cloud.
3. Select the repository and branch.
4. Set the app file to app.py.
5. Use a Python version compatible with the project requirements.
6. Ensure data files are included in the repository root or data directory.
7. Deploy and monitor the app after the initial launch.

## Future improvements
- Add client-specific drill-down pages
- Include exportable PDF reports
- Add automated KPI threshold alerting
- Improve scenario modelling with non-linear assumptions
- Expand data-quality metrics by dataset and client group

## Project commands
```bash
pip install -r requirements.txt
python src/generate_data.py
pytest
streamlit run app.py
```
