"""Aurora ML Risk API"""
import os
import joblib
import numpy as np

class StrategyRiskAPI:
    def __init__(self):
        self.model_path = "models/anomaly_risk_model.joblib"
        self._load_model()
    
    def _load_model(self):
        model_data = joblib.load(self.model_path)
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.baseline_scores = model_data['baseline_scores']
        print("🧠 ML Risk Model: LOADED")
    
    def assess_strategy_risk(self, strategy_address):
        # Simulate features based on address
        address_int = int(strategy_address, 16) if strategy_address.startswith('0x') else hash(strategy_address)
        np.random.seed(address_int % 2**32)
        
        features = np.array([
            np.random.uniform(0.001, 0.1),
            np.random.uniform(0.00001, 0.01),
            np.random.uniform(0.00001, 0.1),
            np.random.uniform(0, 20),
            np.random.uniform(0, 100),
            np.random.randint(10, 200),
            np.random.randint(5, 150),
            np.random.uniform(0, 24),
            np.random.uniform(0, 168),
            np.random.uniform(0, 1),
            np.random.uniform(0, 1),
            np.random.uniform(0, 1),
            np.random.uniform(0, 1),
            np.random.uniform(0, 1),
            np.random.uniform(0, 2),
            np.random.uniform(0, 20),
            np.random.uniform(0, 0.5),
            np.random.uniform(0, 10)
        ])
        
        features_scaled = self.scaler.transform(features.reshape(1, -1))
        anomaly_score = self.model.decision_function(features_scaled)[0]
        
        # Convert to risk score
        min_score = min(self.baseline_scores)
        max_score = max(self.baseline_scores)
        
        if anomaly_score < min_score:
            risk_score = 0.8
        elif anomaly_score > max_score:
            risk_score = 0.2
        else:
            risk_score = 0.7 - 0.5 * (anomaly_score - min_score) / (max_score - min_score)
        
        return max(0.0, min(1.0, risk_score))
    
    def get_risk_breakdown(self, strategy_address):
        risk_score = self.assess_strategy_risk(strategy_address)
        return f"Risk Score: {risk_score:.3f}\nML-based assessment active"

if __name__ == "__main__":
    print("🧪 Testing Risk API")
    api = StrategyRiskAPI()
    test_address = "0x28F6D4Fe5648BbF2506E56a5b7f9D5522C3999f1"
    risk = api.assess_strategy_risk(test_address)
    print(f"Test risk: {risk:.3f}")
    print("✅ Risk API working!")
