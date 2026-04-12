# dashboard/app.py
# FinOps Guardian — Production Dashboard v2.0
# Team Catalyst Core | Tic Tech Toe '26

import os
import sys
import pandas as pd 
import numpy as np
import plotly.graph_objects as go
import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.database import FinOpsDatabase

# ─── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FinOps Guardian",
    page_icon="🛡",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ─── GLOBAL CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500&family=Inter:wght@400;500&family=DM+Mono:wght@400;500&display=swap');

/* ── Reset & base ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stAppViewContainer"],
[data-testid="stApp"] {
    background: #05060d !important;
    color: #d4dae8 !important;
    font-family: 'DM Sans', sans-serif !important;
}

[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(ellipse 80% 50% at 15% 10%, rgba(14,30,80,0.45) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 85% 85%, rgba(60,10,90,0.30) 0%, transparent 60%),
        #05060d !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer,
[data-testid="stToolbar"],
[data-testid="stDecoration"] { display: none !important; }

/* ── Sidebar ── */
/* ── SIDEBAR FIXED + VISIBLE ── */

/* ── Hide ONLY header (fix overlay issue) ── */
header[data-testid="stHeader"] {
    display: none !important;
}

/* Optional: remove top padding gap created by header */
[data-testid="stAppViewContainer"] {
    padding-top: 0rem !important;
}
/* ── Block container ── */
.block-container {
    padding: 2.5rem 3rem 3rem !important;
    max-width: 1600px !important;
}

