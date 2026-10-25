# Validation report

**Project:** E-Commerce Business Intelligence and Customer Analytics System

**Dataset run:** 25 October 2026, using the existing local Olist CSV files

## Actual pipeline result

The reproducible pipeline completed successfully and generated cleaned CSVs, `data/olist_analytics.sqlite`, and `reports/generated/validation_report.json`. Raw CSV files were not changed.

| Check | Result |
| --- | --- |
| Source files | 9 found; headers and row counts parsed successfully |
| Exact duplicate rows removed | 261,831 from `geolocation`; 0 from every other source table |
| Duplicate primary keys | 0 for orders, customers, products, and sellers |
| Orphan core foreign keys | 0 for orders/customers, items/orders/products/sellers, payments/orders, and reviews/orders |
| Orders in analytic summary | 99,441 |
| Delivered orders | 96,478 |
| Delivered-order payment revenue | BRL 15,422,461.77 |
| Average delivery duration | 12.5582 days |
| Python versus SQLite | Exact match for delivered-order count, payment revenue, and average delivery duration |
| Automated unit tests | 3 passed, 0 failed |
| Documented SQL queries | 5 executed successfully against `data/olist_analytics.sqlite` |

Expected missingness was retained rather than imputed: 2,965 orders lack a customer-delivery timestamp (for example, non-delivered orders) and 610 products lack a category. Review score has no missing values in the local file.

## Checked analytical results

| Question | Verified result | Scope / caution |
| --- | --- | --- |
| Highest monthly payment revenue | November 2017: BRL 1,153,528.05 across 7,289 delivered orders | Delivered orders only |
| Largest state by payment revenue | SP: BRL 5,770,266.19 across 40,501 delivered orders | Customer state, not seller state |
| Top category by product GMV | `health_beauty`: 9,465 items, BRL 1,233,131.72 | Price only; freight excluded |
| Late deliveries | 7,826 delivered after estimated date | Based on 96,478 delivered orders with the required dates |
| Customer ordering pattern | 93,099 one-order customers; 2,997 repeat customers | Person defined by `customer_unique_id` |
| Review score by delivery timing | 2.57 late vs 4.29 on/before estimate | Descriptive association, not causal evidence |

## Controls and evidence

- Exact duplicate removal, text trimming, and date parsing are in `src/olist_analytics.py`.
- Negative money values and broken core relationships stop the pipeline instead of being silently repaired.
- `vw_order_summary` aggregates item, payment, and review data before joins; this prevents revenue multiplication.
- `validate_python_sql()` compares independently calculated Python and SQLite results and raises an error if they differ.
- `tests/test_olist_analytics.py` checks negative-payment rejection, orphan-order rejection, and Python/SQLite agreement using a small controlled fixture.

## Remaining manual validation

- [ ] Build and save the Power BI `.pbix` file locally using the dashboard guide. Power BI Desktop was not available in the macOS validation environment, so no `.pbix` was created or checked.
- [ ] Reconcile the Power BI cards against the three expected values in `docs/power-bi-guide.md` with filters cleared.
- [ ] Add dashboard screenshots and a short conclusion to the final college report/presentation.
- [x] Keep raw CSVs, generated database/outputs, virtual environment, and secrets out of Git.
