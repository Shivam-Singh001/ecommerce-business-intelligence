-- Execute after `python -m src.olist_analytics` creates data/olist_analytics.sqlite.
-- Revenue below is payment value for delivered orders. Product GMV excludes freight.

-- 1. Monthly completed-order payment revenue.
SELECT substr(order_purchase_timestamp, 1, 7) AS purchase_month,
       COUNT(*) AS delivered_orders,
       ROUND(SUM(payment_value), 2) AS payment_revenue
FROM vw_order_summary
WHERE order_status = 'delivered'
GROUP BY 1 ORDER BY 1;

-- 2. Top customer states by delivered-order payment revenue.
SELECT customer_state, COUNT(*) AS delivered_orders, ROUND(SUM(payment_value), 2) AS payment_revenue
FROM vw_order_summary
WHERE order_status = 'delivered'
GROUP BY customer_state
ORDER BY payment_revenue DESC, customer_state
LIMIT 10;

-- 3. Delivery performance (completed orders with known dates only).
SELECT ROUND(AVG(julianday(order_delivered_customer_date) - julianday(order_purchase_timestamp)), 2) AS average_delivery_days,
       ROUND(AVG(julianday(order_delivered_customer_date) - julianday(order_estimated_delivery_date)), 2) AS average_delay_days,
       SUM(CASE WHEN julianday(order_delivered_customer_date) > julianday(order_estimated_delivery_date) THEN 1 ELSE 0 END) AS late_orders
FROM vw_order_summary
WHERE order_status = 'delivered' AND order_delivered_customer_date IS NOT NULL;

-- 4. Top categories by delivered-order merchandise value (freight excluded).
SELECT COALESCE(t.product_category_name_english, p.product_category_name, 'unclassified') AS category,
       COUNT(*) AS units_sold, ROUND(SUM(i.price), 2) AS product_gmv
FROM items i
JOIN orders o ON o.order_id = i.order_id
LEFT JOIN products p ON p.product_id = i.product_id
LEFT JOIN category_translation t ON t.product_category_name = p.product_category_name
WHERE o.order_status = 'delivered'
GROUP BY 1 ORDER BY product_gmv DESC LIMIT 10;

-- 5. Repeat-customer distribution. customer_unique_id, not customer_id, identifies a person.
WITH customer_orders AS (
  SELECT customer_unique_id, COUNT(*) AS order_count
  FROM vw_order_summary GROUP BY customer_unique_id
)
SELECT CASE WHEN order_count = 1 THEN 'one order' ELSE 'repeat customer' END AS customer_group,
       COUNT(*) AS customers
FROM customer_orders GROUP BY 1 ORDER BY 1;
