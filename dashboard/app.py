# dashboard/app.py
# FinOps Guard — Premium Decision Intelligence Interface
# Team Catalyst Core | Tic Tech Toe '26

import os
import sys
import time
import pandas as pd 
import numpy as np
import plotly.graph_objects as go
import streamlit as st

# Force project root into path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.database import FinOpsDatabase

# ─── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FinOps Guard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State
if 'processed' not in st.session_state:
    st.session_state.processed = False

# ─── GLOBAL CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@200;300;400;500&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Reset & Base Layout ── */
*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background-color: #030712 !important;
    color: #e2e8f0 !important;
    font-family: 'Inter', sans-serif !important;
}

[data-testid="stAppViewContainer"] {
    background: 
        radial-gradient(circle at 10% 20%, rgba(16, 185, 129, 0.03) 0%, transparent 50%),
        radial-gradient(circle at 90% 80%, rgba(16, 185, 129, 0.02) 0%, transparent 50%),
        #030712 !important;
}

/* Hide Streamlit watermark / footer / MainMenu */
#MainMenu, footer {
    visibility: hidden !important;
    display: none !important;
}
header[data-testid="stHeader"] {
    background-color: transparent !important;
}
[data-testid="stAppViewContainer"] {
    padding-top: 0rem !important;
}

.block-container {
    padding: 3rem 4rem !important;
    max-width: 1500px !important;
}

/* ── Custom Landing Elements ── */
.welcome-container {
    margin-top: 1rem;
    margin-bottom: 2rem;
}

.welcome-header {
    font-family: 'Montserrat', sans-serif;
    font-size: 68px;
    font-weight: 200;
    letter-spacing: -2.8px;
    background: linear-gradient(135deg, #ffffff 40%, #10b981 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    line-height: 1.05;
    margin-bottom: 0.75rem;
}

.welcome-subtitle {
    font-family: 'Inter', sans-serif;
    font-size: 14.5px;
    color: #10b981;
    font-weight: 400;
    letter-spacing: 2px;
    margin-bottom: 3.5rem;
    text-transform: uppercase;
}

/* ── Styled Cards ── */
.fg-card {
    background: rgba(15, 23, 42, 0.4);
    border: 1px solid rgba(255, 255, 255, 0.04);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 24px;
    backdrop-filter: blur(20px);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    transition: transform 0.2s, border-color 0.2s;
}
.fg-card:hover {
    border-color: rgba(14, 165, 233, 0.15);
}

.fg-header-classy {
    font-family: 'Montserrat', sans-serif;
    font-size: 15px;
    font-weight: 400;
    color: #f8fafc;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
    text-transform: uppercase;
}

.fg-body-classy {
    font-size: 13px;
    color: #cbd5e1;
    line-height: 1.6;
}

/* ── KPI Grid ── */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 2rem;
}
.kpi-card {
    background: rgba(15, 23, 42, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.04);
    border-radius: 14px;
    padding: 20px 24px;
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(12px);
    box-shadow: 0 4px 15px rgba(0,0,0,0.4);
    transition: border-color 0.3s, transform 0.2s;
}
.kpi-card:hover {
    border-color: rgba(16, 185, 129, 0.2);
    transform: translateY(-2px);
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    border-radius: 14px 14px 0 0;
}
.kpi-blue::before  { background: rgba(16, 185, 129, 0.6); }
.kpi-red::before   { background: rgba(251, 113, 133, 0.6); }
.kpi-amber::before { background: rgba(251, 191, 36, 0.6); }
.kpi-green::before { background: rgba(52, 211, 153, 0.6); }

.kpi-label {
    font-size: 11px;
    color: #cbd5e1;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 6px;
    font-family: 'Montserrat', sans-serif;
}
.kpi-value {
    font-family: 'Montserrat', sans-serif;
    font-size: 32px;
    font-weight: 300;
    color: #f1f5f9;
    letter-spacing: -1px;
    line-height: 1.1;
}
.kpi-delta {
    margin-top: 6px;
    font-size: 11px;
    color: #94a3b8;
}

/* ── Alert Bar ── */
.alert-strip {
    background: rgba(251, 113, 133, 0.05);
    border: 1px solid rgba(251, 113, 133, 0.15);
    border-radius: 12px;
    padding: 14px 20px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    gap: 12px;
    color: #fda4af;
    font-size: 13.5px;
}

/* ── Metrics Cards ── */
.metric-block {
    background: rgba(255, 255, 255, 0.015);
    border: 1px solid rgba(255, 255, 255, 0.03);
    border-radius: 10px;
    padding: 16px;
    text-align: center;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.01);
}
.mb-label {
    font-size: 10px;
    color: #cbd5e1;
    font-family: 'JetBrains Mono', monospace;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
}
.mb-value {
    font-family: 'Montserrat', sans-serif;
    font-size: 22px;
    font-weight: 400;
    color: #ffffff;
}
.mb-sub {
    font-size: 10.5px;
    color: #a1a1aa;
    margin-top: 2px;
}

