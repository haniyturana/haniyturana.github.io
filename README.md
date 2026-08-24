# Haniy Turana — Data Analytics Portfolio

Live portfolio: [https://haniyturana.github.io/](https://haniyturana.github.io/)

This portfolio presents selected work across retail analytics, commercial
decision support, demand forecasting, inventory intelligence, pricing and data
engineering.

## Featured work

- **Retail Space & Range Optimisation** — an interactive case study covering
  the business problem, decision framework, store clustering, shelf-space and
  gross-profit productivity, SKU rationalisation, scenario modelling,
  implementation risks and a controlled-test recommendation.
- **Retail Demand Forecasting** — a reactive decision engine combining category,
  horizon, service-level, lead-time and scenario controls with SKU reorder
  recommendations.
- **Inventory Reconciliation** — a cross-system exception intelligence case
  with warehouse, status, type, priority, age and value filters, sortable
  exceptions and investigation trails.
- **Pricing & Clearance Simulator** — a five-strategy commercial model with
  adjustable stock, price, markdown, clearance, fees, write-off and holding
  assumptions plus objective-based recommendations.
- **Product Sales Growth Treemap** — an interactive view of product-level
  year-over-year performance.
- **Jewellery Retail Performance & Campaign Intelligence** — a synthetic
  multi-outlet and e-commerce case study connecting commercial performance,
  inventory health, campaign uplift and prioritised operating actions.
- Additional Spark, Hadoop and NoSQL analytics projects.

## Technologies

HTML, CSS, JavaScript, Python, SQL, R, Spark, Hadoop, Polars, Pandas,
Scikit-learn, XGBoost, LightGBM and Streamlit.

## Project structure

```text
index.html          Portfolio homepage
styles.css          Homepage styling
script.js           Homepage interactions
projects/           Interactive project dashboards
resume/             Résumé PDF
README.md           Project documentation
```

## Run locally

Open `index.html` directly in a browser, or open the folder in VS Code and use
the Live Server extension.

The Live Server option is recommended when testing navigation and interactive
project pages:

1. Open the repository folder in VS Code.
2. Right-click `index.html`.
3. Select **Open with Live Server**.
4. Test the homepage and every link under `projects/`.

## Space & Range interactive controls

The featured case study uses synthetic assumptions and includes:

- Store-cluster selection for urban, family and value-focused missions.
- Balanced, growth, margin and inventory-recovery strategies.
- Connected KPI, chart, insight and recommendation updates.
- A sortable and filterable SKU action table.
- Space-reallocation and SKU-reduction simulator controls.
- Current-versus-proposed outcomes and implementation trade-offs.

All outputs are illustrative decision-support examples, not financial forecasts
or achieved business results.

## Other interactive case-study controls

- **Forecasting:** category, horizon, service level, lead time and demand
  scenario; connected KPIs, charts, insights and sortable SKU actions.
- **Reconciliation:** operational and financial filters; connected exception
  KPIs, six diagnostic charts, a sortable exception table and expandable
  investigation trails.
- **Pricing:** twelve commercial assumptions including sliders for discount,
  clearance and period; five strategies; six charts; detailed economics; and
  recommendations for profit, cash, speed, simplicity or balance.

Every case study includes its business problem, decision framework,
methodology, limitations, implementation considerations and links to the other
case studies.

## Accessibility

The portfolio includes semantic landmarks, keyboard-accessible project cards,
visible focus states, skip navigation, labelled form controls, accessible SVG
chart descriptions, responsive tables and reduced-motion support. Interactive
information is communicated with text labels as well as colour.

## Publish with GitHub Pages

This site is published from the `main` branch and repository root.

1. Upload the **contents** of this folder to the repository root.
2. Confirm that `index.html`, `styles.css`, `script.js`, `projects/` and
   `resume/` appear directly on the repository's main page.
3. Go to **Settings → Pages**.
4. Select **Deploy from a branch → main → / (root)**.
5. Save and wait for the Pages deployment to complete.

Do not upload the portfolio as one outer folder. GitHub Pages must find
`index.html` directly at the publishing root.

## Deployment checklist

- Confirm `index.html` is at the repository root.
- Upload the complete `projects/` and `resume/` folders.
- Preserve filename casing because GitHub Pages paths are case-sensitive.
- Confirm the résumé, GitHub, LinkedIn and external-project URLs.
- Test the Space & Range cluster, strategy, table and simulator controls.
- Test the Forecasting category and horizon controls.
- Test Reconciliation filters, table sorting and investigation details.
- Test Pricing inputs, sliders and every decision objective, including optional
  costs set to zero.
- Check desktop and mobile layouts.
- Wait for the GitHub Pages deployment to show a green status.
- Use a hard refresh after deployment if an older cached page appears.

## Data notice

The portfolio dashboards use synthetic or sanitised data for demonstration.
Figures are illustrative and do not represent confidential employer
information. The Space & Range case study is independent portfolio work and
does not represent any employer’s actual operations, results or commercial
decisions.
