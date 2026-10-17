# FMCG Data Dictionary

## Overview
All sample data in this project is **synthetic** — generated using Python with a fixed random seed (`42`) for reproducibility. The data simulates one month (September 2026) of FMCG sales activity across 5 stores and 10 products. Three deliberate demand spikes have been injected to test anomaly detection.

---

## Source 1: Sales Transactions (`sample_fmcg_sales.csv`)

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `event_id` | String | Unique transaction identifier | `EVT-000001` |
| `timestamp` | DateTime | When the sale occurred (YYYY-MM-DD HH:MM:SS) | `2026-09-01 14:23:45` |
| `product_id` | String | Product identifier (P001–P010) | `P003` |
| `product_name` | String | Human-readable product name | `Maggi 2-Min Noodles` |
| `category` | String | Product category | `Instant Food` |
| `store_id` | String | Store identifier (S01–S05) | `S01` |
| `store_name` | String | Store location name | `Mumbai Central` |
| `units_sold` | Integer | Number of units sold (≥1) | `30` |
| `selling_price` | Float | Price per unit in INR | `14.28` |

- **Records**: 1,500 (10 products × 5 stores × 30 days)
- **Unique Event IDs**: 1,500 (all unique)
- **Date Range**: 2026-09-01 to 2026-09-30
- **Injected Spikes**: 3 (Maggi/Mumbai day 10, Coca-Cola/Bangalore day 18, Parle-G/Delhi day 25)

---

## Source 2: Product Pricing (`sample_fmcg_prices.csv`)

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `price_id` | String | Unique price record ID | `PRC-00001` |
| `product_id` | String | Product identifier | `P001` |
| `product_name` | String | Product name | `Lays Classic Chips` |
| `store_id` | String | Store identifier | `S01` |
| `selling_price` | Float | Price per unit in INR | `30.00` |
| `effective_date` | Date | When this price took effect | `2026-09-01` |
| `change_reason` | String | Reason for the price change | `Promotional Discount` |

- **Records**: ~100–150 (initial prices + 1–2 changes per product-store)
- **Price Range**: Varies by product (₹10–₹260)

---

## Source 3: Calendar Context (`sample_fmcg_calendar.csv`)

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `date` | Date | Calendar date (YYYY-MM-DD) | `2026-09-07` |
| `day_of_week` | String | Day name | `Monday` |
| `is_weekend` | Boolean | Whether Saturday or Sunday | `False` |
| `is_promotion` | Boolean | Whether a promotion is active | `True` |
| `event_name` | String | Promotion name or "None" | `Weekend Mega Sale` |
| `month` | String | Month name | `September` |
| `week_number` | Integer | ISO week number | `36` |

- **Records**: 30 (one per day)
- **Promotion Periods**: 3 (9 promotional days total)

---

## Data Suitability
This synthetic dataset is suitable for demonstrating FMCG streaming analytics because:
1. It covers realistic Indian FMCG products with plausible prices and sales volumes.
2. It includes multiple dimensions (product, store, category, time) for meaningful aggregation.
3. Deliberate demand spikes provide testable anomaly-detection scenarios.
4. The volume (1,500 sales records) is sufficient for a streaming demonstration while remaining manageable.
5. Reproducible random seeds ensure consistent results across runs.
