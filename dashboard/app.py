"""
FMCG Streaming Analytics Dashboard
====================================
A Streamlit-based dashboard that displays processed FMCG sales data,
analytics summaries, and demand anomaly alerts from MongoDB.

Run with: streamlit run dashboard/app.py
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from database import FMCGDatabase

# --- Page Configuration ---
st.set_page_config(
    page_title="FMCG Streaming Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS ---
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
    }
    .alert-critical { border-left: 4px solid #ff4444; padding-left: 10px; }
    .alert-high { border-left: 4px solid #ff8800; padding-left: 10px; }
    .alert-medium { border-left: 4px solid #ffcc00; padding-left: 10px; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_db_connection():
    """Create and cache database connection."""
    db = FMCGDatabase()
    db.connect()
    return db


def render_header():
    """Render the dashboard header."""
    st.title("📊 FMCG Streaming Analytics Dashboard")
    st.caption("Real-time sales monitoring and demand anomaly detection")
    st.divider()


def render_kpi_cards(summary):
    """Render top-level KPI metric cards."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📦 Total Units Sold",
            value=f"{summary.get('total_units_sold', 0):,}",
        )
    
    with col2:
        st.metric(
            label="💰 Total Revenue",
            value=f"₹{summary.get('total_revenue', 0):,.2f}",
        )
    
    with col3:
        st.metric(
            label="🏪 Stores Tracked",
            value=summary.get("stores_tracked", 0),
        )
    
    with col4:
        st.metric(
            label="🚨 Anomalies Detected",
            value=summary.get("anomalies_detected", 0),
        )


def render_product_charts(summary):
    """Render product-level sales charts."""
    st.subheader("📦 Sales by Product")
    
    col1, col2 = st.columns(2)
    
    with col1:
        product_units = summary.get("product_breakdown", {})
        if product_units:
            df = pd.DataFrame(
                list(product_units.items()),
                columns=["Product", "Units Sold"],
            ).sort_values("Units Sold", ascending=True)
            
            fig = px.bar(
                df, x="Units Sold", y="Product", orientation="h",
                title="Units Sold by Product",
                color="Units Sold",
                color_continuous_scale="Viridis",
            )
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        product_revenue = summary.get("product_revenue", {})
        if product_revenue:
            df = pd.DataFrame(
                list(product_revenue.items()),
                columns=["Product", "Revenue"],
            ).sort_values("Revenue", ascending=False)
            
            fig = px.pie(
                df, values="Revenue", names="Product",
                title="Revenue Distribution by Product",
                hole=0.4,
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)


def render_store_charts(summary):
    """Render store-level sales charts."""
    st.subheader("🏪 Sales by Store")
    
    col1, col2 = st.columns(2)
    
    with col1:
        store_units = summary.get("store_breakdown", {})
        if store_units:
            df = pd.DataFrame(
                list(store_units.items()),
                columns=["Store", "Units Sold"],
            )
            fig = px.bar(
                df, x="Store", y="Units Sold",
                title="Units Sold by Store",
                color="Units Sold",
                color_continuous_scale="Tealgrn",
            )
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        store_revenue = summary.get("store_revenue", {})
        if store_revenue:
            df = pd.DataFrame(
                list(store_revenue.items()),
                columns=["Store", "Revenue (₹)"],
            )
            fig = px.bar(
                df, x="Store", y="Revenue (₹)",
                title="Revenue by Store",
                color="Revenue (₹)",
                color_continuous_scale="Sunset",
            )
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)


def render_category_chart(summary):
    """Render category-level breakdown."""
    st.subheader("📂 Sales by Category")
    
    category_units = summary.get("category_breakdown", {})
    category_revenue = summary.get("category_revenue", {})
    
    if category_units:
        df = pd.DataFrame({
            "Category": list(category_units.keys()),
            "Units Sold": list(category_units.values()),
            "Revenue (₹)": [category_revenue.get(c, 0) for c in category_units.keys()],
        })
        
        fig = px.bar(
            df, x="Category", y=["Units Sold", "Revenue (₹)"],
            title="Category Performance",
            barmode="group",
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)


def render_anomaly_alerts(db):
    """Render demand anomaly alerts."""
    st.subheader("🚨 Demand Anomaly Alerts")
    
    alerts = db.get_anomaly_alerts(limit=20)
    
    if not alerts:
        st.info("No anomalies detected yet. Run the consumer to process sales data.")
        return
    
    for alert in alerts:
        severity = alert.get("severity", "MEDIUM")
        icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(
            severity, "⚪"
        )
        
        with st.expander(
            f"{icon} {alert.get('alert_id', 'N/A')} — "
            f"{alert.get('product_name', 'Unknown')} @ {alert.get('store_name', 'Unknown')} "
            f"[{severity}]",
            expanded=(severity in ("CRITICAL", "HIGH")),
        ):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Units Sold", alert.get("units_sold", "N/A"))
            with col2:
                st.metric("Baseline Mean", f"{alert.get('rolling_mean', 0):.1f}")
            with col3:
                st.metric("Spike Ratio", f"{alert.get('spike_ratio', 0):.1f}σ")
            
            st.caption(
                f"Detected: {alert.get('detected_at', 'N/A')} | "
                f"Event: {alert.get('event_id', 'N/A')} | "
                f"Threshold: {alert.get('threshold_value', 'N/A')}"
            )


