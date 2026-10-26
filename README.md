# E-Commerce Business Intelligence and Customer Analytics System

**Student:** Shivam, BCA, Maharaja Surajmal Institute

**Dataset:** Olist Brazilian E-Commerce Public Dataset

**Status:** Reproducible Python/SQLite analysis complete; Power BI `.pbix` report still needs to be built locally.

This project transforms the existing Olist CSV files into cleaned analytical data, a local SQLite database, documented SQL, visual exploratory analysis, and a Power BI-ready order-level table. Raw data is never modified or committed.

## Verified results (local dataset run)

These results were generated from the local dataset on 25 October 2026. They describe historical Olist data, not current e-commerce performance.

| Metric | Verified value |
| --- | ---: |
| Orders | 99,441 |
| Delivered orders | 96,478 |
| Delivered-order payment revenue | BRL 15,422,461.77 |
| Average delivery duration | 12.5582 days |
| Python/SQLite validation | Match |

Further evidence, quality checks, and interpretation limits are in [docs/validation-report.md](docs/validation-report.md).

## Quick start

The nine original Olist CSV files are already in `data/`. Do not rename, move, edit, or commit them.

```bash
# macOS/Linux
source venv/bin/activate
python -m src.olist_analytics
python -m unittest discover -s tests -v
```

The first command generates ignored, reproducible outputs:

- `data/processed/` — cleaned CSVs, `order_summary.csv`, and item/category analysis data;
- `data/olist_analytics.sqlite` — SQLite source tables and `vw_order_summary` view;
- `reports/generated/validation_report.json` — quality and reconciliation evidence.

## Project structure

| Location | Purpose |
| --- | --- |
| `notebooks/01_data_understanding.ipynb` | Original data-understanding work, preserved |
| `notebooks/02_business_analysis.ipynb` | Reproducible charts and evidence-based insights |
| `src/olist_analytics.py` | Cleaning, key checks, SQLite build, and Python-vs-SQL validation |
| `sql/analytics_queries.sql` | Business questions expressed in SQLite SQL |
| `docs/data-dictionary.md` | Table grain, keys, measures, and relationship rules |
| `docs/power-bi-guide.md` | Power BI import, measures, visuals, and reconciliation steps |
| `docs/validation-report.md` | Actual local-run evidence and remaining validation work |

## Important modelling decisions

- `customer_unique_id` identifies a person across orders; `customer_id` identifies one customer record.
- Payment and item rows are each aggregated by `order_id` before they join. Joining raw payments to raw items would multiply values and overstate revenue.
- **Payment revenue** is `SUM(payment_value)` for delivered orders. **Product GMV** is `SUM(items.price)` and excludes freight; they are not interchangeable.
- Delivery metrics include only delivered orders with the timestamps needed for the calculation.
- Missing product categories are retained as missing rather than guessed. Exact duplicate geolocation rows are removed because they are repeated coordinate records, while the original raw CSV is left unchanged.

## Power BI Dashboard

The interactive dashboard is available on Power BI Service.

[**Open E-Commerce Business Intelligence Dashboard**](https://app.powerbi.com/groups/me/reports/fe30dae6-9a8b-4f72-a0e7-45a8ee957649/91c256d171b6dea3d6a9?experience=power-bi)

The dashboard includes:

- Delivered payment revenue
- Delivered order count
- Average delivery duration
- Late delivered orders
- Monthly revenue trends
- Top 10 customer states by revenue
- Delivered orders by review score

*Note: Access to the interactive report may require signing in to Power BI with an authorized account. The report is hosted on Power BI Service; a `.pbix` file is not currently included in this repository.*


## Safe version control

`.gitignore` excludes raw CSVs, generated CSVs/databases/reports, the local environment, secrets, and notebook checkpoints. Only code, notebooks, SQL, and documentation belong in Git.
