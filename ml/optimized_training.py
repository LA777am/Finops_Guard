import argparse
import json
import logging
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'
import pickle
import warnings
from typing import Dict, List, Tuple, Any

import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd
import torch
torch.set_num_threads(1)
import torch.nn as nn
from prophet import Prophet
from sklearn.ensemble import IsolationForest
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.svm import OneClassSVM
from torch.utils.data import DataLoader, TensorDataset

# Disable warnings and Optuna logging for clean output
warnings.filterwarnings('ignore')
optuna.logging.set_verbosity(optuna.logging.ERROR)

#####################################################################
# Configuration
#####################################################################
class Config:
    DATA_PATH = "data/synthetic/billing_data.csv"
    ARTIFACTS_DIR = "ml/artifacts"
    TARGET_COL = "is_anomaly"
    COST_COL = "cost_usd"
    DATE_COL = "date"
    GROUP_COLS = ["service", "team"]
    
#####################################################################
# 1) Data Handling & Preprocessing
#####################################################################
def load_and_preprocess_data(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)
    df[Config.DATE_COL] = pd.to_datetime(df[Config.DATE_COL])
    return df

def segment_dataframe(df: pd.DataFrame) -> dict:
    segments = {}
    for (service, team), group in df.groupby(Config.GROUP_COLS):
        segment_id = f"{service}_{team}".replace(" ", "_").lower()
        
        # Resample daily
        group = group.set_index(Config.DATE_COL).resample('D').agg({
            Config.COST_COL: 'sum',
            Config.TARGET_COL: 'max' # if any anomaly occurred that day, mark as anomaly
        }).reset_index()
        
        # zero safe for cost, ffill for others (if we had them)
        group[Config.COST_COL] = group[Config.COST_COL].fillna(0)
        group[Config.TARGET_COL] = group[Config.TARGET_COL].fillna(0)
        
        segments[segment_id] = group
    return segments

def cap_outliers_for_features(series: pd.Series, lower_q=0.01, upper_q=0.99):
    lower = series.quantile(lower_q)
    upper = series.quantile(upper_q)
    return series.clip(lower, upper)

#####################################################################
# 2) Feature Engineering
#####################################################################
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    
    # Optional sorting just in case
    df = df.sort_values(Config.DATE_COL)
    
    cost_capped = cap_outliers_for_features(df[Config.COST_COL])
    
    # Create base + newly requested features
    df['cost_capped'] = cost_capped
    
    for window in [7, 14, 30]:
        df[f'rolling_mean_{window}'] = df['cost_capped'].rolling(window=window, min_periods=1).mean()
        df[f'rolling_std_{window}'] = df['cost_capped'].rolling(window=window, min_periods=1).std().fillna(0)
        
    df['pct_change_1d'] = df['cost_capped'].pct_change(1).fillna(0)
    df['pct_change_7d'] = df['cost_capped'].pct_change(7).fillna(0)
    
    df['ema_7'] = df['cost_capped'].ewm(span=7, adjust=False).mean()
    df['ema_14'] = df['cost_capped'].ewm(span=14, adjust=False).mean()
    
    df['rolling_min_7'] = df['cost_capped'].rolling(window=7, min_periods=1).min()
    df['rolling_max_7'] = df['cost_capped'].rolling(window=7, min_periods=1).max()
    
    # ratio to rolling max
    # safe division
    df['ratio_to_rolling_max_7'] = np.where(
        df['rolling_max_7'] > 0, 
        df['cost_capped'] / df['rolling_max_7'], 
        0
    )
    
    # Z-score base stat
    df['zscore_base'] = np.where(
        df['rolling_std_7'] > 0,
        (df['cost_capped'] - df['rolling_mean_7']) / df['rolling_std_7'],
        0
    )
    
    df = df.dropna()
    df = df.drop(columns=['cost_capped'])
    return df

#####################################################################
# LSTM Architecture & Training
#####################################################################
class LSTMAutoencoder(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int, num_layers: int):
        super().__init__()
        self.encoder = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True)
        self.decoder = nn.LSTM(hidden_dim, input_dim, num_layers, batch_first=True)
    
    def forward(self, x):
        _, (h, c) = self.encoder(x)
        h_rep = h[-1].unsqueeze(1).repeat(1, x.size(1), 1)
        out, _ = self.decoder(h_rep)
        return out

