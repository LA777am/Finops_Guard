# ml/anomaly/statistical.py
import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.tsa.seasonal import seasonal_decompose

def zscore_anomaly_detection(series, threshold=2.5):
    """Z-score based anomaly detection with seasonal decomposition."""
    if len(series) >= 14:  
        try:
            decomposition = seasonal_decompose(series, model='additive', period=7, extrapolate_trend='freq')
            residuals = decomposition.resid.fillna(0)
        except:
            residuals = series
    else:
        residuals = series
    
    z_scores = np.abs(stats.zscore(residuals))
    anomalies = z_scores > threshold
    
    return pd.DataFrame({
        'zscore': z_scores,
        'is_anomaly_zscore': anomalies.astype(int),
        'anomaly_severity': pd.cut(z_scores, 
                                   bins=[-np.inf, 2, 3, 4, np.inf], 
                                   labels=['normal', 'low', 'medium', 'high'])
    }, index=series.index)

def gesd_test(series, max_anomalies=10, alpha=0.05):
    """Generalized ESD test for multiple anomalies."""
    result = pd.Series(0, index=series.index)
    temp_series = series.copy().dropna()
    
    for i in range(max_anomalies):
        n = len(temp_series)
        if n < 3:
            break
            
        mean = temp_series.mean()
        std = temp_series.std(ddof=1)
        if std == 0:
            break
            
        abs_diff = np.abs(temp_series - mean)
        max_idx = abs_diff.idxmax()
        test_stat = abs_diff[max_idx] / std
        
        p = 1 - alpha / (2 * (n - i))
        t = stats.t.ppf(p, n - i - 2)
        critical = t * (n - i) / np.sqrt((n - i - 2 + t**2) * (n - i - 1))
        
        if test_stat > critical:
            result.loc[max_idx] = 1
            temp_series = temp_series.drop(max_idx)
        else:
            break
            
    return result