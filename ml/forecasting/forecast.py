# ml/forecasting/forecast.py
import pandas as pd
import numpy as np
from prophet import Prophet
import lightgbm as lgb
from sklearn.metrics import mean_absolute_percentage_error
import warnings
import logging

# Suppress Prophet's extremely noisy cmdstanpy logs
logger = logging.getLogger('cmdstanpy')
logger.addHandler(logging.NullHandler())
logger.propagate = False
logger.setLevel(logging.CRITICAL)
warnings.filterwarnings('ignore')

def train_prophet_model(df, date_col='date', cost_col='total_cost'):
    """Train Facebook Prophet for time-series forecasting."""
    prophet_df = df[[date_col, cost_col]].rename(
        columns={date_col: 'ds', cost_col: 'y'}
    )
    
    model = Prophet(
        yearly_seasonality=False, # Set to False since we only have 180 days of data
        weekly_seasonality=True,
        daily_seasonality=False,
        interval_width=0.8,  # 80% confidence interval
        changepoint_prior_scale=0.05
    )
    
    model.fit(prophet_df)
    return model

def prophet_forecast(model, periods=90):
    """Generate forecasts for 90 days"""
    future = model.make_future_dataframe(periods=periods)
    forecast = model.predict(future)
    
    result = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(periods)
    result.columns = ['date', 'forecast_50th', 'forecast_10th', 'forecast_90th']
    result['forecast_10th'] = result['forecast_10th'].clip(lower=0)
    result['forecast_50th'] = result['forecast_50th'].clip(lower=0)
    result['forecast_90th'] = result['forecast_90th'].clip(lower=0)
        
    return result

def train_lightgbm_model(features_df, cost_col='total_cost', test_days=30):
    """Train LightGBM for gradient-boosted forecasting."""
    feature_cols = [
        'cost_lag_1', 'cost_lag_7', 'cost_lag_30',
        'rolling_mean_7', 'rolling_mean_30',
        'rolling_std_7', 'cost_change_1d', 'cost_change_7d',
        'day_of_week', 'month', 'week_of_year',
        'is_weekend', 'is_month_end'
    ]
    
    available_cols = [c for c in feature_cols if c in features_df.columns]
    
    # Train/test split
    train = features_df.iloc[:-test_days]
    test = features_df.iloc[-test_days:]
    
    X_train = train[available_cols].fillna(0)
    y_train = train[cost_col].fillna(0)
    X_test = test[available_cols].fillna(0)
    y_test = test[cost_col].fillna(0)
    
    model = lgb.LGBMRegressor(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=6,
        random_state=42,
        n_jobs=1,
        verbose=-1
    )
    
    model.fit(X_train, y_train,
              eval_set=[(X_test, y_test)],
              callbacks=[lgb.early_stopping(50, verbose=False)])
    
    y_pred = model.predict(X_test)
    mape = mean_absolute_percentage_error(y_test, y_pred)
    
    return model, mape, available_cols

def calculate_budget_breach_probability(forecast_df, budget_threshold):
    """Calculate probability and estimated date of budget breach (Bug-fixed)."""
    cumulative_spend = forecast_df['forecast_50th'].cumsum()
    cumulative_upper = forecast_df['forecast_90th'].cumsum()
    
    # Find first day cumulative spend exceeds budget
    breach_50 = cumulative_spend[cumulative_spend >= budget_threshold]
    breach_90 = cumulative_upper[cumulative_upper >= budget_threshold]
    
    # SAFE DATE EXTRACTION: Look up the actual 'date' column using the row index
    if not breach_50.empty:
        # Get the date from the dataframe and format it
        date_val = forecast_df.loc[breach_50.index[0], 'date']
        breach_date_50 = date_val.strftime('%Y-%m-%d')
    else:
        breach_date_50 = "No Breach Predicted"
        
    if not breach_90.empty:
        date_val_90 = forecast_df.loc[breach_90.index[0], 'date']
        breach_date_90 = date_val_90.strftime('%Y-%m-%d')
    else:
        breach_date_90 = "No Breach Predicted"
    
    # Probability: what % of forecast scenarios exceed budget threshold on a daily basis
    total_days = len(forecast_df)
    days_above_budget = (forecast_df['forecast_50th'] > (budget_threshold / 30)).sum()
    probability = round(days_above_budget / total_days * 100, 1)
    
    return {
        'breach_probability': probability,
        'estimated_breach_date_50th': breach_date_50,
        'estimated_breach_date_90th': breach_date_90,
        'current_trajectory': 'HIGH RISK' if probability > 70 else 'MEDIUM RISK' if probability > 40 else 'LOW RISK'
    }