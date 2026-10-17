"""
Tests for FMCG Kafka Producer.
Tests configuration, JSON serialization, and message construction.
Uses mocked Kafka producer for unit tests.
"""

import csv
import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


class TestCSVReading:
    """Test that the producer can read and validate CSV files."""
    
    def test_read_sales_csv(self):
        from producer import read_csv_records
        records = read_csv_records(os.path.join(DATA_DIR, "sample_fmcg_sales.csv"))
        assert len(records) > 0
        assert "event_id" in records[0]
    
    def test_read_missing_file_raises(self):
        from producer import read_csv_records
        with pytest.raises(FileNotFoundError):
            read_csv_records("nonexistent_file.csv")
    
    def test_csv_records_are_dicts(self):
        from producer import read_csv_records
        records = read_csv_records(os.path.join(DATA_DIR, "sample_fmcg_sales.csv"))
        assert isinstance(records[0], dict)


class TestJSONSerialization:
    """Test that records serialize to valid JSON."""
    
    def test_sales_record_json(self):
        record = {
            "event_id": "EVT-000001",
            "timestamp": "2026-09-01 10:30:00",
            "product_id": "P001",
            "product_name": "Lays Classic Chips",
            "category": "Snacks",
            "store_id": "S01",
            "store_name": "Mumbai Central",
            "units_sold": "15",
            "selling_price": "30.0",
        }
        serialized = json.dumps(record)
        deserialized = json.loads(serialized)
        assert deserialized["event_id"] == "EVT-000001"
        assert deserialized["product_name"] == "Lays Classic Chips"
    
    def test_all_fields_preserved(self):
        record = {
            "event_id": "EVT-TEST",
            "units_sold": "42",
            "selling_price": "99.99",
        }
        result = json.loads(json.dumps(record))
        assert set(result.keys()) == set(record.keys())


class TestProducerConfiguration:
    """Test producer configuration values."""
    
    def test_default_bootstrap_servers(self):
        from producer import KAFKA_BOOTSTRAP
        assert "9092" in KAFKA_BOOTSTRAP
    
    def test_default_sales_topic(self):
        from producer import SALES_TOPIC
        assert SALES_TOPIC == "fmcg-sales"
    
    def test_send_interval_is_number(self):
        from producer import SEND_INTERVAL
        assert isinstance(SEND_INTERVAL, float)
        assert SEND_INTERVAL >= 0


class TestSendRecordsMocked:
    """Test send_records with a mocked Kafka producer."""
    
    def test_send_with_limit(self):
        from producer import send_records
        
        # Create mock producer
        mock_producer = MagicMock()
        mock_future = MagicMock()
        mock_metadata = MagicMock()
        mock_metadata.topic = "test-topic"
        mock_metadata.partition = 0
        mock_metadata.offset = 0
        mock_future.get.return_value = mock_metadata
        mock_producer.send.return_value = mock_future
        
        records = [
            {"event_id": f"EVT-{i:03d}", "product_id": "P001", "units_sold": "10"}
            for i in range(20)
        ]
        
        sent = send_records(mock_producer, "test-topic", records, "event_id", limit=5)
        assert sent == 5
        assert mock_producer.send.call_count == 5
    
    def test_send_adds_ingestion_timestamp(self):
        from producer import send_records
        
        mock_producer = MagicMock()
        mock_future = MagicMock()
        mock_metadata = MagicMock()
        mock_metadata.topic = "test-topic"
        mock_metadata.partition = 0
        mock_metadata.offset = 0
        mock_future.get.return_value = mock_metadata
        mock_producer.send.return_value = mock_future
        
        records = [{"event_id": "EVT-001", "product_id": "P001"}]
        
        send_records(mock_producer, "test-topic", records, "event_id", limit=1)
        
        # Check that ingestion_timestamp was added to the record
        call_args = mock_producer.send.call_args
        sent_value = call_args[1]["value"] if "value" in call_args[1] else call_args[0][2]
        assert "ingestion_timestamp" in records[0]  # Record was mutated
    
    def test_handles_send_failure(self):
        from producer import send_records
        
        mock_producer = MagicMock()
        mock_future = MagicMock()
        mock_future.get.side_effect = Exception("Broker unavailable")
        mock_producer.send.return_value = mock_future
        
        records = [{"event_id": "EVT-001", "product_id": "P001"}]
        
        sent = send_records(mock_producer, "test-topic", records, "event_id", limit=1)
        assert sent == 0  # Should count as failed