def create_lstm_sequences(data: np.ndarray, seq_len: int):
    xs = []
    for i in range(len(data) - seq_len):
        xs.append(data[i:(i + seq_len)])
    return np.array(xs)

#####################################################################
# 3) Optuna Wrapper Classes
#####################################################################

class ModelTuner:
    def __init__(self, X_train, y_train, X_val, y_val, trials=30):
        self.X_train, self.y_train = X_train, y_train
        self.X_val, self.y_val = X_val, y_val
        self.trials = trials
        
        # Determine if class weight/threshold calib is needed
        self.anomaly_rate = y_train.mean()
        self.needs_calibration = self.anomaly_rate < 0.10

    def tune_isolation_forest(self):
        def objective(trial):
            params = {
                'n_estimators': trial.suggest_int('n_estimators', 100, 400),
                'max_samples': trial.suggest_float('max_samples', 0.5, 1.0),
                'contamination': trial.suggest_float('contamination', 0.01, 0.15),
                'max_features': trial.suggest_float('max_features', 0.5, 1.0),
                'n_jobs': 1,
                'random_state': 42
            }
            model = IsolationForest(**params)
            model.fit(self.X_train)
            
            scores = -model.decision_function(self.X_val) # higher is more anomalous
            
            # calibrate threshold
            best_f1 = 0
            for thresh in np.percentile(scores, np.linspace(80, 99.9, 20)):
                preds = (scores > thresh).astype(int)
                f1 = f1_score(self.y_val, preds, zero_division=0)
                if f1 > best_f1:
                    best_f1 = f1
                    
            trial.set_user_attr("best_thresh", best_f1)
            return best_f1
            
        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=self.trials)
        return study.best_params
        
    def tune_ocsvm(self, X_train_scaled, X_val_scaled):
        def objective(trial):
            params = {
                'kernel': 'rbf',
                'nu': trial.suggest_float('nu', 0.01, 0.2),
                'gamma': trial.suggest_categorical('gamma', ['scale', 'auto'])
            }
            model = OneClassSVM(**params)
            model.fit(X_train_scaled)
            scores = -model.decision_function(X_val_scaled)
            
            best_f1 = 0
            for thresh in np.percentile(scores, np.linspace(80, 99.9, 20)):
                preds = (scores > thresh).astype(int)
                f1 = f1_score(self.y_val, preds, zero_division=0)
                if f1 > best_f1: best_f1 = f1
            return best_f1
            
        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=self.trials)
        return study.best_params

    def tune_lstm(self, X_train_seq, X_val_seq, y_val_seq):
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        def objective(trial):
            hidden_dim = trial.suggest_categorical('hidden_dim', [16, 64])
            num_layers = trial.suggest_int('num_layers', 1, 2)
            lr = trial.suggest_float('lr', 1e-4, 1e-2, log=True)
            epochs = trial.suggest_int('epochs', 10, 25)
            
            # Hardcoded elements for constrained resource
            input_dim = X_train_seq.shape[-1]
            model = LSTMAutoencoder(input_dim, hidden_dim, num_layers).to(device)
            optimizer = torch.optim.Adam(model.parameters(), lr=lr)
            criterion = nn.MSELoss()
            
            X_t = torch.tensor(X_train_seq, dtype=torch.float32).to(device)
            dataset = TensorDataset(X_t)
            loader = DataLoader(dataset, batch_size=32, shuffle=True)
            
            # Quick train loop for optuna
            model.train()
            # If fast_dev and trials are small we could reduce epochs but we honour space
            for _ in range(epochs):
                for (batch,) in loader:
                    optimizer.zero_grad()
                    out = model(batch)
                    loss = criterion(out, batch)
                    loss.backward()
                    optimizer.step()
                    
            model.eval()
            with torch.no_grad():
                X_v = torch.tensor(X_val_seq, dtype=torch.float32).to(device)
                out_v = model(X_v)
                errors = torch.mean((out_v - X_v)**2, dim=(1,2)).cpu().numpy()
                
            best_f1 = 0
            for percentile in [95, 96, 97, 98, 99]:
                thresh = np.percentile(errors, percentile)
                preds = (errors > thresh).astype(int)
                f1 = f1_score(y_val_seq, preds, zero_division=0)
                if f1 > best_f1: best_f1 = f1
                
            return best_f1
            
        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=self.trials)
        return study.best_params

    def tune_lightgbm(self, X_train, y_train, X_val, y_val):
        def objective(trial):
            params = {
                'num_leaves': trial.suggest_int('num_leaves', 15, 63),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.1, log=True),
                'n_estimators': trial.suggest_int('n_estimators', 100, 500),
                'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
                'objective': 'regression',
                'metric': 'mape',
                'n_jobs': 1,
                'verbose': -1
            }
            cb = lgb.early_stopping(stopping_rounds=20, verbose=False)
            model = lgb.LGBMRegressor(**params)
            model.fit(X_train, y_train, eval_set=[(X_val, y_val)], callbacks=[cb])
            
            preds = model.predict(X_val)
            valid_idx = y_val > 0
            mape = np.mean(np.abs((y_val[valid_idx] - preds[valid_idx]) / y_val[valid_idx])) * 100
            if np.isnan(mape): mape = 999.0
            return mape
            
        study = optuna.create_study(direction="minimize")
        study.optimize(objective, n_trials=self.trials)
        return study.best_params

    def tune_prophet(self, df_train, df_val):
        def objective(trial):
            params = {
                'changepoint_prior_scale': trial.suggest_float('changepoint_prior_scale', 0.01, 0.5),
                'seasonality_prior_scale': trial.suggest_float('seasonality_prior_scale', 1.0, 10.0),
                'weekly_seasonality': True,
                'yearly_seasonality': False, 
                'daily_seasonality': False
            }
            model = Prophet(**params)
            model.fit(df_train)
            
            future = model.make_future_dataframe(periods=len(df_val))
            forecast = model.predict(future)
            preds = forecast.tail(len(df_val))['yhat'].values
            
            actuals = df_val['y'].values
            valid_idx = actuals > 0
            
            if np.sum(valid_idx) == 0:
                return 999.0
                
            mape = np.mean(np.abs((actuals[valid_idx] - preds[valid_idx]) / actuals[valid_idx])) * 100
            if np.isnan(mape): mape = 999.0
            return mape
            
        import logging
        logging.getLogger("prophet").setLevel(logging.ERROR)
        logging.getLogger("cmdstanpy").setLevel(logging.ERROR)
        
        study = optuna.create_study(direction="minimize")
        study.optimize(objective, n_trials=min(self.trials, 10)) # Prophet is slow, limit cap
        return study.best_params


