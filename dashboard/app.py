# dashboard/app.py
import os
import sys
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Ensure Python can find our DB and ML modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import FinOpsDatabase

st.markdown("""
<style>
body {
    background-color: #0b0f19;
    color: #e6edf3;
}

.block-container {
    padding: 2rem 3rem;
}

.metric-card {
    background: linear-gradient(145deg, #111827, #0b1220);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.4);
}

.section-title {
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 10px;
    letter-spacing: 0.5px;
}
</style>
""", unsafe_allow_html=True)
st.set_page_config(page_title="Catalyst Core | FinOps Guardian", page_icon="🛡️", layout="wide")

st.title("🛡️ FinOps Guardian")
st.subheader("AI-Powered Multi-Cloud Cost Anomaly Detection & Forecasting")

# Sidebar Configuration
st.sidebar.header("Configuration")
budget_threshold = st.sidebar.number_input("Monthly Budget ($)", value=50000, step=1000)

@st.cache_data(show_spinner=False, ttl=300)
def load_data():
    """Fetch read-only data from PostgreSQL Neon Database"""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        st.error("DATABASE_URL environment variable is missing. Cannot connect to database.")
        st.stop()
        
    db = FinOpsDatabase(db_url)
    try:
        anomalies_df = db.fetch_anomalies(limit=10000)
        forecasts_df = db.fetch_forecasts(limit=5000)
        return anomalies_df, forecasts_df
    except Exception as e:
        st.error(f"Database fetch failed: {str(e)}")
        st.stop()

with st.spinner("Connecting to PostgreSQL and fetching intelligence..."):
    anomalies_df, forecasts_df = load_data()

if anomalies_df is None or anomalies_df.empty:
    st.warning("No anomalies found in the database. Please run ml/run_pipeline_once.py first.")
    st.stop()

# Ensure datetimes are proper
anomalies_df['date'] = pd.to_datetime(anomalies_df['date'])
if not forecasts_df.empty:
    forecasts_df['date'] = pd.to_datetime(forecasts_df['date'])

# TOP METRICS ROW
col1, col2, col3, col4 = st.columns(4)

# Calculate global metrics
total_anomalies = int(anomalies_df['is_anomaly'].sum())
high_severity_count = len(anomalies_df[(anomalies_df['is_anomaly'] == True) & (anomalies_df['severity_label'] == 'high')])

# Calculate estimated savings roughly by applying proxy
mock_savings = high_severity_count * 2500

col1.metric("Total Anomalies Detected", total_anomalies, "Last 180 days")
col2.metric("High Severity Alerts", high_severity_count, delta_color="inverse")
col3.metric("Estimated Potential Savings", f"${mock_savings:,}")
col4.metric("Active Budget Threshold", f"${budget_threshold:,}")

st.divider()

# SERVICE SELECTOR
services = anomalies_df['service_category'].dropna().unique().tolist()
if not services:
    st.info("No service categories found in anomalies data.")
    st.stop()
    
selected_service = st.selectbox("Select Cloud Service to Analyze", sorted(services))

# Filter DataFrame directly for selected service
service_df = anomalies_df[anomalies_df['service_category'] == selected_service].sort_values('date')
if not forecasts_df.empty:
    service_forecast_df = forecasts_df[forecasts_df['service_category'] == selected_service].sort_values('date')
else:
    service_forecast_df = pd.DataFrame()

# TAB LAYOUT
tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 Anomaly Detection", 
    "🧠 LLM Insights & Root Cause", 
    "📈 Multi-Horizon Forecast", 
    "🚨 Budget Breach Prediction"
])

