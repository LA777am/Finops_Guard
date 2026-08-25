#!/usr/bin/env python3
"""
Live Data Stream Generator for FinOps Guardian
Continuously generates new billing data to simulate real-time cloud costs
"""

import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def generate_live_record(timestamp):
    """Generate a single billing record for the given timestamp"""
    providers = ['AWS', 'Azure', 'GCP']
    services = ['compute', 'storage', 'networking', 'managed_services']
    teams = ['engineering', 'data', 'devops', 'product']
    environments = ['production', 'staging', 'development']
    
    records = []
    
    for provider in providers:
        for service in services:
            for team in teams:
                # Base cost with time-based variation
                hour = timestamp.hour
                day_of_week = timestamp.weekday()
                
                base_cost = random.uniform(100, 1000)
                
                # Business hours multiplier (higher during work hours)
                if 9 <= hour <= 17 and day_of_week < 5:
                    base_cost *= 1.5
                
                # Weekend reduction
                if day_of_week >= 5:
                    base_cost *= 0.7
                
                # Service-specific multipliers
                if service == "compute":
                    base_cost *= random.uniform(1.2, 1.8)
                elif service == "storage":
                    base_cost *= random.uniform(0.8, 1.2)
                elif service == "networking":
                    base_cost *= random.uniform(0.9, 1.3)
                
                # Add noise
                cost = base_cost + random.gauss(0, 20)
                
                # Anomaly injection (5% chance)
                is_anomaly = 0
                if random.random() < 0.05:
                    cost *= random.uniform(3, 8)
                    is_anomaly = 1
                
                records.append({
                    'date': timestamp,
                    'provider': provider,
                    'service': service,
                    'team': team,
                    'environment': random.choice(environments),
                    'resource_id': f"{provider}-{service}-{random.randint(1000, 9999)}",
                    'cost_usd': max(0, cost),
                    'usage_quantity': random.uniform(1, 1000),
                    'usage_unit': 'hours' if service == 'compute' else 'GB',
                    'region': random.choice(['us-east-1', 'eu-west-1', 'ap-south-1']),
                    'is_anomaly': is_anomaly
                })
    
    return pd.DataFrame(records)


def stream_live_data(interval_seconds=60, output_file='data/synthetic/billing_data.csv'):
    """
    Continuously generate new billing data
    
    Args:
        interval_seconds: Time between data generation cycles
        output_file: Path to output CSV file
    """
    print("=" * 70)
    print("🔴 LIVE DATA STREAM GENERATOR - FinOps Guardian")
    print("=" * 70)
    print(f"📊 Generating new data every {interval_seconds} seconds")
    print(f"💾 Output file: {output_file}")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print("\nPress Ctrl+C to stop\n")
    
    iteration = 0
    
    try:
        last_df = pd.read_csv(output_file)
        last_date = pd.to_datetime(last_df['date'], format='mixed').max()
    except Exception:
        last_date = pd.Timestamp('2025-06-30')
    
    try:
        while True:
            iteration += 1
            # Advance simulated time by 1 day per iteration to seamlessly continue the graph
            current_time = last_date + timedelta(days=iteration)
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Iteration #{iteration} - Generating data for {current_time.strftime('%Y-%m-%d')}...")
            
            # Generate new records
            df = generate_live_record(current_time)
            
            # Check if file exists
            file_exists = os.path.exists(output_file)
            
            # Append to CSV
            df.to_csv(
                output_file,
                mode='a' if file_exists else 'w',
                header=not file_exists,
                index=False
            )
            
            anomaly_count = df['is_anomaly'].sum()
            total_cost = df['cost_usd'].sum()
            
            print(f"  ✅ Added {len(df)} records")
            print(f"  🚨 Anomalies: {anomaly_count}")
            print(f"  💰 Total cost: ${total_cost:,.2f}")
            
            if anomaly_count > 0:
                print(f"  ⚠️  WARNING: {anomaly_count} anomalies detected!")
            
            print(f"  ⏳ Next update in {interval_seconds} seconds...\n")
            
            time.sleep(interval_seconds)
            
    except KeyboardInterrupt:
        print("\n" + "=" * 70)
        print("🛑 Stream generator stopped by user")
        print(f"📊 Total iterations: {iteration}")
        print(f"⏰ Stopped at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Live billing data stream generator')
    parser.add_argument('--interval', type=int, default=60, 
                       help='Seconds between data generation (default: 60)')
    parser.add_argument('--output', type=str, default='data/synthetic/billing_data.csv',
                       help='Output CSV file path')
    
    args = parser.parse_args()
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    stream_live_data(interval_seconds=args.interval, output_file=args.output)
