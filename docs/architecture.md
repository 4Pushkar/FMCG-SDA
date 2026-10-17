# FMCG Streaming Analytics — Architecture

## System Overview

```
┌─────────────────────┐
│  Sample CSV Data    │
│  (sales, prices,    │
│   calendar)         │
└────────┬────────────┘
         │ Read CSV
         ▼
┌─────────────────────┐     ┌─────────────────────┐
│  Python Producer    │────▶│  Apache Kafka        │
│  (producer.py)      │     │  (Docker Container)  │
│                     │     │                      │
│  • Reads CSV rows   │     │  Topics:             │
│  • Converts to JSON │     │  • fmcg-sales        │
│  • Adds timestamp   │     │  • fmcg-price        │
│  • Sends to Kafka   │     │  • fmcg-calendar     │
└─────────────────────┘     └────────┬────────────┘
                                     │ Consume
                                     ▼
                            ┌─────────────────────┐
                            │  Python Consumer     │
                            │  (consumer.py)       │
                            │                      │
                            │  • Parses JSON       │
                            │  • Validates fields  │
                            │  • Calls Analytics   │
                            └────────┬────────────┘
                                     │
                                     ▼
                            ┌─────────────────────┐
                            │  Analytics Engine    │
                            │  (analytics.py)      │
                            │                      │
                            │  • Revenue calc      │
                            │  • Rolling metrics   │
                            │  • Anomaly detection │
                            └────────┬────────────┘
                                     │
                          ┌──────────┴──────────┐
                          ▼                     ▼
                 ┌────────────────┐    ┌────────────────┐
                 │  MongoDB       │    │  Console Logs  │
                 │  (Docker)      │    │                │
                 │                │    │  Real-time     │
                 │  Collections:  │    │  processing    │
                 │  • sales       │    │  output        │
                 │  • alerts      │    │                │
                 │  • summaries   │    └────────────────┘
                 └───────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │  Streamlit      │
                │  Dashboard      │
                │  (app.py)       │
                │                 │
                │  • KPI cards    │
                │  • Charts       │
                │  • Alerts       │
                │  • Sales table  │
                └─────────────────┘
```

## Component Details

### 1. Data Sources
- **Sales CSV**: 1,500 synthetic transaction records (10 products × 5 stores × 30 days)
- **Prices CSV**: ~100–150 price change records
- **Calendar CSV**: 30 daily records with promotional context

### 2. Apache Kafka (Docker)
- **Image**: `apache/kafka:3.8.0` (KRaft mode — no Zookeeper)
- **Port**: `localhost:9092`
- **Topics**: `fmcg-sales`, `fmcg-price`, `fmcg-calendar`
- **Mode**: Single-node broker with controller

### 3. Python Producer (`src/producer.py`)
- Reads CSV files and converts each row to a JSON message
- Adds `ingestion_timestamp` to each message
- Uses the event ID as the Kafka message key
- Waits for broker acknowledgement before logging success
- Supports CLI arguments: `--topics`, `--limit`, `--interval`

### 4. Python Consumer (`src/consumer.py`)
- Subscribes to `fmcg-sales` topic
- Validates each message for required fields
- Passes valid records to the analytics engine
- Logs processing results and anomaly alerts to console
- Saves results to MongoDB (optional)

### 5. Analytics Engine (`src/analytics.py`)
- Calculates `revenue = units_sold × selling_price`
- Maintains per-product, per-store, and per-category running totals
- Detects anomalies using a rolling-window method:
  - Keeps last N sales per product-store pair
  - Flags when `units_sold > rolling_mean + (threshold × rolling_std)`
  - Default threshold: 2.0 standard deviations
  - Requires ≥5 data points before flagging

### 6. MongoDB (Docker)
- **Image**: `mongo:7.0`
- **Port**: `localhost:27017`
- **Database**: `fmcg_analytics`
- **Collections**:
  - `processed_sales` — enriched sales with revenue and anomaly flags
  - `anomaly_alerts` — detected demand spikes
  - `analytics_summary` — periodic metric snapshots

### 7. Streamlit Dashboard (`dashboard/app.py`)
- **Port**: `localhost:8501`
- Displays KPI cards, product/store charts, anomaly alerts, and sales table
- Reads data from MongoDB
- Optional auto-refresh mode

## Technology Choices

| Technology | Purpose | Justification |
|-----------|---------|---------------|
| Python 3.13 | Application code | Primary language, widely taught, extensive library ecosystem |
| kafka-python-ng | Kafka client | Actively maintained fork of kafka-python, compatible with Python 3.12+ |
| Apache Kafka 3.8 | Message streaming | Industry-standard streaming platform, KRaft mode eliminates Zookeeper |
| MongoDB 7.0 | Data persistence | Flexible schema suits evolving analytics output, easy JSON storage |
| Streamlit | Dashboard | Minimal setup for data-focused dashboards, Python-native |
| Plotly | Visualization | Interactive charts with minimal code |
| Docker Compose | Infrastructure | Reproducible local development environment |