/* ── Telemetry List Cards ── */
.alert-card {
    background: rgba(15, 23, 42, 0.3);
    border: 1px solid rgba(255, 255, 255, 0.04);
    border-left: 3px solid;
    border-radius: 10px;
    padding: 18px 20px;
    margin-bottom: 12px;
    transition: background-color 0.2s;
}
.alert-card:hover {
    background: rgba(15, 23, 42, 0.45);
}
.sev-high   { border-left-color: #fb7185; }
.sev-medium { border-left-color: #fbbf24; }
.sev-low    { border-left-color: #34d399; }

.alert-date  { font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #cbd5e1; }
.alert-title { font-family: 'Montserrat', sans-serif; font-size: 14px; font-weight: 400; color: #f1f5f9; margin: 4px 0 6px; }
.alert-body  { font-size: 12.5px; color: #cbd5e1; line-height: 1.6; }

.alert-pill {
    display: inline-block;
    font-size: 9.5px;
    font-family: 'JetBrains Mono', monospace;
    padding: 2px 8px;
    border-radius: 12px;
    margin-right: 6px;
    margin-top: 6px;
}
.pill-red    { background: rgba(251,113,133,0.06); color: #fda4af; border: 1px solid rgba(251,113,133,0.15); }
.pill-amber  { background: rgba(251,191,36,0.06); color: #fcd34d; border: 1px solid rgba(251,191,36,0.15); }
.pill-green  { background: rgba(52,211,153,0.06); color: #6ee7b7; border: 1px solid rgba(52,211,153,0.15); }
.pill-blue   { background: rgba(16,185,129,0.06); color: #a7f3d0; border: 1px solid rgba(16,185,129,0.15); }

/* ── Risk Badge ── */
.risk-badge {
    display: inline-block;
    font-family: 'Montserrat', sans-serif;
    font-size: 20px;
    font-weight: 300;
    padding: 12px 24px;
    border-radius: 30px;
    letter-spacing: 0.5px;
}
.risk-high   { background: rgba(251,113,133,0.06);  color: #fb7185; border: 1px solid rgba(251,113,133,0.15); }
.risk-medium { background: rgba(251,191,36,0.06); color: #fbbf24; border: 1px solid rgba(251,191,36,0.15); }
.risk-low    { background: rgba(52,211,153,0.06); color: #34d399; border: 1px solid rgba(52,211,153,0.15); }

/* ── Tabs Overrides ── */
[data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid rgba(255,255,255,0.04) !important;
    gap: 0 !important;
}
[data-baseweb="tab"] {
    font-family: 'Montserrat', sans-serif !important;
    font-weight: 400 !important;
    font-size: 12.5px !important;
    color: #cbd5e1 !important;
    padding: 12px 24px !important;
    background: transparent !important;
    border: none !important;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}
[aria-selected="true"][data-baseweb="tab"] {
    color: #34d399 !important;
    border-bottom: 2px solid #10b981 !important;
}

/* ── Form Inputs ── */
[data-baseweb="select"] > div, [data-baseweb="input"] > div {
    background: rgba(15, 23, 42, 0.5) !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
    border-radius: 8px !important;
    color: #f1f5f9 !important;
}

/* ── Black Sidebar Redesign ── */
[data-testid="stSidebar"] {
    background-color: #000000 !important;
    background-image: none !important;
    border-right: 1px solid rgba(255, 255, 255, 0.04) !important;
    display: flex !important;
    visibility: visible !important;
}
[data-testid="stSidebarContent"] {
    background-color: #000000 !important;
}

/* ── Premium Button Hover Effects & Transitions ── */
.stButton > button, .stDownloadButton > button {
    background: rgba(15, 23, 42, 0.6) !important;
    color: #f1f5f9 !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
    border-radius: 8px !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.stButton > button:hover, .stDownloadButton > button:hover {
    background: rgba(16, 185, 129, 0.1) !important;
    border-color: rgba(16, 185, 129, 0.4) !important;
    color: #34d399 !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.1) !important;
}

.stButton > button:active, .stDownloadButton > button:active {
    transform: translateY(0px) !important;
}

/* Primary Button Override */
.stButton > button[kind="primary"] {
    background: #10b981 !important;
    color: #ffffff !important;
    border: none !important;
}

.stButton > button[kind="primary"]:hover {
    background: #059669 !important;
    color: #ffffff !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3) !important;
}

hr { border-color: rgba(255,255,255,0.04) !important; margin: 2rem 0 !important; }
</style>
""", unsafe_allow_html=True)


# ─── UNCACHED DATA LAYER (INSTANT UPDATE DIRECT FROM DB) ────────────────────────
def load_data_uncached():
    db_url = os.getenv("DATABASE_URL")
    empty_anomalies = pd.DataFrame(columns=[
        'date', 'provider', 'service_category', 'team', 'cost_usd', 'is_anomaly', 
        'severity_label', 'severity_score', 'impact_score', 'priority', 'root_cause', 
        'llm_insight', 'recommended_action', 'estimated_savings', 'model_votes'
    ])
    empty_forecasts = pd.DataFrame(columns=['date', 'service_category', 'forecast_50', 'forecast_10', 'forecast_90', 'horizon_days'])
    
    if not db_url:
        return empty_anomalies, empty_forecasts
        
    try:
        db = FinOpsDatabase(db_url)
        anomalies_df = db.fetch_anomalies(limit=10000)
        forecasts_df = db.fetch_forecasts(limit=5000)
        
        if not anomalies_df.empty:
            anomalies_df['date'] = pd.to_datetime(anomalies_df['date'])
        else:
            anomalies_df = empty_anomalies
            
        if not forecasts_df.empty:
            forecasts_df['date'] = pd.to_datetime(forecasts_df['date'])
        else:
            forecasts_df = empty_forecasts
            
        return anomalies_df, forecasts_df
    except Exception:
        return empty_anomalies, empty_forecasts


def load_metrics_uncached():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        return pd.DataFrame()
    try:
        db = FinOpsDatabase(db_url)
        return db.fetch_latest_metrics()
    except Exception:
        return pd.DataFrame()


# ─── PLOTLY BASE CONFIG (HIGH-FIDELITY Obs/Steel) ──────────────────────────────
PLOTLY_BASE = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='Inter', color='#94a3b8', size=11),
    hovermode='x unified',
    margin=dict(l=10, r=10, t=36, b=10),
    legend=dict(
        bgcolor='rgba(15,23,42,0.3)',
        bordercolor='rgba(255,255,255,0.03)',
        borderwidth=1,
        font=dict(size=10, color='#94a3b8')
    ),
    xaxis=dict(
        gridcolor='rgba(255,255,255,0.02)',
        zerolinecolor='rgba(255,255,255,0.03)',
        tickfont=dict(size=10, color='#64748b')
    ),
    yaxis=dict(
        gridcolor='rgba(255,255,255,0.03)',
        zerolinecolor='rgba(255,255,255,0.03)',
        tickfont=dict(size=10, color='#64748b')
    )
)


# ─── PLOTLY CHART BUILDERS ──────────────────────────────────────────────────────
def create_time_series(service_df, anomalies_only):
    """Clean cost line with soft area gradient and circle anomaly indicators"""
    if service_df.empty:
        fig = go.Figure()
        fig.update_layout(**PLOTLY_BASE, height=340)
        return fig

    daily = service_df.groupby('date')['cost_usd'].sum().reset_index()
    # Normalize dates to standard '%Y-%m-%d' string keys for perfect key lookup match
    daily['date_str'] = pd.to_datetime(daily['date']).dt.strftime('%Y-%m-%d')
    daily_map = dict(zip(daily['date_str'], daily['cost_usd']))
    
    fig = go.Figure()

    # Translucent Area Gradient
    fig.add_trace(go.Scatter(
        x=daily['date_str'], y=daily['cost_usd'],
        mode='lines',
        line=dict(color='rgba(16,185,129,0)', width=0),
        fill='tozeroy',
        fillcolor='rgba(16,185,129,0.03)',
        showlegend=False,
        hoverinfo='skip'
    ))

    # Clean spend line
    fig.add_trace(go.Scatter(
        x=daily['date_str'], y=daily['cost_usd'],
        mode='lines',
        name='Spend Baseline',
        line=dict(color='#10b981', width=1.5, shape='spline', smoothing=0.6),
        hovertemplate='<b>%{x|%b %d, %Y}</b><br>Spend: $%{y:,.2f}<extra></extra>'
    ))

    # Small circular markers for anomalies
    sev_config = {
        'high':   {'color': 'rgba(251,113,133,0.5)', 'border': 'rgba(251,113,133,0.9)', 'size': 6},
        'medium': {'color': 'rgba(251,191,36,0.5)', 'border': 'rgba(251,191,36,0.9)', 'size': 5},
        'low':    {'color': 'rgba(52,211,153,0.5)', 'border': 'rgba(52,211,153,0.9)', 'size': 4},
    }

    for sev, cfg in sev_config.items():
        sev_df = anomalies_only[anomalies_only['severity_label'] == sev]
        if sev_df.empty:
            continue

        sev_df = sev_df.copy()
        # Normalize anomaly dates to string keys
        sev_df['date_str'] = pd.to_datetime(sev_df['date']).dt.strftime('%Y-%m-%d')
        sev_df['y_val'] = sev_df['date_str'].map(daily_map)
        sev_df = sev_df.dropna(subset=['y_val']).drop_duplicates(subset=['date_str'])

        fig.add_trace(go.Scatter(
            x=sev_df['date_str'],
            y=sev_df['y_val'],
            mode='markers',
            name=f'{sev.capitalize()} Signal',
            marker=dict(
                color=cfg['color'],
                size=cfg['size'],
                symbol='circle',
                line=dict(color=cfg['border'], width=1.5)
            ),
            hovertemplate=(
                '<b>%{x|%b %d, %Y}</b><br>'
                f'Risk: {sev.upper()}<br>'
                'Spike Cost: $%{y:,.2f}<extra></extra>'
            )
        ))

    fig.update_layout(
        **PLOTLY_BASE,
        title=dict(text='Spend Chronology & Detected Anomalies', font=dict(size=12, color='#cbd5e1', family='Montserrat')),
        height=340,
    )
    return fig


def create_severity_donut(anomalies_only):
    """Obsidian severity breakdown donut"""
    if anomalies_only.empty:
        fig = go.Figure()
        fig.update_layout(**PLOTLY_BASE, height=280)
        return fig

    counts = anomalies_only['severity_label'].value_counts()
    labels = counts.index.tolist()
    values = counts.values.tolist()

    color_map = {'high': '#fb7185', 'medium': '#fbbf24', 'low': '#34d399'}
    colors = [color_map.get(l, '#475569') for l in labels]

    fig = go.Figure(go.Pie(
        labels=[l.upper() for l in labels],
        values=values,
        hole=0.7,
        marker=dict(colors=colors, line=dict(color='#030712', width=3.5)),
        textinfo='none',
        hovertemplate='<b>%{label}</b><br>Incidents: %{value}<br>Share: %{percent}<extra></extra>'
    ))

    total = sum(values)
    fig.update_layout(
        **PLOTLY_BASE,
        height=280,
        showlegend=True,
        annotations=[
            dict(
                text=f"<b style='font-size:24px; color:#ffffff; font-family:Montserrat;'>{total}</b><br><span style='font-size:10px; color:#cbd5e1; font-family:Inter; letter-spacing:1px;'>SIGNALS</span>",
                x=0.5,
                y=0.5,
                xanchor='center',
                yanchor='middle',
                showarrow=False
            )
        ]
    )
    return fig


def create_service_bar(df):
    """Muted overlay bar - cost by service category"""
    if df.empty or 'service_category' not in df.columns:
        fig = go.Figure()
        fig.update_layout(**PLOTLY_BASE, height=280)
        return fig

    agg = df.groupby('service_category')['cost_usd'].sum().sort_values(ascending=True)
    anomaly_agg = df[df['is_anomaly'] == True].groupby('service_category')['cost_usd'].sum()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=agg.index.tolist(),
        x=agg.values.tolist(),
        orientation='h',
        name='Normal Baseline',
        marker=dict(
            color='rgba(16,185,129,0.15)',
            line=dict(color='rgba(16,185,129,0.3)', width=1)
        ),
        hovertemplate='<b>%{y}</b><br>Normal: $%{x:,.0f}<extra></extra>'
    ))

    if not anomaly_agg.empty:
        anomaly_x = [anomaly_agg.get(s, 0) for s in agg.index.tolist()]
        fig.add_trace(go.Bar(
            y=agg.index.tolist(),
            x=anomaly_x,
            orientation='h',
            name='Attributed Anomaly',
            marker=dict(
                color='rgba(52,211,153,0.2)',
                line=dict(color='rgba(52,211,153,0.4)', width=1)
            ),
            hovertemplate='<b>%{y}</b><br>Anomalous: $%{x:,.0f}<extra></extra>'
        ))

    fig.update_layout(
        **PLOTLY_BASE,
        barmode='overlay',
        height=280,
        title=dict(text='Expenditure by Service Category', font=dict(size=12, color='#cbd5e1', family='Montserrat')),
        xaxis_title='',
        yaxis_title='',
    )
    return fig


def create_heatmap(df):
    """Clean average cost intensity heatmap"""
    if df.empty or len(df) < 10 or 'service_category' not in df.columns or 'date' not in df.columns:
        fig = go.Figure()
        fig.update_layout(**PLOTLY_BASE, height=260)
        return fig

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
            [0.0, '#030712'],
            [0.2, '#0f172a'],
            [0.5, '#064e3b'],
            [0.8, '#059669'],
            [1.0, '#34d399']
        ],
        showscale=True,
        colorbar=dict(
            thickness=10,
            len=0.8,
            tickfont=dict(color='#cbd5e1', size=9),
            outlinecolor='rgba(0,0,0,0)'
        ),
        hovertemplate='<b>%{y}</b> — %{x}<br>Avg: $%{z:,.2f}<extra></extra>'
    ))

    fig.update_layout(
        **PLOTLY_BASE,
        title=dict(text='Operational Spend Intensity Matrix', font=dict(size=12, color='#cbd5e1', family='Montserrat')),
        height=260
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False)
    return fig


def create_forecast_chart(hist_df, forecast_df, budget_threshold):
    """90-Day Prophet Forecast with clean transparent band"""
    if hist_df.empty:
        fig = go.Figure()
        fig.update_layout(**PLOTLY_BASE, height=360)
        return fig
        
    fig = go.Figure()

    # Historical
    hist_daily = hist_df.groupby('date')['cost_usd'].sum().reset_index()
    fig.add_trace(go.Scatter(
        x=hist_daily['date'], y=hist_daily['cost_usd'],
        name='Historical Cost',
        line=dict(color='#10b981', width=1.5, shape='spline', smoothing=0.6),
        hovertemplate='<b>%{x|%b %d, %Y}</b><br>Spend: $%{y:,.2f}<extra></extra>'
    ))

    if not forecast_df.empty:
        # 80% Confidence Band
        fig.add_trace(go.Scatter(
            x=forecast_df['date'].tolist() + forecast_df['date'].tolist()[::-1],
            y=forecast_df['forecast_90'].tolist() + forecast_df['forecast_10'].tolist()[::-1],
            fill='toself',
            fillcolor='rgba(16,185,129,0.03)',
            line=dict(color='rgba(0,0,0,0)'),
            name='80% Confidence Range',
            hoverinfo='skip'
        ))

        # P50 Median Forecast Line
        fig.add_trace(go.Scatter(
            x=forecast_df['date'], y=forecast_df['forecast_50'],
            name='P50 Trajectory',
            line=dict(color='#34d399', width=1.5, dash='dash', shape='spline', smoothing=0.6),
            hovertemplate='<b>%{x|%b %d, %Y}</b><br>Forecast: $%{y:,.2f}<extra></extra>'
        ))

    # Daily Budget threshold line
    all_dates = hist_daily['date'].tolist()
    if not forecast_df.empty:
        all_dates += forecast_df['date'].tolist()

    if all_dates:
        daily_budget = budget_threshold / 30
        fig.add_trace(go.Scatter(
            x=[all_dates[0], all_dates[-1]],
            y=[daily_budget, daily_budget],
            name='Daily Budget Bound',
            line=dict(color='rgba(255,255,255,0.25)', width=1, dash='dot'),
            hoverinfo='skip'
        ))

    fig.update_layout(
        **PLOTLY_BASE,
        height=360,
        title=dict(text='Spend Forecast & Budget Projection Bounds', font=dict(size=12, color='#64748b', family='Montserrat')),
    )
    return fig


# ─── ROUTING & MAIN CONTROLLER ──────────────────────────────────────────────────
if not st.session_state.processed:
    # ─── NAVIGATION BAR HEADER ───
    st.markdown("""
<div style="display: flex; justify-content: space-between; align-items: center; padding: 0.8rem 1.8rem; margin-bottom: 1.5rem; background-color: #02050d; border-bottom: 1.5px solid #0f172a; border-radius: 12px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);">
<div style="font-family: 'Montserrat', sans-serif; font-size: 19px; font-weight: 300; color: #f8fafc; letter-spacing: -0.5px; display: flex; align-items: center; gap: 8px;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
<span>FinOps Guard</span>
</div>
</div>
""", unsafe_allow_html=True)

    # ─── WELCOME LANDING PORTAL ───
    col_desc, col_upload = st.columns([1.1, 0.9], gap="large")
    
    with col_desc:
        st.markdown("""
<div class="welcome-container">
<div class="welcome-header">FinOps Guard</div>
<div class="welcome-subtitle">Decision Intelligence &amp; Cost Remediation Engine</div>
<div style="font-family: 'Inter', sans-serif; font-size: 14.8px; color: #cbd5e1; font-weight: 300; line-height: 1.6; margin-bottom: 2rem; letter-spacing: -0.05px;">
    FinOps Guard transforms cloud cost management from reactive monitoring into predictive, explainable intelligence. By analyzing multi-cloud billing telemetry, the platform automatically flags spend anomalies, isolates their exact root causes, and projects future budget trends to help finance and engineering teams optimize spend before cost overruns happen.
</div>
<div style="display: flex; flex-direction: column; gap: 2.2rem; margin-top: 1.5rem;">
    <div style="display: flex; gap: 1.5rem; align-items: flex-start;">
        <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.2); padding: 12px; border-radius: 12px; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.1);">
            <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
        </div>
        <div>
            <div style="font-family: 'Montserrat', sans-serif; font-size: 17.5px; font-weight: 400; color: #ffffff; margin-bottom: 6px; letter-spacing: 0.3px;">Predictive Detection</div>
            <div style="font-family: 'Inter', sans-serif; font-size: 14.5px; color: #cbd5e1; line-height: 1.6; font-weight: 300;">Multi-algorithm detection pipelines that analyze billing telemetry in real-time, catching complex spend anomalies while filtering out normal seasonal spikes.</div>
        </div>
    </div>
    <div style="display: flex; gap: 1.5rem; align-items: flex-start;">
        <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.2); padding: 12px; border-radius: 12px; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.1);">
            <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <circle cx="12" cy="12" r="6"/>
                <circle cx="12" cy="12" r="2"/>
            </svg>
        </div>
        <div>
            <div style="font-family: 'Montserrat', sans-serif; font-size: 17.5px; font-weight: 400; color: #ffffff; margin-bottom: 6px; letter-spacing: 0.3px;">Root-Cause Analysis</div>
            <div style="font-family: 'Inter', sans-serif; font-size: 14.5px; color: #cbd5e1; line-height: 1.6; font-weight: 300;">Instant attribution mapping that identifies the exact services and teams driving cost deviations, providing clear remediation steps and estimated savings.</div>
        </div>
    </div>
    <div style="display: flex; gap: 1.5rem; align-items: flex-start;">
        <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.2); padding: 12px; border-radius: 12px; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.1);">
            <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 3v18h18"/>
                <path d="m18.7 8-5.1 5.2-2.8-2.7L7 14.3"/>
            </svg>
        </div>
        <div>
            <div style="font-family: 'Montserrat', sans-serif; font-size: 17.5px; font-weight: 400; color: #ffffff; margin-bottom: 6px; letter-spacing: 0.3px;">Budget Projections</div>
            <div style="font-family: 'Inter', sans-serif; font-size: 14.5px; color: #cbd5e1; line-height: 1.6; font-weight: 300;">Predictive spend forecasting that models future budget trajectories, alerting teams to potential budget breaches weeks before they occur.</div>
        </div>
    </div>
</div>
</div>
""", unsafe_allow_html=True)
        
    with col_upload:
        if 'pipeline_running' not in st.session_state:
            st.session_state.pipeline_running = False
            
        if not st.session_state.pipeline_running:
            st.markdown("""
<div style="background: rgba(15, 23, 42, 0.4); border: 1px solid rgba(255, 255, 255, 0.04); border-radius: 20px; padding: 2.5rem; backdrop-filter: blur(20px); box-shadow: 0 10px 30px rgba(0,0,0,0.5); margin-top: 2.5rem;">
    <div style="font-family: 'Montserrat', sans-serif; font-size: 18px; font-weight: 400; color: #f1f5f9; margin-bottom: 8px; letter-spacing: 0.5px;">Telemetry Ingestion Portal</div>
    <div style="font-family: 'Inter', sans-serif; font-size: 13px; color: #64748b; margin-bottom: 2rem; font-weight: 300; line-height: 1.4;">Upload a cloud provider billing export dataset or run a simulated analytics demo.</div>
</div>
""", unsafe_allow_html=True)
            
            # Streamlit uploader
            uploaded_file = st.file_uploader("Upload billing CSV", type=['csv'], label_visibility="collapsed")
            
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            
            # Side-by-side action buttons
            btn_col1, btn_col2 = st.columns(2)
            
            with btn_col1:
                sample_data_path = 'data/synthetic/billing_data.csv'
                if os.path.exists(sample_data_path):
                    with open(sample_data_path, 'rb') as f:
                        sample_bytes = f.read()
                    st.download_button(
                        label="Download Sample CSV",
                        data=sample_bytes,
                        file_name="sample_billing_telemetry.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                else:
                    st.button("Download Sample CSV", disabled=True, use_container_width=True)
                    
            with btn_col2:
                run_demo = st.button("Run Demo Pipeline", type="primary", use_container_width=True)

            if uploaded_file is not None or run_demo:
                st.session_state.pipeline_running = True
                if uploaded_file is not None:
                    st.session_state.df_to_run = pd.read_csv(uploaded_file)
                else:
                    st.session_state.df_to_run = pd.read_csv(sample_data_path)
                st.rerun()

        else:
            # Elegant Centered & Upward-Shifted Loading Animation UI with spacious margins
            st.markdown("<div style='height: 4rem;'></div>", unsafe_allow_html=True)
            loading_placeholder = st.empty()
            
            def pipeline_callback(status_msg):
                loading_placeholder.markdown(f"""
<style>
@keyframes pulse_node {{
    0% {{ transform: scale(1); opacity: 0.3; }}
    50% {{ transform: scale(1.1); opacity: 0.9; }}
    100% {{ transform: scale(1); opacity: 0.3; }}
}}
.pulsing-node {{
    width: 110px;
    height: 110px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(16, 185, 129, 0.3) 0%, rgba(16, 185, 129, 0) 70%);
    border: 3px dashed rgba(16, 185, 129, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    animation: pulse_node 1.5s infinite ease-in-out;
    margin: 0 auto 1.5rem;
}}
</style>
<div style="margin-top: 2rem; margin-bottom: 4rem; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center;">
    <div class="pulsing-node">
        <svg width="42" height="42" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
    </div>
    <div style="font-family: 'Montserrat', sans-serif; font-size: 20px; font-weight: 300; color: #f8fafc; letter-spacing: -0.5px; margin-bottom: 0.5rem; text-transform: uppercase;">
        FinOps Guard Engine
    </div>
    <div style="font-family: 'Inter', sans-serif; font-size: 13.5px; color: #10b981; max-width: 450px; line-height: 1.5; font-weight: 300;">
        {status_msg}
    </div>
</div>
""", unsafe_allow_html=True)

            # Clear existing tables first
            try:
                db_url = os.getenv("DATABASE_URL")
                db = FinOpsDatabase(db_url)
                db.clear_all_tables()
            except Exception as e:
                st.error(f"Failed to connect to database: {e}")
                st.session_state.pipeline_running = False
                st.stop()

            # Execute full pipeline with status yields
            from ml.pipeline import run_full_pipeline
            df_input = st.session_state.df_to_run
            results, correlated = run_full_pipeline(df_input, budget_threshold=50000, progress_callback=pipeline_callback)

            # Insert anomalies, forecasts, and metrics
            pipeline_callback("Stage 6: Synchronizing analysis, forecasts, and metrics with database...")
            
            for service, result in results.items():
                anomalies_df = result['anomalies'].copy()
                data_df = result['data'].copy()

                anomalies_df['date'] = data_df['date'].values
                anomalies_df['provider'] = data_df.get('provider', 'AWS')
                anomalies_df['service_category'] = service
                anomalies_df['team'] = data_df.get('team', 'unknown')
                anomalies_df['cost_usd'] = data_df['total_cost'].values

                anomalies_df.rename(columns={'final_anomaly': 'is_anomaly'}, inplace=True)
                if 'vote_count' in anomalies_df.columns:
                    anomalies_df['model_votes'] = anomalies_df['vote_count']
                else:
                    anomalies_df['model_votes'] = 1

                defaults = {
                    "llm_insight": "Normal behavior",
                    "root_cause": "None",
                    "recommended_action": "None",
                    "estimated_savings": "$0",
                    "severity_score": 0.0
                }
                for col, default_val in defaults.items():
                    if col not in anomalies_df.columns:
                        anomalies_df[col] = default_val
                    else:
                        anomalies_df[col] = anomalies_df[col].fillna(default_val)

                anomalies_df["is_anomaly"] = anomalies_df["is_anomaly"].astype(int)
                anomaly_mask = anomalies_df["is_anomaly"] == 1
                anomalies_df["impact_score"] = 0.0
                anomalies_df["priority"] = "P3 - Low"

                anomalies_df.loc[anomaly_mask, "impact_score"] = (
                    anomalies_df.loc[anomaly_mask, "severity_score"] *
                    anomalies_df.loc[anomaly_mask, "cost_usd"]
                )

                def get_priority(row):
                    impact = row["impact_score"]
                    severity = row["severity_score"]
                    if round(severity, 2) >= 1.0 and impact < 1500:
                        return "P1 - High"
                    if impact > 3000:
                        return "P0 - Critical"
                    elif impact > 1500:
                        return "P1 - High"
                    elif impact > 500:
                        return "P2 - Medium"
                    else:
                        return "P3 - Low"

                anomalies_df.loc[anomaly_mask, "priority"] = (
                    anomalies_df.loc[anomaly_mask].apply(get_priority, axis=1)
                )

                if not anomalies_df.empty:
                    db.insert_anomalies(anomalies_df)

                metrics = {
                    "model_name": f"{service}_lightgbm",
                    "f1_score": float(result.get("f1", 0)),
                    "precision_score": float(result.get("precision", 0)),
                    "recall_score": float(result.get("recall", 0)),
                    "mape": float(result.get("mape", 0))
                }
                db.insert_metrics(metrics)

                forecast_df = result.get("forecast")
                if forecast_df is not None and not forecast_df.empty:
                    forecast_df = forecast_df.copy()
                    forecast_df["provider"] = "MULTI"
                    forecast_df["service_category"] = service
                    forecast_df["team"] = "all"
                    forecast_df["horizon_days"] = 90
                    forecast_df.rename(columns={
                        "forecast_50th": "forecast_50",
                        "forecast_90th": "forecast_90",
                        "forecast_10th": "forecast_10"
                    }, inplace=True)
                    forecast_df = forecast_df[[
                        "date", "provider", "service_category", "team",
                        "forecast_50", "forecast_90", "forecast_10", "horizon_days"
                    ]]
                    db.insert_forecasts(forecast_df)

            st.session_state.pipeline_running = False
            st.session_state.processed = True
            st.rerun()

else:
    # ─── ACTIVE DECISION INTERFACE ───
    anomalies_df, forecasts_df = load_data_uncached()
    metrics_df = load_metrics_uncached()

    if anomalies_df.empty:
        st.warning("No operational data loaded in database.")
        if st.sidebar.button("Return to Telemetry Ingestion"):
            st.session_state.processed = False
            st.rerun()
        st.stop()

    # ─── SIDEBAR FILTER PANEL ───
    with st.sidebar:
        st.markdown("""
<div style="margin-bottom: 1.5rem;">
    <div style="font-family: 'Montserrat', sans-serif; font-size: 20px; font-weight: 300; color: #f8fafc; letter-spacing: -1.0px; display: flex; align-items: center; gap: 8px;">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        <span>FinOps Guard</span>
    </div>
</div>
""", unsafe_allow_html=True)

        # Clear Home Page Return Button
        if st.button("← Go to Home Page", use_container_width=True, type="secondary"):
            st.session_state.processed = False
            st.rerun()

        st.markdown("<hr style='margin: 1rem 0 !important;'>", unsafe_allow_html=True)
        st.markdown("<div style='font-family:Montserrat; font-size:11px; color:#cbd5e1; margin-bottom:8px; text-transform:uppercase;'>Operational Filters</div>", unsafe_allow_html=True)

        all_providers = sorted(anomalies_df['provider'].dropna().unique().tolist()) if 'provider' in anomalies_df.columns else []
        all_services = sorted(anomalies_df['service_category'].dropna().unique().tolist()) if 'service_category' in anomalies_df.columns else []

        selected_providers = st.multiselect(
            "Providers",
            options=all_providers,
            default=all_providers
        )

        selected_service = st.selectbox(
            "Service Stream",
            options=all_services if all_services else ["No Data"]
        )

        if not anomalies_df.empty and not anomalies_df['date'].isna().all():
            date_min = anomalies_df['date'].min().date()
            date_max = anomalies_df['date'].max().date()
            date_range = st.date_input(
                "Chronology Filter",
                value=(date_min, date_max),
                min_value=date_min,
                max_value=date_max
            )
        else:
            date_range = None

        st.markdown("<hr style='margin: 1rem 0 !important;'>", unsafe_allow_html=True)
        st.markdown("<div style='font-family:Montserrat; font-size:11px; color:#cbd5e1; margin-bottom:8px; text-transform:uppercase;'>Budget Rules</div>", unsafe_allow_html=True)
        
        budget_threshold = st.number_input(
            "Monthly Target ($)",
            value=50000,
            step=1000
        )

    # ─── HEADER ───
    col_title, col_ts = st.columns([5, 2])
    with col_title:
        st.markdown("""
<div style="margin-bottom: 2rem;">
    <div style="font-family: 'Montserrat', sans-serif; font-size: 38px; font-weight: 200; color: #f8fafc; letter-spacing: -1.5px; line-height: 1.1;">
        FinOps Guard
    </div>
    <div style="font-family: 'Inter', sans-serif; font-size: 12.5px; color: #cbd5e1; font-weight: 300; letter-spacing: 0.5px; margin-top: 4px; text-transform: uppercase;">
        Multi-Cloud Cost Intelligence &amp; Autonomous Audit Engine
    </div>
</div>
""", unsafe_allow_html=True)
    with col_ts:
        st.markdown(f"""
<div style="text-align: right; margin-top: 8px;">
    <div style="font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #475569; letter-spacing: 0.5px; text-transform: uppercase;">Chronology bounds</div>
    <div style="font-family: 'Inter', sans-serif; font-size: 12px; color: #94a3b8; margin-top: 2px;">{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')} UTC</div>
</div>
""", unsafe_allow_html=True)

    # Apply filters
    filtered_df = anomalies_df.copy()
    if selected_providers:
        filtered_df = filtered_df[filtered_df['provider'].isin(selected_providers)]
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        filtered_df = filtered_df[
            (filtered_df['date'].dt.date >= date_range[0]) &
            (filtered_df['date'].dt.date <= date_range[1])
        ]

    # Service filters
    if 'service_category' in filtered_df.columns:
        if filtered_df.empty or selected_service not in filtered_df['service_category'].values:
            service_df = pd.DataFrame(columns=filtered_df.columns)
        else:
            service_df = filtered_df[filtered_df['service_category'] == selected_service]
    else:
        service_df = pd.DataFrame()

    anomalies_only = service_df[service_df['is_anomaly'] == True].copy() if not service_df.empty else pd.DataFrame()

    service_forecast_df = pd.DataFrame()
    if not forecasts_df.empty and 'service_category' in forecasts_df.columns:
        service_forecast_df = forecasts_df[forecasts_df['service_category'] == selected_service].sort_values('date')

    # Calculate metrics
    total_anomalies = int(filtered_df['is_anomaly'].sum()) if not filtered_df.empty else 0
    high_sev_count = int((filtered_df['severity_label'] == 'high').sum()) if not filtered_df.empty else 0
    p0_p1_count = int(filtered_df['priority'].str.contains('P0|P1', na=False).sum()) if not filtered_df.empty and 'priority' in filtered_df.columns else high_sev_count
    
    total_impact = filtered_df['impact_score'].sum() if not filtered_df.empty and 'impact_score' in filtered_df.columns else 0

    # ─── KPI METRICS STRIP ───
    st.markdown(f"""
<div class="kpi-grid">
    <div class="kpi-card kpi-blue">
        <div class="kpi-label">Active Signals</div>
        <div class="kpi-value">{total_anomalies:,}</div>
        <div class="kpi-delta">Filtered historical boundaries</div>
    </div>
    <div class="kpi-card kpi-red">
        <div class="kpi-label">Priority P0 + P1</div>
        <div class="kpi-value">{p0_p1_count:,}</div>
        <div class="kpi-delta">Immediate remediation required</div>
    </div>
    <div class="kpi-card kpi-amber">
        <div class="kpi-label">Cumulative Exposure</div>
        <div class="kpi-value">${total_impact:,.0f}</div>
        <div class="kpi-delta">Attributed monetary risk impact</div>
    </div>
    <div class="kpi-card kpi-green">
        <div class="kpi-label">Target Budget</div>
        <div class="kpi-value">${budget_threshold:,}</div>
        <div class="kpi-delta">Active monthly spend threshold</div>
    </div>
</div>
""", unsafe_allow_html=True)

    if high_sev_count > 0:
        st.markdown(f"""
<div class="alert-strip">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fb7185" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
    <span style="font-family: 'Inter', sans-serif; font-weight:400;">Causal Intelligence Alert: <b>{high_sev_count}</b> critical cost anomalies detected — immediate remediation suggested.</span>
</div>
""", unsafe_allow_html=True)

    # ─── NAVIGATION TABS ───
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Telemetry Matrix",
        "Explainable Causal Attribution",
        "Forecast Trajectory",
        "Service Distribution",
        "Model Calibration"
    ])

    # ═══════════════════════════════════════════════════════════════════════════════
    # TAB 1 — TELEMETRY MATRIX
    # ═══════════════════════════════════════════════════════════════════════════════
    with tab1:
        st.markdown(f'<div class="fg-header-classy" style="margin-top: 1rem;">Anomaly Matrix &bull; {selected_service.upper()}</div>', unsafe_allow_html=True)
        st.markdown('<div class="fg-body-classy" style="margin-bottom: 2rem;">Ensemble voting consensus and anomaly chronological patterns.</div>', unsafe_allow_html=True)

        t_flags = len(anomalies_only)
        if not anomalies_only.empty and 'model_votes' in anomalies_only.columns:
            avg_votes = round(anomalies_only['model_votes'].mean(), 2)
            strong = int((anomalies_only['model_votes'] >= 3).sum())
            weak = int((anomalies_only['model_votes'] < 3).sum())
        else:
            avg_votes, strong, weak = '-', '-', '-'

        m1, m2, m3, m4 = st.columns(4)
        m1.markdown(f'<div class="metric-block"><div class="mb-label">Total Flags</div><div class="mb-value">{t_flags}</div><div class="mb-sub">Consensus incidents</div></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="metric-block"><div class="mb-label">Average Agreement</div><div class="mb-value">{avg_votes}</div><div class="mb-sub">Model votes out of 3</div></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="metric-block"><div class="mb-label">High Confidence</div><div class="mb-value">{strong}</div><div class="mb-sub">Consensus >= 2 models</div></div>', unsafe_allow_html=True)
        m4.markdown(f'<div class="metric-block"><div class="mb-label">Low Confidence</div><div class="mb-value">{weak}</div><div class="mb-sub">Single model signals</div></div>', unsafe_allow_html=True)
        
        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

        chart_col, donut_col = st.columns([7.2, 2.8])
        with chart_col:
            if not service_df.empty:
                fig_ts = create_time_series(service_df, anomalies_only)
                st.plotly_chart(fig_ts, use_container_width=True, key=f"ts_{selected_service}")
            else:
                st.info("No cost telemetry found for current selection.")

        with donut_col:
            st.markdown('<div class="fg-header-classy" style="font-size: 12px; margin-bottom: 4px; text-align: center;">Risk Level Share</div>', unsafe_allow_html=True)
            fig_donut = create_severity_donut(anomalies_only)
            st.plotly_chart(fig_donut, use_container_width=True, key=f"donut_{selected_service}")

            # Elegant pill legends
            if not anomalies_only.empty:
                st.markdown("<div style='display: flex; justify-content: center; gap: 8px; flex-wrap: wrap; margin-top:-10px;'>", unsafe_allow_html=True)
                for sev, cls in [('high','pill-red'),('medium','pill-amber'),('low','pill-green')]:
                    cnt = int((anomalies_only['severity_label'] == sev).sum())
                    if cnt:
                        st.markdown(f'<span class="alert-pill {cls}">{sev.upper()} ({cnt})</span>', unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)
        
        # Correlated anomalies table
        st.markdown('<div class="fg-header-classy">Simultaneous Spiking Patterns</div>', unsafe_allow_html=True)
        st.markdown('<div class="fg-body-classy" style="margin-bottom:1rem;">Dates where multiple operational streams triggered anomalies simultaneously.</div>', unsafe_allow_html=True)

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
                    'Streams Spiking': correlated_events.values,
                    'Telemetry State': ['CRITICAL SYSTEM DEVIATION' if v >= 4 else 'HIGH DIVERGENCE' if v >= 3 else 'ELEVATED FLUCTUATION' for v in correlated_events.values]
                })
                st.dataframe(
                    corr_data.reset_index(drop=True),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No cross-stream simultaneous spiking anomalies detected.")
        else:
            st.info("Insufficient aggregated data for cross-stream pattern analysis.")

    # ═══════════════════════════════════════════════════════════════════════════════
    # TAB 2 — ROOT CAUSE ATTRIBUTION
    # ═══════════════════════════════════════════════════════════════════════════════
    with tab2:
        st.markdown('<div class="fg-header-classy" style="margin-top: 1rem;">Explainable AI Root Cause Attributions</div>', unsafe_allow_html=True)
        st.markdown('<div class="fg-body-classy" style="margin-bottom: 2rem;">SHAP attributions mapping telemetry variance to structural root causes and estimated hard savings.</div>', unsafe_allow_html=True)

        if anomalies_only.empty:
            st.info("System operating normally. No cost anomalies detected in active service category.")
        else:
            # Sort by impact
            display_anomalies = anomalies_only.sort_values(
                'impact_score' if 'impact_score' in anomalies_only.columns else 'cost_usd',
                ascending=False
            ).head(20)

            for _, row in display_anomalies.iterrows():
                sev = str(row.get('severity_label', 'low')).lower()
                sev_cls = {'high': 'sev-high', 'medium': 'sev-medium'}.get(sev, 'sev-low')
                pill_cls = {'high': 'pill-red', 'medium': 'pill-amber'}.get(sev, 'pill-green')
                date_str = row['date'].strftime('%b %d, %Y')
                cost = float(row.get('cost_usd', 0))
                priority = str(row.get('priority', 'P3 - Low'))
                impact = float(row.get('impact_score', 0))

                with st.expander(f"{date_str}  &bull;  ${cost:,.2f}  &bull;  {priority.upper()}", expanded=False):
                    c1, c2 = st.columns([3, 1])

                    with c1:
                        st.markdown(f"""
<div class="alert-card {sev_cls}">
    <div class="alert-date">{date_str}</div>
    <div class="alert-title">{row.get('root_cause', 'Causal Analysis Pending')}</div>
    <div class="alert-body">{row.get('llm_insight', 'No explanation generated.')}</div>
    <div style="margin-top: 10px;">
        <span class="alert-pill {pill_cls}">{sev.upper()} RISK</span>
        <span class="alert-pill pill-blue">{priority.upper()}</span>
        <span class="alert-pill pill-blue">PROVIDER: {row.get('provider', 'N/A').upper()}</span>
        <span class="alert-pill pill-blue">TEAM: {row.get('team', 'N/A').upper()}</span>
    </div>
</div>
""", unsafe_allow_html=True)

                    with c2:
                        action = str(row.get('recommended_action', 'Audit logs.'))
                        savings = str(row.get('estimated_savings', 'N/A'))
                        st.markdown(f"""
<div class="metric-block" style="margin-bottom:8px;">
    <div class="mb-label">Exposure Score</div>
    <div class="mb-value" style="font-size: 18px;">${impact:,.0f}</div>
</div>
<div class="metric-block" style="margin-bottom:8px;">
    <div class="mb-label">Remediation Benefit</div>
    <div class="mb-value" style="font-size: 16px; color:#86efac;">{savings}</div>
</div>
<div class="metric-block">
    <div class="mb-label">Remediation Action</div>
    <div class="mb-value" style="font-size: 11px; font-family:'Inter'; color:#94a3b8; font-weight:300;">{action}</div>
</div>
""", unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════════
    # TAB 3 — PREDICTION ENGINE
    # ═══════════════════════════════════════════════════════════════════════════════
    with tab3:
        st.markdown('<div class="fg-header-classy" style="margin-top: 1rem;">Spend Forecast &amp; Predictive Budget Trajectory</div>', unsafe_allow_html=True)
        st.markdown('<div class="fg-body-classy" style="margin-bottom: 2rem;">Prophet models predicting spend bounds over 7, 30, and 90-day intervals.</div>', unsafe_allow_html=True)

        horizon = st.radio("Forecast Window", ["7-Day", "30-Day", "90-Day"], horizontal=True, index=2)
        horizon_days = {'7-Day': 7, '30-Day': 30, '90-Day': 90}[horizon]

        forecast_subset = service_forecast_df.head(horizon_days) if not service_forecast_df.empty else pd.DataFrame()

        fig_fc = create_forecast_chart(service_df, forecast_subset, budget_threshold)
        st.plotly_chart(fig_fc, use_container_width=True, key=f"fc_{selected_service}")

        if not forecast_subset.empty:
            m1, m2, m3, m4 = st.columns(4)
            proj_total = float(forecast_subset['forecast_50'].sum())
            proj_upper = float(forecast_subset['forecast_90'].sum())
            proj_lower = float(forecast_subset['forecast_10'].sum())
            remaining = budget_threshold - proj_total

            m1.markdown(f'<div class="metric-block"><div class="mb-label">Projected Total ({horizon})</div><div class="mb-value">${proj_total:,.0f}</div><div class="mb-sub">P50 median spending</div></div>', unsafe_allow_html=True)
            m2.markdown(f'<div class="metric-block"><div class="mb-label">Maximum Range Bound</div><div class="mb-value">${proj_upper:,.0f}</div><div class="mb-sub">P90 upper boundary</div></div>', unsafe_allow_html=True)
            m3.markdown(f'<div class="metric-block"><div class="mb-label">Minimum Range Bound</div><div class="mb-value">${proj_lower:,.0f}</div><div class="mb-sub">P10 lower boundary</div></div>', unsafe_allow_html=True)
            
            color_state = "#86efac" if remaining > 0 else "#fca5a5"
            m4.markdown(f'<div class="metric-block"><div class="mb-label">Target Budget Margin</div><div class="mb-value" style="color:{color_state};">${remaining:,.0f}</div><div class="mb-sub">vs. active monthly cap</div></div>', unsafe_allow_html=True)

            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown('<div class="fg-header-classy">Predictive Risk Evaluation</div>', unsafe_allow_html=True)

            proj_30 = float(service_forecast_df.head(30)['forecast_50'].sum()) if not service_forecast_df.empty else 0
            is_breach = proj_30 > budget_threshold
            trajectory = "HIGH TRAJECTORY RISK" if proj_30 > budget_threshold * 0.9 else "ELEVATED RISK" if proj_30 > budget_threshold * 0.7 else "STABLE TRAJECTORY"
            risk_cls = {'HIGH TRAJECTORY RISK': 'risk-high', 'ELEVATED RISK': 'risk-medium', 'STABLE TRAJECTORY': 'risk-low'}.get(trajectory, 'risk-low')
            breach_pct = round(proj_30 / budget_threshold * 100, 1)

            b1, b2 = st.columns([1, 2])
            with b1:
                st.markdown(f'<div class="risk-badge {risk_cls}" style="margin-top: 15px;">{trajectory}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="fg-body-classy" style="margin-top: 12px; font-size:13.5px; color:#94a3b8;">30-Day Projected spend: <b style="color:#f1f5f9;">${proj_30:,.0f}</b> ({breach_pct}% of target threshold)</div>', unsafe_allow_html=True)
            with b2:
                mini_df = service_forecast_df.head(30)
                fig_mini = go.Figure()
                fig_mini.add_trace(go.Bar(
                    x=mini_df['date'], y=mini_df['forecast_50'],
                    marker_color=['rgba(251,113,133,0.5)' if v > budget_threshold/30 else 'rgba(14,165,233,0.3)' for v in mini_df['forecast_50']],
                    hovertemplate='%{x|%b %d}: $%{y:,.0f}<extra></extra>'
                ))
                fig_mini.update_layout(
                    **PLOTLY_BASE,
                    height=160,
                    showlegend=False,
                    title=dict(text='30-Day Projected Spend Distribution', font=dict(size=10, color='#64748b', family='Montserrat'))
                )
                st.plotly_chart(fig_mini, use_container_width=True, key="mini_forecast")
        else:
            st.info("Insufficient forecast telemetry inside database.")

    # ═══════════════════════════════════════════════════════════════════════════════
    # TAB 4 — SERVICE INTELLIGENCE
    # ═══════════════════════════════════════════════════════════════════════════════
    with tab4:
        st.markdown('<div class="fg-header-classy" style="margin-top: 1rem;">Service Expenditure Distribution</div>', unsafe_allow_html=True)
        st.markdown('<div class="fg-body-classy" style="margin-bottom: 2rem;">Spend categories comparative allocation metrics and matrix intensity.</div>', unsafe_allow_html=True)

        bar_col, heat_col = st.columns([1, 1])
        with bar_col:
            fig_bar = create_service_bar(filtered_df)
            st.plotly_chart(fig_bar, use_container_width=True, key="service_distribution_bar")
        with heat_col:
            fig_heat = create_heatmap(filtered_df)
            st.plotly_chart(fig_heat, use_container_width=True, key="service_intensity_heatmap")

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<div class="fg-header-classy">Cloud Provider Allocation Matrix</div>', unsafe_allow_html=True)

        if not filtered_df.empty:
            prov_agg = filtered_df.groupby('provider').agg(
                total_cost=('cost_usd', 'sum'),
                anomaly_count=('is_anomaly', 'sum'),
                avg_daily=('cost_usd', 'mean')
            ).reset_index()

            prov_cols = st.columns(len(prov_agg))
            colors = ['#10b981', '#34d399', '#059669']
            for i, (_, row) in enumerate(prov_agg.iterrows()):
                c = colors[i % len(colors)]
                prov_cols[i].markdown(f"""
                <div class="kpi-card" style="border-top: 2px solid {c}; padding: 18px 20px;">
                    <div class="kpi-label">{row['provider']}</div>
                    <div class="kpi-value" style="font-size:24px;">${row['total_cost']:,.0f}</div>
                    <div class="kpi-delta">{int(row['anomaly_count'])} signals &bull; ${row['avg_daily']:,.0f}/day average</div>
                </div>
                """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════════
    # TAB 5 — MODEL CALIBRATION
    # ═══════════════════════════════════════════════════════════════════════════════
    with tab5:
        st.markdown('<div class="fg-header-classy" style="margin-top: 1rem;">Machine Learning Model Calibration &amp; Performance</div>', unsafe_allow_html=True)
        st.markdown('<div class="fg-body-classy" style="margin-bottom: 2rem;">F1-Score, Precision, and Recall parameters evaluated on standard test datasets.</div>', unsafe_allow_html=True)

        if not metrics_df.empty:
            for _, row in metrics_df.iterrows():
                svc_name = str(row.get('model_name', 'unknown')).replace('_lightgbm', '')
                f1 = float(row.get('f1_score', 0))
                prec = float(row.get('precision_score', 0))
                rec = float(row.get('recall_score', 0))
                mape = float(row.get('mape', 0))

                st.markdown(f'<div style="font-family:\'Montserrat\'; font-size:12px; color:#f8fafc; font-weight:400; text-transform:uppercase; margin-bottom:8px;">{svc_name} models</div>', unsafe_allow_html=True)
                mc1, mc2, mc3, mc4 = st.columns(4)
                
                f1_color = "#10b981" if f1 > 0.8 else "#f59e0b"
                mc1.markdown(f'<div class="metric-block"><div class="mb-label">F1-Score</div><div class="mb-value" style="color:{f1_color};">{f1:.3f}</div><div class="mb-sub">Combined evaluation parameter</div></div>', unsafe_allow_html=True)
                mc2.markdown(f'<div class="metric-block"><div class="mb-label">Precision</div><div class="mb-value">{prec:.3f}</div><div class="mb-sub">Accuracy of anomaly signals</div></div>', unsafe_allow_html=True)
                mc3.markdown(f'<div class="metric-block"><div class="mb-label">Recall</div><div class="mb-value">{rec:.3f}</div><div class="mb-sub">Incident capture rate</div></div>', unsafe_allow_html=True)
                
                mape_color = "#10b981" if mape < 0.15 else "#f59e0b"
                mc4.markdown(f'<div class="metric-block"><div class="mb-label">MAPE</div><div class="mb-value" style="color:{mape_color};">{mape*100:.1f}%</div><div class="mb-sub">Mean Absolute Percentage Error</div></div>', unsafe_allow_html=True)
                st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        else:
            st.info("Run model pipeline to generate calibration logs.")

        st.markdown("<hr>", unsafe_allow_html=True)
        
        # Download Data button
        if not anomalies_only.empty:
            csv = anomalies_only.to_csv(index=False)
            st.download_button(
                label="Export Incidents Telemetry (CSV)",
                data=csv,
                file_name=f"finops_guard_{selected_service}_incidents.csv",
                mime="text/csv",
                use_container_width=True
            )