"""Reproducible data preparation, SQLite modelling, and validation for Olist."""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Dict, Iterable

import pandas as pd

FILES = {
    "orders": "olist_orders_dataset.csv",
    "items": "olist_order_items_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "products": "olist_products_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}
DATE_COLUMNS = {
    "orders": ["order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date", "order_delivered_customer_date", "order_estimated_delivery_date"],
    "items": ["shipping_limit_date"],
    "reviews": ["review_creation_date", "review_answer_timestamp"],
}


def load_raw(data_dir: Path) -> Dict[str, pd.DataFrame]:
    """Read the official files without changing them; UTF-8 BOM is supported."""
    missing = [filename for filename in FILES.values() if not (data_dir / filename).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing source files in {data_dir}: {', '.join(missing)}")
    return {name: pd.read_csv(data_dir / filename, encoding="utf-8-sig") for name, filename in FILES.items()}


def _parse_dates(frame: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    result = frame.copy()
    for column in columns:
        result[column] = pd.to_datetime(result[column], errors="coerce")
    return result


def clean_tables(raw: Dict[str, pd.DataFrame]) -> tuple[Dict[str, pd.DataFrame], Dict[str, int]]:
    """Remove exact duplicates, trim text, and parse dates without imputing values."""
    cleaned: Dict[str, pd.DataFrame] = {}
    duplicates_removed: Dict[str, int] = {}
    for name, frame in raw.items():
        duplicates_removed[name] = int(frame.duplicated().sum())
        tidy = frame.drop_duplicates().copy()
        for column in tidy.select_dtypes(include=["object", "string"]):
            tidy[column] = tidy[column].str.strip()
        cleaned[name] = _parse_dates(tidy, DATE_COLUMNS.get(name, []))

    for table, column in (("items", "price"), ("items", "freight_value"), ("payments", "payment_value")):
        invalid = int((cleaned[table][column] < 0).sum())
        if invalid:
            raise ValueError(f"{table}.{column} has {invalid} negative values; inspect the source before continuing.")
    return cleaned, duplicates_removed


def quality_checks(tables: Dict[str, pd.DataFrame], duplicates_removed: Dict[str, int]) -> Dict[str, object]:
    """Measure relationships and quality conditions; halt only on broken core keys."""
    orders, customers, items = tables["orders"], tables["customers"], tables["items"]
    checks = {
        "rows_after_cleaning": {name: int(len(frame)) for name, frame in tables.items()},
        "exact_duplicates_removed": duplicates_removed,
        "duplicate_primary_keys": {
            "orders.order_id": int(orders.order_id.duplicated().sum()),
            "customers.customer_id": int(customers.customer_id.duplicated().sum()),
            "products.product_id": int(tables["products"].product_id.duplicated().sum()),
            "sellers.seller_id": int(tables["sellers"].seller_id.duplicated().sum()),
        },
        "orphan_foreign_keys": {
            "orders.customer_id": int((~orders.customer_id.isin(customers.customer_id)).sum()),
            "items.order_id": int((~items.order_id.isin(orders.order_id)).sum()),
            "items.product_id": int((~items.product_id.isin(tables["products"].product_id)).sum()),
            "items.seller_id": int((~items.seller_id.isin(tables["sellers"].seller_id)).sum()),
            "payments.order_id": int((~tables["payments"].order_id.isin(orders.order_id)).sum()),
            "reviews.order_id": int((~tables["reviews"].order_id.isin(orders.order_id)).sum()),
        },
        "missing_values": {
            "orders.delivered_customer_date": int(orders.order_delivered_customer_date.isna().sum()),
            "products.category": int(tables["products"].product_category_name.isna().sum()),
            "reviews.score": int(tables["reviews"].review_score.isna().sum()),
        },
    }
    failures = list(checks["duplicate_primary_keys"].values()) + list(checks["orphan_foreign_keys"].values())
    if any(failures):
        raise ValueError("Primary-key or foreign-key integrity check failed; no analytics outputs were produced.")
    return checks


def order_summary(tables: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return one safe analytic row per order; aggregates are completed before joins."""
    items = tables["items"]
    item_totals = items.groupby("order_id", as_index=False).agg(
        item_count=("order_item_id", "count"), product_gmv=("price", "sum"), freight_value=("freight_value", "sum")
    )
    payments = tables["payments"].groupby("order_id", as_index=False).agg(payment_value=("payment_value", "sum"))
    reviews = tables["reviews"].groupby("order_id", as_index=False).agg(review_score=("review_score", "mean"), review_count=("review_id", "count"))
    result = tables["orders"].merge(
        tables["customers"][["customer_id", "customer_unique_id", "customer_city", "customer_state"]], on="customer_id", how="left"
    ).merge(item_totals, on="order_id", how="left").merge(payments, on="order_id", how="left").merge(reviews, on="order_id", how="left")
    for column in ("item_count", "product_gmv", "freight_value", "payment_value", "review_count"):
        result[column] = result[column].fillna(0)
    result["purchase_month"] = result.order_purchase_timestamp.dt.to_period("M").astype("string")
    result["delivery_days"] = (result.order_delivered_customer_date - result.order_purchase_timestamp).dt.total_seconds() / 86400
    result["delivery_delay_days"] = (result.order_delivered_customer_date - result.order_estimated_delivery_date).dt.total_seconds() / 86400
    return result


def enriched_items(tables: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Build item-level data for category analysis without payment-table multiplication."""
    return tables["items"].merge(tables["orders"][["order_id", "order_status", "order_purchase_timestamp"]], on="order_id", how="left").merge(
        tables["products"][["product_id", "product_category_name"]], on="product_id", how="left"
    ).merge(tables["category_translation"], on="product_category_name", how="left")


def build_database(tables: Dict[str, pd.DataFrame], database_path: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database_path) as connection:
        for name, frame in tables.items():
            frame.to_sql(name, connection, if_exists="replace", index=False)
        connection.executescript("""
            CREATE INDEX IF NOT EXISTS idx_orders_order_id ON orders(order_id);
            CREATE INDEX IF NOT EXISTS idx_items_order_id ON items(order_id);
            CREATE INDEX IF NOT EXISTS idx_payments_order_id ON payments(order_id);
            CREATE INDEX IF NOT EXISTS idx_reviews_order_id ON reviews(order_id);
            CREATE INDEX IF NOT EXISTS idx_items_product_id ON items(product_id);
            DROP VIEW IF EXISTS vw_order_summary;
            CREATE VIEW vw_order_summary AS
            WITH item_totals AS (
                SELECT order_id, COUNT(*) item_count, SUM(price) product_gmv, SUM(freight_value) freight_value FROM items GROUP BY order_id
            ), payment_totals AS (
                SELECT order_id, SUM(payment_value) payment_value FROM payments GROUP BY order_id
            ), review_totals AS (
                SELECT order_id, AVG(review_score) review_score, COUNT(review_id) review_count FROM reviews GROUP BY order_id
            )
            SELECT o.order_id, o.order_status, o.order_purchase_timestamp, o.order_delivered_customer_date, o.order_estimated_delivery_date,
                   c.customer_unique_id, c.customer_city, c.customer_state,
                   COALESCE(i.item_count, 0) item_count, COALESCE(i.product_gmv, 0) product_gmv,
                   COALESCE(i.freight_value, 0) freight_value, COALESCE(p.payment_value, 0) payment_value,
                   r.review_score, COALESCE(r.review_count, 0) review_count
            FROM orders o JOIN customers c ON o.customer_id = c.customer_id
            LEFT JOIN item_totals i ON o.order_id = i.order_id
            LEFT JOIN payment_totals p ON o.order_id = p.order_id
            LEFT JOIN review_totals r ON o.order_id = r.order_id;
        """)


def validate_python_sql(summary: pd.DataFrame, database_path: Path) -> Dict[str, object]:
    delivered = summary.loc[summary.order_status.eq("delivered")]
    python_metrics = {
        "delivered_orders": int(len(delivered)),
        "delivered_payment_revenue": round(float(delivered.payment_value.sum()), 2),
        "average_delivery_days": round(float(delivered.delivery_days.dropna().mean()), 4),
    }
    with sqlite3.connect(database_path) as connection:
        row = connection.execute("""
            SELECT COUNT(*), ROUND(SUM(payment_value), 2), ROUND(AVG(julianday(order_delivered_customer_date) - julianday(order_purchase_timestamp)), 4)
            FROM vw_order_summary WHERE order_status = 'delivered'
        """).fetchone()
    sql_metrics = {"delivered_orders": int(row[0]), "delivered_payment_revenue": float(row[1]), "average_delivery_days": float(row[2])}
    matches = python_metrics == sql_metrics
    if not matches:
        raise AssertionError(f"Python/SQL mismatch: Python={python_metrics}; SQL={sql_metrics}")
    return {"python": python_metrics, "sql": sql_metrics, "matches": matches}


def run_pipeline(data_dir: Path, output_dir: Path, database_path: Path, report_path: Path) -> Dict[str, object]:
    raw = load_raw(data_dir)
    tables, duplicates_removed = clean_tables(raw)
    checks = quality_checks(tables, duplicates_removed)
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in tables.items():
        frame.to_csv(output_dir / f"{name}_clean.csv", index=False)
    summary = order_summary(tables)
    summary.to_csv(output_dir / "order_summary.csv", index=False)
    enriched_items(tables).to_csv(output_dir / "order_items_enriched.csv", index=False)
    build_database(tables, database_path)
    validation = validate_python_sql(summary, database_path)
    report = {"quality_checks": checks, "order_summary_rows": int(len(summary)), "python_sql_validation": validation}
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare, model, and validate Olist analytics data.")
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--database", type=Path, default=Path("data/olist_analytics.sqlite"))
    parser.add_argument("--report", type=Path, default=Path("reports/generated/validation_report.json"))
    arguments = parser.parse_args()
    print(json.dumps(run_pipeline(arguments.data_dir, arguments.output_dir, arguments.database, arguments.report), indent=2))


if __name__ == "__main__":
    main()
