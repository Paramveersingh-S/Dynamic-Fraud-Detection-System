import mlflow
import wandb
from typing import Dict, Any

class DualLogger:
    """
    Track experiments in BOTH MLflow AND W&B simultaneously:
    MLflow: primary model registry, artifact storage
    W&B: rich visualization, hyperparameter sweeps, model comparisons
    """
    def __init__(self, experiment_name: str):
        mlflow.set_experiment(experiment_name)
        wandb.init(project="fraud-detection", name=experiment_name)
    
    def log_metrics(self, metrics: Dict[str, float], step: int = None):
        mlflow.log_metrics(metrics, step=step)
        wandb.log(metrics, step=step)
    
    def log_model(self, model, model_name: str):
        # Log to MLflow
        try:
            import xgboost as xgb
            if isinstance(model, xgb.Booster):
                mlflow.xgboost.log_model(model, model_name)
        except ImportError:
            pass
            
        # Log to W&B
        artifact = wandb.Artifact(model_name, type="model")
        wandb.log_artifact(artifact)
    
    def log_confusion_matrix(self, y_true, y_pred, labels):
        wandb.log({"conf_mat": wandb.plot.confusion_matrix(probs=None,
                                                          y_true=y_true, 
                                                          preds=y_pred,
                                                          class_names=labels)})
