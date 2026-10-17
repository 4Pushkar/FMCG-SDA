"""
FMCG MongoDB Database Module
==============================
Handles persistence of processed sales records, analytics summaries,
and demand anomaly alerts to MongoDB.

Collections:
  - processed_sales:  Individual processed sales records with revenue.
  - analytics_summary: Periodic snapshots of aggregate metrics.
  - anomaly_alerts:    Detected demand spikes and anomalies.

Uses upsert operations where possible to limit duplicate writes
on re-processing.
"""

import os
import sys
from datetime import datetime
from typing import Any, Optional

if hasattr(sys.stdout, "reconfigure"):
    try:
        getattr(sys.stdout, "reconfigure")(encoding="utf-8", errors="replace")
        getattr(sys.stderr, "reconfigure")(encoding="utf-8", errors="replace")
    except Exception:
        pass

from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "fmcg_analytics")


class FMCGDatabase:
    """MongoDB persistence layer for FMCG analytics results."""
    
    def __init__(self, uri: Optional[str] = None, db_name: Optional[str] = None):
        """Initialize database connection.
        
        Args:
            uri: MongoDB connection URI. Defaults to MONGO_URI env var.
            db_name: Database name. Defaults to MONGO_DB_NAME env var.
        """
        self.uri: str = uri or MONGO_URI
        self.db_name: str = db_name or MONGO_DB_NAME
        self.client: Any = None
        self.db: Any = None
        self.connected: bool = False
    
    def connect(self) -> bool:
        """Establish connection to MongoDB.
        
        Returns:
            bool: True if connected successfully, False otherwise.
        """
        try:
            from pymongo import MongoClient
            from pymongo.errors import ConnectionFailure
            
            self.client = MongoClient(
                self.uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
            )
            # Verify connection
            self.client.admin.command("ping")
            self.db = self.client[self.db_name]
            self.connected = True
            print(f"  ✓ Connected to MongoDB: {self.db_name}")
            
            # Create indexes
            self._create_indexes()
            
            return True
            
        except Exception as e:
            self.connected = False
            self.db = None
            self.client = None
            print(f"  ⚠ MongoDB not available: {e}")
            print("    Consumer will continue without database persistence.")
            return False
    
    def _create_indexes(self):
        """Create indexes for efficient querying."""
        if not self.connected or self.db is None:
            return
        
        try:
            self.db.processed_sales.create_index("event_id", unique=True)
            self.db.processed_sales.create_index("product_id")
            self.db.processed_sales.create_index("store_id")
            self.db.processed_sales.create_index("timestamp")
            
            self.db.anomaly_alerts.create_index("alert_id", unique=True)
            self.db.anomaly_alerts.create_index("product_id")
            self.db.anomaly_alerts.create_index("detected_at")
            
            self.db.analytics_summary.create_index("snapshot_time")
        except Exception as e:
            print(f"  ⚠ Index creation issue: {e}")
    
    def save_processed_sale(self, record):
        """Save a processed sales record using upsert on event_id.
        
        Args:
            record: Processed sales record dictionary.
            
        Returns:
            bool: True if saved successfully.
        """
        if not self.connected or self.db is None:
            return False
        
        try:
            event_id = record.get("event_id")
            if not event_id:
                return False
            
            # Remove non-serializable fields
            doc = {k: v for k, v in record.items() 
                   if k != "anomaly_details" or not isinstance(v, dict)}
            
            # Flatten anomaly_details if present
            if "anomaly_details" in record and isinstance(record["anomaly_details"], dict):
                doc["anomaly_is_spike"] = record["anomaly_details"].get("is_anomaly", False)
                doc["anomaly_reason"] = record["anomaly_details"].get("reason", "")
            
            self.db.processed_sales.update_one(
                {"event_id": event_id},
                {"$set": doc},
                upsert=True,
            )
            return True
        except Exception as e:
            print(f"  ⚠ DB write error (sale): {e}")
            return False
    
    def save_anomaly_alert(self, alert):
        """Save a demand anomaly alert using upsert on alert_id.
        
        Args:
            alert: Anomaly alert dictionary.
            
        Returns:
            bool: True if saved successfully.
        """
        if not self.connected or self.db is None:
            return False
        
        try:
            alert_id = alert.get("alert_id")
            if not alert_id:
                return False
            
            self.db.anomaly_alerts.update_one(
                {"alert_id": alert_id},
                {"$set": alert},
                upsert=True,
            )
            return True
        except Exception as e:
            print(f"  ⚠ DB write error (alert): {e}")
            return False
    
    def save_summary(self, summary):
        """Save an analytics summary snapshot.
        
        Args:
            summary: Analytics summary dictionary.
            
        Returns:
            bool: True if saved successfully.
        """
        if not self.connected or self.db is None:
            return False
        
        try:
            summary["snapshot_time"] = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            self.db.analytics_summary.insert_one(summary)
            return True
        except Exception as e:
            print(f"  ⚠ DB write error (summary): {e}")
            return False
    
    def get_recent_sales(self, limit=50):
        """Retrieve recent processed sales records.
        
        Args:
            limit: Maximum records to return.
            
        Returns:
            list[dict]: Recent sales records.
        """
        if not self.connected or self.db is None:
            return []
        
        try:
            cursor = self.db.processed_sales.find(
                {}, {"_id": 0}
            ).sort("timestamp", -1).limit(limit)
            return list(cursor)
        except Exception:
            return []
    
    def get_anomaly_alerts(self, limit=20):
        """Retrieve recent anomaly alerts.
        
        Args:
            limit: Maximum alerts to return.
            
        Returns:
            list[dict]: Recent anomaly alerts.
        """
        if not self.connected or self.db is None:
            return []
        
        try:
            cursor = self.db.anomaly_alerts.find(
                {}, {"_id": 0}
            ).sort("detected_at", -1).limit(limit)
            return list(cursor)
        except Exception:
            return []
    
    def get_latest_summary(self):
        """Retrieve the most recent analytics summary.
        
        Returns:
            dict or None: Latest summary snapshot.
        """
        if not self.connected or self.db is None:
            return None
        
        try:
            doc = self.db.analytics_summary.find_one(
                {}, {"_id": 0}, sort=[("snapshot_time", -1)]
            )
            return doc
        except Exception:
            return None
    
    def get_stats(self):
        """Get collection counts for verification.
        
        Returns:
            dict: Document counts per collection.
        """
        if not self.connected or self.db is None:
            return {"connected": False}
        
        try:
            return {
                "connected": True,
                "database": self.db_name,
                "processed_sales_count": self.db.processed_sales.count_documents({}),
                "anomaly_alerts_count": self.db.anomaly_alerts.count_documents({}),
                "summary_snapshots_count": self.db.analytics_summary.count_documents({}),
            }
        except Exception as e:
            return {"connected": True, "error": str(e)}
    
    def close(self):
        """Close the database connection."""
        if self.client:
            self.client.close()
        self.connected = False
        self.client = None
        self.db = None
        print("  ✓ MongoDB connection closed")
