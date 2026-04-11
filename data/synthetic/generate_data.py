# data/synthetic/generate_data.py
import pandas as pd
import numpy as np
from faker import Faker
import random
import os

fake = Faker()

def generate_cloud_billing_data(days=180, services=None):
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
                    trend = day * random.uniform(0.1, 0.5)
                    seasonality = 50 * np.sin(2 * np.pi * day / 7)  # weekly pattern
                    noise = random.gauss(0, 20)
                    cost = base_cost + trend + seasonality + noise
                    
                    # Inject anomalies at specific points
                    if day in [45, 90, 120, 150]:  # sudden spikes
                        cost *= random.uniform(3, 5)
                    if 60 <= day <= 75:  # gradual drift
                        cost *= (1 + (day - 60) * 0.05)
                    
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
                        'is_anomaly': 1 if (day in [45, 90, 120, 150] or 60 <= day <= 75) else 0
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