# ml/normalize.py
import pandas as pd
import numpy as np

SERVICE_MAPPING = {
    # AWS services
    'Amazon EC2': 'compute', 'Amazon S3': 'storage', 'Amazon RDS': 'managed_services', 'Amazon CloudFront': 'networking', 'AWS Lambda': 'compute',
    # Azure services
    'Virtual Machines': 'compute', 'Blob Storage': 'storage', 'Azure SQL': 'managed_services', 'Azure CDN': 'networking',
    # GCP services
    'Compute Engine': 'compute', 'Cloud Storage': 'storage', 'Cloud SQL': 'managed_services', 'Cloud CDN': 'networking',
}

def normalize_billing_data(df):
    """Normalize raw billing data to unified schema"""
    # Map service names (handles both raw cloud data and our synthetic data)
    if 'service_name' in df.columns:
        df['service_category'] = df['service_name'].map(SERVICE_MAPPING).fillna('other')
    elif 'service' in df.columns:
        df['service_category'] = df['service']
    else:
        df['service_category'] = 'other'
        
    df['date'] = pd.to_datetime(df['date'])
    
    # Clean money values
    df['cost_usd'] = df['cost_usd'].fillna(0).clip(lower=0)
    df['team'] = df['team'].fillna('unknown')
    df['environment'] = df['environment'].fillna('unknown')
    
    # Add base time features
    df['day_of_week'] = df['date'].dt.dayofweek
    df['day_of_month'] = df['date'].dt.day
    df['month'] = df['date'].dt.month
    df['week_of_year'] = df['date'].dt.isocalendar().week.astype(int)
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
    
    df = df.sort_values('date').reset_index(drop=True)
    return df

def aggregate_daily(df):
    """Aggregate to daily cost per service/team"""
    agg_funcs = {
        'total_cost': pd.NamedAgg(column='cost_usd', aggfunc='sum'),
        'avg_cost': pd.NamedAgg(column='cost_usd', aggfunc='mean'),
        'record_count': pd.NamedAgg(column='cost_usd', aggfunc='count')
    }
    
    # Keep anomaly flags if they exist (for testing)
    if 'is_anomaly' in df.columns:
        agg_funcs['is_anomaly'] = pd.NamedAgg(column='is_anomaly', aggfunc='max')
        
    daily = df.groupby(['date', 'provider', 'service_category', 'team', 'environment']).agg(**agg_funcs).reset_index()
    return daily

def create_time_series(df, groupby_cols=['date', 'service_category']):
    """Create aggregated time series for anomaly detection"""
    ts = df.groupby(groupby_cols)['total_cost'].sum().reset_index()
    ts = ts.sort_values('date')
    return ts