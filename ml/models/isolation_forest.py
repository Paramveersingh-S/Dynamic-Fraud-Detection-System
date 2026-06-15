from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import numpy as np

class FraudIsolationForest:
    """
    Isolation Forest isolates anomalies by random partitioning.
    Anomalies (fraud) are isolated in fewer splits -> shorter path length.
    
    Use as a secondary signal, not primary decision.
    """
    def __init__(self, n_estimators=100, contamination=0.001, random_state=42):
        self.model = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            max_samples="auto",
            random_state=random_state,
            n_jobs=-1
        )
        self.scaler = StandardScaler()
    
    def fit(self, X_train: np.ndarray):
        """Train on NORMAL transactions only (no labels needed)"""
        X_scaled = self.scaler.fit_transform(X_train)
        self.model.fit(X_scaled)
    
    def score(self, X: np.ndarray) -> np.ndarray:
        """
        Returns anomaly score in [0, 1]:
        - 0 = normal
        - 1 = highly anomalous (likely fraud)
        """
        X_scaled = self.scaler.transform(X)
        raw_scores = self.model.score_samples(X_scaled)
        
        # Normalize: convert negative anomaly scores to [0,1]
        norm_scores = (raw_scores - raw_scores.min()) / (raw_scores.max() - raw_scores.min())
        # Invert so 1 is most anomalous
        return 1.0 - norm_scores
