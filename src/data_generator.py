"""
FMCG Sample Data Generator
===========================
Generates synthetic FMCG (Fast-Moving Consumer Goods) sales, pricing, and
calendar data for the streaming analytics pipeline demonstration.

All data is SYNTHETIC — generated with reproducible random seeds.
It is NOT sourced from any real retailer or the M5/Walmart dataset.

The generator deliberately injects demand spikes to test anomaly detection.
"""

import csv
import os
import random
import sys
from datetime import datetime, timedelta

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Reproducible randomness
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# --- Configuration ---
NUM_DAYS = 30  # One month of data
START_DATE = datetime(2026, 9, 1)

# Products: (product_id, product_name, category, base_price, base_daily_units)
PRODUCTS = [
    ("P001", "Lays Classic Chips",       "Snacks",     30.00,  15),
    ("P002", "Coca-Cola 500ml",          "Beverages",  40.00,  25),
    ("P003", "Maggi 2-Min Noodles",      "Instant Food", 14.00, 30),
    ("P004", "Parle-G Biscuits",         "Biscuits",   10.00,  40),
    ("P005", "Amul Butter 100g",         "Dairy",      56.00,  12),
    ("P006", "Surf Excel Detergent 1kg", "Home Care",  190.00,  8),
    ("P007", "Colgate MaxFresh 150g",    "Personal Care", 95.00, 10),
    ("P008", "Tata Tea Gold 500g",       "Beverages",  260.00,  7),
    ("P009", "Britannia Bread",          "Bakery",     45.00,  20),
    ("P010", "Dettol Soap 75g",          "Personal Care", 42.00, 14),
]

# Stores
STORES = [
    ("S01", "Mumbai Central"),
    ("S02", "Delhi NCR Hub"),
    ("S03", "Bangalore Koramangala"),
    ("S04", "Hyderabad Banjara Hills"),
    ("S05", "Chennai T Nagar"),
]

# Deliberate demand spike configuration
# (product_id, store_id, spike_day_offset, spike_multiplier)
DEMAND_SPIKES = [
    ("P003", "S01", 10, 4.0),   # Maggi spike in Mumbai on day 10
    ("P002", "S03", 18, 3.5),   # Coca-Cola spike in Bangalore on day 18
    ("P004", "S02", 25, 5.0),   # Parle-G spike in Delhi on day 25
]

# Promotions
PROMOTIONS = [
    (7, 9, "Weekend Mega Sale"),         # Days 7-9
    (14, 16, "Mid-Month Clearance"),     # Days 14-16
    (21, 23, "Festival Special Offer"),  # Days 21-23
]


def get_data_dir():
    """Return absolute path to the data directory."""
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def generate_sales_data():
    """Generate synthetic FMCG sales transaction records.
    
    Returns:
        list[dict]: Sales records with event_id, timestamp, product details,
                    store details, units_sold, and selling_price.
    """
    records = []
    event_counter = 0
    
    for day_offset in range(NUM_DAYS):
        current_date = START_DATE + timedelta(days=day_offset)
        weekday = current_date.strftime("%A")
        is_weekend = current_date.weekday() >= 5
        
        for store_id, store_name in STORES:
            for prod_id, prod_name, category, base_price, base_units in PRODUCTS:
                event_counter += 1
                event_id = f"EVT-{event_counter:06d}"
                
                # Base units with natural daily variation (±30%)
                variation = random.uniform(0.7, 1.3)
                units = int(base_units * variation)
                
                # Weekend boost (+20%)
                if is_weekend:
                    units = int(units * 1.2)
                
                # Check for deliberate demand spike
                for spike_prod, spike_store, spike_day, spike_mult in DEMAND_SPIKES:
                    if (prod_id == spike_prod and store_id == spike_store 
                            and day_offset == spike_day):
                        units = int(base_units * spike_mult)
                
                # Small price variation (±2%) around base price
                selling_price = round(base_price * random.uniform(0.98, 1.02), 2)
                
                # Generate timestamp within business hours (8 AM - 10 PM)
                hour = random.randint(8, 21)
                minute = random.randint(0, 59)
                second = random.randint(0, 59)
                timestamp = current_date.replace(
                    hour=hour, minute=minute, second=second
                )
                
                records.append({
                    "event_id": event_id,
                    "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "product_id": prod_id,
                    "product_name": prod_name,
                    "category": category,
                    "store_id": store_id,
                    "store_name": store_name,
                    "units_sold": max(1, units),  # At least 1 unit
                    "selling_price": selling_price,
                })
    
    return records


def generate_price_data():
    """Generate synthetic price change records.
    
    Returns:
        list[dict]: Price records showing price changes over time.
    """
    records = []
    price_counter = 0
    
    for prod_id, prod_name, category, base_price, _ in PRODUCTS:
        for store_id, store_name in STORES:
            # Initial price
            price_counter += 1
            records.append({
                "price_id": f"PRC-{price_counter:05d}",
                "product_id": prod_id,
                "product_name": prod_name,
                "store_id": store_id,
                "selling_price": base_price,
                "effective_date": START_DATE.strftime("%Y-%m-%d"),
                "change_reason": "Initial Price",
            })
            
            # 1-2 price changes during the month
            num_changes = random.randint(1, 2)
            current_price = base_price
            for _ in range(num_changes):
                price_counter += 1
                change_day = random.randint(5, NUM_DAYS - 1)
                change_date = START_DATE + timedelta(days=change_day)
                
                # Price change: -5% to +8%
                change_pct = random.uniform(-0.05, 0.08)
                current_price = round(base_price * (1 + change_pct), 2)
                
                reason = random.choice([
                    "Seasonal Adjustment",
                    "Promotional Discount",
                    "Supplier Cost Change",
                    "Competitive Pricing",
                    "Festive Offer",
                ])
                
                records.append({
                    "price_id": f"PRC-{price_counter:05d}",
                    "product_id": prod_id,
                    "product_name": prod_name,
                    "store_id": store_id,
                    "selling_price": current_price,
                    "effective_date": change_date.strftime("%Y-%m-%d"),
                    "change_reason": reason,
                })
    
    return records


