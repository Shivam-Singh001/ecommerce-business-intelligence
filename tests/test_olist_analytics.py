import sqlite3
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.olist_analytics import build_database, clean_tables, order_summary, quality_checks, validate_python_sql


def fixture_tables():
    return {
        "orders": pd.DataFrame({"order_id": ["o1", "o2"], "customer_id": ["c1", "c2"], "order_status": ["delivered", "canceled"], "order_purchase_timestamp": ["2018-01-01", "2018-01-02"], "order_approved_at": [None, None], "order_delivered_carrier_date": [None, None], "order_delivered_customer_date": ["2018-01-05", None], "order_estimated_delivery_date": ["2018-01-06", None]}),
        "customers": pd.DataFrame({"customer_id": ["c1", "c2"], "customer_unique_id": ["u1", "u2"], "customer_city": ["a", "b"], "customer_state": ["SP", "RJ"]}),
        "items": pd.DataFrame({"order_id": ["o1", "o1", "o2"], "order_item_id": [1, 2, 1], "product_id": ["p1", "p2", "p1"], "seller_id": ["s1", "s1", "s1"], "shipping_limit_date": [None, None, None], "price": [10.0, 5.0, 8.0], "freight_value": [2.0, 1.0, 2.0]}),
        "payments": pd.DataFrame({"order_id": ["o1", "o1", "o2"], "payment_sequential": [1, 2, 1], "payment_type": ["credit_card", "voucher", "credit_card"], "payment_installments": [1, 1, 1], "payment_value": [10.0, 8.0, 10.0]}),
        "reviews": pd.DataFrame({"review_id": ["r1"], "order_id": ["o1"], "review_score": [5], "review_comment_title": [None], "review_comment_message": [None], "review_creation_date": [None], "review_answer_timestamp": [None]}),
        "products": pd.DataFrame({"product_id": ["p1", "p2"], "product_category_name": ["cat", "cat"]}),
        "sellers": pd.DataFrame({"seller_id": ["s1"]}),
        "geolocation": pd.DataFrame({"geolocation_zip_code_prefix": [1]}),
        "category_translation": pd.DataFrame({"product_category_name": ["cat"], "product_category_name_english": ["category"]}),
    }


class PipelineTests(unittest.TestCase):
    def test_python_and_sql_metrics_agree(self):
        tables, removed = clean_tables(fixture_tables())
        quality_checks(tables, removed)
        summary = order_summary(tables)
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "test.sqlite"
            build_database(tables, database)
            result = validate_python_sql(summary, database)
            self.assertTrue(result["matches"])
            with sqlite3.connect(database) as connection:
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM vw_order_summary").fetchone()[0], 2)

    def test_negative_monetary_value_is_rejected(self):
        tables = fixture_tables()
        tables["payments"].loc[0, "payment_value"] = -1
        with self.assertRaises(ValueError):
            clean_tables(tables)

    def test_orphan_order_is_rejected(self):
        tables = fixture_tables()
        tables["items"].loc[0, "order_id"] = "missing"
        cleaned, removed = clean_tables(tables)
        with self.assertRaises(ValueError):
            quality_checks(cleaned, removed)


if __name__ == "__main__":
    unittest.main()
