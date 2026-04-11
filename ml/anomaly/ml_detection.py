# ml/anomaly/ml_detection.py
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import os

def train_isolation_forest(features_df, contamination=0.05):
    """Train Isolation Forest on engineered cost features."""
    feature_cols = [
        'cost_lag_1', 'cost_lag_7', 'rolling_mean_7', 
        'rolling_std_7', 'cost_change_1d', 'cost_change_7d',
        'deviation_from_mean', 'day_of_week', 'is_weekend'
    ]
    
    available_cols = [c for c in feature_cols if c in features_df.columns]
    X = features_df[available_cols].fillna(0)
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    model = IsolationForest(
        n_estimators=100,
        contamination=contamination,
        random_state=42,
        n_jobs=1
    )   
    model.fit(X_scaled)
    
    predictions = model.predict(X_scaled)
    scores = model.score_samples(X_scaled)
    
    # Ensure directory exists before saving model
    os.makedirs('ml/anomaly/models', exist_ok=True)
    joblib.dump(model, 'ml/anomaly/models/isolation_forest.pkl')
    joblib.dump(scaler, 'ml/anomaly/models/scaler.pkl')
    
    return pd.DataFrame({
        'is_anomaly_if': (predictions == -1).astype(int),
        'anomaly_score_if': -scores 
    }, index=features_df.index)