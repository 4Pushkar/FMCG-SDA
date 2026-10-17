# FMCG Streaming Data Analytics

A streaming analytics project demonstrating real-time FMCG (Fast-Moving Consumer Goods) sales monitoring with demand anomaly detection.

## Architecture

```
CSV Data → Python Producer → Apache Kafka → Python Consumer → Analytics Engine → MongoDB → Dashboard
```

## Quick Start

### Prerequisites
- Python 3.12+ (tested with 3.13.1)
- Docker Desktop (for Kafka and MongoDB)
- Windows 10/11 with PowerShell

### 1. Set up the environment

```powershell
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
copy .env.example .env
```

### 2. Generate sample data

```powershell
python src/data_generator.py
```

### 3. Start Docker services (Kafka + MongoDB)

```powershell
docker compose up -d

# Wait for Kafka to be ready (~30 seconds)
docker compose ps
```

### 4. Run the producer (send 10 messages for demo)

```powershell
python src/producer.py --topics sales --limit 10 --interval 0.5
```

### 5. Run the consumer

```powershell
python src/consumer.py --limit 10
```

### 6. Run the full pipeline (all records)

```powershell
# Producer: send all 1,500 sales records
python src/producer.py --topics sales price calendar --interval 0.1

# Consumer: process all messages
python src/consumer.py
```

### 7. Launch the dashboard

```powershell
streamlit run dashboard/app.py
```

### 8. Run tests

```powershell
pytest tests/ -v
```

## Project Structure

```
FMC_Kafka/
├── data/                    # Generated sample datasets
│   ├── sample_fmcg_sales.csv
│   ├── sample_fmcg_prices.csv
│   └── sample_fmcg_calendar.csv
├── src/                     # Core application code
│   ├── data_generator.py    # Synthetic data generation
│   ├── producer.py          # Kafka producer
│   ├── consumer.py          # Kafka consumer + analytics
│   ├── analytics.py         # Sales metrics + anomaly detection
│   └── database.py          # MongoDB persistence
├── dashboard/
│   └── app.py               # Streamlit dashboard
├── tests/                   # Automated tests
│   ├── test_data.py
│   ├── test_analytics.py
│   └── test_producer.py
├── docs/                    # Documentation
│   ├── architecture.md
│   └── data_dictionary.md
├── report/                  # Academic submission
│   └── FMCG_Streaming_Data_Analytics_Report.docx
├── docker-compose.yml       # Kafka + MongoDB containers
├── requirements.txt         # Python dependencies
├── .env.example             # Environment configuration template
└── README.md                # This file
```

## Key Features

- **Synthetic FMCG Data**: 1,500 sales transactions across 10 Indian FMCG products and 5 stores
- **Demand Anomaly Detection**: Rolling-window statistical method (mean + 2σ threshold)
- **3 Injected Demand Spikes**: Deliberate test cases for anomaly detection verification
- **MongoDB Persistence**: Processed sales, anomaly alerts, and analytics summaries
- **Interactive Dashboard**: Streamlit-based with Plotly charts and real-time alerts

## Data Sources

| Source | File | Records | Type |
|--------|------|---------|------|
| Product Sales | `sample_fmcg_sales.csv` | 1,500 | Synthetic |
| Product Pricing | `sample_fmcg_prices.csv` | ~100–150 | Synthetic |
| Calendar Context | `sample_fmcg_calendar.csv` | 30 | Synthetic |

All data is generated using `src/data_generator.py` with random seed `42` for reproducibility.

## Stopping Services

```powershell
docker compose down
```

To also remove persistent data volumes:
```powershell
docker compose down -v
```