/* ── Typography ── */
.fg-hero {
    font-family: 'Montserrat', sans-serif;
    font-size: clamp(28px, 3.5vw, 46px);
    font-weight: 300;
    letter-spacing: -1.5px;
    line-height: 1.1;
    color: #eef2ff; 
    background: linear-gradient(120deg, #e8eeff 0%, #7ba4ff 50%, #b06fff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.3rem;
}
.fg-sub {
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    color: #eef2ff;
    letter-spacing: 0.3px;
    margin-bottom: 0.3rem;
    font-weight: 300; /* THIN */
}
.fg-section {
    font-family: 'Montserrat', sans-serif;
    font-size: 18px;
    font-weight: 400;
    color: #e2e8ff;
    letter-spacing: -0.2px;
    margin-bottom: 1rem;
}
.fg-mono {
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    color: #6b7aa6;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

/* ── KPI cards ── */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 2rem;
}
.kpi-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 16px;
    padding: 22px 24px 20px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.3s, transform 0.25s;
    backdrop-filter: blur(12px);
    box-shadow:
        0 4px 20px rgba(0,0,0,0.6),
        inset 0 1px 0 rgba(255,255,255,0.05);
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    border-radius: 16px 16px 0 0;
}
.kpi-card.kpi-blue::before  { background: linear-gradient(90deg, #3a6bff, #6a9fff); }
.kpi-card.kpi-red::before   { background: linear-gradient(90deg, #ff3b5c, #ff7a6e); }
.kpi-card.kpi-amber::before { background: linear-gradient(90deg, #f59e0b, #fcd34d); }
.kpi-card.kpi-green::before { background: linear-gradient(90deg, #10b981, #6ee7b7); }
.kpi-card:hover {
    border-color: rgba(120,140,255,0.25);
    transform: translateY(-3px) scale(1.01);

    box-shadow:
        0 6px 24px rgba(0,0,0,0.6),              
        0 0 12px rgba(90,120,255,0.18),         
        0 0 24px rgba(90,120,255,0.10),         
        inset 0 1px 0 rgba(255,255,255,0.05);
}
.kpi-label {
    font-size: 11px;
    color: #9fb0d4; 
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 10px;
    font-family: 'Montserrat', sans-serif;
    font-weight: 400;
}
.kpi-value {
    font-family: 'Montserrat', sans-serif;
    font-size: 32px;
    font-weight: 400;
    color: #f5f7ff;
    letter-spacing: -1px;
    line-height: 1;
}
.kpi-delta {
    margin-top: 8px;
    font-size: 11px;
    font-family: 'Inter', sans-serif;
    color: #7f8db3;
}

/* ── Alert cards ── */
.alert-card {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.06);
    border-left: 3px solid;
    border-radius: 12px;
    padding: 16px 18px;
    margin-bottom: 10px;
    transition: background 0.2s;
}
.alert-card:hover { background: rgba(255,255,255,0.04); }
.alert-card.sev-high   { border-left-color: #ff3b5c; }
.alert-card.sev-medium { border-left-color: #f59e0b; }
.alert-card.sev-low    { border-left-color: #10b981; }

.alert-date  { font-family: 'DM Mono', monospace; font-size: 11px; color: #4a5880; }
.alert-title { font-family: 'Syne', sans-serif; font-size: 14px; font-weight: 600; color: #d0d8f0; margin: 4px 0; }
.alert-body  { font-size: 12px; color: #6a7a9a; line-height: 1.6; }
.alert-pill  {
    display: inline-block;
    font-size: 10px; font-family: 'DM Mono', monospace;
    padding: 2px 8px; border-radius: 20px;
    margin-right: 6px; margin-top: 6px;
    letter-spacing: 0.3px;
}
.pill-red    { background: rgba(255,59,92,0.15);  color: #ff8fa3; border: 1px solid rgba(255,59,92,0.3); }
.pill-amber  { background: rgba(245,158,11,0.15); color: #fcd34d; border: 1px solid rgba(245,158,11,0.3); }
.pill-green  { background: rgba(16,185,129,0.15); color: #6ee7b7; border: 1px solid rgba(16,185,129,0.3); }
.pill-blue   { background: rgba(58,107,255,0.15); color: #93b4ff; border: 1px solid rgba(58,107,255,0.3); }

/* ── Risk badge ── */
.risk-badge {
    display: inline-block;
    font-family: 'Syne', sans-serif;
    font-size: 22px;
    font-weight: 800;
    padding: 14px 28px;
    border-radius: 50px;
    letter-spacing: -0.5px;
}
.risk-high   { background: rgba(255,59,92,0.15);  color: #ff3b5c; border: 1px solid rgba(255,59,92,0.4); }
.risk-medium { background: rgba(245,158,11,0.12); color: #f59e0b; border: 1px solid rgba(245,158,11,0.35); }
.risk-low    { background: rgba(16,185,129,0.12); color: #10b981; border: 1px solid rgba(16,185,129,0.35); }

/* ── Tab overrides ── */
[data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid rgba(255,255,255,0.06) !important;
    gap: 0 !important;
}
[data-baseweb="tab"] {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    color: #4a5880 !important;
    padding: 10px 22px !important;
    background: transparent !important;
    border: none !important;
    border-radius: 0 !important;
}
[aria-selected="true"][data-baseweb="tab"] {
    color: #93b4ff !important;
    border-bottom: 2px solid #3a6bff !important;
}

/* ── Divider ── */
hr { border-color: rgba(255,255,255,0.05) !important; margin: 1.5rem 0 !important; }

/* ── Selectbox / Input ── */
[data-baseweb="select"] > div,
[data-baseweb="input"] > div {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 10px !important;
    color: #d0d8f0 !important;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    background: rgba(255,255,255,0.02) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 12px !important;
    margin-bottom: 8px !important;
}
[data-testid="stExpander"] summary {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    color: #a0b0d0 !important;
    padding: 12px 16px !important;
}

/* ── Status row ── */
.status-row {
    display: flex;
    gap: 8px;
    margin-bottom: 0.75rem;
    flex-wrap: wrap;
}
.status-dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    display: inline-block;
    margin-right: 5px;
    position: relative;
    top: -1px;
}
.dot-green { background: #10b981; box-shadow: 0 0 6px #10b981; }
.dot-amber { background: #f59e0b; }
.dot-red   { background: #ff3b5c; box-shadow: 0 0 6px #ff3b5c; }

/* ── Metric block ── */
.metric-block {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 18px 20px;
    text-align: center;
}
.metric-block .mb-label { font-size: 11px; color: #4a5880; font-family: 'DM Mono', monospace; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 6px; }
.metric-block .mb-value { font-family: 'Montserrat', sans-serif; font-size: 24px; font-weight: 700; color: #e8eeff; }
.metric-block .mb-sub   { font-size: 11px; color: #3a5aaa; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)
# ─── DATA LAYER ──────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def load_data():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        st.error("DATABASE_URL environment variable is not set.")
        st.stop()
    db = FinOpsDatabase(db_url)
    try:
        anomalies_df = db.fetch_anomalies(limit=10000)
        forecasts_df = db.fetch_forecasts(limit=5000)
        anomalies_df['date'] = pd.to_datetime(anomalies_df['date'])
        if not forecasts_df.empty:
            forecasts_df['date'] = pd.to_datetime(forecasts_df['date'])
        return anomalies_df, forecasts_df
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        st.stop()


@st.cache_data(ttl=300, show_spinner=False)
def load_metrics():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        return pd.DataFrame()
    db = FinOpsDatabase(db_url)
    try:
        return db.fetch_metrics()
    except Exception:
        return pd.DataFrame()



# ─── PLOTLY THEME ────────────────────────────────────────────────────────────────
PLOTLY_BASE = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='Inter', color='#9fb0d4', size=11),  # 🔥 global text

    hovermode='x unified',
    margin=dict(l=10, r=10, t=36, b=10),

    legend=dict(
        bgcolor='rgba(255,255,255,0.04)',
        bordercolor='rgba(255,255,255,0.08)',
        borderwidth=1,
        font=dict(size=11, color='#c7d2ff')  # 🔥 brighter legend
    ),

    xaxis=dict(
        gridcolor='rgba(255,255,255,0.04)',    # slightly visible grid
        zerolinecolor='rgba(255,255,255,0.05)',
        tickfont=dict(size=11, color='#b8c6e8'),  # 🔥 FIXED
        title_font=dict(size=12, color='#dbe4ff')  # if titles exist
    ),

    yaxis=dict(
        gridcolor='rgba(255,255,255,0.06)',
        zerolinecolor='rgba(255,255,255,0.05)',
        tickfont=dict(size=11, color='#b8c6e8'),  # 🔥 FIXED
        title_font=dict(size=12, color='#dbe4ff')
    )
)




# ─── CHART BUILDERS ──────────────────────────────────────────────────────────────
def create_time_series(service_df, anomalies_only):
    """Smoothed cost line with severity-coded anomaly markers"""
    daily = service_df.groupby('date')['cost_usd'].sum().reset_index()
    daily_map = dict(zip(daily['date'], daily['cost_usd']))
    fig = go.Figure()

    # Gradient fill baseline
    fig.add_trace(go.Scatter(
        x=daily['date'], y=daily['cost_usd'],
        mode='lines',
        line=dict(color='rgba(58,107,255,0)', width=0),
        fill='tozeroy',
        fillcolor='rgba(58,107,255,0.07)',
        showlegend=False,
        hoverinfo='skip'
    ))

    # Main cost line — smooth spline
    fig.add_trace(go.Scatter(
        x=daily['date'], y=daily['cost_usd'],
        mode='lines',
        name='Cloud Spend',
        line=dict(color='#3a6bff', width=2, shape='spline', smoothing=0.8),
        hovertemplate='<b>%{x|%b %d}</b><br>Cost: $%{y:,.2f}<extra></extra>'
    ))

    # Severity-coded anomaly markers
    sev_config = {
        'high':   {'color': '#ff3b5c', 'size': 14, 'symbol': 'x-thin'},
        'medium': {'color': '#f59e0b', 'size': 11, 'symbol': 'x-thin'},
        'low':    {'color': '#10b981', 'size': 9,  'symbol': 'x-thin'},
    }

    for sev, cfg in sev_config.items():
        sev_df = anomalies_only[anomalies_only['severity_label'] == sev]

        if sev_df.empty:
            continue

        # Map to daily values
        sev_df = sev_df.copy()
        sev_df['y_val'] = sev_df['date'].map(daily_map)

        # Drop failed mappings
        sev_df = sev_df.dropna(subset=['y_val'])

        # Remove duplicates per day
        sev_df = sev_df.drop_duplicates(subset=['date'])

        fig.add_trace(go.Scatter(
            x=sev_df['date'],
            y=sev_df['y_val'],  # ✅ correct alignment
            mode='markers',
            name=f'{sev.capitalize()} Anomaly',
            marker=dict(
                color=cfg['color'],
                size=cfg['size'],
                symbol=cfg['symbol'],
                line=dict(color=cfg['color'], width=2.5)
            ),
            hovertemplate=(
                '<b>%{x}</b><br>'
                f'Severity: {sev.upper()}<br>'
                'Cost: $%{y:,.2f}<extra></extra>'
            )
        ))

    fig.update_layout(
        **PLOTLY_BASE,
        title=dict(text='Cost History & Anomaly Detection', font=dict(size=13, color='#7080a0')),
        height=340,
    )
    return fig


def create_severity_donut(anomalies_only):
    """Donut chart — severity distribution"""
    if anomalies_only.empty:
        fig = go.Figure()
        fig.update_layout(**PLOTLY_BASE, height=280)
        return fig

    counts = anomalies_only['severity_label'].value_counts()
    labels = counts.index.tolist()
    values = counts.values.tolist()

    color_map = {'high': '#ff3b5c', 'medium': '#f59e0b', 'low': '#10b981'}
    colors = [color_map.get(l, '#4a5880') for l in labels]

    fig = go.Figure(go.Pie(
        labels=[l.capitalize() for l in labels],
        values=values,
        hole=0.65,
        marker=dict(colors=colors, line=dict(color='#05060d', width=3)),
        textinfo='none',
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>'
    ))

    total = sum(values)
    fig.update_layout(
        **PLOTLY_BASE,
        height=280,
        showlegend=True,
        annotations=[
            dict(
                text=f"<b>{total}</b><br><span style='font-size:10px'>Total</span>",
                x=0.5,
                y=0.5,
                xanchor='center',
                yanchor='middle',
                showarrow=False,
                font=dict(size=18, color='#d0d8f0', family='Syne')
            )
        ]
    )
    return fig


def create_service_bar(df):
    """Horizontal stacked bar — cost by service"""
    if df.empty:
        return go.Figure()

    agg = df.groupby('service_category')['cost_usd'].sum().sort_values(ascending=True)
    anomaly_agg = df[df['is_anomaly'] == True].groupby('service_category')['cost_usd'].sum()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=agg.index.tolist(),
        x=agg.values.tolist(),
        orientation='h',
        name='Normal Spend',
        marker=dict(
            color='rgba(58,107,255,0.35)',
            line=dict(color='rgba(58,107,255,0.6)', width=1)
        ),
        hovertemplate='<b>%{y}</b><br>Total: $%{x:,.0f}<extra></extra>'
    ))

    if not anomaly_agg.empty:
        anomaly_x = [anomaly_agg.get(s, 0) for s in agg.index.tolist()]
        fig.add_trace(go.Bar(
            y=agg.index.tolist(),
            x=anomaly_x,
            orientation='h',
            name='Anomalous Spend',
            marker=dict(
                color='rgba(255,59,92,0.45)',
                line=dict(color='rgba(255,59,92,0.7)', width=1)
            ),
            hovertemplate='<b>%{y}</b><br>Anomalous: $%{x:,.0f}<extra></extra>'
        ))

    fig.update_layout(
        **PLOTLY_BASE,
        barmode='overlay',
        height=280,
        title=dict(text='Cost by Service Category', font=dict(size=13, color='#7080a0')),
        xaxis_title='',
        yaxis_title='',
    )
    return fig


def create_heatmap(df):
    """Cost intensity heatmap — day of week vs service"""
    if df.empty or len(df) < 10:
        return go.Figure()

    df = df.copy()
    df['dow'] = df['date'].dt.day_name()

    dow_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    pivot = df.groupby(['service_category', 'dow'])['cost_usd'].mean().unstack(fill_value=0)
    pivot = pivot.reindex(columns=[d for d in dow_order if d in pivot.columns])

    fig = go.Figure(go.Heatmap(
        z=pivot.values.tolist(),
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=[
            [0.0, '#05060d'],
            [0.3, '#0d1a4a'],
            [0.6, '#1e3a8a'],
            [0.85, '#3a6bff'],
            [1.0, '#ff3b5c']
        ],
        showscale=True,
        colorbar=dict(
            thickness=10,
            len=0.8,
            tickfont=dict(color='#4a5880', size=9),
            outlinecolor='rgba(0,0,0,0)'
        ),
        hovertemplate='<b>%{y}</b> — %{x}<br>Avg Cost: $%{z:,.2f}<extra></extra>'
    ))

    fig.update_layout(**PLOTLY_BASE, height=260)

    fig.update_xaxes(
        side='bottom',
        tickfont=dict(size=11, color='#b8c6e8'),  # 🔥 brighter
        showgrid=False
    )

    fig.update_yaxes(
        tickfont=dict(size=11, color='#b8c6e8'),  # 🔥 brighter
        showgrid=False
    )
    return fig


def create_forecast_chart(hist_df, forecast_df, budget_threshold):
    """Forecast with P10/P90 band and budget threshold line"""
    fig = go.Figure()

    # Historical
    hist_daily = hist_df.groupby('date')['cost_usd'].sum().reset_index()
    fig.add_trace(go.Scatter(
        x=hist_daily['date'], y=hist_daily['cost_usd'],
        name='Historical',
        line=dict(color='#3a6bff', width=2, shape='spline', smoothing=0.6),
        hovertemplate='<b>%{x|%b %d}</b><br>Actual: $%{y:,.2f}<extra></extra>'
    ))

    if not forecast_df.empty:
        # Confidence band
        fig.add_trace(go.Scatter(
            x=forecast_df['date'].tolist() + forecast_df['date'].tolist()[::-1],
            y=forecast_df['forecast_90'].tolist() + forecast_df['forecast_10'].tolist()[::-1],
            fill='toself',
            fillcolor='rgba(180,140,255,0.10)',
            line=dict(color='rgba(0,0,0,0)'),
            name='80% Confidence',
            hoverinfo='skip'
        ))

        # P50 forecast line
        fig.add_trace(go.Scatter(
            x=forecast_df['date'], y=forecast_df['forecast_50'],
            name='Forecast P50',
            line=dict(color='#b06fff', width=2, dash='dot', shape='spline'),
            hovertemplate='<b>%{x|%b %d}</b><br>Forecast: $%{y:,.2f}<extra></extra>'
        ))

    # Budget threshold
    all_dates = hist_daily['date'].tolist()
    if not forecast_df.empty:
        all_dates += forecast_df['date'].tolist()

    if all_dates:
        daily_budget = budget_threshold / 30
        fig.add_trace(go.Scatter(
            x=[all_dates[0], all_dates[-1]],
            y=[daily_budget, daily_budget],
            name='Daily Budget',
            line=dict(color='rgba(255,59,92,0.6)', width=1.5, dash='dash'),
            hoverinfo='skip'
        ))

    fig.update_layout(
        **PLOTLY_BASE,
        height=360,
        title=dict(text='90-Day Spend Forecast with Confidence Interval', font=dict(size=13, color='#7080a0')),
    )
    return fig
# ─── HEADER ──────────────────────────────────────────────────────────────────────
col_title, col_ts = st.columns([5, 2])

with col_title:
    st.markdown('<div class="fg-hero">FinOps Guardian</div>', unsafe_allow_html=True)
    st.markdown('<div class="fg-sub">AI-Powered Multi-Cloud Cost Anomaly Detection &amp; Spend Forecasting &nbsp;|&nbsp; Team Catalyst Core</div>', unsafe_allow_html=True)

with col_ts:
    st.markdown(f'<div class="fg-mono" style="text-align:right;padding-top:8px">Last updated<br>{pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")} UTC</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
with st.spinner("Loading FinOps Intelligence..."):
    anomalies_df, forecasts_df = load_data()
    metrics_df = load_metrics()
if anomalies_df is None or anomalies_df.empty:
    st.error("No data loaded from database.")
    st.stop()   
# ─── CUSTOM SIDEBAR ─────────────────────────────────────────────
with st.sidebar:

    st.markdown("### ⚙️ Control Panel")

    # ── DATA PREP ──
    all_providers = sorted(anomalies_df['provider'].dropna().unique().tolist()) if 'provider' in anomalies_df.columns else []
    all_services = sorted(anomalies_df['service_category'].dropna().unique().tolist()) if 'service_category' in anomalies_df.columns else []

    # ── FILTERS ──
    st.markdown("#### Filters")

    selected_providers = st.multiselect(
        "Cloud Provider",
        options=all_providers,
        default=all_providers
    )

    selected_service = st.selectbox(
        "Service Category",
        options=all_services if all_services else ["No Data"]
    )

    if not anomalies_df.empty:
        date_min = anomalies_df['date'].min().date()
        date_max = anomalies_df['date'].max().date()

        date_range = st.date_input(
            "Date Range",
            value=(date_min, date_max),
            min_value=date_min,
            max_value=date_max
        )
    else:
        date_range = None

    st.markdown("---")

    # ── FINOPS CONTROLS ──
    st.markdown("#### Budget Controls")

    budget_threshold = st.number_input(
        "Monthly Budget ($)",
        value=50000,
        step=1000
    )

    alert_threshold = st.slider(
        "Alert Threshold",
        0, 100, 60
    )

    st.markdown("---")

    # ── PROVIDER STATUS ──
    st.markdown("#### Provider Status")

    if all_providers:
        for p in all_providers:
            st.markdown(f"🟢 {p}")
    else:
        st.caption("No providers found")

    st.markdown("---")

    # ── MODELS ──
    st.markdown("#### Active Models")

    models = [
        "Z-Score",
        "Isolation Forest",
        "LSTM Autoencoder",
        "Prophet",
        "LightGBM",
        "SHAP"
    ]

    for m in models:
        st.markdown(f"🧠 {m}")

    st.markdown("---")

    # ── DEBUG (REMOVE LATER) ──
    st.caption(f"Rows Loaded: {len(anomalies_df)}")

# ─── APPLY FILTERS ───────────────────────────────────────────────────────────────
filtered_df = anomalies_df.copy()

if selected_providers:
    filtered_df = filtered_df[filtered_df['provider'].isin(selected_providers)]

if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    filtered_df = filtered_df[
        (filtered_df['date'].dt.date >= date_range[0]) &
        (filtered_df['date'].dt.date <= date_range[1])
    ]

service_df = filtered_df[filtered_df['service_category'] == selected_service].copy()
anomalies_only = service_df[service_df['is_anomaly'] == True].copy()

service_forecast_df = pd.DataFrame()
if not forecasts_df.empty:
    service_forecast_df = forecasts_df[forecasts_df['service_category'] == selected_service].sort_values('date')

# ─── KPI STRIP ───────────────────────────────────────────────────────────────────
total_anomalies   = int(filtered_df['is_anomaly'].sum())
if 'priority' in filtered_df.columns:
    p0_p1_count = int(filtered_df['priority'].str.contains('P0|P1', na=False).sum())
else:
    p0_p1_count = int(
        ((filtered_df['is_anomaly'] == True) &
         (filtered_df['severity_label'] == 'high')).sum()
    )
total_impact      = filtered_df['impact_score'].sum() if 'impact_score' in filtered_df.columns else 0
high_sev_count    = int((filtered_df['severity_label'] == 'high').sum())

# Use priority column safely
if 'priority' in filtered_df.columns:
    p0_p1_count = int(filtered_df[filtered_df['priority'].str.contains('P0|P1', na=False)].shape[0])
else:
    p0_p1_count = high_sev_count

st.markdown(f"""
<div class="kpi-grid">
  <div class="kpi-card kpi-blue">
    <div class="kpi-label">Total Anomalies</div>
    <div class="kpi-value">{total_anomalies:,}</div>
    <div class="kpi-delta">Last 180 days · all providers</div>
  </div>
  <div class="kpi-card kpi-red">
    <div class="kpi-label">P0 + P1 Critical</div>
    <div class="kpi-value">{p0_p1_count:,}</div>
    <div class="kpi-delta">Requires immediate action</div>
  </div>
  <div class="kpi-card kpi-amber">
    <div class="kpi-label">Total Impact Score</div>
    <div class="kpi-value">${total_impact:,.0f}</div>
    <div class="kpi-delta">Estimated cost exposure</div>
  </div>
  <div class="kpi-card kpi-green">
    <div class="kpi-label">Monthly Budget</div>
    <div class="kpi-value">${budget_threshold:,}</div>
    <div class="kpi-delta">Active threshold · all services</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ─── MAIN TABS ───────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Anomaly Matrix",
    "Root Cause Attribution",
    "Prediction Engine",
    "Service Intelligence",
    "Model Performance"
])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — ANOMALY MATRIX
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown(f'<div class="fg-section">Anomaly Intelligence — {selected_service.upper()}</div>', unsafe_allow_html=True)
    st.markdown('<div class="fg-sub" style="margin-bottom:1rem">Ensemble detection · Confidence scoring · Model agreement</div>', unsafe_allow_html=True)
    # ─── MODEL INTELLIGENCE STRIP (REPLACEMENT) ───

    flags = anomalies_only.copy()

    total_flags = len(flags)

    if 'model_votes' in flags.columns:
        avg_votes = round(flags['model_votes'].mean(), 2)
        strong = int((flags['model_votes'] >= 3).sum())
        weak = int((flags['model_votes'] < 3).sum())
    else:
        avg_votes, strong, weak = '-', '-', '-'

    m1, m2, m3, m4 = st.columns(4)

    m1.markdown(f'''
    <div class="metric-block">
    <div class="mb-label">Total Flags</div>
    <div class="mb-value">{total_flags}</div>
    <div class="mb-sub">Detected anomalies</div>
    </div>
    ''', unsafe_allow_html=True)

    m2.markdown(f'''
    <div class="metric-block">
    <div class="mb-label">Avg Model Agreement</div>
    <div class="mb-value">{avg_votes}</div>
    <div class="mb-sub">Votes per anomaly</div>
    </div>
    ''', unsafe_allow_html=True)

    m3.markdown(f'''
    <div class="metric-block">
    <div class="mb-label">High Confidence</div>
    <div class="mb-value">{strong}</div>
    <div class="mb-sub">≥ 3 models agreed</div>
    </div>
    ''', unsafe_allow_html=True)

    m4.markdown(f'''
    <div class="metric-block">
    <div class="mb-label">Low Confidence</div>
    <div class="mb-value">{weak}</div>
    <div class="mb-sub">1–2 model signals</div>
    </div>
    ''', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    # ─── MODEL CONTRIBUTION BAR ───


    # ─── MODEL AGREEMENT DISTRIBUTION (REAL DATA) ───
    if 'model_votes' in service_df.columns:

        vote_dist = service_df[service_df['is_anomaly'] == True]['model_votes'].value_counts().sort_index()

        fig_models = go.Figure(go.Bar(
            x=[f"{v} Models" for v in vote_dist.index],
            y=vote_dist.values,
            marker=dict(
                color=['#4a5880' if v == 1 else '#f59e0b' if v == 2 else '#10b981' for v in vote_dist.index]
            )
        ))

        fig_models.update_layout(
            **PLOTLY_BASE,
            height=220,
            showlegend=False,
            title=dict(
                text='Detection Confidence (Model Agreement)',
                font=dict(size=13, color='#7080a0')
            )
        )

        

    else:
        st.caption("No model vote data available")


    # Main chart 70% | Donut 30%
    chart_col, donut_col = st.columns([7, 3])

    with chart_col:
        if not service_df.empty:
            fig_ts = create_time_series(service_df, anomalies_only)
            st.plotly_chart(fig_ts, width='stretch')
        else:
            st.info("No data for selected filters.")

    with donut_col:
        st.markdown('<div class="fg-mono" style="margin-bottom:8px">Severity Breakdown</div>', unsafe_allow_html=True)
        fig_donut = create_severity_donut(anomalies_only)
        st.plotly_chart(fig_donut, width='stretch')

        # Quick counts
        if not anomalies_only.empty:
            for sev, cls in [('high','pill-red'),('medium','pill-amber'),('low','pill-green')]:
                cnt = int((anomalies_only['severity_label'] == sev).sum())
                if cnt:
                    st.markdown(f'<span class="alert-pill {cls}">{sev.upper()} &nbsp;{cnt}</span>', unsafe_allow_html=True)

    st.markdown("---")

    # Correlated anomalies section
    st.markdown('<div class="fg-section">Cross-Service Correlated Anomalies</div>', unsafe_allow_html=True)
    st.markdown('<div class="fg-sub" style="margin-bottom:1rem">Dates where 2+ services spiked simultaneously — the Creep Pattern</div>', unsafe_allow_html=True)

    # Compute correlated events from full filtered data
    if len(filtered_df) > 10:
        pivot = filtered_df.groupby(['date', 'service_category'])['cost_usd'].sum().unstack(fill_value=0)
        z = pd.DataFrame()
        for col in pivot.columns:
            z[col] = np.abs((pivot[col] - pivot[col].mean()) / (pivot[col].std() + 1e-9))
        spiking_count = (z > 2.0).sum(axis=1)
        correlated_events = spiking_count[spiking_count >= 2]

        if len(correlated_events) > 0:
            corr_data = pd.DataFrame({
                'Date': correlated_events.index.strftime('%Y-%m-%d'),
                'Services Spiking': correlated_events.values,
                'Risk Level': ['CRITICAL' if v >= 4 else 'HIGH' if v >= 3 else 'ELEVATED' for v in correlated_events.values]
            })
            st.dataframe(
                corr_data.reset_index(drop=True),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.success("No correlated anomaly events detected in the selected period.")
    else:
        st.info("Insufficient data for cross-service correlation analysis.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — ROOT CAUSE ATTRIBUTION
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="fg-section">Automated Root Cause Attribution</div>', unsafe_allow_html=True)
    st.markdown('<div class="fg-sub" style="margin-bottom:1.5rem">SHAP-powered causal analysis — ranked by cost impact</div>', unsafe_allow_html=True)

    if anomalies_only.empty:
        st.success("No anomalies detected for this service. Cost pattern is within normal bounds.")
    else:
        # Sort by impact descending
        display_anomalies = anomalies_only.sort_values(
            'impact_score' if 'impact_score' in anomalies_only.columns else 'cost_usd',
            ascending=False
        ).head(20)

        for _, row in display_anomalies.iterrows():
            sev = str(row.get('severity_label', 'low')).lower()
            sev_cls = {'high': 'sev-high', 'medium': 'sev-medium'}.get(sev, 'sev-low')
            pill_cls = {'high': 'pill-red', 'medium': 'pill-amber'}.get(sev, 'pill-green')
            date_str = row['date'].strftime('%Y-%m-%d')
            cost = float(row.get('cost_usd', 0))
            priority = str(row.get('priority', 'P3 - Low'))
            impact = float(row.get('impact_score', 0))

            with st.expander(f"{date_str}  |  ${cost:,.2f}  |  {priority}"):
                c1, c2 = st.columns([3, 1])

                with c1:
                    st.markdown(f"""
<div class="alert-card {sev_cls}">
  <div class="alert-date">{date_str}</div>
  <div class="alert-title">Root Cause: {row.get('root_cause', 'Investigating...')}</div>
  <div class="alert-body">{row.get('llm_insight', 'No AI insight available.')}</div>
  <div style="margin-top:10px">
    <span class="alert-pill {pill_cls}">{sev.upper()}</span>
    <span class="alert-pill pill-blue">{priority}</span>
  </div>
</div>
""", unsafe_allow_html=True)

                with c2:
                    action = str(row.get('recommended_action', 'Investigate manually'))
                    savings = str(row.get('estimated_savings', 'N/A'))
                    st.markdown(f"""
<div class="metric-block" style="margin-bottom:8px">
  <div class="mb-label">Impact Score</div>
  <div class="mb-value">${impact:,.0f}</div>
</div>
<div class="metric-block" style="margin-bottom:8px">
  <div class="mb-label">Est. Savings</div>
  <div class="mb-value" style="font-size:16px">{savings}</div>
</div>
<div class="metric-block">
  <div class="mb-label">Action</div>
  <div class="mb-value" style="font-size:12px;font-family:DM Sans">{action}</div>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — PREDICTION ENGINE
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="fg-section">Multi-Horizon Spend Forecast</div>', unsafe_allow_html=True)

    # Horizon selector
    horizon = st.radio("Forecast Horizon", ["7-Day", "30-Day", "90-Day"], horizontal=True, index=2)
    horizon_days = {'7-Day': 7, '30-Day': 30, '90-Day': 90}[horizon]

    forecast_subset = service_forecast_df.head(horizon_days) if not service_forecast_df.empty else pd.DataFrame()

    fig_fc = create_forecast_chart(service_df, forecast_subset, budget_threshold)
    st.plotly_chart(fig_fc, width='stretch')

    # Horizon summary metrics
    if not forecast_subset.empty:
        m1, m2, m3, m4 = st.columns(4)
        proj_total  = float(forecast_subset['forecast_50'].sum())
        proj_upper  = float(forecast_subset['forecast_90'].sum())
        proj_lower  = float(forecast_subset['forecast_10'].sum())
        remaining   = budget_threshold - proj_total

        m1.markdown(f'<div class="metric-block"><div class="mb-label">Projected Total ({horizon})</div><div class="mb-value">${proj_total:,.0f}</div><div class="mb-sub">P50 median forecast</div></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="metric-block"><div class="mb-label">Worst Case</div><div class="mb-value">${proj_upper:,.0f}</div><div class="mb-sub">P90 upper bound</div></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="metric-block"><div class="mb-label">Best Case</div><div class="mb-value">${proj_lower:,.0f}</div><div class="mb-sub">P10 lower bound</div></div>', unsafe_allow_html=True)
        m4.markdown(f'<div class="metric-block"><div class="mb-label">Budget Remaining</div><div class="mb-value" style="color:{"#10b981" if remaining > 0 else "#ff3b5c"}">${remaining:,.0f}</div><div class="mb-sub">vs. monthly threshold</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="fg-section">Predictive Budget Intelligence</div>', unsafe_allow_html=True)

    if not forecast_subset.empty:
        proj_30 = float(service_forecast_df.head(30)['forecast_50'].sum()) if not service_forecast_df.empty else 0
        is_breach = proj_30 > budget_threshold
        trajectory = "HIGH RISK" if proj_30 > budget_threshold * 0.9 else "MEDIUM RISK" if proj_30 > budget_threshold * 0.7 else "LOW RISK"
        risk_cls = {'HIGH RISK': 'risk-high', 'MEDIUM RISK': 'risk-medium', 'LOW RISK': 'risk-low'}.get(trajectory, 'risk-low')
        breach_pct = round(proj_30 / budget_threshold * 100, 1)

        b1, b2 = st.columns([2, 3])
        with b1:
            st.markdown(f'<div class="risk-badge {risk_cls}">{trajectory}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="fg-sub" style="margin-top:12px">30-day projected spend: <b>${proj_30:,.0f}</b> ({breach_pct}% of budget)</div>', unsafe_allow_html=True)

        with b2:
            # Mini forecast bar
            if not service_forecast_df.empty:
                mini_df = service_forecast_df.head(30)
                fig_mini = go.Figure()
                fig_mini.add_trace(go.Bar(
                    x=mini_df['date'], y=mini_df['forecast_50'],
                    marker_color=['#ff3b5c' if v > budget_threshold/30 else '#3a6bff' for v in mini_df['forecast_50']],
                    hovertemplate='%{x|%b %d}: $%{y:,.0f}<extra></extra>'
                ))
                fig_mini.update_layout(
                    **PLOTLY_BASE,
                    height=180,
                    showlegend=False,
                    title=dict(text='30-Day Daily Forecast', font=dict(size=11, color='#7080a0'))
                )
                st.plotly_chart(fig_mini, width='stretch')
    else:
        st.info("No forecast data available. Run the pipeline to generate forecasts.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — SERVICE INTELLIGENCE
# ═══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="fg-section">Service Cost Intelligence</div>', unsafe_allow_html=True)

    bar_col, heat_col = st.columns([1, 1])

    with bar_col:
        fig_bar = create_service_bar(filtered_df)
        st.plotly_chart(fig_bar, width='stretch')

    with heat_col:
        fig_heat = create_heatmap(filtered_df)
        st.plotly_chart(fig_heat, width='stretch')

    st.markdown("---")

    # Provider breakdown
    st.markdown('<div class="fg-section">Provider Cost Breakdown</div>', unsafe_allow_html=True)

    if not filtered_df.empty:
        prov_agg = filtered_df.groupby('provider').agg(
            total_cost=('cost_usd', 'sum'),
            anomaly_count=('is_anomaly', 'sum'),
            avg_daily=('cost_usd', 'mean')
        ).reset_index()

        prov_cols = st.columns(len(prov_agg))
        colors = ['#3a6bff', '#b06fff', '#10b981', '#f59e0b']
        for i, (_, row) in enumerate(prov_agg.iterrows()):
            c = colors[i % len(colors)]
            prov_cols[i].markdown(f"""
<div class="kpi-card" style="border-top: 2px solid {c}">
  <div class="kpi-label">{row['provider']}</div>
  <div class="kpi-value" style="font-size:24px">${row['total_cost']:,.0f}</div>
  <div class="kpi-delta">{int(row['anomaly_count'])} anomalies · ${row['avg_daily']:,.0f}/day avg</div>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5 — MODEL PERFORMANCE
# ═══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown('<div class="fg-section">ML Model Performance Metrics</div>', unsafe_allow_html=True)
    st.markdown('<div class="fg-sub" style="margin-bottom:1.5rem">Measured on held-out test data — not estimates</div>', unsafe_allow_html=True)

    if not metrics_df.empty:
        # Show per-service metrics
        for _, row in metrics_df.iterrows():
            svc_name = str(row.get('model_name', 'unknown')).replace('_lightgbm', '')
            f1    = float(row.get('f1_score', 0))
            prec  = float(row.get('precision_score', 0))
            rec   = float(row.get('recall_score', 0))
            mape  = float(row.get('mape', 0))

            st.markdown(f'<div class="fg-mono" style="margin-bottom:8px">{svc_name.upper()}</div>', unsafe_allow_html=True)
            mc1, mc2, mc3, mc4 = st.columns(4)
            mc1.markdown(f'<div class="metric-block"><div class="mb-label">F1-Score</div><div class="mb-value" style="color:{"#10b981" if f1>0.8 else "#f59e0b"}">{f1:.3f}</div><div class="mb-sub">Primary eval metric</div></div>', unsafe_allow_html=True)
            mc2.markdown(f'<div class="metric-block"><div class="mb-label">Precision</div><div class="mb-value">{prec:.3f}</div><div class="mb-sub">Accuracy of flags</div></div>', unsafe_allow_html=True)
            mc3.markdown(f'<div class="metric-block"><div class="mb-label">Recall</div><div class="mb-value">{rec:.3f}</div><div class="mb-sub">Anomaly capture rate</div></div>', unsafe_allow_html=True)
            mc4.markdown(f'<div class="metric-block"><div class="mb-label">MAPE</div><div class="mb-value" style="color:{"#10b981" if mape<0.15 else "#f59e0b"}">{mape*100:.1f}%</div><div class="mb-sub">Forecast accuracy</div></div>', unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

    else:
        # Fallback — compute from filtered data if possible
        st.info("Run the pipeline to populate model metrics. Showing detection statistics from DB.")

        if not filtered_df.empty and 'is_anomaly' in filtered_df.columns:
            total_obs  = len(filtered_df)
            total_anom = int(filtered_df['is_anomaly'].sum())
            anom_rate  = total_anom / total_obs * 100 if total_obs else 0

            sc1, sc2, sc3 = st.columns(3)
            sc1.markdown(f'<div class="metric-block"><div class="mb-label">Total Observations</div><div class="mb-value">{total_obs:,}</div></div>', unsafe_allow_html=True)
            sc2.markdown(f'<div class="metric-block"><div class="mb-label">Anomalies Detected</div><div class="mb-value">{total_anom:,}</div></div>', unsafe_allow_html=True)
            sc3.markdown(f'<div class="metric-block"><div class="mb-label">Anomaly Rate</div><div class="mb-value">{anom_rate:.1f}%</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    # Model voting distribution bar
    st.markdown('<div class="fg-section">Detection Model Agreement</div>', unsafe_allow_html=True)
    st.markdown('<div class="fg-sub" style="margin-bottom:1rem">How many models agreed on each flagged anomaly</div>', unsafe_allow_html=True)

    if not anomalies_only.empty and 'model_votes' in service_df.columns:
        vote_dist = service_df[service_df['is_anomaly'] == True]['model_votes'].value_counts().sort_index()
        fig_votes = go.Figure(go.Bar(
            x=[f'{v} Model{"s" if v!=1 else ""}' for v in vote_dist.index],
            y=vote_dist.values,
            marker=dict(
                color=['#10b981' if v >= 3 else '#f59e0b' if v == 2 else '#4a5880' for v in vote_dist.index],
                line=dict(color='rgba(0,0,0,0)', width=0)
            ),
            hovertemplate='%{x}: %{y} anomalies<extra></extra>'
        ))
        fig_votes.update_layout(
            **PLOTLY_BASE,
            height=220,
            title=dict(text='Vote Distribution — Ensemble Confidence', font=dict(size=13, color='#7080a0')),
            showlegend=False
        )
        st.plotly_chart(fig_votes, width='stretch')
    else:
        st.caption("Vote distribution data not available for this view.")

    # Export
    st.markdown("---")
    if not anomalies_only.empty:
        csv = anomalies_only.to_csv(index=False)
        st.download_button(
            label="Export Anomaly Report — CSV",
            data=csv,
            file_name=f"finops_guardian_{selected_service}_anomalies.csv",
            mime="text/csv"
        )