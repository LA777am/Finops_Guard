import os
import pandas as pd
import sys
from dotenv import load_dotenv
load_dotenv()

# 🔥 FORCE PROJECT ROOT INTO PATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.pipeline import run_full_pipeline
from db.database import FinOpsDatabase

# ================== LOAD DATA ==================
file_path = "data/synthetic/billing_data.csv"

if not os.path.exists(file_path):
    raise FileNotFoundError("Billing data not found")

df = pd.read_csv(file_path)

print("🚀 Running full ML pipeline ONCE...")

results, correlated = run_full_pipeline(df)

print("📊 Connecting to DB...")

db = FinOpsDatabase(os.getenv("DATABASE_URL"))

total_inserted = 0

# ================== LOOP THROUGH SERVICES ==================
for service, result in results.items():

    anomalies_df = result['anomalies'].copy()
    data_df = result['data'].copy()

    # ---------------- BASE COLUMN ALIGNMENT ----------------
    anomalies_df['date'] = data_df['date'].values
    anomalies_df['provider'] = data_df.get('provider', 'AWS')
    anomalies_df['service_category'] = service
    anomalies_df['team'] = data_df.get('team', 'unknown')
    anomalies_df['cost_usd'] = data_df['total_cost'].values

    # Rename anomaly column
    anomalies_df.rename(columns={'final_anomaly': 'is_anomaly'}, inplace=True)
    
    if 'vote_count' in anomalies_df.columns:
        anomalies_df['model_votes'] = anomalies_df['vote_count']
    else:
        anomalies_df['model_votes'] = 1

    # ---------------- SAFETY: REQUIRED COLUMNS & REMOVE NANS ----------------
    defaults = {
        "llm_insight": "Normal behavior",
        "root_cause": "None",
        "recommended_action": "None",
        "estimated_savings": "$0",
        "severity_score": 0.0
    }

    # ---------------- SAFETY: REQUIRED COLUMNS ----------------
    for col, default_val in defaults.items():
        if col not in anomalies_df.columns:
            anomalies_df[col] = default_val
        else:
            anomalies_df[col] = anomalies_df[col].fillna(default_val)

    # ================== IMPACT + PRIORITY ==================

    # Ensure is_anomaly is numeric (avoid mask bugs)
    anomalies_df["is_anomaly"] = anomalies_df["is_anomaly"].astype(int)

    # Define mask FIRST
    anomaly_mask = anomalies_df["is_anomaly"] == 1

    # Initialize columns
    anomalies_df["impact_score"] = 0.0
    anomalies_df["priority"] = "P3 - Low"

    # Compute impact ONLY for anomalies
    anomalies_df.loc[anomaly_mask, "impact_score"] = (
        anomalies_df.loc[anomaly_mask, "severity_score"] *
        anomalies_df.loc[anomaly_mask, "cost_usd"]
    )

    # Priority logic (row-based)
    def get_priority(row):
        impact = row["impact_score"]
        severity = row["severity_score"]

        # Force high severity to minimum P1
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

    # Apply ONLY to anomalies
    anomalies_df.loc[anomaly_mask, "priority"] = (
        anomalies_df.loc[anomaly_mask].apply(get_priority, axis=1)
    )
        
    print(f"  [DEBUG] Data Prep complete for {service}. Total rows: {len(anomalies_df)}. Anomaly count: {anomalies_df['is_anomaly'].sum()}")
    if 'model_votes' in anomalies_df.columns:
        print(f"  [DEBUG] Vote Distribution for {service}: {anomalies_df['model_votes'].value_counts().to_dict()}")

    # ---------------- DEBUG ANOMALY ROWS ONLY ----------------
    print(f"\n[DEBUG ANOMALY ROWS] {service}")
    print(anomalies_df[anomalies_df["is_anomaly"] == 1][[
        "llm_insight",
        "root_cause",
        "recommended_action",
        "estimated_savings"
    ]].head(5))
    # ---------------- INSERT ----------------
    print(f"Inserting {service} anomalies...")
    print("\n[DEBUG VOTES DISTRIBUTION]")
    print(anomalies_df["model_votes"].value_counts())

    print("\n[DEBUG SEVERITY DISTRIBUTION]")
    print(anomalies_df["severity_label"].value_counts())

    print(anomalies_df[anomalies_df["is_anomaly"] == 1][[
        "cost_usd",
        "severity_score",
        "impact_score",
        "priority"
    ]].head(5))

    anomaly_only_df = anomalies_df.copy()

    inserted = db.insert_anomalies(anomaly_only_df)
    total_inserted += inserted
    # ================== INSERT METRICS ==================
    mape = result.get("mape", 0)
    precision = result.get("precision", 0)
    recall = result.get("recall", 0)
    f1 = result.get("f1", 0)

    metrics = {
        "model_name": f"{service}_lightgbm",
        "f1_score": float(f1),
        "precision_score": float(precision),
        "recall_score": float(recall),
        "mape": float(mape)
    }

    print(f"Inserting {service} metrics...")
    db.insert_metrics(metrics)
    # ================== INSERT FORECAST ==================
    forecast_df = result.get("forecast")

    if forecast_df is not None and not forecast_df.empty:

        forecast_df = forecast_df.copy()

        forecast_df["provider"] = "MULTI"
        forecast_df["service_category"] = service
        forecast_df["team"] = "all"
        forecast_df["horizon_days"] = 90

        # ✅ FIX COLUMN NAMES (CRITICAL)
        forecast_df.rename(columns={
            "forecast_50th": "forecast_50",
            "forecast_90th": "forecast_90",
            "forecast_10th": "forecast_10"
        }, inplace=True)

        forecast_df = forecast_df[[
            "date",
            "provider",
            "service_category",
            "team",
            "forecast_50",
            "forecast_90",
            "forecast_10",
            "horizon_days"
        ]]

        print(f"Inserting {service} forecasts...")
        db.insert_forecasts(forecast_df)

# ================== DONE ==================
print(f"✅ Total inserted rows: {total_inserted}")
print("🔥 PIPELINE COMPLETE — DB IS NOW SOURCE OF TRUTH")