"""
FMCG Streaming Simulation Runner
=================================
Simulates the Kafka streaming pipeline in standalone / offline mode.
Processes sales events through FMCGAnalytics, flags demand anomalies,
and outputs real-time streaming logs without requiring external Docker services.

Usage:
    python src/simulate_stream.py [--limit N] [--interval SECONDS]
"""

import argparse
import csv
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

from analytics import FMCGAnalytics


def get_data_path():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, "data", "sample_fmcg_sales.csv")


def run_simulation(limit=0, interval=0.02):
    filepath = get_data_path()
    if not os.path.exists(filepath):
        print(f"Error: Data file not found at {filepath}")
        print("Please run `python src/data_generator.py` first.")
        sys.exit(1)

    with open(filepath, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    if limit > 0:
        records = reader[:limit]
    else:
        records = reader

    total_records = len(records)
    print("=" * 70)
    print("FMCG Streaming Pipeline Simulation")
    print(f"Total Events to Process: {total_records}")
    print(f"Streaming interval: {interval}s")
    print("=" * 70)

    analytics = FMCGAnalytics()
    processed = 0
    anomalies_found = 0

    try:
        for i, record in enumerate(records, 1):
            result = analytics.process_sale(record)
            processed += 1

            event_id = result.get("event_id", "N/A")
            product = result.get("product_name", "Unknown")[:25]
            store = result.get("store_name", "Unknown")
            units = str(result.get("units_sold", 0))
            revenue = result.get("revenue", 0.0)

            if result.get("is_anomaly"):
                anomalies_found += 1
                details = result.get("anomaly_details", {})
                mean = details.get("rolling_mean", 0)
                spike = details.get("spike_ratio", 0)
                severity = details.get("severity", "MEDIUM")

                print(
                    f"\n  🚨 [ANOMALY DETECTED] [{severity}] {event_id} | {product} @ {store}\n"
                    f"     Units Sold: {units} (Baseline Mean: {mean:.1f}, Spike: {spike:.1f}σ)\n"
                    f"     Revenue: ₹{revenue:>8.2f} | Running Total: ₹{result['running_total_revenue']:>12,.2f}\n"
                )
            else:
                print(
                    f"  [{processed:4d}/{total_records}] {event_id} | {product:25s} | "
                    f"Units: {units:>3s} | Rev: ₹{revenue:>8.2f} | "
                    f"Total Rev: ₹{result['running_total_revenue']:>12,.2f}"
                )

            if interval > 0:
                time.sleep(interval)

    except KeyboardInterrupt:
        print("\nSimulation paused by user.")

    finally:
        summary = analytics.get_summary()
        print("\n" + "=" * 70)
        print("Simulation Complete — Final Analytics Summary")
        print("=" * 70)
        print(f"  Messages processed: {processed}")
        print(f"  Total units sold:   {summary['total_units_sold']:,}")
        print(f"  Total revenue:      ₹{summary['total_revenue']:,.2f}")
        print(f"  Products tracked:   {summary['products_tracked']}")
        print(f"  Stores tracked:     {summary['stores_tracked']}")
        print(f"  Anomalies detected: {anomalies_found}")

        if summary.get("recent_anomalies"):
            print("\n  Detected Demand Spikes:")
            for a in summary["recent_anomalies"]:
                print(
                    f"    • {a.get('alert_id')}: {a.get('product_name')} @ {a.get('store_name')} "
                    f"| Units: {a.get('units_sold')} | Spike: {a.get('spike_ratio', 0):.1f}σ "
                    f"[{a.get('severity')}]"
                )
        print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Simulate FMCG Kafka Stream")
    parser.add_argument("--limit", type=int, default=0, help="Max records to process (0 = all)")
    parser.add_argument("--interval", type=float, default=0.01, help="Delay between messages in seconds")
    args = parser.parse_args()

    run_simulation(limit=args.limit, interval=args.interval)


if __name__ == "__main__":
    main()
