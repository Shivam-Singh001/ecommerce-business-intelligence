# Data dictionary and modelling rules

## Source tables

| Table | Grain | Key fields | Use in analysis |
| --- | --- | --- | --- |
| `orders` | One row per order | `order_id`, `customer_id` | Status and lifecycle timestamps |
| `customers` | One customer record per order context | `customer_id`; `customer_unique_id` | Customer geography and repeat-customer analysis |
| `items` | One item within an order | `order_id`, `order_item_id`, `product_id`, `seller_id` | Price, freight, products, sellers |
| `payments` | One payment component | `order_id`, `payment_sequential` | Payment type, instalments, payment value |
| `reviews` | One submitted review | `review_id`, `order_id` | Review score and feedback timestamps |
| `products` | One product | `product_id` | Category and product attributes |
| `sellers` | One seller | `seller_id` | Seller geography |
| `geolocation` | A zip-code coordinate observation | zip-code prefix and coordinates | Geography reference only; duplicate coordinate rows are removed in cleaned output |
| `category_translation` | One Portuguese-to-English category mapping | `product_category_name` | Dashboard-friendly category labels |

## Derived analytics tables

| Table/view | Grain | Definition |
| --- | --- | --- |
| `order_summary.csv` / `vw_order_summary` | One row per order | Orders joined to customer attributes, with item, payment, and review values separately aggregated before joining |
| `order_items_enriched.csv` | One row per order item | Items with order status/date and Portuguese/English product category |

## Measures and cautions

| Field | Definition | Interpretation rule |
| --- | --- | --- |
| `payment_value` | Sum of payment components for an order | Use for payment-revenue reconciliation |
| `product_gmv` | Sum of item `price` for an order | Excludes freight; do not label it payment revenue |
| `freight_value` | Sum of item freight values | Not a seller-payout measure |
| `delivery_days` | Customer-delivery timestamp minus purchase timestamp | Only meaningful where both timestamps exist |
| `delivery_delay_days` | Customer-delivery timestamp minus estimated-delivery timestamp | Positive means delivered after the estimate |
| `review_score` | Average score per order where review rows exist | Missing does not mean a zero score |

## Relationships

- `orders.customer_id` → `customers.customer_id`
- `items.order_id`, `payments.order_id`, `reviews.order_id` → `orders.order_id`
- `items.product_id` → `products.product_id`; `items.seller_id` → `sellers.seller_id`
- `products.product_category_name` → `category_translation.product_category_name`

All core foreign-key checks returned zero orphans in the verified local run. Keep filter direction single in Power BI, and never join raw items directly to raw payment rows.
