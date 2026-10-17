"""
FMCG Analytics Engine
=====================
Calculates FMCG sales metrics, maintains rolling aggregates,
and detects demand anomalies using a rolling baseline approach.

Anomaly Detection Method:
  - Maintains a rolling window of recent sales per product-store pair.
  - Computes the rolling mean and standard deviation.
  - Flags a record as a "demand spike" if units_sold exceeds:
      rolling_mean + (threshold × rolling_std_dev)
  - Default threshold is 2.0 standard deviations.

Limitations:
  - This is a simple statistical rule, not a predictive ML model.
  - It requires sufficient history in the rolling window to be meaningful.
  - It may miss gradual trends or seasonal patterns.
  - False positives are possible during natural high-variance periods.
"""

import os
from collections import defaultdict
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

ANOMALY_THRESHOLD = float(os.getenv("ANOMALY_THRESHOLD", "2.0"))
ROLLING_WINDOW_SIZE = int(os.getenv("ROLLING_WINDOW_SIZE", "20"))


class FMCGAnalytics:
    """Streaming analytics engine for FMCG sales data.
    
    Maintains running aggregates and detects demand anomalies
    using a rolling-window statistical method.
    """
    
    def __init__(self, threshold=None, window_size=None):
        """Initialize the analytics engine.
        
        Args:
            threshold: Number of standard deviations above the rolling mean
                       to flag as an anomaly. Default: ANOMALY_THRESHOLD.
            window_size: Number of recent observations to keep per product-store
                         pair. Default: ROLLING_WINDOW_SIZE.
        """
        self.threshold = threshold or ANOMALY_THRESHOLD
        self.window_size = window_size or ROLLING_WINDOW_SIZE
        
        # Running totals
        self.total_units = 0
        self.total_revenue = 0.0
        self.message_count = 0
        
        # Per-product aggregates
        self.product_units = defaultdict(int)
        self.product_revenue = defaultdict(float)
        
        # Per-store aggregates
        self.store_units = defaultdict(int)
        self.store_revenue = defaultdict(float)
        
        # Per-category aggregates
        self.category_units = defaultdict(int)
        self.category_revenue = defaultdict(float)
        
        # Rolling window for anomaly detection: {(product_id, store_id): [units_sold, ...]}
        self.rolling_windows = defaultdict(list)
        
        # Detected anomalies
        self.anomalies = []
    
    def process_sale(self, record):
        """Process a single sales record and return enriched result.
        
        Args:
            record: Dict with at least product_id, store_id, units_sold,
                    selling_price, and product_name.
                    
        Returns:
            dict: Enriched record with revenue, running totals, and
                  anomaly detection results.
        """
        self.message_count += 1
        
        # Extract fields
        product_id = record.get("product_id", "unknown")
        product_name = record.get("product_name", "unknown")
        store_id = record.get("store_id", "unknown")
        store_name = record.get("store_name", "unknown")
        category = record.get("category", "unknown")
        
        try:
            units_sold = int(record.get("units_sold", 0))
        except (ValueError, TypeError):
            units_sold = 0
        
        try:
            selling_price = float(record.get("selling_price", 0))
        except (ValueError, TypeError):
            selling_price = 0.0
        
        # Calculate revenue for this transaction
        revenue = round(units_sold * selling_price, 2)
        
        # Update running totals
        self.total_units += units_sold
        self.total_revenue += revenue
        
        # Update per-dimension aggregates
        self.product_units[product_id] += units_sold
        self.product_revenue[product_id] += revenue
        self.store_units[store_id] += units_sold
        self.store_revenue[store_id] += revenue
        self.category_units[category] += units_sold
        self.category_revenue[category] += revenue
        
        # Anomaly detection
        anomaly_result = self._check_anomaly(product_id, store_id, units_sold)
        
        # Update rolling window AFTER checking (so current value isn't in its own baseline)
        key = (product_id, store_id)
        self.rolling_windows[key].append(units_sold)
        if len(self.rolling_windows[key]) > self.window_size:
            self.rolling_windows[key].pop(0)
        
        # Build enriched result
        result = {
            **record,
            "revenue": revenue,
            "running_total_units": self.total_units,
            "running_total_revenue": round(self.total_revenue, 2),
            "message_number": self.message_count,
            "is_anomaly": anomaly_result["is_anomaly"],
            "anomaly_details": anomaly_result,
            "processed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
        }
        
        # Store anomaly if detected
        if anomaly_result["is_anomaly"]:
            alert = {
                "alert_id": f"ALERT-{len(self.anomalies) + 1:04d}",
                "event_id": record.get("event_id", ""),
                "timestamp": record.get("timestamp", ""),
                "product_id": product_id,
                "product_name": product_name,
                "store_id": store_id,
                "store_name": store_name,
                "units_sold": units_sold,
                "rolling_mean": anomaly_result["rolling_mean"],
                "rolling_std": anomaly_result["rolling_std"],
                "threshold_value": anomaly_result["threshold_value"],
                "spike_ratio": anomaly_result["spike_ratio"],
                "detected_at": result["processed_at"],
                "severity": self._classify_severity(anomaly_result["spike_ratio"]),
            }
            self.anomalies.append(alert)
            result["alert"] = alert
        
        return result
    
    def _check_anomaly(self, product_id, store_id, units_sold):
        """Check if current units_sold is an anomaly for this product-store pair.
        
        Uses rolling mean + threshold × rolling std deviation.
        Requires at least 5 data points in the window for a meaningful check.
        
        Args:
            product_id: Product identifier.
            store_id: Store identifier.
            units_sold: Current transaction units.
            
        Returns:
            dict: Anomaly detection details.
        """
        key = (product_id, store_id)
        window = self.rolling_windows[key]
        
        # Need at least 5 points for meaningful statistics
        if len(window) < 5:
            return {
                "is_anomaly": False,
                "reason": "insufficient_data",
                "window_size": len(window),
                "rolling_mean": None,
                "rolling_std": None,
                "threshold_value": None,
                "spike_ratio": None,
            }
        
        # Calculate rolling statistics
        rolling_mean = sum(window) / len(window)
        variance = sum((x - rolling_mean) ** 2 for x in window) / len(window)
        rolling_std = variance ** 0.5
        
        # Avoid division by zero — if std is very small, use a minimum
        if rolling_std < 1.0:
            rolling_std = 1.0
        
        threshold_value = rolling_mean + (self.threshold * rolling_std)
        spike_ratio = round((units_sold - rolling_mean) / rolling_std, 2)
        
        is_anomaly = units_sold > threshold_value
        
        return {
            "is_anomaly": is_anomaly,
            "reason": "demand_spike" if is_anomaly else "normal",
            "window_size": len(window),
            "rolling_mean": round(rolling_mean, 2),
            "rolling_std": round(rolling_std, 2),
            "threshold_value": round(threshold_value, 2),
            "spike_ratio": spike_ratio,
            "units_sold": units_sold,
        }
    
    @staticmethod
    def _classify_severity(spike_ratio):
        """Classify anomaly severity based on how far above the threshold.
        
        Args:
            spike_ratio: Standard deviations above mean.
            
        Returns:
            str: Severity level.
        """
        if spike_ratio is None:
            return "unknown"
        if spike_ratio >= 4.0:
            return "CRITICAL"
        elif spike_ratio >= 3.0:
            return "HIGH"
        elif spike_ratio >= 2.0:
            return "MEDIUM"
        else:
            return "LOW"
    
    def get_summary(self):
        """Return current analytics summary.
        
        Returns:
            dict: Summary of all tracked metrics.
        """
        return {
            "total_messages_processed": self.message_count,
            "total_units_sold": self.total_units,
            "total_revenue": round(self.total_revenue, 2),
            "products_tracked": len(self.product_units),
            "stores_tracked": len(self.store_units),
            "anomalies_detected": len(self.anomalies),
            "product_breakdown": dict(self.product_units),
            "product_revenue": {k: round(v, 2) for k, v in self.product_revenue.items()},
            "store_breakdown": dict(self.store_units),
            "store_revenue": {k: round(v, 2) for k, v in self.store_revenue.items()},
            "category_breakdown": dict(self.category_units),
            "category_revenue": {k: round(v, 2) for k, v in self.category_revenue.items()},
            "recent_anomalies": self.anomalies[-10:],  # Last 10 alerts
        }
