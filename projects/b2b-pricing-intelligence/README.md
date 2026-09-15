# B2B Pricing Intelligence

Static HTML/CSS/JavaScript diagnostic dashboard with Plotly. It identifies unusual customer-SKU pricing relationships for commercial review. No Python backend is required. The portfolio homepage links to `projects/b2b-pricing-intelligence/` alongside the Jewellery case study.

## Reproduce

Install pandas, numpy, scipy, openpyxl, matplotlib and IPython in the notebook environment. Open `pricinganalysis/pricinganalysis_ucimlrepo.ipynb` and run all cells. The first cell reuses an existing cleaned `df` or downloads both years of the official UCI workbook and applies the stated cleaning rules. Raw files are cached in the ignored `pricinganalysis/.data-cache/` directory.

The notebook exporter writes six aggregate datasets and gzip copies into this folder's `data/`. Modern browsers load gzip copies using the browser's built-in decompressor; the plain JSON files are the fallback. Customer-SKU results use dictionary-encoded rows to avoid repeating product descriptions and rule explanations. No raw transaction rows or original customer IDs are exported.

## Publication files

- Repository `index.html` (homepage link).
- This entire `projects/b2b-pricing-intelligence/` folder, including JSON and gzip data.
- `pricinganalysis/pricinganalysis_ucimlrepo.ipynb`, `export_dashboard.py`, `load_uci.py`, and `.gitignore` for reproducibility.
- `pricinganalysis/execute_notebook.py`, `finish_population.py` and `test_dashboard.py` for validation.

Do not publish `.data-cache`, virtual environments, or raw datasets. A Git commit and push to the GitHub Pages source branch is required before refreshing the public website will show local changes.

## Interpretation

The separate **Commercial Pricing Simulator — Scenario Analysis** runs entirely in JavaScript with blank inputs. All costs, warranty probabilities, current prices and benchmarks are user-defined. Warranty period supplies context only; positive claim probability requires explicit confirmation that it covers the entered period. The simulator uses `cost to serve / (1 - target gross margin)` for the Recommended Price Floor. Its outputs do not change historical KPIs or diagnostic review statuses.

The executive Total Identified Revenue KPI excludes unidentified customers. Overall cleaned revenue, including missing-customer revenue, remains in notebook data-quality totals. Exact duplicates, non-product stock codes and positive extremes are retained to match the supplied cleaning rules. This may affect commercial interpretation; inspect outlier tables in the notebook before making decisions. Customer IDs are account proxies, not verified B2B entities. Small/Medium/Large/Strategic are descriptive revenue-based segments, not contractual tiers.

Pricing Review cases have a material below-median price gap and at-or-below-median customer-SKU quantity. Possible Volume Justification cases have higher quantity. Both require at least 10 SKU customers, 30 SKU orders and 3 customer-SKU orders. The notebook's `gap_threshold` defaults to 0.15: a configurable screening choice, not an economically optimal threshold. Review flags do not establish that prices should increase.

Exploratory regressions and hypothetical historical sensitivity remain separate from review logic. No proposed customer price, confidence label or monetary opportunity is exported. Seasonality, inventory availability and customer mix are uncontrolled; promotions and contracts are unavailable. Historical sensitivity is not forecast revenue or a recommended price. No actual margin is claimed.

Source: Chen, D. (2012). [Online Retail II](https://doi.org/10.24432/C5CG6D), UCI Machine Learning Repository. CC BY 4.0. Data has been cleaned and aggregated for this case study.
