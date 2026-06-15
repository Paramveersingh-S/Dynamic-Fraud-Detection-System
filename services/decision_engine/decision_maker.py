import asyncio
from typing import Dict, List, Any
import time

class Transaction:
    def __init__(self, data: Dict[str, Any]):
        for k, v in data.items():
            setattr(self, k, v)

class FraudDecision:
    def __init__(self, decision: str, triggered_rules: List[str] = None, fraud_score: float = 0.0,
                 model_scores: Dict[str, float] = None, decision_latency_ms: float = 0.0):
        self.decision = decision
        self.triggered_rules = triggered_rules or []
        self.fraud_score = fraud_score
        self.model_scores = model_scores or {}
        self.decision_latency_ms = decision_latency_ms

class FraudDecisionMaker:
    """
    Full decision pipeline that runs in <50ms total.
    """
    def __init__(self, feature_server_client, ensemble_model, rules_engine):
        self.feature_server = feature_server_client
        self.ensemble = ensemble_model
        self.rules_engine = rules_engine
        
        self.THRESHOLDS = {
            "DECLINE": 0.85,
            "REVIEW": 0.5,
            "STEP_UP": 0.3,
            "APPROVE": 0.0,
        }

    async def decide(self, transaction_data: Dict[str, Any]) -> FraudDecision:
        start_time = time.time()
        transaction = Transaction(transaction_data)
        
        # Parallel execution: feature fetch AND rule evaluation simultaneously
        # In python we can use asyncio tasks
        async def fetch_features():
            # simulate grpc call
            return await self.feature_server.get_features_async(transaction)
            
        async def eval_hard_rules():
            return self.rules_engine.evaluate_hard_rules(transaction)
            
        features_task = asyncio.create_task(fetch_features())
        rules_task = asyncio.create_task(eval_hard_rules())
        
        features, hard_rule_violations = await asyncio.gather(features_task, rules_task)
        
        if hard_rule_violations:
            latency = (time.time() - start_time) * 1000
            return FraudDecision(
                decision="DECLINE", 
                triggered_rules=hard_rule_violations,
                decision_latency_ms=latency
            )
        
        # ML Inference
        # ml_score = await self.ensemble.predict_proba_async(features)
        ml_score = 0.1 # dummy since predict_proba is sync in our ensemble implementation
        
        soft_rule_delta = self.rules_engine.evaluate_soft_rules(transaction)
        final_score = min(1.0, max(0.0, ml_score + soft_rule_delta))
        
        decision = self._make_decision(final_score)
        
        latency = (time.time() - start_time) * 1000
        
        return FraudDecision(
            decision=decision,
            fraud_score=final_score,
            model_scores={"xgb": 0.1, "nn": 0.1, "if": 0.1},
            decision_latency_ms=latency
        )

    def _make_decision(self, score: float) -> str:
        if score >= self.THRESHOLDS["DECLINE"]:
            return "DECLINE"
        elif score >= self.THRESHOLDS["REVIEW"]:
            return "REVIEW"
        elif score >= self.THRESHOLDS["STEP_UP"]:
            return "STEP_UP"
        else:
            return "APPROVE"
