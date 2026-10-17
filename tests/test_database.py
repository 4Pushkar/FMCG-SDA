"""
Unit tests for FMCGDatabase persistence module.
"""

from unittest.mock import MagicMock
from database import FMCGDatabase


def test_database_initial_state():
    """Verify initial database attributes before connection."""
    db = FMCGDatabase(uri="mongodb://localhost:27017", db_name="test_db")
    assert db.connected is False
    assert db.db is None
    assert db.client is None
    assert db.db_name == "test_db"


def test_disconnected_database_methods_do_not_raise():
    """Verify all methods safely degrade when disconnected and db is None."""
    db = FMCGDatabase()
    
    # None of these should throw 'NoneType' object has no attribute
    db._create_indexes()
    assert db.save_processed_sale({"event_id": "EVT123"}) is False
    assert db.save_anomaly_alert({"alert_id": "ALT123"}) is False
    assert db.save_summary({"total_revenue": 100}) is False
    assert db.get_recent_sales() == []
    assert db.get_anomaly_alerts() == []
    assert db.get_latest_summary() is None
    
    stats = db.get_stats()
    assert stats == {"connected": False}
    
    # Closing a disconnected db should be clean
    db.close()
    assert db.connected is False
    assert db.db is None


def test_database_mocked_operations():
    """Verify operations succeed when mock MongoDB client/db is connected."""
    db = FMCGDatabase(db_name="test_db")
    mock_db = MagicMock()
    mock_client = MagicMock()
    
    db.client = mock_client
    db.db = mock_db
    db.connected = True
    
    # Test index creation
    db._create_indexes()
    assert mock_db.processed_sales.create_index.call_count == 4
    assert mock_db.anomaly_alerts.create_index.call_count == 3
    assert mock_db.analytics_summary.create_index.call_count == 1
    
    # Test save_processed_sale
    sale_record = {
        "event_id": "EVT-001",
        "product_id": "P01",
        "revenue": 150.0,
        "anomaly_details": {"is_anomaly": True, "reason": "spike"}
    }
    result = db.save_processed_sale(sale_record)
    assert result is True
    assert mock_db.processed_sales.update_one.called
    
    # Test save_anomaly_alert
    alert = {"alert_id": "ALT-001", "severity": "HIGH"}
    assert db.save_anomaly_alert(alert) is True
    assert mock_db.anomaly_alerts.update_one.called
    
    # Test save_summary
    summary = {"total_revenue": 5000}
    assert db.save_summary(summary) is True
    assert mock_db.analytics_summary.insert_one.called
    
    # Test close
    db.close()
    assert mock_client.close.called
    assert db.connected is False
    assert db.db is None
