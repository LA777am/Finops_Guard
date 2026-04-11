# ml/attribution/shap_attribution.py
import pandas as pd
import numpy as np
import shap
import joblib
import os
from sklearn.ensemble import RandomForestRegressor

def train_attribution_model(features_df, cost_col='total_cost'):
    """Train Random Forest to predict cost, used for SHAP explainability."""
    feature_cols = [
        'cost_lag_1', 'cost_lag_7', 'rolling_mean_7',
        'rolling_std_7', 'cost_change_1d', 'cost_change_7d',
        'day_of_week', 'month', 'is_weekend', 'is_month_end'
    ]
    
    available_cols = [c for c in feature_cols if c in features_df.columns]
    X = features_df[available_cols].fillna(0)
    y = features_df[cost_col].fillna(0)
    
    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=1)
    model.fit(X, y)
    
    os.makedirs('ml/attribution/models', exist_ok=True)
    joblib.dump(model, 'ml/attribution/models/rf_model.pkl')
    
    return model, X

def get_shap_attribution(model, X, anomaly_indices):
    """Use SHAP to explain contributing factors for detected anomalies."""
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)
    
    attributions = []
    
    for idx in anomaly_indices:
        # Check if the anomaly index exists in our feature set
        if idx not in X.index:
            continue
            
        # Get the integer location of the index
        iloc_idx = X.index.get_loc(idx)
            
        sample_shap = shap_values[iloc_idx]
        feature_names = X.columns.tolist()
        
        attribution_df = pd.DataFrame({
            'feature': feature_names,
            'shap_value': sample_shap,
            'abs_impact': np.abs(sample_shap)
        }).sort_values('abs_impact', ascending=False)
        
        # Map technical features to human-readable root causes
        root_cause_map = {
            'cost_lag_1': 'Previous day cost pattern',
            'cost_lag_7': 'Weekly cost pattern deviation',
            'rolling_mean_7': 'Weekly average baseline shift',
            'rolling_std_7': 'Cost volatility increase',
            'cost_change_1d': 'Sudden daily cost spike',
            'cost_change_7d': 'Week-over-week cost increase',
            'day_of_week': 'Day-of-week pattern anomaly',
            'is_weekend': 'Unexpected weekend activity',
            'is_month_end': 'Month-end billing anomaly'
        }
        
        attribution_df['root_cause'] = attribution_df['feature'].map(root_cause_map).fillna(attribution_df['feature'])
        
        # Failsafe if attribution is empty
        if len(attribution_df) == 0:
            continue
            
        attributions.append({
            'anomaly_index': idx,
            'top_causes': attribution_df.head(3)[['root_cause', 'shap_value', 'abs_impact']].to_dict('records'),
            'primary_cause': attribution_df.iloc[0]['root_cause'],
            'impact_score': attribution_df.iloc[0]['abs_impact']
        })
    
    return attributions