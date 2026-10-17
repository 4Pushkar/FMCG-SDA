"""
FMCG Kafka Consumer
====================
Consumes sales events from Kafka, processes them through the analytics
engine, detects demand anomalies, and persists results to MongoDB.

Flow:
  1. Connect to Kafka broker and subscribe to fmcg-sales topic.
  2. For each message:
     a. Parse JSON payload.
     b. Validate required fields.
     c. Run through FMCGAnalytics for metrics and anomaly detection.
     d. Save processed record and any alerts to MongoDB.
     e. Log results to console.
  3. Periodically save analytics summary snapshot.
  4. On shutdown, save final summary and close connections.
"""

import json
import os
import sys
import signal
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
SALES_TOPIC = os.getenv("KAFKA_SALES_TOPIC", "fmcg-sales")
CONSUMER_GROUP = os.getenv("CONSUMER_GROUP_ID", "fmcg-analytics-group")

# Required fields in a sales message
REQUIRED_FIELDS = ["event_id", "product_id", "store_id", "units_sold", "selling_price"]


def create_kafka_consumer():
    """Create and return a Kafka consumer instance.
    
    Returns:
        KafkaConsumer: Configured consumer subscribed to the sales topic.
    """
    from kafka import KafkaConsumer
    
    print(f"  Connecting to Kafka broker at {KAFKA_BOOTSTRAP}...")
    
    consumer = KafkaConsumer(
        SALES_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id=CONSUMER_GROUP,
        auto_offset_reset="earliest",  # Read from beginning if no committed offset
        enable_auto_commit=True,
        auto_commit_interval_ms=5000,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        consumer_timeout_ms=30000,  # Stop after 30s of no messages
        max_poll_records=50,
    )
    
    print(f"  ✓ Subscribed to topic: {SALES_TOPIC}")
    print(f"  ✓ Consumer group: {CONSUMER_GROUP}")
    
    return consumer


