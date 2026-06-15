import pandas as pd
import numpy as np
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset, TargetDriftPreset, DataQualityPreset

class FraudDriftDetector:
    """
    Monitor for:
    1. Feature drift: distribution shift in input features
    2. Prediction drift: change in model score distribution
    3. Target drift: change in actual fraud rate
    4. Data quality: missing values, outliers, type errors
    """
    def __init__(self, reference_dataset: pd.DataFrame):
        self.reference = reference_dataset
        self.report = Report(metrics=[
            DataDriftPreset(stattest="psi", stattest_threshold=0.2),
            TargetDriftPreset(),
            DataQualityPreset(),
        ])
    
    def check_drift(self, current_data: pd.DataFrame) -> dict:
        self.report.run(
            reference_data=self.reference,
            current_data=current_data
        )
        return self.report.as_dict()
    
    def compute_psi(self, reference: np.ndarray, current: np.ndarray, bins=10) -> float:
        """
        Population Stability Index:
        PSI = Σ (Actual% - Expected%) * ln(Actual% / Expected%)
        """
        ref_hist, bin_edges = np.histogram(reference, bins=bins, density=False)
        curr_hist, _ = np.histogram(current, bins=bin_edges, density=False)
        
        # Avoid zero division
        ref_perc = np.maximum(ref_hist / len(reference), 1e-4)
        curr_perc = np.maximum(curr_hist / len(current), 1e-4)
        
        psi = np.sum((curr_perc - ref_perc) * np.log(curr_perc / ref_perc))
        return float(psi)
