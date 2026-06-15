import numpy as np
from typing import Dict

class FraudDetectionEnsemble:
    """
    Stacking ensemble with learned weights:
    
    Level 0 (base models):
    - XGBoost score (primary, highest weight)
    - Neural Network score
    - Isolation Forest score
    
    Level 1 (meta-learner):
    - Logistic Regression on out-of-fold base model predictions
    - Learns optimal weighting of models
    """
    def __init__(self, xgb_model, nn_model, if_model, meta_learner=None):
        self.xgb_model = xgb_model
        self.nn_model = nn_model
        self.if_model = if_model
        
        if meta_learner is None:
            self.weights = {"xgb": 0.5, "nn": 0.35, "if": 0.15}
            self.meta_learner = None
        else:
            self.meta_learner = meta_learner
    
    def predict_proba(self, features: np.ndarray) -> float:
        """
        Real-time inference (must complete in <10ms):
        1. XGBoost prediction (TorchScript or native XGB C++ backend)
        2. Neural network prediction (TorchScript, batched)
        3. Isolation Forest prediction
        4. Meta-learner combination
        5. Return final fraud probability score [0,1]
        """
        # Pseudo implementation for illustration
        xgb_score = 0.1 # dummy: self.xgb_model.predict(features)
        nn_score = 0.1  # dummy: self.nn_model(features)
        if_score = 0.1  # dummy: self.if_model.score(features)
        
        if self.meta_learner:
            meta_X = np.array([[xgb_score, nn_score, if_score]])
            final_score = self.meta_learner.predict_proba(meta_X)[0][1]
        else:
            final_score = (
                self.weights["xgb"] * xgb_score +
                self.weights["nn"] * nn_score +
                self.weights["if"] * if_score
            )
            
        return final_score
    
    def get_model_contributions(self, features: np.ndarray) -> Dict:
        """Return individual model scores for debugging"""
        return {
            "xgb": 0.1,
            "nn": 0.1,
            "if": 0.1
        }
