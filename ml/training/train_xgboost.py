import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from ml.models.xgboost_model import XGBoostFraudModel
from ml.evaluation.fraud_metrics import evaluate_fraud_model
from ml.experiments.mlflow_setup import DualLogger

def main():
    print("Loading data for XGBoost...")
    # In a real scenario, this loads from the offline feature store (Snowflake/Parquet)
    # X_train, y_train = load_data('train')
    # X_val, y_val = load_data('val')
    
    # Dummy data for the script to be structurally complete
    X_train = pd.DataFrame(np.random.rand(100, 95), columns=[f"feat_{i}" for i in range(95)])
    y_train = pd.Series(np.random.randint(0, 2, 100))
    X_val = pd.DataFrame(np.random.rand(20, 95), columns=[f"feat_{i}" for i in range(95)])
    y_val = pd.Series(np.random.randint(0, 2, 20))
    
    logger = DualLogger("xgboost_training")
    
    model = XGBoostFraudModel()
    print("Starting XGBoost training with Optuna hyperparameter search...")
    model.train(X_train, y_train, X_val, y_val, mlflow_run_id="run_123")
    
    print("Calibrating threshold...")
    model.calibrate_threshold(X_val, y_val, target_precision=0.9)
    
    print("Evaluating model...")
    metrics = evaluate_fraud_model(y_val, model.model.predict(X_val))
    
    logger.log_metrics(metrics)
    logger.log_model(model.model, "xgboost_champion")
    
    print("Training complete!")

if __name__ == "__main__":
    main()
