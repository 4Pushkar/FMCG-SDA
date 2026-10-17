"""
FMCG Kafka Producer
====================
Reads FMCG sample CSV data and publishes structured JSON messages
to Apache Kafka topics.

Topics:
  - fmcg-sales:    Sales transaction events
  - fmcg-price:    Product pricing changes
  - fmcg-calendar: Calendar and promotional context

Each message includes the original record fields plus an ingestion_timestamp
indicating when the message was published to Kafka.
"""

import csv
import json
import os
import sys
import time
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from dotenv import load_dotenv

# Load environment configuration
load_dotenv()

# --- Configuration from environment ---
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
SALES_TOPIC = os.getenv("KAFKA_SALES_TOPIC", "fmcg-sales")
PRICE_TOPIC = os.getenv("KAFKA_PRICE_TOPIC", "fmcg-price")
CALENDAR_TOPIC = os.getenv("KAFKA_CALENDAR_TOPIC", "fmcg-calendar")
SEND_INTERVAL = float(os.getenv("PRODUCER_SEND_INTERVAL", "0.3"))
MESSAGE_LIMIT = int(os.getenv("PRODUCER_MESSAGE_LIMIT", "0"))  # 0 = no limit


def get_data_dir():
    """Return absolute path to the data directory."""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"
    )


def read_csv_records(filepath):
    """Read CSV file and return list of dictionaries.
    
    Args:
        filepath: Absolute path to the CSV file.
        
    Returns:
        list[dict]: Records from the CSV file.
        
    Raises:
        FileNotFoundError: If the CSV file does not exist.
        ValueError: If the CSV file is empty.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Data file not found: {filepath}")
    
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        records = list(reader)
    
    if not records:
        raise ValueError(f"Data file is empty: {filepath}")
    
    return records


def create_kafka_producer():
    """Create and return a Kafka producer instance.
    
    Returns:
        KafkaProducer: Configured producer instance.
        
    Raises:
        ConnectionError: If Kafka broker is not reachable.
    """
    from kafka import KafkaProducer
    
    print(f"  Connecting to Kafka broker at {KAFKA_BOOTSTRAP}...")
    
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8") if k else None,
        acks="all",                  # Wait for all replicas
        retries=3,                   # Retry on transient failures
        retry_backoff_ms=500,
        request_timeout_ms=10000,
        max_block_ms=15000,          # Max wait to connect
    )
    
    print("  ✓ Connected to Kafka broker")
    return producer


def send_records(producer, topic, records, key_field, limit=0):
    """Send records to a Kafka topic with acknowledgement verification.
    
    Args:
        producer: KafkaProducer instance.
        topic: Kafka topic name.
        records: List of record dictionaries to send.
        key_field: Field name to use as the message key.
        limit: Maximum number of records to send (0 = all).
        
    Returns:
        int: Number of successfully sent messages.
    """
    if limit > 0:
        records = records[:limit]
    
    sent_count = 0
    error_count = 0
    
    print(f"\n  Sending {len(records)} records to topic '{topic}'...")
    print(f"  Send interval: {SEND_INTERVAL}s")
    print("-" * 70)
    
    for i, record in enumerate(records, 1):
        # Add ingestion timestamp (when published, not when event occurred)
        record["ingestion_timestamp"] = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )
        
        message_key = record.get(key_field, f"key-{i}")
        
        try:
            # Send and wait for acknowledgement
            future = producer.send(topic, key=message_key, value=record)
            metadata = future.get(timeout=10)  # Block until acknowledged
            
            sent_count += 1
            
            # Log acknowledgement details
            event_label = record.get("event_id", record.get("price_id", record.get("date", f"rec-{i}")))
            print(
                f"  [{sent_count:4d}/{len(records)}] ✓ Sent "
                f"| Topic: {metadata.topic} "
                f"| Partition: {metadata.partition} "
                f"| Offset: {metadata.offset} "
                f"| Key: {message_key} "
                f"| ID: {event_label}"
            )
            
        except Exception as e:
            error_count += 1
            print(f"  [{i:4d}/{len(records)}] ✗ FAILED | Error: {e}")
        
        # Throttle sending
        if SEND_INTERVAL > 0:
            time.sleep(SEND_INTERVAL)
    
    print("-" * 70)
    print(f"  Sent: {sent_count} | Failed: {error_count} | Total: {len(records)}")
    
    return sent_count


def run_producer(topics=None, limit=0):
    """Run the complete producer pipeline.
    
    Args:
        topics: List of topics to publish ("sales", "price", "calendar").
                Defaults to ["sales"] if not specified.
        limit: Max messages per topic. 0 = all records.
        
    Returns:
        dict: Summary of sent message counts per topic.
    """
    if topics is None:
        topics = ["sales"]
    
    data_dir = get_data_dir()
    
    # Topic configuration: (topic_name, csv_file, key_field)
    topic_config = {
        "sales": (SALES_TOPIC, "sample_fmcg_sales.csv", "event_id"),
        "price": (PRICE_TOPIC, "sample_fmcg_prices.csv", "product_id"),
        "calendar": (CALENDAR_TOPIC, "sample_fmcg_calendar.csv", "date"),
    }
    
    print("=" * 70)
    print("FMCG Kafka Producer")
    print("=" * 70)
    print(f"  Broker: {KAFKA_BOOTSTRAP}")
    print(f"  Topics: {', '.join(topics)}")
    print(f"  Message limit per topic: {'all' if limit == 0 else limit}")
    
    producer = create_kafka_producer()
    summary = {}
    
    try:
        for topic_key in topics:
            if topic_key not in topic_config:
                print(f"\n  ⚠ Unknown topic '{topic_key}', skipping.")
                continue
            
            topic_name, csv_file, key_field = topic_config[topic_key]
            csv_path = os.path.join(data_dir, csv_file)
            
            print(f"\n  Loading: {csv_file}")
            records = read_csv_records(csv_path)
            print(f"  Loaded {len(records)} records")
            
            sent = send_records(producer, topic_name, records, key_field, limit)
            summary[topic_name] = sent
    
    finally:
        producer.flush()
        producer.close()
        print("\n  ✓ Producer closed cleanly")
    
    print("\n" + "=" * 70)
    print("Producer Summary")
    print("=" * 70)
    for topic, count in summary.items():
        print(f"  {topic}: {count} messages sent")
    print("=" * 70)
    
    return summary


def main():
    """Entry point — parse CLI arguments and run the producer."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="FMCG Kafka Producer — publish sample data to Kafka topics"
    )
    parser.add_argument(
        "--topics",
        nargs="+",
        choices=["sales", "price", "calendar"],
        default=["sales"],
        help="Topics to publish (default: sales)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Max messages per topic (default: 0 = all)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=None,
        help="Seconds between messages (overrides .env)",
    )
    
    args = parser.parse_args()
    
    # Override interval if specified
    global SEND_INTERVAL
    if args.interval is not None:
        SEND_INTERVAL = args.interval
    
    try:
        run_producer(topics=args.topics, limit=args.limit)
    except KeyboardInterrupt:
        print("\n  Producer interrupted by user.")
        sys.exit(0)
    except ConnectionError as e:
        print(f"\n  ✗ Kafka connection failed: {e}")
        print("    Ensure Kafka is running: docker compose up -d")
        sys.exit(1)
    except Exception as e:
        print(f"\n  ✗ Producer error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
