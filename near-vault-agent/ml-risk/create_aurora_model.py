#!/usr/bin/env python3
import requests
import pandas as pd
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import numpy as np
import os

# Minimal working version for Aurora
def create_mock_features():
    return {
        'avg_value': 0.1,
        'std_value': 0.05,
        'max_value': 1.0,
        'avg_gas_used': 21000,
        'std_gas_used': 5000,
        'tx_count': 100,
        'unique_users': 50,
        'avg_time_between_tx': 12,
        'max_time_between_tx': 3600,
        'failed_tx_ratio': 0.01,
        'high_value_tx_ratio': 0.1,
        'repeat_user_ratio': 0.3,
        'weekend_activity_ratio': 0.2,
        'night_activity_ratio': 0.15,
        'avg_tx_per_user': 2.0,
        'max_tx_per_user': 10,
        'gini_coefficient': 0.3,
        'activity_burst_score': 1.0
    }

def main():
    print("🔬 Creating Aurora ML Risk Model")
    
    # Create mock baseline data (5 protocols)
    baseline_data = [create_mock_features() for _ in range(5)]
    df = pd.DataFrame(baseline_data)
    
    # Train model
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df)
    
    model = IsolationForest(contamination=0.1, random_state=42)
    model.fit(X_scaled)
    
    # Get baseline scores
    baseline_scores = model.decision_function(X_scaled).tolist()
    
    # Save with correct format
    os.makedirs("models", exist_ok=True)
    model_data = {
        'model': model,
        'scaler': scaler,
        'baseline_scores': baseline_scores,
        'feature_names': df.columns.tolist()
    }
    
    joblib.dump(model_data, 'models/anomaly_risk_model.joblib')
    print("✅ Aurora ML model created successfully!")
    
    return baseline_scores

if __name__ == "__main__":
    main()