with tab1:
    st.subheader(f"Cost History & Anomalies — {selected_service}")
    
    fig = go.Figure()
    
    # Historical Line Plot
    fig.add_trace(go.Scatter(
        x=service_df['date'], y=service_df['cost_usd'],
        mode='lines', name='Actual Cloud Spend',
        line=dict(color='#2962ff', width=2)
    ))
    
    # Red Markers for Anomalies
    anomaly_mask = service_df['is_anomaly'] == True
    if anomaly_mask.any():
        anomaly_data = service_df[anomaly_mask]
        fig.add_trace(go.Scatter(
            x=anomaly_data['date'], y=anomaly_data['cost_usd'],
            mode='markers', name='Anomaly Detected',
            marker=dict(color='#ff1744', size=12, symbol='x', line=dict(color='white', width=1))
        ))
    
    fig.update_layout(
        height=400, 
        margin=dict(l=0, r=0, t=30, b=0), 
        paper_bgcolor="rgba(0,0,0,0)", 
        plot_bgcolor="rgba(0,0,0,0)", 
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Automated AI Root Cause Attribution")
    
    actual_anomalies = service_df[service_df['is_anomaly'] == True].sort_values('date', ascending=False)
    
    if len(actual_anomalies) > 0:
        for idx, row in actual_anomalies.head(15).iterrows():
 

            severity_str = str(row.get('severity_label', 'Unknown')).upper()
            date_str = row['date'].strftime('%Y-%m-%d')
            
            with st.expander(f"⚠️ {date_str} | Severity: **{severity_str}** | Cost: **${row['cost_usd']:.2f}**"):
                st.markdown(f"**Insight:** {row.get('llm_insight', 'N/A')}")
                st.markdown(f"**Root Cause:** {row.get('root_cause', 'N/A')}")
                st.markdown(f"**Recommended Action:** {row.get('recommended_action', 'N/A')}")
                st.markdown(f"**Estimated Savings:** {row.get('estimated_savings', 'N/A')}")
    else:
        st.success("No anomalies detected for this service. Cost pattern is normal.")

with tab3:
    st.subheader("Spend Forecast")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=service_df['date'], y=service_df['cost_usd'], name='Historical Spend', line=dict(color='#2962ff')))
    
    if not service_forecast_df.empty:
        fig.add_trace(go.Scatter(
            x=service_forecast_df['date'], 
            y=service_forecast_df['forecast_50'], 
            name='Predicted Trajectory', 
            line=dict(color='#ff9100', dash='dash')
        ))
        
        # Determine bounds fields handling potential empty data
        y_upper = service_forecast_df['forecast_90'] if 'forecast_90' in service_forecast_df.columns else service_forecast_df['forecast_50'] * 1.1
        y_lower = service_forecast_df['forecast_10'] if 'forecast_10' in service_forecast_df.columns else service_forecast_df['forecast_50'] * 0.9

        fig.add_trace(go.Scatter(
            x=service_forecast_df['date'].tolist() + service_forecast_df['date'].tolist()[::-1],
            y=y_upper.tolist() + y_lower.tolist()[::-1],
            fill='toself', fillcolor='rgba(255, 145, 0, 0.1)', line=dict(color='rgba(255,255,255,0)'),
            name='80% Confidence Interval'
        ))
    else:
        st.info("No forecast data available for this service in the database.")
        
    fig.update_layout(
        height=400, 
        paper_bgcolor="rgba(0,0,0,0)", 
        plot_bgcolor="rgba(0,0,0,0)", 
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.subheader("Predictive Budget Intelligence")
    
    if not service_forecast_df.empty and len(service_forecast_df) > 0:
        # Aggregate 30-day view
        thirty_day_forecast = service_forecast_df.head(30)
        max_forecast = thirty_day_forecast['forecast_50'].sum()
        
        is_breach = max_forecast > budget_threshold
        status = "HIGH RISK" if is_breach else "LOW RISK"
        color = "🔴" if is_breach else "🟢"
        
        st.markdown(f"### {color} Status: {status}")
        st.caption("Based on 30-day aggregated median forecast vs active budget.")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("30-Day Forecast Sum", f"${max_forecast:,.2f}")
        c2.metric("Budget Remaining", f"${(budget_threshold - max_forecast):,.2f}")
        
    else:
        st.write("Insufficient forecast data to compute budget risk.")