def render_recent_sales(db):
    """Render recent sales table."""
    st.subheader("📋 Recent Sales Records")
    
    sales = db.get_recent_sales(limit=30)
    
    if not sales:
        st.info("No processed sales data available yet.")
        return
    
    df = pd.DataFrame(sales)
    display_cols = [
        "event_id", "timestamp", "product_name", "store_name",
        "units_sold", "selling_price", "revenue", "is_anomaly",
    ]
    available_cols = [c for c in display_cols if c in df.columns]
    
    if available_cols:
        st.dataframe(
            df[available_cols],
            use_container_width=True,
            height=400,
        )


class OfflineMockDB:
    """Mock database adapter for offline demonstration mode."""
    def __init__(self, alerts, sales):
        self._alerts = alerts
        self._sales = sales
        self.connected = True

    def get_anomaly_alerts(self, limit=20):
        return list(reversed(self._alerts))[:limit]

    def get_recent_sales(self, limit=30):
        return list(reversed(self._sales))[:limit]

    def get_stats(self):
        return {
            "database": "Offline Analytics (Direct CSV Stream)",
            "processed_sales_count": len(self._sales),
            "anomaly_alerts_count": len(self._alerts),
            "summary_snapshots_count": 1,
        }


@st.cache_data
def get_offline_analytics_data():
    """Process local CSV through analytics engine when MongoDB is not running."""
    import csv
    from analytics import FMCGAnalytics

    sales_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "sample_fmcg_sales.csv"
    )
    if not os.path.exists(sales_path):
        return None, [], []

    analytics = FMCGAnalytics()
    processed_records = []
    alerts = []

    with open(sales_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            res = analytics.process_sale(r)
            processed_records.append(res)
            if res.get("is_anomaly") and res.get("anomaly_details", {}).get("alert"):
                alerts.append(res["anomaly_details"]["alert"])

    summary = analytics.get_summary()
    return summary, alerts, processed_records


def main():
    """Main dashboard entry point."""
    render_header()
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        auto_refresh = st.checkbox("Auto-refresh (30s)", value=False)
        if auto_refresh:
            import time
            st.caption("Dashboard will refresh every 30 seconds")
        
        st.divider()
        st.header("ℹ️ About")
        st.write(
            "This dashboard displays real-time FMCG sales analytics "
            "processed from Kafka streaming events."
        )
        st.write(
            "**Anomaly Detection:** Uses rolling-window statistical method "
            "(mean + 2σ threshold) to flag unexpected demand spikes."
        )
    
    # Connect to database
    db = get_db_connection()
    summary = None
    
    if not db.connected:
        st.warning(
            "ℹ️ **MongoDB is not connected** (Docker not running). "
            "Dashboard is running in **Offline Analytics Mode** using the generated dataset."
        )
        summary, alerts, sales = get_offline_analytics_data()
        if not summary:
            st.error(
                "Could not find sample data in `data/`. Please run: `python src/data_generator.py`"
            )
            return
        db = OfflineMockDB(alerts, sales)
    else:
        summary = db.get_latest_summary()
        if not summary:
            st.warning(
                "No analytics summary found in MongoDB. "
                "Run the consumer to process sales data first."
            )
            use_offline = st.button("Load sample data from CSV instead")
            if use_offline:
                summary, alerts, sales = get_offline_analytics_data()
                db = OfflineMockDB(alerts, sales)
            else:
                st.code(
                    "# Step 1: Start services\n"
                    "docker compose up -d\n\n"
                    "# Step 2: Run producer\n"
                    "python src/producer.py --topics sales --limit 50\n\n"
                    "# Step 3: Run consumer\n"
                    "python src/consumer.py --limit 50\n\n"
                    "# Step 4: Refresh this dashboard",
                    language="bash",
                )
                return
    
    # Render dashboard sections
    render_kpi_cards(summary)
    st.divider()
    
    render_product_charts(summary)
    st.divider()
    
    render_store_charts(summary)
    st.divider()
    
    render_category_chart(summary)
    st.divider()
    
    render_anomaly_alerts(db)
    st.divider()
    
    render_recent_sales(db)
    
    # Footer
    st.divider()
    stats = db.get_stats()
    st.caption(
        f"Database: {stats.get('database', 'N/A')} | "
        f"Sales: {stats.get('processed_sales_count', 0)} | "
        f"Alerts: {stats.get('anomaly_alerts_count', 0)} | "
        f"Snapshots: {stats.get('summary_snapshots_count', 0)} | "
        f"Last refreshed: {datetime.now().strftime('%H:%M:%S')}"
    )
    
    # Auto-refresh
    if auto_refresh:
        import time
        time.sleep(30)
        st.rerun()


if __name__ == "__main__":
    main()
