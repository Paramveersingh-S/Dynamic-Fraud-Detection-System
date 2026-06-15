import numpy as np
from sklearn.metrics import brier_score_loss, roc_auc_score, average_precision_score, f1_score
from scipy.stats import ks_2samp

def evaluate_fraud_model(y_true, y_pred_proba, threshold=0.5):
    """
    Compute and return advanced fraud metrics.
    """
    metrics = {}
    metrics['auc_roc'] = float(roc_auc_score(y_true, y_pred_proba))
    metrics['auc_pr'] = float(average_precision_score(y_true, y_pred_proba))
    metrics['brier_score'] = float(brier_score_loss(y_true, y_pred_proba))
    
    preds_binary = (y_pred_proba >= threshold).astype(int)
    metrics['f1_score'] = float(f1_score(y_true, preds_binary))
    
    # Precision@K
    k_vals = [0.001, 0.01, 0.05]
    n = len(y_true)
    sorted_indices = np.argsort(y_pred_proba)[::-1]
    sorted_y = np.array(y_true)[sorted_indices]
    for k in k_vals:
        k_idx = int(n * k)
        if k_idx > 0:
            metrics[f'precision@{k}'] = float(np.sum(sorted_y[:k_idx]) / k_idx)
        else:
            metrics[f'precision@{k}'] = 0.0
            
    # KS Statistic
    fraud_scores = np.array(y_pred_proba)[np.array(y_true) == 1]
    legit_scores = np.array(y_pred_proba)[np.array(y_true) == 0]
    if len(fraud_scores) > 0 and len(legit_scores) > 0:
        ks_stat, _ = ks_2samp(fraud_scores, legit_scores)
        metrics['ks_statistic'] = float(ks_stat)
    else:
        metrics['ks_statistic'] = 0.0
        
    return metrics
