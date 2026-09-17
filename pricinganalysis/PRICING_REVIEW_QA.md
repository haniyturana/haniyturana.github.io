# Pricing Review QA — 17 September 2026

## Transaction trace

Customer alias C01315 was resolved using the exporter's sorted identified-customer alias mapping after the existing merchandise cleaning step. The cached cleaned transactions and original `online_retail_II.xlsx` agree:

| SKU | Description | Invoice | Invoice date | Quantity | Unit price | Calculated revenue | Effective price | Latest price | SKU median |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 84927E | FLOWERS TILE HOOK | 524174 | 2010-09-27 16:30 | 192 | £0.08 | £15.36 | £0.08 | £0.08 | £2.10 |
| 84493 | BLUE/PINK NEST STRIPE BOX | 524174 | 2010-09-27 16:30 | 567 | £0.08 | £45.36 | £0.08 | £0.08 | £2.55 |

Original workbook: sheet `Year 2009-2010`, Excel rows **358743** and **358750**, respectively (including the header). Each customer–SKU pair has exactly one cleaned transaction and one distinct invoice.

- Revenue is Quantity × UnitPrice: 192 × £0.08 = £15.36; 567 × £0.08 = £45.36.
- Effective Price is sum(Revenue) / sum(Quantity): £15.36 / 192 = £0.08 and £45.36 / 567 = £0.08.
- Latest Price is UnitPrice from the final transaction after sorting by InvoiceDate within the customer–SKU pair. With one transaction, it is unambiguously £0.08 for each.
- The benchmark is the median of customer-level effective prices for the SKU, not the median invoice-line price. The resulting gaps are 96.19047619% and 96.86274510%.
- Both are merchandise records with named products, positive quantities and prices, and a non-cancelled invoice. Neither SKU is an excluded service/administrative code. They are valid under the current cleaning rules. Their commercial correctness cannot be confirmed from this dataset: it contains no contract, clearance or promotion explanation for the unusual prices.
- No duplicate contribution, revenue mismatch, aggregation error or latest-price calculation error was found in these pairs. Both remain Insufficient Evidence; each has only one order and the exported SKU eligibility flag is false.

**The reported £50.08 latest price is not present in the current local export for C01315 / 84927E.** Its stored `price` and `latest_price` are both 0.08, consistent with cleaned and raw records. Browser QA also checks the expanded detail displays £0.08. The discrepancy cannot be attributed to a data or aggregation issue from the available evidence; its origin in the previously viewed output remains unresolved. No cleaning change or observation removal was made.

## Business-facing changes

The default order is Pricing Review → Possible Volume Justification → Maintain / No Material Gap → Insufficient Evidence, with descending price gap within each status and stable customer/SKU tie-breakers. Explicit largest/smallest gap sorts remain available.

The main table contains the requested ten fields. Native, keyboard-operable row details retain Customer Segment, Latest Price, Reason, Revenue and SKU median customer quantity. Tablet/mobile layouts show labeled records without horizontal table scrolling.

Counts follow all active filters and cover all matching pages. Unfiltered counts:

| Status | Cases |
| --- | ---: |
| **Pricing Review** | **72** |
| Possible Volume Justification | 2,428 |
| Maintain / No Material Gap | 52,376 |
| Insufficient Evidence | 426,112 |

No exported data, cleaning code, aggregation code, status rules, benchmark definitions, eligibility rules, model or 15% gap threshold changed.

## Validation

The expanded `test_dashboard.py` browser suite passed in headless Edge using a local HTTP server and the cached Plotly asset. It verified search, segment, status and product-scope filters; default status priority and within-status gap order; explicit ascending/descending gap sorting; filtered counts; keyboard expansion/collapse; next/previous pagination; and empty results. Pricing Review had no internal horizontal overflow at 1440, 768, 390 and 320 pixels, including expanded details. The broader suite passed desktop/tablet/mobile page-overflow checks, existing classification assertions, models and commercial simulator checks, with no JavaScript errors. Git comparison confirmed analytical source files and all exported data were unchanged; `git diff --check` passed.

Changes are local and have not been deployed.
