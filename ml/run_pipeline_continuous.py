#!/usr/bin/env python3
"""
Continuous ML Pipeline Runner for FinOps Guardian
Runs the anomaly detection pipeline continuously in a loop
"""

import time
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_continuous_pipeline(interval_seconds=60):
    """
    Run ML pipeline continuously
    
    Args:
        interval_seconds: Time between pipeline executions
    """
    print("=" * 70)
    print("🔄 CONTINUOUS ML PIPELINE - FinOps Guardian")
    print("=" * 70)
    print(f"⏱️  Pipeline interval: {interval_seconds} seconds")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print("\nPress Ctrl+C to stop\n")
    
    iteration = 0
    success_count = 0
    failure_count = 0
    
    try:
        while True:
            iteration += 1
            start_time = time.time()
            
            print("\n" + "=" * 70)
            print(f"🚀 ITERATION #{iteration}")
            print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 70 + "\n")
            
            try:
                # Import here to avoid issues with module reloading
                import pandas as pd
                from ml.pipeline import run_full_pipeline
                from db.database import FinOpsDatabase
                
                # Load data
                file_path = "data/synthetic/billing_data.csv"
                
                if not os.path.exists(file_path):
                    print(f"❌ Data file not found: {file_path}")
                    print("   Make sure generate_live_stream.py is running!")
                    time.sleep(interval_seconds)
                    continue
                
                print("📂 Loading billing data...")
                df = pd.read_csv(file_path).tail(50000)
                print(f"   Loaded {len(df)} records")
                
                # Run pipeline
                print("\n🧠 Running ML pipeline...")
                results, correlated = run_full_pipeline(df)
                
                # Connect to database
                print("\n📊 Connecting to database...")
                db = FinOpsDatabase(os.getenv("DATABASE_URL"))
                
                total_inserted = 0
                
                # Process each service
                for service, result in results.items():
                    print(f"\n  Processing: {service}")
                    
                    anomalies_df = result['anomalies'].copy()
                    data_df = result['data'].copy()
                    
                    # Prepare data
                    anomalies_df['date'] = data_df['date'].values
                    anomalies_df['provider'] = data_df.get('provider', 'AWS')
                    anomalies_df['service_category'] = service
                    anomalies_df['team'] = data_df.get('team', 'unknown')
                    anomalies_df['cost_usd'] = data_df['total_cost'].values
                    
                    anomalies_df.rename(columns={'final_anomaly': 'is_anomaly'}, inplace=True)
                    
                    if 'vote_count' in anomalies_df.columns:
                        anomalies_df['model_votes'] = anomalies_df['vote_count']
                    else:
                        anomalies_df['model_votes'] = 1
                    
                    # Add defaults for missing columns
                    defaults = {
                        "llm_insight": "Normal behavior",
                        "root_cause": "None",
                        "recommended_action": "None",
                        "estimated_savings": "$0",
                        "severity_score": 0.0
                    }
                    
                    for col, default_val in defaults.items():
                        if col not in anomalies_df.columns:
                            anomalies_df[col] = default_val
                        else:
                            anomalies_df[col] = anomalies_df[col].fillna(default_val)
                    
                    # Calculate impact and priority
                    anomalies_df["is_anomaly"] = anomalies_df["is_anomaly"].astype(int)
                    anomaly_mask = anomalies_df["is_anomaly"] == 1
                    
                    anomalies_df["impact_score"] = 0.0
                    anomalies_df["priority"] = "P3 - Low"
                    
                    anomalies_df.loc[anomaly_mask, "impact_score"] = (
                        anomalies_df.loc[anomaly_mask, "severity_score"] *
                        anomalies_df.loc[anomaly_mask, "cost_usd"]
                    )
                    
                    def get_priority(row):
                        impact = row["impact_score"]
                        severity = row["severity_score"]
                        
                        if round(severity, 2) >= 1.0 and impact < 2000:
                            return "P1 - High"
                        if impact > 8000:
                            return "P0 - Critical"
                        elif impact > 5000:
                            return "P1 - High"
                        elif impact > 2000:
                            return "P2 - Medium"
                        else:
                            return "P3 - Low"
                    
                    anomalies_df.loc[anomaly_mask, "priority"] = (
                        anomalies_df.loc[anomaly_mask].apply(get_priority, axis=1)
                    )
                    
                    # Insert only anomalies
                    anomaly_only_df = anomalies_df[anomalies_df["is_anomaly"] == 1].copy()
                    
                    if not anomaly_only_df.empty:
                        inserted = db.insert_anomalies(anomaly_only_df)
                        total_inserted += inserted
                        print(f"    ✅ Inserted {inserted} anomalies")
                    else:
                        print(f"    ℹ️  No anomalies detected")
                        
                    # Insert forecasts
                    if 'forecast' in result and not result['forecast'].empty:
                        forecast_df = result['forecast'].copy()
                        forecast_df['service_category'] = service
                        f_inserted = db.insert_forecasts(forecast_df)
                        print(f"    📈 Inserted {f_inserted} forecast records")
                
                # Calculate execution time
                execution_time = time.time() - start_time
                success_count += 1
                
                print("\n" + "=" * 70)
                print(f"✅ PIPELINE COMPLETED SUCCESSFULLY")
                print(f"   Total anomalies inserted: {total_inserted}")
                print(f"   Execution time: {execution_time:.2f} seconds")
                print(f"   Success rate: {success_count}/{iteration} ({success_count/iteration*100:.1f}%)")
                print("=" * 70)
                
            except Exception as e:
                failure_count += 1
                execution_time = time.time() - start_time
                
                print("\n" + "=" * 70)
                print(f"❌ PIPELINE FAILED")
                print(f"   Error: {str(e)}")
                print(f"   Execution time: {execution_time:.2f} seconds")
                print(f"   Failure rate: {failure_count}/{iteration} ({failure_count/iteration*100:.1f}%)")
                print("=" * 70)
            
            # Wait before next iteration
            wait_time = max(0, interval_seconds - execution_time)
            if wait_time > 0:
                print(f"\n⏳ Waiting {wait_time:.1f} seconds before next iteration...")
                time.sleep(wait_time)
            else:
                print(f"\n⚠️  Pipeline took longer than interval ({execution_time:.1f}s > {interval_seconds}s)")
                print("   Starting next iteration immediately...")
    
    except KeyboardInterrupt:
        print("\n\n" + "=" * 70)
        print("🛑 PIPELINE STOPPED BY USER")
        print("=" * 70)
        print(f"📊 Statistics:")
        print(f"   Total iterations: {iteration}")
        print(f"   Successful: {success_count}")
        print(f"   Failed: {failure_count}")
        print(f"   Success rate: {success_count/iteration*100:.1f}%" if iteration > 0 else "   N/A")
        print(f"⏰ Stopped at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Continuous ML pipeline runner')
    parser.add_argument('--interval', type=int, default=60,
                       help='Seconds between pipeline runs (default: 60)')
    
    args = parser.parse_args()
    
    run_continuous_pipeline(interval_seconds=args.interval)
