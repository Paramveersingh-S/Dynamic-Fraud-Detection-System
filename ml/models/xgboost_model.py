import xgboost as xgb
import mlflow
import optuna
import shap
import numpy as np
import pandas as pd
from typing import Dict
from sklearn.metrics import average_precision_score, roc_auc_score, precision_score, recall_score, f1_score

class XGBoostFraudModel:
    def __init__(self):
        self.model = None
        self.feature_names = None
        self.threshold = 0.5
    
    def train(self, X_train: pd.DataFrame, y_train: pd.Series, X_val: pd.DataFrame, y_val: pd.Series, mlflow_run_id: str):
        self.feature_names = list(X_train.columns)
        
        # Calculate scale_pos_weight
        negative_count = len(y_train) - y_train.sum()
        positive_count = y_train.sum()
        scale_pos_weight = negative_count / positive_count if positive_count > 0 else 1.0
        
        dtrain = xgb.DMatrix(X_train, label=y_train, feature_names=self.feature_names)
        dval = xgb.DMatrix(X_val, label=y_val, feature_names=self.feature_names)
        
        def objective(trial):
            params = {
                "objective": "binary:logistic",
                "eval_metric": "aucpr",
                "scale_pos_weight": scale_pos_weight,
                "max_depth": trial.suggest_int("max_depth", 3, 10),
                "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
                "subsample": trial.suggest_float("subsample", 0.6, 1.0),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
                "gamma": trial.suggest_float("gamma", 0, 5),
                "alpha": trial.suggest_float("alpha", 0, 10),
                "lambda": trial.suggest_float("lambda", 0, 10)
            }
            
            bst = xgb.train(
                params,
                dtrain,
                num_boost_round=100,
                evals=[(dval, "val")],
                early_stopping_rounds=10,
                verbose_eval=False
            )
            
            preds = bst.predict(dval)
            aucpr = average_precision_score(y_val, preds)
            return aucpr
            
        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=5) # 5 trials for demo purposes
        
        best_params = study.best_params
        best_params["objective"] = "binary:logistic"
        best_params["eval_metric"] = "aucpr"
        best_params["scale_pos_weight"] = scale_pos_weight
        
        self.model = xgb.train(
            best_params,
            dtrain,
            num_boost_round=200,
            evals=[(dval, "val")],
            early_stopping_rounds=20,
            verbose_eval=True
        )
        
    def calibrate_threshold(self, X_val, y_val, target_precision: float = 0.9):
        dval = xgb.DMatrix(X_val, feature_names=self.feature_names)
        preds = self.model.predict(dval)
        
        # Simple threshold search
        thresholds = np.arange(0.1, 1.0, 0.05)
        best_thresh = 0.5
        best_recall = 0.0
        
        for t in thresholds:
            p = (preds >= t).astype(int)
            prec = precision_score(y_val, p, zero_division=0)
            rec = recall_score(y_val, p, zero_division=0)
            if prec >= target_precision and rec > best_recall:
                best_recall = rec
                best_thresh = t
                
        self.threshold = best_thresh
        return self.threshold
    
    def explain(self, X: np.ndarray, transaction_id: str) -> Dict:
        explainer = shap.TreeExplainer(self.model)
        shap_values = explainer.shap_values(X)
        
        # Format top 5 features
        top_idx = np.argsort(np.abs(shap_values[0]))[-5:][::-1]
        explanation = {self.feature_names[i]: float(shap_values[0][i]) for i in top_idx}
        return {"transaction_id": transaction_id, "top_features": explanation}
    
    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
        dtest = xgb.DMatrix(X_test, feature_names=self.feature_names)
        preds = self.model.predict(dtest)
        preds_binary = (preds >= self.threshold).astype(int)
        
        metrics = {
            "auc_roc": roc_auc_score(y_test, preds),
            "auc_pr": average_precision_score(y_test, preds),
            "f1_score": f1_score(y_test, preds_binary)
        }
        return metrics
