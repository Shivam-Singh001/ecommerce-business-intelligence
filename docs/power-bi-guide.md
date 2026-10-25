# Power BI dashboard guide

No `.pbix` file has been created yet. This guide prepares a beginner to build one from the verified local outputs.

## 1. Generate and import the data

1. From the project root, run `python -m src.olist_analytics`.
2. In Power BI Desktop select **Get Data → Text/CSV**.
3. Select `data/processed/order_summary.csv`. It is the recommended starter table because it has one row per order and avoids accidental many-to-many joins.
4. In Power Query set timestamp fields to Date/Time, monetary fields to Decimal Number, `item_count`/`review_count` to Whole Number, and `purchase_month` to Text or a month-start date created from it.
5. Verify that Power BI imported 99,441 rows before continuing.

## 2. Measures (DAX)

Replace `OrderSummary` with your imported table name if Power BI chooses a different name.

```DAX
Delivered Orders =
CALCULATE(COUNTROWS(OrderSummary), OrderSummary[order_status] = "delivered")

Payment Revenue =
CALCULATE(SUM(OrderSummary[payment_value]), OrderSummary[order_status] = "delivered")

Average Delivery Days =
CALCULATE(
    AVERAGE(OrderSummary[delivery_days]),
    OrderSummary[order_status] = "delivered",
    NOT(ISBLANK(OrderSummary[delivery_days]))
)

Late Delivered Orders =
CALCULATE(
    COUNTROWS(OrderSummary),
    OrderSummary[order_status] = "delivered",
    OrderSummary[delivery_delay_days] > 0
)

Average Review Score = AVERAGE(OrderSummary[review_score])
```

## 3. Recommended one-page dashboard

- KPI cards: Delivered Orders, Payment Revenue, Average Delivery Days, Late Delivered Orders.
- Line chart: `purchase_month` by Payment Revenue.
- Bar chart: `customer_state` by Payment Revenue (Top 10).
- Bar chart: English category by product GMV. Import `order_items_enriched.csv` only if category analysis is needed.
- Column chart: order status distribution.
- Scatter or column chart: review score by delivery-delay bucket.
- Slicers: purchase month, customer state, and order status.

Use descriptive titles and show BRL formatting. Do not imply that association between late delivery and review score proves causation.

## 4. Reconciliation before sharing

With all dashboard filters cleared, these values should match the local verified run:

| Measure | Expected value |
| --- | ---: |
| Delivered Orders | 96,478 |
| Payment Revenue | BRL 15,422,461.77 |
| Average Delivery Days | 12.5582 |

If any value differs, first check filters and aggregation, then compare with `sql/analytics_queries.sql`. Record the outcome in the validation report. Save the resulting `.pbix` locally; do not claim it is included unless you actually add it.
