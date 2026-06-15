from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Fraud Case Management API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CaseDecision(BaseModel):
    decision: str
    notes: Optional[str] = None
    action: Optional[str] = None

@app.get("/v1/cases")
def get_cases(status: str = "pending", priority: int = 1, limit: int = 50):
    """Returns prioritized review queue, sorted by fraud_score DESC"""
    return [
        {
            "case_id": str(uuid.uuid4()),
            "transaction_id": str(uuid.uuid4()),
            "priority": priority,
            "status": status,
            "fraud_score": 0.89,
            "created_at": datetime.now()
        }
    ]

@app.get("/v1/cases/{case_id}")
def get_case_details(case_id: str):
    """Returns full case details for investigator"""
    return {
        "case_id": case_id,
        "transaction": {
            "amount": 1500.0,
            "merchant_category": "electronics",
            "is_international": True
        },
        "ml_scores": {"xgb": 0.91, "nn": 0.85, "if": 0.72},
        "shap_explanation": {"amount": +0.4, "device_fraud_rate": +0.3, "is_new_device": +0.1},
        "triggered_rules": ["HIGH_AMOUNT_NEW_USER", "RAPID_AMOUNT_ESCALATION"]
    }

@app.post("/v1/cases/{case_id}/decision")
def make_decision(case_id: str, decision: CaseDecision):
    """
    Submit investigator decision:
    -> Update fraud_labels table
    -> Trigger account action (block/unblock)
    -> Feed label back into training pipeline
    """
    return {"status": "success", "message": f"Case {case_id} marked as {decision.decision}"}

@app.get("/v1/analytics/summary")
def get_analytics_summary():
    """Returns business analytics summary"""
    return {
        "fraud_rate_today": 0.0015,
        "cases_resolved_today": 120,
        "avg_review_time_mins": 5.4,
        "precision_at_current_threshold": 0.92,
        "recall_at_current_threshold": 0.65
    }

@app.get("/v1/users/{user_id}/risk_profile")
def get_user_risk_profile(user_id: str):
    """Returns full user risk analysis"""
    return {
        "user_id": user_id,
        "overall_risk": "HIGH",
        "total_fraud_flags_30d": 3,
        "avg_fraud_score_30d": 0.45,
        "account_age_days": 15,
        "known_devices": 2
    }
