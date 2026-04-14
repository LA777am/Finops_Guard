# data/synthetic/generate_data.py
import pandas as pd
import numpy as np
from faker import Faker
import random
import os

fake = Faker()

def generate_cloud_billing_data(days=365, services=None):
    if services is None:
        services = ['compute', 'storage', 'networking', 'managed_services']
    
    providers = ['AWS', 'Azure', 'GCP']
    teams = ['engineering', 'data', 'devops', 'product']
    environments = ['production', 'staging', 'development']
    
    records = []
    base_date = pd.Timestamp('2025-01-01')
    
    for day in range(days):
        current_date = base_date + pd.Timedelta(days=day)
        
        for provider in providers:
            for service in services:
                for team in teams:
                    # Base cost with trend and seasonality
                    base_cost = random.uniform(100, 1000)

                    # Long-term trend (growth)
                    trend = day * 0.2 + (day // 180) * 50

                    # Weekly seasonality
                    weekly = 50 * np.sin(2 * np.pi * day / 7)

                    # Monthly seasonality
                    monthly = 100 * np.sin(2 * np.pi * day / 30)

                    # Noise
                    noise = random.gauss(0, 20)

                    cost = base_cost + trend + weekly + monthly + noise
                    if service == "compute":
                        cost *= random.uniform(1.2, 1.8)
                    elif service == "storage":
                        cost *= random.uniform(0.8, 1.2)
                    elif service == "networking":
                        cost *= random.uniform(0.9, 1.3)
                    
                    # Weekend effect (lower usage)
                    if current_date.weekday() >= 5:  # Saturday, Sunday
                        cost *= 0.7
                    is_anomaly = 0

                    # Random spikes
                    if random.random() < 0.02:
                        cost *= random.uniform(3, 6)
                        is_anomaly = 1

                    # Gradual drift anomaly
                    if random.random() < 0.01:
                        cost *= (1 + random.uniform(0.5, 1.5))
                        is_anomaly = 1
                    
                    # Rare catastrophic anomaly (0.3%)
                    if random.random() < 0.003:
                        cost *= random.uniform(8, 15)
                        is_anomaly = 1
                    records.append({
                        'date': current_date,
                        'provider': provider,
                        'service': service,
                        'team': team,
                        'environment': random.choice(environments),
                        'resource_id': f"{provider}-{service}-{fake.uuid4()[:8]}",
                        'cost_usd': max(0, cost),
                        'usage_quantity': random.uniform(1, 1000),
                        'usage_unit': 'hours' if service == 'compute' else 'GB',
                        'region': random.choice(['us-east-1', 'eu-west-1', 'ap-south-1']),
                        'is_anomaly': is_anomaly
                    })
    
    df = pd.DataFrame(records)
    
    # Ensure the directory exists before saving
    os.makedirs('data/synthetic', exist_ok=True)
    df.to_csv('data/synthetic/billing_data.csv', index=False)
    
    print(f"Generated {len(df)} records successfully.")
    return df

if __name__ == "__main__":
    df = generate_cloud_billing_data()
    print("Anomaly Distribution:")
    print(df['is_anomaly'].value_counts())