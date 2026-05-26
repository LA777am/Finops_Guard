# ml/pipeline.py
import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sklearn.metrics import precision_score, recall_score, f1_score
from ml.anomaly.statistical import zscore_anomaly_detection
from ml.anomaly.ml_detection import train_isolation_forest
from ml.anomaly.deep_learning import train_lstm_autoencoder
from ml.anomaly.ensemble import ensemble_anomaly_detection, detect_correlated_anomalies
from ml.attribution.shap_attribution import train_attribution_model, get_shap_attribution
from ml.forecasting.forecast import (train_prophet_model, prophet_forecast, 
                                      train_lightgbm_model, calculate_budget_breach_probability)
from ml.normalize import normalize_billing_data, aggregate_daily
from ml.features import engineer_features
from ml.llm_wrapper import enrich_with_llm
def run_full_pipeline(raw_df, budget_threshold=50000, progress_callback=None):
    if progress_callback:
        progress_callback("Stage 1: Normalizing billing telemetry...")
    else:
        print("Step 1: Normalizing data...")
    normalized_df = normalize_billing_data(raw_df)
    daily_df = aggregate_daily(normalized_df)
    
    if progress_callback:
        progress_callback("Stage 2: Performing dimensional lag engineering...")
    else:
        print("Step 2: Engineering features...")
    results = {}
    
    for service in daily_df['service_category'].unique():
        try:
            service_df = daily_df[daily_df['service_category'] == service].copy()
            service_df = engineer_features(service_df, cost_col='total_cost')
            
            if len(service_df) < 30:
                if progress_callback:
                    progress_callback(f"  Skipped {service.upper()}: insufficient training data")
                else:
                    print(f"  Skipped {service}: too few records after lags")
                continue
            
            if progress_callback:
                progress_callback(f"Stage 3: Running 3-Layer Ensemble on {service.upper()}...")
            else:
                print(f"  Processing: {service}")
            
            # ANOMALY DETECTION (3 layers)
            zscore_results = zscore_anomaly_detection(service_df['total_cost'])
            if_results = train_isolation_forest(service_df)
            lstm_results = train_lstm_autoencoder(service_df)
            
            ensemble_results = ensemble_anomaly_detection(zscore_results, if_results, lstm_results)
            # Treat zscore as weak ground truth proxy (temporary)
            y_true = zscore_results['is_anomaly_zscore']
            y_pred = ensemble_results['final_anomaly']

            precision = precision_score(y_true, y_pred, zero_division=0)
            recall = recall_score(y_true, y_pred, zero_division=0)
            f1 = f1_score(y_true, y_pred, zero_division=0)
            # ================== LLM ENRICHMENT (ADD THIS BLOCK) ==================


            # Filter anomalies only
            anomaly_mask = ensemble_results['final_anomaly'] == 1
            anomaly_indices = ensemble_results[anomaly_mask].index

            anomaly_rows = service_df.loc[anomaly_indices].copy()
            anomaly_meta = ensemble_results.loc[anomaly_indices].copy()
            
            # Initialize with requested defaults
            ensemble_results["llm_insight"] = "Normal behavior"
            ensemble_results["root_cause"] = "None"
            ensemble_results["recommended_action"] = "None"
            ensemble_results["estimated_savings"] = "$0"
            
            non_empty_anomalies = len(anomaly_rows)
            print(f"  [DEBUG] Executing {non_empty_anomalies} LLM calls for {service}")
            
            if non_empty_anomalies > 0:
                llm_insights = []
                root_causes = []
                actions = []
                savings = []

                for idx in anomaly_rows.index:
                    try:
                        llm_output = enrich_with_llm({
                            "cost": float(anomaly_rows.loc[idx, 'total_cost']),
                            "severity": anomaly_meta.loc[idx, 'severity_label'],
                            "service": service,
                            "team": anomaly_rows.loc[idx].get("team", "unknown")
                        })
                    
                        llm_insights.append(llm_output.get("insight", "Normal behavior"))
                        root_causes.append(llm_output.get("root_cause", "None"))
                        actions.append(llm_output.get("action", "None"))
                        savings.append(llm_output.get("savings", "$0"))
                        
                    except Exception as e:
                        llm_insights.append("No insight")
                        root_causes.append("Unknown")
                        actions.append("Investigate manually")
                        savings.append("N/A")

                # Attach back to ensemble_results safely using the mask
                ensemble_results.loc[anomaly_mask, "llm_insight"] = llm_insights
                ensemble_results.loc[anomaly_mask, "root_cause"] = root_causes
                ensemble_results.loc[anomaly_mask, "recommended_action"] = actions
                ensemble_results.loc[anomaly_mask, "estimated_savings"] = savings

                # ====================================================================
                        
            # ROOT CAUSE + FORECASTING
            if progress_callback:
                progress_callback(f"Stage 4: Running SHAP Attribution & Prophet Forecast on {service.upper()}...")
            rf_model, X_features = train_attribution_model(service_df)
            anomaly_indices = ensemble_results[ensemble_results['final_anomaly'] == 1].index.tolist()
            attributions = get_shap_attribution(rf_model, X_features, anomaly_indices[:10])
            
            prophet_model = train_prophet_model(service_df)
            prophet_pred = prophet_forecast(prophet_model, periods=90)
            
            # LightGBM is trained but Prophet is used for the main 90-day trajectory in the UI
            lgbm_model, lgbm_mape, feat_cols = train_lightgbm_model(service_df)
            breach_info = calculate_budget_breach_probability(prophet_pred, budget_threshold)
            
                
            results[service] = {
                'anomalies': ensemble_results,
                'attributions': attributions,
                'forecast': prophet_pred,
                'breach_info': breach_info,
                'anomaly_count': ensemble_results['final_anomaly'].sum(),
                'data': service_df,
                'mape': lgbm_mape,
                'precision': precision,
                'recall': recall,
                'f1': f1 
            }

        except Exception as e:
            print(f"  ERROR processing {service}: {str(e)} — Skipping this service")
            continue  # Safety net
    
    # Safe correlation detection
    if progress_callback:
        progress_callback("Stage 5: Detecting cross-service correlation patterns...")
    safe_daily_df = daily_df.reset_index() if 'service_category' not in daily_df.columns else daily_df
    correlated = detect_correlated_anomalies(safe_daily_df)
    
    print("Pipeline complete.")
    print(ensemble_results.columns)
    return results, correlated