def generate_calendar_data():
    """Generate calendar/promotional context data.
    
    Returns:
        list[dict]: Calendar records with date, weekday, and promotion info.
    """
    records = []
    
    for day_offset in range(NUM_DAYS):
        current_date = START_DATE + timedelta(days=day_offset)
        weekday = current_date.strftime("%A")
        is_weekend = current_date.weekday() >= 5
        
        # Check for promotions
        promo_flag = False
        event_name = "None"
        for promo_start, promo_end, promo_name in PROMOTIONS:
            if promo_start <= day_offset <= promo_end:
                promo_flag = True
                event_name = promo_name
                break
        
        records.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "day_of_week": weekday,
            "is_weekend": is_weekend,
            "is_promotion": promo_flag,
            "event_name": event_name,
            "month": current_date.strftime("%B"),
            "week_number": current_date.isocalendar()[1],
        })
    
    return records


def write_csv(filepath, records, fieldnames):
    """Write records to a CSV file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    print(f"  Written {len(records)} records to {filepath}")


def validate_data(sales, prices, calendar):
    """Validate generated data and print summary statistics."""
    print("\n--- Data Validation ---")
    
    # Sales validation
    event_ids = [r["event_id"] for r in sales]
    assert len(event_ids) == len(set(event_ids)), "Duplicate event IDs found!"
    assert all(r["units_sold"] >= 1 for r in sales), "Invalid units_sold found!"
    assert all(r["selling_price"] > 0 for r in sales), "Invalid price found!"
    
    unique_products = set(r["product_id"] for r in sales)
    unique_stores = set(r["store_id"] for r in sales)
    total_revenue = sum(r["units_sold"] * r["selling_price"] for r in sales)
    
    print(f"  Sales records: {len(sales)}")
    print(f"  Unique event IDs: {len(set(event_ids))}")
    print(f"  Unique products: {len(unique_products)}")
    print(f"  Unique stores: {len(unique_stores)}")
    print(f"  Date range: {sales[0]['timestamp'][:10]} to {sales[-1]['timestamp'][:10]}")
    print(f"  Total estimated revenue: ₹{total_revenue:,.2f}")
    
    # Price validation
    print(f"  Price records: {len(prices)}")
    assert all(r["selling_price"] > 0 for r in prices), "Invalid price record!"
    
    # Calendar validation
    print(f"  Calendar records: {len(calendar)}")
    promo_days = sum(1 for r in calendar if r["is_promotion"])
    print(f"  Promotion days: {promo_days}")
    
    # Verify spikes are present
    spike_count = 0
    for spike_prod, spike_store, spike_day, spike_mult in DEMAND_SPIKES:
        spike_date = (START_DATE + timedelta(days=spike_day)).strftime("%Y-%m-%d")
        for r in sales:
            if (r["product_id"] == spike_prod and r["store_id"] == spike_store
                    and r["timestamp"].startswith(spike_date)):
                base = next(p[4] for p in PRODUCTS if p[0] == spike_prod)
                if r["units_sold"] >= base * (spike_mult * 0.9):
                    spike_count += 1
                    break
    print(f"  Injected demand spikes verified: {spike_count}/{len(DEMAND_SPIKES)}")
    
    print("  ✓ All validations passed\n")


def main():
    """Generate all sample datasets and validate them."""
    print("=" * 60)
    print("FMCG Sample Data Generator")
    print("=" * 60)
    print(f"  Random seed: {RANDOM_SEED}")
    print(f"  Date range: {START_DATE.strftime('%Y-%m-%d')} to "
          f"{(START_DATE + timedelta(days=NUM_DAYS-1)).strftime('%Y-%m-%d')}")
    print(f"  Products: {len(PRODUCTS)}")
    print(f"  Stores: {len(STORES)}")
    print(f"  Deliberate demand spikes: {len(DEMAND_SPIKES)}")
    print()
    
    data_dir = get_data_dir()
    
    # Generate sales data
    print("Generating sales data...")
    sales = generate_sales_data()
    write_csv(
        os.path.join(data_dir, "sample_fmcg_sales.csv"),
        sales,
        ["event_id", "timestamp", "product_id", "product_name", "category",
         "store_id", "store_name", "units_sold", "selling_price"],
    )
    
    # Generate price data
    print("Generating price data...")
    prices = generate_price_data()
    write_csv(
        os.path.join(data_dir, "sample_fmcg_prices.csv"),
        prices,
        ["price_id", "product_id", "product_name", "store_id",
         "selling_price", "effective_date", "change_reason"],
    )
    
    # Generate calendar data
    print("Generating calendar data...")
    calendar = generate_calendar_data()
    write_csv(
        os.path.join(data_dir, "sample_fmcg_calendar.csv"),
        calendar,
        ["date", "day_of_week", "is_weekend", "is_promotion",
         "event_name", "month", "week_number"],
    )
    
    # Validate
    validate_data(sales, prices, calendar)
    
    print("=" * 60)
    print("Data generation complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
