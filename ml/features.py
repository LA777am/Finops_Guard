# ml/features.py
import pandas as pd
import numpy as np
from scipy import stats

def engineer_features(df, cost_col='total_cost', date_col='date'):
    """Create all ML features from time series data with safety nets"""
    df = df.copy().sort_values(date_col)
    
    # Lag features — previous day/week costs (grouped by provider/team/environment)
    df['cost_lag_1'] = df.groupby(['provider', 'team', 'environment'])[cost_col].shift(1)
    df['cost_lag_7'] = df.groupby(['provider', 'team', 'environment'])[cost_col].shift(7)
    df['cost_lag_30'] = df.groupby(['provider', 'team', 'environment'])[cost_col].shift(30)
    
    # Rolling statistics (grouped by provider/team/environment)
    df['rolling_mean_7'] = df.groupby(['provider', 'team', 'environment'])[cost_col].transform(lambda x: x.rolling(7, min_periods=1).mean())
    df['rolling_std_7'] = df.groupby(['provider', 'team', 'environment'])[cost_col].transform(lambda x: x.rolling(7, min_periods=1).std())
    df['rolling_mean_30'] = df.groupby(['provider', 'team', 'environment'])[cost_col].transform(lambda x: x.rolling(30, min_periods=1).mean())
    df['rolling_std_30'] = df.groupby(['provider', 'team', 'environment'])[cost_col].transform(lambda x: x.rolling(30, min_periods=1).std())
    
    # Cost change features (grouped by provider/team/environment)
    df['cost_change_1d'] = df.groupby(['provider', 'team', 'environment'])[cost_col].pct_change(1)
    df['cost_change_7d'] = df.groupby(['provider', 'team', 'environment'])[cost_col].pct_change(7)
    
    # Z-score feature
    df['zscore'] = np.abs(stats.zscore(df[cost_col].fillna(0)))
    
    # Deviation from rolling mean
    df['deviation_from_mean'] = (df[cost_col] - df['rolling_mean_7']) / (df['rolling_std_7'] + 1e-9)
    
    # Time features
    df['day_of_week'] = pd.to_datetime(df[date_col]).dt.dayofweek
    df['month'] = pd.to_datetime(df[date_col]).dt.month
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
    df['is_month_end'] = pd.to_datetime(df[date_col]).dt.is_month_end.astype(int)
    
    # SAFETY NET: Clean up any infinities created by division by zero
    df = df.replace([np.inf, -np.inf], np.nan)
    
    # SAFETY NET: Drop NaNs created by lag features
    df = df.dropna().reset_index(drop=True)
    
    return df