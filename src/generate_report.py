"""
FMCG Academic Report Generator
================================
Generates the Word document (.docx) submission report for the
FMCG Streaming Data Analytics project.

Run: python src/generate_report.py
Output: report/FMCG_Streaming_Data_Analytics_Report.docx
"""

import os
import sys
import csv
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def get_project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def count_csv_records(filepath):
    """Count records in a CSV file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)  # skip header
            return sum(1 for _ in reader)
    except Exception:
        return "N/A"


def generate_report():
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT
    
    root = get_project_root()
    doc = Document()
    
    # --- Styles ---
    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(11)
    
    # ======================= TITLE PAGE =======================
    for _ in range(6):
        doc.add_paragraph("")
    
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("FMCG Streaming Data Analytics")
    run.bold = True
    run.font.size = Pt(28)
    run.font.color.rgb = RGBColor(0, 51, 102)
    
    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run("Real-Time Sales Monitoring & Demand Anomaly Detection")
    run.font.size = Pt(16)
    run.font.color.rgb = RGBColor(80, 80, 80)
    
    doc.add_paragraph("")
    
    info = doc.add_paragraph()
    info.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = info.add_run(
        "BTech Assignment\n"
        "Python · Apache Kafka · MongoDB · Streamlit\n\n"
        f"Date: {datetime.now().strftime('%B %d, %Y')}"
    )
    run.font.size = Pt(12)
    run.font.color.rgb = RGBColor(100, 100, 100)
    
    doc.add_page_break()
    
    # ======================= TABLE OF CONTENTS =======================
    doc.add_heading("Table of Contents", level=1)
    toc_items = [
        "1. Project Objective",
        "2. Industry Justification",
        "3. Data Sources",
        "4. Data Dictionary",
        "5. Pipeline Architecture",
        "6. Kafka Topics and Consumer Design",
        "7. Implementation Details",
        "8. Producer Code Explanation",
        "9. Sample Data Generation",
        "10. Real-Time Business Decision",
        "11. Testing and Verification",
        "12. Terminal Output Evidence",
        "13. Limitations and Conclusion",
        "14. References",
    ]
    for item in toc_items:
        p = doc.add_paragraph(item)
        p.paragraph_format.space_after = Pt(2)
    
    doc.add_page_break()
    
    # ======================= 1. PROJECT OBJECTIVE =======================
    doc.add_heading("1. Project Objective", level=1)
    doc.add_paragraph(
        "This project implements a reproducible FMCG (Fast-Moving Consumer Goods) "
        "streaming analytics system that demonstrates how incoming product sales data "
        "can support timely business decisions. The primary business use case is detecting "
        "unexpected demand increases and helping a store or regional manager prioritize "
        "replenishment or inventory allocation before stock shortages occur."
    )
    doc.add_paragraph(
        "The system generates synthetic but realistic FMCG sales data, publishes it as "
        "a stream of events through Apache Kafka, processes the events in real time using "
        "a Python consumer, calculates sales metrics, detects demand anomalies, persists "
        "results to MongoDB, and displays insights through a Streamlit dashboard."
    )
    
    # ======================= 2. INDUSTRY JUSTIFICATION =======================
    doc.add_heading("2. Industry Justification", level=1)
    doc.add_paragraph(
        "The FMCG industry is characterized by high product volumes, thin margins, and "
        "perishable inventory. A delayed response to a sudden demand spike — whether "
        "caused by a viral social-media trend, a regional festival, or a competitor's "
        "stock-out — can result in lost sales and customer dissatisfaction. Traditional "
        "batch-based reporting (daily or weekly) leaves managers reacting hours or days "
        "after the event has started."
    )
    doc.add_paragraph(
        "A streaming analytics pipeline closes this gap by processing each transaction "
        "as it occurs, computing rolling baselines, and immediately flagging deviations. "
        "This enables operational teams to make informed replenishment decisions during "
        "the demand surge, rather than after it has subsided."
    )
    
    # ======================= 3. DATA SOURCES =======================
    doc.add_heading("3. Data Sources", level=1)
    doc.add_paragraph(
        "Three logical data sources are used in this project. All data is synthetic, "
        "generated using Python with a fixed random seed (42) for reproducibility. "
        "The M5 Forecasting–Accuracy dataset from Kaggle (based on Walmart sales) was "
        "considered as a historical reference but was not used because it requires "
        "Kaggle authentication and is licensed for competition use. Instead, realistic "
        "synthetic data was generated to avoid misrepresenting data provenance."
    )
    
    # Data sources table
    table = doc.add_table(rows=4, cols=6)
    table.style = 'Light Grid Accent 1'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    headers = ["Source", "Data Type", "Key Fields", "Volume", "Frequency", "Nature"]
    for i, h in enumerate(headers):
        table.rows[0].cells[i].text = h
        for paragraph in table.rows[0].cells[i].paragraphs:
            for run in paragraph.runs:
                run.bold = True
    
    sales_count = count_csv_records(os.path.join(root, "data", "sample_fmcg_sales.csv"))
    price_count = count_csv_records(os.path.join(root, "data", "sample_fmcg_prices.csv"))
    cal_count = count_csv_records(os.path.join(root, "data", "sample_fmcg_calendar.csv"))
    
    sources = [
        ["Product Sales", "Transactional", "event_id, timestamp, product_id, store_id, units_sold, selling_price",
         f"{sales_count} records", "Per-transaction", "Synthetic"],
        ["Product Pricing", "Reference", "price_id, product_id, store_id, selling_price, effective_date",
         f"{price_count} records", "On price change", "Synthetic"],
        ["Calendar Context", "Dimensional", "date, day_of_week, is_weekend, is_promotion, event_name",
         f"{cal_count} records", "Daily", "Synthetic"],
    ]
    for row_idx, source in enumerate(sources, 1):
        for col_idx, val in enumerate(source):
            table.rows[row_idx].cells[col_idx].text = val
    
    doc.add_paragraph("")
    doc.add_paragraph(
        "Entry mechanism: The Python producer (producer.py) reads each CSV file "
        "and publishes records as JSON messages to the corresponding Kafka topic."
    )
    
    # ======================= 4. DATA DICTIONARY =======================
    doc.add_heading("4. Data Dictionary", level=1)
    
    doc.add_heading("4.1 Sales Transactions (sample_fmcg_sales.csv)", level=2)
    sales_fields = [
        ("event_id", "String", "Unique transaction identifier (EVT-000001)"),
        ("timestamp", "DateTime", "Sale occurrence time (YYYY-MM-DD HH:MM:SS)"),
        ("product_id", "String", "Product identifier (P001–P010)"),
        ("product_name", "String", "Human-readable product name"),
        ("category", "String", "Product category (Snacks, Beverages, etc.)"),
        ("store_id", "String", "Store identifier (S01–S05)"),
        ("store_name", "String", "Store location name"),
        ("units_sold", "Integer", "Number of units sold (≥1)"),
        ("selling_price", "Float", "Price per unit in INR"),
    ]
    
    t = doc.add_table(rows=len(sales_fields)+1, cols=3)
    t.style = 'Light Grid Accent 1'
    for i, h in enumerate(["Field", "Type", "Description"]):
        t.rows[0].cells[i].text = h
        for run in t.rows[0].cells[i].paragraphs[0].runs:
            run.bold = True
    for row_idx, (field, dtype, desc) in enumerate(sales_fields, 1):
        t.rows[row_idx].cells[0].text = field
        t.rows[row_idx].cells[1].text = dtype
        t.rows[row_idx].cells[2].text = desc
    
    doc.add_paragraph(f"\nTotal records: {sales_count}. All event IDs are unique. "
                      "Units sold are always ≥1. Prices are positive.")
    
    doc.add_heading("4.2 Product Pricing (sample_fmcg_prices.csv)", level=2)
    doc.add_paragraph(
        f"Contains {price_count} price records. Fields: price_id, product_id, "
        "product_name, store_id, selling_price, effective_date, change_reason. "
        "Each product-store pair has an initial price and 1–2 subsequent changes."
    )
    
    doc.add_heading("4.3 Calendar Context (sample_fmcg_calendar.csv)", level=2)
    doc.add_paragraph(
        f"Contains {cal_count} records (one per day). Fields: date, day_of_week, "
        "is_weekend, is_promotion, event_name, month, week_number. "
        "Three promotional periods are defined across the month."
    )
    
    # ======================= 5. PIPELINE ARCHITECTURE =======================
    doc.add_heading("5. Pipeline Architecture", level=1)
    doc.add_paragraph(
        "The system follows a standard streaming ETL pattern:"
    )
    doc.add_paragraph(
        "CSV Data → Python Producer → Apache Kafka → Python Consumer → "
        "Analytics Engine → MongoDB → Streamlit Dashboard",
        style='Intense Quote'
    )
    
    components = [
        ("Apache Kafka 3.8 (Docker)", 
         "Runs in KRaft mode (no Zookeeper dependency). Single-node broker at localhost:9092. "
         "Three topics: fmcg-sales, fmcg-price, fmcg-calendar."),
        ("Python Producer (producer.py)", 
         "Reads CSV files, converts rows to JSON, adds ingestion timestamp, publishes to Kafka "
         "with acks=all, and logs verified acknowledgements with partition and offset."),
        ("Python Consumer (consumer.py)", 
         "Subscribes to fmcg-sales, validates each message, passes valid records to the "
         "analytics engine, saves results to MongoDB, and logs processing output."),
        ("Analytics Engine (analytics.py)", 
         "Calculates revenue (units × price), maintains rolling per-product/store aggregates, "
         "and detects demand anomalies using mean + 2σ threshold over a 20-record rolling window."),
        ("MongoDB 7.0 (Docker)", 
         "Persists processed sales, anomaly alerts, and periodic analytics summaries. "
         "Uses upsert operations on event_id/alert_id to prevent duplicates."),
        ("Streamlit Dashboard (app.py)", 
         "Displays KPI cards, product/store/category charts (Plotly), anomaly alert cards, "
         "and a recent sales data table. Reads from MongoDB."),
    ]
    
    for name, desc in components:
        doc.add_heading(name, level=3)
        doc.add_paragraph(desc)
    
    # ======================= 6. KAFKA TOPICS =======================
    doc.add_heading("6. Kafka Topics and Consumer Design", level=1)
    
    doc.add_heading("6.1 Topics", level=2)
    t = doc.add_table(rows=4, cols=4)
    t.style = 'Light Grid Accent 1'
    for i, h in enumerate(["Topic", "Message Key", "Content", "Volume"]):
        t.rows[0].cells[i].text = h
        for run in t.rows[0].cells[i].paragraphs[0].runs:
            run.bold = True
    
    topics = [
        ("fmcg-sales", "event_id", "Sales transaction JSON", f"{sales_count} messages"),
        ("fmcg-price", "product_id", "Price change JSON", f"{price_count} messages"),
        ("fmcg-calendar", "date", "Calendar context JSON", f"{cal_count} messages"),
    ]
    for row_idx, (topic, key, content, vol) in enumerate(topics, 1):
        t.rows[row_idx].cells[0].text = topic
        t.rows[row_idx].cells[1].text = key
        t.rows[row_idx].cells[2].text = content
        t.rows[row_idx].cells[3].text = vol
    
    doc.add_heading("6.2 Consumer Design", level=2)
    doc.add_paragraph(
        "The consumer uses the consumer group 'fmcg-analytics-group' with "
        "auto_offset_reset='earliest' to process all messages from the beginning "
        "on first run. It validates each message for required fields (event_id, "
        "product_id, store_id, units_sold, selling_price) before processing. "
        "Invalid messages are logged and skipped without crashing the service."
    )
    
    # ======================= 7. IMPLEMENTATION DETAILS =======================
    doc.add_heading("7. Implementation Details", level=1)
    
    doc.add_heading("7.1 Anomaly Detection Method", level=2)
    doc.add_paragraph(
        "The analytics engine detects demand spikes using a rolling-window statistical "
        "approach. For each product-store combination, it maintains a rolling window of "
        "the last 20 sales records. When a new sale arrives, it compares the units_sold "
        "against the rolling baseline:"
    )
    doc.add_paragraph(
        "    threshold_value = rolling_mean + (2.0 × rolling_std_dev)", 
        style='Intense Quote'
    )
    doc.add_paragraph(
        "If units_sold exceeds this threshold, the sale is flagged as a demand anomaly. "
        "The system requires at least 5 data points before making anomaly judgments, "
        "avoiding false positives during the warm-up period."
    )
    doc.add_paragraph(
        "Limitations: This is a simple statistical rule, not a predictive ML model. "
        "It may miss gradual trends, seasonal patterns, or very slow shifts in demand. "
        "False positives are possible during natural high-variance periods. It serves "
        "as a practical demonstration of streaming anomaly detection suitable for an "
        "academic project."
    )
    
    doc.add_heading("7.2 Technology Stack", level=2)
    t = doc.add_table(rows=8, cols=3)
    t.style = 'Light Grid Accent 1'
    for i, h in enumerate(["Technology", "Version", "Purpose"]):
        t.rows[0].cells[i].text = h
        for run in t.rows[0].cells[i].paragraphs[0].runs:
            run.bold = True
    
    stack = [
        ("Python", "3.13.1", "Application language"),
        ("kafka-python-ng", "2.2.3", "Kafka client library (maintained fork)"),
        ("Apache Kafka", "3.8.0", "Message streaming (KRaft mode, Docker)"),
        ("MongoDB", "7.0", "Data persistence (Docker)"),
        ("Streamlit", "1.39.0", "Dashboard framework"),
        ("Plotly", "5.24.1", "Interactive charts"),
        ("Docker Compose", "v2", "Container orchestration"),
    ]
    for row_idx, (tech, ver, purpose) in enumerate(stack, 1):
        t.rows[row_idx].cells[0].text = tech
        t.rows[row_idx].cells[1].text = ver
        t.rows[row_idx].cells[2].text = purpose
    
    # ======================= 8. PRODUCER CODE EXPLANATION =======================
    doc.add_heading("8. Producer Code Explanation", level=1)
    doc.add_paragraph("The producer (src/producer.py) performs the following steps:")
    
    steps = [
        "Reads sample_fmcg_sales.csv (and optionally prices/calendar CSVs) from the data/ directory using Python's csv.DictReader.",
        "Validates that the CSV file exists and contains data. Raises clear errors if the file is missing or empty.",
        "Converts each CSV row into a JSON-serializable Python dictionary.",
        "Adds an 'ingestion_timestamp' field recording when the message is being published (distinct from the original event timestamp).",
        "Creates a KafkaProducer configured with JSON value serializer, acks='all' for durability, and retry logic.",
        "Publishes each record to the appropriate Kafka topic (fmcg-sales, fmcg-price, or fmcg-calendar) using the event_id as the message key.",
        "Blocks on each send using future.get(timeout=10) to wait for broker acknowledgement before logging success.",
        "Logs verified acknowledgement details: message number, topic, partition, offset, and event ID.",
        "Supports a configurable send interval (default 0.3 seconds) to control streaming pace.",
        "Supports a --limit flag to send a limited number of records for demonstration (e.g., --limit 10).",
        "Handles connection errors and keyboard interrupts gracefully.",
        "Flushes and closes the producer on completion to ensure all buffered messages are delivered.",
    ]
    for step in steps:
        doc.add_paragraph(step, style='List Number')
    
    # ======================= 9. SAMPLE DATA GENERATION =======================
    doc.add_heading("9. Sample Data Generation Method", level=1)
    doc.add_paragraph(
        "The data generator (src/data_generator.py) creates synthetic FMCG data with "
        "the following characteristics:"
    )
    doc.add_paragraph(
        f"• 10 Indian FMCG products (Lays, Coca-Cola, Maggi, Parle-G, Amul, etc.)\n"
        f"• 5 store locations (Mumbai, Delhi, Bangalore, Hyderabad, Chennai)\n"
        f"• 30 days of data (September 2026)\n"
        f"• Random seed: 42 (reproducible across runs)\n"
        f"• Natural daily sales variation: ±30% around base units\n"
        f"• Weekend boost: +20% on Saturdays and Sundays\n"
        f"• 3 deliberate demand spikes injected for anomaly detection testing:\n"
        f"  - Maggi 2-Min Noodles at Mumbai Central on Day 10 (4× normal)\n"
        f"  - Coca-Cola 500ml at Bangalore Koramangala on Day 18 (3.5× normal)\n"
        f"  - Parle-G Biscuits at Delhi NCR Hub on Day 25 (5× normal)\n"
        f"• 3 promotional periods with 9 total promotion days\n"
        f"• Price variation: ±2% around base price for sales, with 1–2 explicit price changes per product-store"
    )
    doc.add_paragraph(
        "These spikes are deliberate test cases to verify that the anomaly detection "
        "system correctly identifies unusual demand. They are NOT discoveries from real "
        "commercial data."
    )
    
    # ======================= 10. REAL-TIME BUSINESS DECISION =======================
    doc.add_heading("10. Real-Time Business Decision", level=1)
    doc.add_paragraph(
        "Business Decision: Prioritize Inventory Replenishment During a Demand Spike",
        style='Intense Quote'
    )
    doc.add_paragraph(
        "When the streaming analytics pipeline detects that a product such as Maggi "
        "2-Min Noodles is selling at four times its normal rate at the Mumbai Central "
        "store, the system immediately generates an anomaly alert with the product name, "
        "store location, current sales volume, baseline comparison, and severity level. "
        "A regional supply-chain manager monitoring the dashboard or receiving these "
        "alerts can prioritize an emergency replenishment shipment to that specific store "
        "within hours rather than waiting for the next-day batch report to reveal the "
        "shortage. This is particularly valuable during festival periods or unexpected "
        "events where demand can shift rapidly. Without a streaming system, the manager "
        "would only discover the demand spike in the next morning's report — by which time "
        "the shelf may already be empty and customers have gone elsewhere. The streaming "
        "pipeline cannot guarantee that replacement stock is available in the warehouse "
        "or that logistics can deliver immediately, but it ensures the decision-maker has "
        "the information to act at the earliest possible moment. Even a partial response — "
        "such as redirecting stock from a nearby low-demand store — is enabled by the "
        "real-time visibility that a daily batch system cannot provide."
    )
    
    # ======================= 11. TESTING AND VERIFICATION =======================
    doc.add_heading("11. Testing and Verification", level=1)
    doc.add_paragraph(
        "The project includes automated tests in the tests/ directory, run with pytest:"
    )
    
    test_categories = [
        ("Data Validation (test_data.py)", 
         "Verifies CSV file existence, schema correctness, unique event IDs, positive values, "
         "valid timestamps, multiple products/stores, and promotional data."),
        ("Analytics Engine (test_analytics.py)", 
         "Tests revenue calculation, running totals, product/store breakdowns, anomaly detection "
         "with sufficient/insufficient data, severity classification, product independence, "
         "and edge cases (zero units, invalid types, missing fields)."),
        ("Producer (test_producer.py)", 
         "Tests CSV reading, JSON serialization, configuration values, send with limits, "
         "ingestion timestamp injection, and failure handling using mocked Kafka producers."),
    ]
    for name, desc in test_categories:
        doc.add_heading(name, level=3)
        doc.add_paragraph(desc)
    
    doc.add_paragraph(
        "\nNote: Unit tests use mocked Kafka producers. A real integration test against "
        "the Docker broker requires Kafka to be running and is verified manually by running "
        "the producer and consumer against the live broker."
    )
    
    # ======================= 12. TERMINAL OUTPUT =======================
    doc.add_heading("12. Terminal Output Evidence", level=1)
    doc.add_paragraph(
        "[PLACEHOLDER: Insert actual terminal screenshot here showing at least 10 "
        "successfully sent messages with verified Kafka acknowledgements including "
        "topic, partition, and offset details.]\n\n"
        "The terminal output log is saved at: artifacts/producer_output.log\n\n"
        "To reproduce this output, run:\n"
        "  .\\venv\\Scripts\\Activate.ps1\n"
        "  python src/producer.py --topics sales --limit 15 --interval 0.3"
    )
    
    # ======================= 13. LIMITATIONS AND CONCLUSION =======================
    doc.add_heading("13. Limitations and Conclusion", level=1)
    
    doc.add_heading("Limitations", level=2)
    limitations = [
        "The anomaly detection uses a simple statistical threshold (mean + 2σ). It is not a machine learning model and cannot learn seasonal patterns or account for external factors.",
        "All data is synthetic. While realistic in structure, it does not represent actual retail sales and cannot be used for genuine business analysis.",
        "The system runs locally with a single Kafka broker. A production deployment would require a multi-broker cluster with proper replication.",
        "The dashboard reads from MongoDB snapshots and does not stream data in true real-time. It relies on periodic page refreshes.",
        "Price and calendar data are published to separate Kafka topics but are not yet joined with sales data during consumer processing. This is an area for future enhancement.",
    ]
    for lim in limitations:
        doc.add_paragraph(lim, style='List Bullet')
    
    doc.add_heading("Conclusion", level=2)
    doc.add_paragraph(
        "This project demonstrates a complete streaming analytics pipeline for FMCG sales "
        "data using industry-standard tools (Apache Kafka, MongoDB, Python). It shows how "
        "real-time event processing can detect demand anomalies and provide actionable "
        "intelligence to operations managers significantly faster than traditional batch "
        "reporting. While the current implementation uses synthetic data and simple "
        "analytics, the architecture is extensible to more sophisticated models and real "
        "data sources."
    )
    
    # ======================= 14. REFERENCES =======================
    doc.add_heading("14. References", level=1)
    references = [
        "Apache Kafka Documentation — https://kafka.apache.org/documentation/",
        "kafka-python-ng (Python Kafka client) — https://pypi.org/project/kafka-python-ng/",
        "MongoDB Documentation — https://www.mongodb.com/docs/",
        "PyMongo Documentation — https://pymongo.readthedocs.io/",
        "Streamlit Documentation — https://docs.streamlit.io/",
        "Plotly Python Documentation — https://plotly.com/python/",
        "M5 Forecasting Competition (reference only) — https://www.kaggle.com/competitions/m5-forecasting-accuracy",
        "Docker Compose Documentation — https://docs.docker.com/compose/",
    ]
    for ref in references:
        doc.add_paragraph(ref, style='List Number')
    
    # Save document
    output_path = os.path.join(root, "report", "FMCG_Streaming_Data_Analytics_Report.docx")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)
    print(f"  ✓ Report saved: {output_path}")
    return output_path


if __name__ == "__main__":
    print("Generating FMCG Streaming Analytics Report...")
    try:
        path = generate_report()
        print(f"  Report generated successfully at: {path}")
    except ImportError as e:
        print(f"  ✗ Missing dependency: {e}")
        print("  Run: pip install python-docx")
        sys.exit(1)
