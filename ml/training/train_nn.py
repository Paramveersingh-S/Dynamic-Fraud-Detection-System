import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from ml.models.neural_network import FraudNNTrainer
from ml.evaluation.fraud_metrics import evaluate_fraud_model

def main():
    print("Loading data for Neural Network...")
    X_train = pd.DataFrame(np.random.rand(100, 95))
    y_train = pd.Series(np.random.randint(0, 2, 100))
    X_val = pd.DataFrame(np.random.rand(20, 95))
    y_val = pd.Series(np.random.randint(0, 2, 20))
    
    trainer = FraudNNTrainer(input_dim=95)
    print("Starting NN training with Focal Loss...")
    trainer.train(X_train, y_train, X_val, y_val, epochs=5)
    
    print("Evaluating NN...")
    y_pred = trainer.predict_proba(X_val)
    metrics = evaluate_fraud_model(y_val, y_pred)
    print(f"Metrics: {metrics}")
    
    print("NN Training complete!")

if __name__ == "__main__":
    main()
