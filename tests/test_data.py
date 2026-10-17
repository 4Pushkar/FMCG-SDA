"""
Tests for FMCG sample data validation.
Verifies CSV schema, data types, unique IDs, and value ranges.
"""

import csv
import os
import sys
import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def load_csv(filename):
    """Load CSV file and return headers and records."""
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        records = list(reader)
    return records


class TestSalesData:
    """Tests for sample_fmcg_sales.csv."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.records = load_csv("sample_fmcg_sales.csv")
    
    def test_file_exists(self):
        assert os.path.exists(os.path.join(DATA_DIR, "sample_fmcg_sales.csv"))
    
    def test_has_records(self):
        assert len(self.records) > 100, f"Expected >100 records, got {len(self.records)}"
    
    def test_required_columns(self):
        expected = {"event_id", "timestamp", "product_id", "product_name",
                    "category", "store_id", "store_name", "units_sold", "selling_price"}
        actual = set(self.records[0].keys())
        missing = expected - actual
        assert not missing, f"Missing columns: {missing}"
    
    def test_unique_event_ids(self):
        event_ids = [r["event_id"] for r in self.records]
        assert len(event_ids) == len(set(event_ids)), "Duplicate event IDs found"
    
    def test_positive_units_sold(self):
        for r in self.records:
            units = int(r["units_sold"])
            assert units >= 1, f"Invalid units_sold={units} for {r['event_id']}"
    
    def test_positive_prices(self):
        for r in self.records:
            price = float(r["selling_price"])
            assert price > 0, f"Invalid price={price} for {r['event_id']}"
    
    def test_valid_timestamps(self):
        from datetime import datetime
        for r in self.records[:10]:  # Spot check first 10
            datetime.strptime(r["timestamp"], "%Y-%m-%d %H:%M:%S")
    
    def test_multiple_products(self):
        products = set(r["product_id"] for r in self.records)
        assert len(products) >= 5, f"Expected ≥5 products, got {len(products)}"
    
    def test_multiple_stores(self):
        stores = set(r["store_id"] for r in self.records)
        assert len(stores) >= 3, f"Expected ≥3 stores, got {len(stores)}"


class TestPriceData:
    """Tests for sample_fmcg_prices.csv."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.records = load_csv("sample_fmcg_prices.csv")
    
    def test_file_exists(self):
        assert os.path.exists(os.path.join(DATA_DIR, "sample_fmcg_prices.csv"))
    
    def test_has_records(self):
        assert len(self.records) >= 50, f"Expected ≥50 records, got {len(self.records)}"
    
    def test_required_columns(self):
        expected = {"price_id", "product_id", "selling_price", "effective_date"}
        actual = set(self.records[0].keys())
        missing = expected - actual
        assert not missing, f"Missing columns: {missing}"
    
    def test_positive_prices(self):
        for r in self.records:
            price = float(r["selling_price"])
            assert price > 0, f"Invalid price={price} for {r['price_id']}"


class TestCalendarData:
    """Tests for sample_fmcg_calendar.csv."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.records = load_csv("sample_fmcg_calendar.csv")
    
    def test_file_exists(self):
        assert os.path.exists(os.path.join(DATA_DIR, "sample_fmcg_calendar.csv"))
    
    def test_has_records(self):
        assert len(self.records) >= 28, f"Expected ≥28 records, got {len(self.records)}"
    
    def test_required_columns(self):
        expected = {"date", "day_of_week", "is_weekend", "is_promotion", "event_name"}
        actual = set(self.records[0].keys())
        missing = expected - actual
        assert not missing, f"Missing columns: {missing}"
    
    def test_has_promotions(self):
        promos = [r for r in self.records if r["is_promotion"] == "True"]
        assert len(promos) > 0, "No promotional days found"