#####################################################################
# Orchestrator
#####################################################################
def optimize_segment(segment_id: str, df: pd.DataFrame, trials: int = 30) -> dict:
    print(f"[{segment_id}] Starting optimization...")
    
    if len(df) > 200000:
        df = df.sample(n=200000, random_state=42).sort_values(Config.DATE_COL)
        
    df = engineer_features(df)
    
    split_idx = int(len(df) * 0.8)
    train_df = df.iloc[:split_idx]
    val_df = df.iloc[split_idx:]
    
    features = [c for c in df.columns if c not in [Config.DATE_COL, Config.TARGET_COL, Config.COST_COL]]
    
    X_train, y_train = train_df[features].values, train_df[Config.TARGET_COL].values
    X_val, y_val = val_df[features].values, val_df[Config.TARGET_COL].values
    
    scaler = StandardScaler().fit(X_train)
    X_train_scaled = scaler.transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    
    tuner = ModelTuner(X_train, y_train, X_val, y_val, trials=trials)
    
    # --- IF ---
    print(f"[{segment_id}] Tuning Isolation Forest...")
    best_if_params = tuner.tune_isolation_forest()
    if_model = IsolationForest(**best_if_params, n_jobs=1, random_state=42).fit(X_train)
    if_scores_train = -if_model.decision_function(X_train)
    if_scores_val = -if_model.decision_function(X_val)
    
    # --- OCSVM ---
    print(f"[{segment_id}] Tuning One-Class SVM...")
    best_ocsvm_params = tuner.tune_ocsvm(X_train_scaled, X_val_scaled)
    svm_model = OneClassSVM(**best_ocsvm_params).fit(X_train_scaled)
    svm_scores_train = -svm_model.decision_function(X_train_scaled)
    svm_scores_val = -svm_model.decision_function(X_val_scaled)
    
    # --- LSTM Autoencoder ---
    print(f"[{segment_id}] Tuning LSTM...")
    lstm_cols = [Config.COST_COL, 'rolling_mean_7', 'rolling_std_7', 'pct_change_1d']
    lstm_train_df = train_df[lstm_cols]
    lstm_val_df = val_df[lstm_cols]
    
    lstm_scaler = StandardScaler().fit(lstm_train_df)
    L_train_scaled = lstm_scaler.transform(lstm_train_df)
    L_val_scaled = lstm_scaler.transform(lstm_val_df)
    
    seq_len = 14 
    L_seq_train = create_lstm_sequences(L_train_scaled, seq_len)
    L_seq_val = create_lstm_sequences(L_val_scaled, seq_len)
    y_seq_train = y_train[seq_len:]
    y_seq_val = y_val[seq_len:]
    
    # Check if empty seq 
    if len(L_seq_train) == 0 or len(L_seq_val) == 0:
        raise ValueError(f"Not enough data for LSTM in segment {segment_id}")

    best_lstm_params = tuner.tune_lstm(L_seq_train, L_seq_val, y_seq_val)
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    lstm_model = LSTMAutoencoder(L_seq_train.shape[-1], best_lstm_params['hidden_dim'], best_lstm_params['num_layers']).to(device)
    optimizer = torch.optim.Adam(lstm_model.parameters(), lr=best_lstm_params['lr'])
    criterion = nn.MSELoss()
    
    dataset = TensorDataset(torch.tensor(L_seq_train, dtype=torch.float32).to(device))
    loader = DataLoader(dataset, batch_size=32, shuffle=True)
    
    lstm_model.train()
    for _ in range(best_lstm_params['epochs']):
        for (batch,) in loader:
            optimizer.zero_grad()
            out = lstm_model(batch)
            loss = criterion(out, batch)
            loss.backward()
            optimizer.step()
            
    lstm_model.eval()
    with torch.no_grad():
        X_t_t = torch.tensor(L_seq_train, dtype=torch.float32).to(device)
        lstm_out_train = lstm_model(X_t_t).cpu().numpy()
        lstm_scores_train = np.mean((lstm_out_train - L_seq_train)**2, axis=(1,2))
        
        X_v_v = torch.tensor(L_seq_val, dtype=torch.float32).to(device)
        lstm_out_val = lstm_model(X_v_v).cpu().numpy()
        lstm_scores_val = np.mean((lstm_out_val - L_seq_val)**2, axis=(1,2))
    
    # --- Z-Score Base ---
    z_scores_train = train_df['zscore_base'].abs().values
    z_scores_val = val_df['zscore_base'].abs().values
    
    align_cut = seq_len
    z_tr = z_scores_train[align_cut:]
    if_tr = if_scores_train[align_cut:]
    svm_tr = svm_scores_train[align_cut:]
    lstm_tr = lstm_scores_train
    aligned_y_train = y_train[align_cut:]
    
    z_va = z_scores_val[align_cut:]
    if_va = if_scores_val[align_cut:]
    svm_va = svm_scores_val[align_cut:]
    lstm_va = lstm_scores_val
    aligned_y_val = y_val[align_cut:]
    
    mm_z = MinMaxScaler().fit(z_tr.reshape(-1, 1))
    mm_if = MinMaxScaler().fit(if_tr.reshape(-1, 1))
    mm_svm = MinMaxScaler().fit(svm_tr.reshape(-1, 1))
    mm_lstm = MinMaxScaler().fit(lstm_tr.reshape(-1, 1))
    
    def get_normalized_scores(z, i, s, l):
        return (
            mm_z.transform(z.reshape(-1, 1)).flatten(),
            mm_if.transform(i.reshape(-1, 1)).flatten(),
            mm_svm.transform(s.reshape(-1, 1)).flatten(),
            mm_lstm.transform(l.reshape(-1, 1)).flatten()
        )
        
    z_v_n, if_v_n, svm_v_n, lstm_v_n = get_normalized_scores(z_va, if_va, svm_va, lstm_va)
    z_t_n, if_t_n, svm_t_n, lstm_t_n = get_normalized_scores(z_tr, if_tr, svm_tr, lstm_tr)
    
    # --- Ensemble Tuning via Optuna ---
    print(f"[{segment_id}] Tuning Ensemble Weights...")
    def ensemble_objective(trial):
        w_z = trial.suggest_float('w_z', 0, 1)
        w_if = trial.suggest_float('w_if', 0, 1)
        w_svm = trial.suggest_float('w_svm', 0, 1)
        w_lstm = trial.suggest_float('w_lstm', 0, 1)
        
        total = w_z + w_if + w_svm + w_lstm
        if total == 0: return 0
        w_z, w_if, w_svm, w_lstm = w_z/total, w_if/total, w_svm/total, w_lstm/total
        
        final_scores_val = (w_z*z_v_n + w_if*if_v_n + w_svm*svm_v_n + w_lstm*lstm_v_n)
        
        best_f1 = 0
        for thresh in np.linspace(0.1, 0.9, 20):
            preds = (final_scores_val > thresh).astype(int)
            f1 = f1_score(aligned_y_val, preds, zero_division=0)
            if f1 > best_f1: best_f1 = f1
        return best_f1
        
    ens_study = optuna.create_study(direction="maximize")
    ens_study.optimize(ensemble_objective, n_trials=30)
    
    w = ens_study.best_params
    total_w = w['w_z'] + w['w_if'] + w['w_svm'] + w['w_lstm']
    ensemble_weights = {k: v/total_w for k,v in w.items()}
    
    final_scores_val = (ensemble_weights['w_z']*z_v_n + 
                        ensemble_weights['w_if']*if_v_n + 
                        ensemble_weights['w_svm']*svm_v_n + 
                        ensemble_weights['w_lstm']*lstm_v_n)
                        
    best_ens_f1, best_ens_thresh = 0, 0
    for thresh in np.linspace(0.1, 0.9, 100):
        preds = (final_scores_val > thresh).astype(int)
        f1 = f1_score(aligned_y_val, preds, zero_division=0)
        if f1 > best_ens_f1:
            best_ens_f1 = f1
            best_ens_thresh = thresh
            
    final_val_preds = (final_scores_val > best_ens_thresh).astype(int)
    
    anomaly_scores = final_scores_val[final_val_preds == 1]
    if len(anomaly_scores) > 0:
        q50 = np.percentile(anomaly_scores, 50)
        q80 = np.percentile(anomaly_scores, 80)
    else:
        q50, q80 = 1.0, 1.0
        
    val_precision = precision_score(aligned_y_val, final_val_preds, zero_division=0)
    val_recall = recall_score(aligned_y_val, final_val_preds, zero_division=0)
    val_roc = roc_auc_score(aligned_y_val, final_scores_val) if len(np.unique(aligned_y_val)) > 1 else 0
    
    # --- LightGBM ---
    print(f"[{segment_id}] Tuning LGBM...")
    best_lgbm_params = tuner.tune_lightgbm(X_train, train_df[Config.COST_COL], X_val, val_df[Config.COST_COL])
    lgbm_model = lgb.LGBMRegressor(**best_lgbm_params, objective='regression')
    lgbm_model.fit(X_train, train_df[Config.COST_COL])
    
    # --- Prophet ---
    print(f"[{segment_id}] Tuning Prophet...")
    p_train = pd.DataFrame({'ds': train_df[Config.DATE_COL], 'y': train_df[Config.COST_COL]})
    p_val = pd.DataFrame({'ds': val_df[Config.DATE_COL], 'y': val_df[Config.COST_COL]})
    best_prophet_params = tuner.tune_prophet(p_train, p_val)
    
    final_prophet = Prophet(**best_prophet_params, weekly_seasonality=True).fit(pd.concat([p_train, p_val]))
    
    metrics = {
        'f1': float(best_ens_f1),
        'precision': float(val_precision),
        'recall': float(val_recall),
        'roc_auc': float(val_roc),
        'false_positive_rate': float((sum(final_val_preds) - sum(final_val_preds * aligned_y_val)) / max(sum(aligned_y_val == 0), 1))
    }
    
    return {
        'params': {
             'isolation_forest': best_if_params,
             'ocsvm': best_ocsvm_params,
             'lstm': best_lstm_params,
             'lgbm': best_lgbm_params,
             'prophet': best_prophet_params,
        },
        'ensemble': {
             'weights': ensemble_weights,
             'threshold': float(best_ens_thresh),
             'severity_quantiles': {'q50': float(q50), 'q80': float(q80)}
        },
        'metrics': metrics,
        'models': {
             'if_model': if_model,
             'svm_model': svm_model,
             'lstm_model': lstm_model,
             'lgbm_model': lgbm_model,
             'prophet_model': final_prophet,
             'scalers': {
                  'svm_scaler': scaler,
                  'lstm_scaler': lstm_scaler,
                  'mm_z': mm_z,
                  'mm_if': mm_if,
                  'mm_svm': mm_svm,
                  'mm_lstm': mm_lstm
             }
        }
    }

