# data/synthetic/generate_large_scale.py

import pandas as pd
import numpy as np
from faker import Faker
import os

fake = Faker()


N_DAYS = 365
PROVIDERS = ['AWS', 'Azure', 'GCP']
SERVICES = ['compute', 'storage', 'networking', 'managed_services']
TEAMS = [f"team_{i}" for i in range(20)]
ENVIRONMENTS = ['prod', 'staging', 'dev']

# reproducibility
np.random.seed(42)


def generate_large_scale_data():
    records = []
    base_date = pd.Timestamp('2024-01-01')

    # anomaly definitions
    spike_days = [45, 90, 120, 150, 200, 250, 300]
    drift_ranges = [(60, 80), (180, 200)]

    for day in range(N_DAYS):
        current_date = base_date + pd.Timedelta(days=day)

        for provider in PROVIDERS:
            for service in SERVICES:
                for team in TEAMS:

                    # ===== BASE SIGNAL =====
                    base_cost = np.random.uniform(100, 1200)

                    # trend
                    trend = day * np.random.uniform(0.1, 0.5)

                    # weekly seasonality
                    weekly = 60 * np.sin(2 * np.pi * day / 7)

                    # monthly seasonality
                    monthly = 40 * np.sin(2 * np.pi * day / 30)

                    # noise
                    noise = np.random.normal(0, 25)

                    cost = base_cost + trend + weekly + monthly + noise
                    is_anomaly = 0

                    #  SPIKE ANOMALY 
                    if day in spike_days:
                        cost *= np.random.uniform(3.5, 6.0)
                        is_anomaly = 1

                    #  DRIFT ANOMALY 
                    for start, end in drift_ranges:
                        if start <= day <= end:
                            drift_factor = 1 + (day - start) * 0.04
                            cost *= drift_factor
                            is_anomaly = 1

                    records.append({
                        'date': current_date,
                        'provider': provider,
                        'service_category': service,
                        'team': team,
                        'environment': np.random.choice(ENVIRONMENTS, p=[0.6, 0.25, 0.15]),
                        'cost_usd': max(0, cost),
                        'usage_quantity': np.random.uniform(1, 1000),
                        'region': np.random.choice(['us-east-1', 'eu-west-1', 'ap-south-1']),
                        'is_anomaly': is_anomaly
                    })

    df = pd.DataFrame(records)


    # SCALE TO 1M+

    df = pd.concat([df] * 3, ignore_index=True)

    # optimize memory
    df['cost_usd'] = df['cost_usd'].astype('float32')
    df['usage_quantity'] = df['usage_quantity'].astype('float32')
    df['is_anomaly'] = df['is_anomaly'].astype('int8')

    df = df.sort_values('date').reset_index(drop=True)


    # SAVE

    os.makedirs('data/processed', exist_ok=True)
    file_path = 'data/processed/large_billing_data.csv'
    df.to_csv(file_path, index=False)


    # LOGS

    print("=" * 50)
    print(f"DATA GENERATED: {len(df):,} rows")
    print(f"ANOMALIES: {df['is_anomaly'].sum():,}")
    print(f"DATE RANGE: {df['date'].min()} → {df['date'].max()}")
    print(f"SAVED AT: {file_path}")
    print("=" * 50)

    return df



# ENTRY POINT

if __name__ == "__main__":
    generate_large_scale_data()