# ml/anomaly/ensemble.py
import pandas as pd
import numpy as np

def ensemble_anomaly_detection(zscore_results, if_results, lstm_results, threshold=2):
    """3-Layer ensemble: Statistical + Isolation Forest + LSTM Autoencoder"""
    combined = pd.DataFrame({
        'zscore_flag': zscore_results['is_anomaly_zscore'],
        'if_flag': if_results['is_anomaly_if'],
        'lstm_flag': lstm_results['is_anomaly_lstm'],
    })
    
    combined['vote_count'] = combined[['zscore_flag', 'if_flag', 'lstm_flag']].sum(axis=1)
    combined['model_votes'] = combined['vote_count']
    combined['final_anomaly'] = (combined['vote_count'] >= 2).astype(int)
    combined['severity_score'] = (combined['vote_count'] / 3).round(2)
    def get_severity_label(score):
        if score < 0.34:
            return "low"
        elif score < 0.99:   # IMPORTANT
            return "medium"
        else:
            return "high"

    combined['severity_label'] = combined['severity_score'].apply(get_severity_label)
    return combined

def detect_correlated_anomalies(df, date_col='date', cost_col='total_cost'):
    """Cross-service correlation to detect when multiple services spike together."""
    pivot = df.pivot_table(index=date_col, columns='service_category', values=cost_col, aggfunc='sum').fillna(0)
    z_scores = pd.DataFrame()
    for col in pivot.columns:
        z_scores[col] = np.abs((pivot[col] - pivot[col].mean()) / (pivot[col].std() + 1e-9))
    
    high_zscore = (z_scores > 2.0).sum(axis=1)
    correlated_anomalies = (high_zscore >= 2).astype(int)
    
    return pd.DataFrame({
        'date': pivot.index,
        'correlated_anomaly': correlated_anomalies.values,
        'services_spiking': high_zscore.values
    })