def main(args):
    print("🚀 Starting FinOps Guardian Optimized Pipeline")
    os.makedirs(Config.ARTIFACTS_DIR, exist_ok=True)
    
    trials = 3 if args.fast_dev else 30
    print(f"Mode: {'Fast Dev (3 trials)' if args.fast_dev else 'Production (30+ trials)'}")
    
    df = load_and_preprocess_data(Config.DATA_PATH)
    segments = segment_dataframe(df)
    
    all_results = {}
    
    for seg_id, seg_df in segments.items():
        if len(seg_df) < 50:
            print(f"Skipping {seg_id} due to insufficient data ({len(seg_df)} rows)")
            continue
            
        try:
            res = optimize_segment(seg_id, seg_df, trials=trials)
            all_results[seg_id] = res
            
            # Save Artifacts for segment
            seg_dir = os.path.join(Config.ARTIFACTS_DIR, seg_id)
            os.makedirs(seg_dir, exist_ok=True)
            
            with open(os.path.join(seg_dir, 'tuned_params.json'), 'w') as f:
                json.dump({
                    'hyperparameters': res['params'],
                    'ensemble': res['ensemble'],
                    'metrics': res['metrics']
                }, f, indent=4)
                
            with open(os.path.join(seg_dir, 'models.pkl'), 'wb') as f:
                # Drop PyTorch model for pickle, save state dict instead
                lstm = res['models'].pop('lstm_model')
                torch.save(lstm.state_dict(), os.path.join(seg_dir, 'lstm.pth'))
                pickle.dump(res['models'], f)
                
        except Exception as e:
            print(f"Error processing segment {seg_id}: {e}")
            continue
            
    # Aggregated metrics for dashboard
    global_metrics = {}
    for s_id, data in all_results.items():
        global_metrics[s_id] = data['metrics']
        
    df_metrics = pd.DataFrame.from_dict(global_metrics, orient='index')
    print("\n================ Metrics ================")
    print(df_metrics)
    
    if not df_metrics.empty:
        df_metrics.to_csv(os.path.join(Config.ARTIFACTS_DIR, 'aggregated_metrics.csv'))
    
    # Save results without models for lightweight global config
    global_config = {k: {'params': v['params'], 'ensemble': v['ensemble'], 'metrics': v['metrics']} for k,v in all_results.items()}
    with open(os.path.join(Config.ARTIFACTS_DIR, 'aggregated_results.pkl'), 'wb') as f:
        pickle.dump(global_config, f)

    print("✅ Pipeline Completed Successfully. Artifacts saved in ML/Artifacts.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fast-dev", action="store_true", help="Run fewer trials for testing")
    args = parser.parse_args()
    main(args)
