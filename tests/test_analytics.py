"""
Tests for FMCG Analytics Engine.
Verifies revenue calculations, rolling aggregates, and anomaly detection.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from analytics import FMCGAnalytics


def make_sale(event_id="EVT-001", product_id="P001", product_name="Test Product",
              store_id="S01", store_name="Test Store", category="Test",
              units_sold=10, selling_price=100.0, timestamp="2026-09-01 10:00:00"):
    """Helper to create a sales record dict."""
    return {
        "event_id": event_id,
        "timestamp": timestamp,
        "product_id": product_id,
        "product_name": product_name,
        "category": category,
        "store_id": store_id,
        "store_name": store_name,
        "units_sold": units_sold,
        "selling_price": selling_price,
    }


class TestRevenueCalculation:
    """Test that revenue is calculated correctly."""
    
    def test_basic_revenue(self):
        engine = FMCGAnalytics()
        result = engine.process_sale(make_sale(units_sold=5, selling_price=20.0))
        assert result["revenue"] == 100.0
    
    def test_revenue_rounding(self):
        engine = FMCGAnalytics()
        result = engine.process_sale(make_sale(units_sold=3, selling_price=14.99))
        assert result["revenue"] == 44.97
    
    def test_single_unit(self):
        engine = FMCGAnalytics()
        result = engine.process_sale(make_sale(units_sold=1, selling_price=56.00))
        assert result["revenue"] == 56.00
    
    def test_large_order(self):
        engine = FMCGAnalytics()
        result = engine.process_sale(make_sale(units_sold=200, selling_price=10.0))
        assert result["revenue"] == 2000.0


class TestRunningTotals:
    """Test that running totals accumulate correctly."""
    
    def test_cumulative_units(self):
        engine = FMCGAnalytics()
        engine.process_sale(make_sale(event_id="E1", units_sold=10))
        result = engine.process_sale(make_sale(event_id="E2", units_sold=20))
        assert result["running_total_units"] == 30
    
    def test_cumulative_revenue(self):
        engine = FMCGAnalytics()
        engine.process_sale(make_sale(event_id="E1", units_sold=5, selling_price=10.0))
        result = engine.process_sale(make_sale(event_id="E2", units_sold=3, selling_price=20.0))
        assert result["running_total_revenue"] == 110.0  # 50 + 60
    
    def test_product_breakdown(self):
        engine = FMCGAnalytics()
        engine.process_sale(make_sale(event_id="E1", product_id="P001", units_sold=10))
        engine.process_sale(make_sale(event_id="E2", product_id="P002", units_sold=20))
        engine.process_sale(make_sale(event_id="E3", product_id="P001", units_sold=5))
        
        summary = engine.get_summary()
        assert summary["product_breakdown"]["P001"] == 15
        assert summary["product_breakdown"]["P002"] == 20
    
    def test_store_breakdown(self):
        engine = FMCGAnalytics()
        engine.process_sale(make_sale(event_id="E1", store_id="S01", units_sold=10))
        engine.process_sale(make_sale(event_id="E2", store_id="S02", units_sold=20))
        
        summary = engine.get_summary()
        assert summary["store_breakdown"]["S01"] == 10
        assert summary["store_breakdown"]["S02"] == 20


class TestAnomalyDetection:
    """Test demand spike detection logic."""
    
    def _build_baseline(self, engine, product_id="P001", store_id="S01",
                         normal_units=10, count=10):
        """Build a baseline of normal sales to enable anomaly detection."""
        for i in range(count):
            engine.process_sale(make_sale(
                event_id=f"BASE-{i:03d}",
                product_id=product_id,
                store_id=store_id,
                units_sold=normal_units,
            ))
    
    def test_no_anomaly_with_insufficient_data(self):
        engine = FMCGAnalytics()
        result = engine.process_sale(make_sale(units_sold=100))
        assert result["is_anomaly"] is False
        assert result["anomaly_details"]["reason"] == "insufficient_data"
    
    def test_normal_sale_not_flagged(self):
        engine = FMCGAnalytics(threshold=2.0)
        self._build_baseline(engine, normal_units=10, count=10)
        
        result = engine.process_sale(make_sale(event_id="NORMAL", units_sold=12))
        assert result["is_anomaly"] is False
    
    def test_spike_detected(self):
        engine = FMCGAnalytics(threshold=2.0)
        self._build_baseline(engine, normal_units=10, count=10)
        
        # 50 units when baseline is ~10 should be flagged
        result = engine.process_sale(make_sale(event_id="SPIKE", units_sold=50))
        assert result["is_anomaly"] is True
        assert result["anomaly_details"]["reason"] == "demand_spike"
    
    def test_spike_generates_alert(self):
        engine = FMCGAnalytics(threshold=2.0)
        self._build_baseline(engine, normal_units=10, count=10)
        
        result = engine.process_sale(make_sale(event_id="SPIKE", units_sold=50))
        assert "alert" in result
        assert result["alert"]["alert_id"].startswith("ALERT-")
    
    def test_severity_classification(self):
        assert FMCGAnalytics._classify_severity(5.0) == "CRITICAL"
        assert FMCGAnalytics._classify_severity(3.5) == "HIGH"
        assert FMCGAnalytics._classify_severity(2.5) == "MEDIUM"
        assert FMCGAnalytics._classify_severity(1.5) == "LOW"
    
    def test_different_products_independent(self):
        engine = FMCGAnalytics(threshold=2.0)
        # Build baseline for P001 only
        self._build_baseline(engine, product_id="P001", normal_units=10, count=10)
        
        # P002 has no baseline — should not be flagged even with high units
        result = engine.process_sale(make_sale(
            event_id="P002-TEST", product_id="P002", units_sold=100
        ))
        assert result["is_anomaly"] is False  # Insufficient data for P002


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_zero_units_handled(self):
        engine = FMCGAnalytics()
        result = engine.process_sale(make_sale(units_sold=0))
        assert result["revenue"] == 0.0
    
    def test_string_units_handled(self):
        engine = FMCGAnalytics()
        record = make_sale()
        record["units_sold"] = "invalid"
        result = engine.process_sale(record)
        assert result["revenue"] == 0.0
    
    def test_missing_fields_handled(self):
        engine = FMCGAnalytics()
        result = engine.process_sale({"event_id": "MINIMAL"})
        assert result["revenue"] == 0.0
        assert result["message_number"] == 1
    
    def test_message_counter(self):
        engine = FMCGAnalytics()
        for i in range(5):
            result = engine.process_sale(make_sale(event_id=f"E{i}"))
        assert result["message_number"] == 5
    
    def test_summary_structure(self):
        engine = FMCGAnalytics()
        engine.process_sale(make_sale())
        summary = engine.get_summary()
        
        required_keys = [
            "total_messages_processed", "total_units_sold", "total_revenue",
            "products_tracked", "stores_tracked", "anomalies_detected",
            "product_breakdown", "store_breakdown", "recent_anomalies",
        ]
        for key in required_keys:
            assert key in summary, f"Missing summary key: {key}"