def validate_message(record):
    """Validate that a message has all required fields.
    
    Args:
        record: Parsed JSON message dictionary.
        
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if not isinstance(record, dict):
        return False, "Message is not a valid dictionary"
    
    missing = [f for f in REQUIRED_FIELDS if f not in record]
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"
    
    try:
        units = int(record["units_sold"])
        if units < 0:
            return False, f"Negative units_sold: {units}"
    except (ValueError, TypeError):
        return False, f"Invalid units_sold: {record['units_sold']}"
    
    try:
        price = float(record["selling_price"])
        if price <= 0:
            return False, f"Invalid selling_price: {price}"
    except (ValueError, TypeError):
        return False, f"Invalid selling_price: {record['selling_price']}"
    
    return True, None


def run_consumer(message_limit=0, save_to_db=True):
    """Run the consumer pipeline.
    
    Args:
        message_limit: Maximum messages to process. 0 = no limit (use timeout).
        save_to_db: Whether to persist results to MongoDB.
        
    Returns:
        dict: Analytics summary at shutdown.
    """
    from analytics import FMCGAnalytics
    from database import FMCGDatabase
    
    print("=" * 70)
    print("FMCG Kafka Consumer & Analytics Engine")
    print("=" * 70)
    
    # Initialize analytics
    analytics = FMCGAnalytics()
    
    # Initialize database (optional)
    db = FMCGDatabase()
    if save_to_db:
        db.connect()
    
    # Create consumer
    consumer = create_kafka_consumer()
    
    # Graceful shutdown
    running = True
    
    def handle_shutdown(signum, frame):
        nonlocal running
        print("\n  Received shutdown signal...")
        running = False
    
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    
    processed = 0
    errors = 0
    anomalies_found = 0
    summary_interval = 100  # Save summary every N messages
    
    print(f"\n  Waiting for messages on '{SALES_TOPIC}'...")
    print(f"  Message limit: {'none (timeout-based)' if message_limit == 0 else message_limit}")
    print("-" * 70)
    
    try:
        for message in consumer:
            if not running:
                break
            
            record = message.value
            
            # Validate message
            is_valid, error_msg = validate_message(record)
            if not is_valid:
                errors += 1
                print(f"  ⚠ Invalid message at offset {message.offset}: {error_msg}")
                continue
            
            # Process through analytics engine
            result = analytics.process_sale(record)
            processed += 1
            
            # Check for anomaly
            if result.get("is_anomaly"):
                anomalies_found += 1
                alert = result.get("alert", {})
                print(
                    f"\n  🚨 ANOMALY DETECTED!"
                    f"\n     Alert: {alert.get('alert_id')}"
                    f"\n     Product: {alert.get('product_name')} ({alert.get('product_id')})"
                    f"\n     Store: {alert.get('store_name')} ({alert.get('store_id')})"
                    f"\n     Units Sold: {alert.get('units_sold')} "
                    f"(baseline: {alert.get('rolling_mean'):.1f} ± {alert.get('rolling_std'):.1f})"
                    f"\n     Spike Ratio: {alert.get('spike_ratio')}σ"
                    f"\n     Severity: {alert.get('severity')}"
                    f"\n"
                )
                
                # Save alert to DB
                if db.connected:
                    db.save_anomaly_alert(alert)
            else:
                # Normal message log (concise)
                event_id = record.get("event_id", "?")
                product = record.get("product_name", "?")
                units = record.get("units_sold", "?")
                revenue = result.get("revenue", 0)
                print(
                    f"  [{processed:4d}] {event_id} | {product:25s} | "
                    f"Units: {units:3s} | Rev: ₹{revenue:>8.2f} | "
                    f"Total Rev: ₹{result['running_total_revenue']:>12,.2f}"
                )
            
            # Save to database
            if db.connected:
                db.save_processed_sale(result)
            
            # Periodic summary
            if processed % summary_interval == 0:
                summary = analytics.get_summary()
                if db.connected:
                    db.save_summary(summary)
                print(f"\n  --- Summary at {processed} messages ---")
                print(f"      Total units: {summary['total_units_sold']:,}")
                print(f"      Total revenue: ₹{summary['total_revenue']:,.2f}")
                print(f"      Anomalies: {summary['anomalies_detected']}")
                print()
            
            # Check limit
            if message_limit > 0 and processed >= message_limit:
                print(f"\n  Reached message limit ({message_limit})")
                break
    
    except Exception as e:
        print(f"\n  ✗ Consumer error: {e}")
    
    finally:
        # Final summary
        summary = analytics.get_summary()
        
        print("\n" + "=" * 70)
        print("Consumer Shutdown — Final Summary")
        print("=" * 70)
        print(f"  Messages processed: {processed}")
        print(f"  Validation errors: {errors}")
        print(f"  Total units sold: {summary['total_units_sold']:,}")
        print(f"  Total revenue: ₹{summary['total_revenue']:,.2f}")
        print(f"  Products tracked: {summary['products_tracked']}")
        print(f"  Stores tracked: {summary['stores_tracked']}")
        print(f"  Anomalies detected: {anomalies_found}")
        
        if summary['recent_anomalies']:
            print(f"\n  Recent Anomalies:")
            for alert in summary['recent_anomalies'][-5:]:
                print(
                    f"    {alert['alert_id']} | {alert['product_name']} "
                    f"@ {alert['store_name']} | {alert['units_sold']} units "
                    f"| {alert['severity']}"
                )
        
        # Save final summary
        if db.connected:
            db.save_summary(summary)
            stats = db.get_stats()
            print(f"\n  MongoDB Stats:")
            print(f"    Processed sales: {stats.get('processed_sales_count', 'N/A')}")
            print(f"    Anomaly alerts: {stats.get('anomaly_alerts_count', 'N/A')}")
            print(f"    Summary snapshots: {stats.get('summary_snapshots_count', 'N/A')}")
            db.close()
        
        consumer.close()
        print("  ✓ Consumer closed cleanly")
        print("=" * 70)
    
    return summary


def main():
    """Entry point — parse CLI arguments and run the consumer."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="FMCG Kafka Consumer — process sales events and detect anomalies"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Max messages to process (default: 0 = until timeout/interrupt)",
    )
    parser.add_argument(
        "--no-db",
        action="store_true",
        help="Skip MongoDB persistence",
    )
    
    args = parser.parse_args()
    
    try:
        run_consumer(message_limit=args.limit, save_to_db=not args.no_db)
    except KeyboardInterrupt:
        print("\n  Consumer interrupted.")
        sys.exit(0)
    except Exception as e:
        print(f"\n  ✗ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
