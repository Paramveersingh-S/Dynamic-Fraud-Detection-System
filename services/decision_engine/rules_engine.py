from typing import Callable, List, Dict

class Rule:
    def __init__(self, name: str, condition: Callable, score_delta: float = 0.0):
        self.name = name
        self.condition = condition
        self.score_delta = score_delta

# Simulated blocklists
blocklist = {"card_123", "card_456"}
OFAC_SANCTIONED_COUNTRIES = {"CU", "IR", "KP", "SY", "RU"}
fraud_device_list = {"device_999", "device_666"}
trusted_merchants = {"merch_amazon", "merch_apple"}

HARD_BLOCK_RULES = [
    Rule("BLOCKED_CARD", condition=lambda t: getattr(t, 'card_id', '') in blocklist),
    Rule("SANCTIONED_COUNTRY", condition=lambda t: getattr(t, 'country', '') in OFAC_SANCTIONED_COUNTRIES),
    Rule("IMPOSSIBLE_VELOCITY", condition=lambda t: getattr(t, 'txns_in_1_second', 0) > 5),
    Rule("KNOWN_FRAUD_DEVICE", condition=lambda t: getattr(t, 'device_fingerprint', '') in fraud_device_list),
]

SOFT_RULES = [
    Rule("HIGH_AMOUNT_NEW_USER", 
         condition=lambda t: getattr(t, 'amount', 0) > 1000 and getattr(t, 'user_account_age_days', 999) < 30,
         score_delta=+0.3),
    Rule("FIRST_INTERNATIONAL",
         condition=lambda t: getattr(t, 'is_international', False) and getattr(t, 'user_international_count', 1) == 0,
         score_delta=+0.2),
    Rule("RAPID_AMOUNT_ESCALATION",
         condition=lambda t: getattr(t, 'amount', 0) > 10 * getattr(t, 'user_avg_txn_amount_30d', float('inf')),
         score_delta=+0.25),
    Rule("LATE_NIGHT_HIGH_AMOUNT",
         condition=lambda t: getattr(t, 'hour', 12) in range(1, 5) and getattr(t, 'amount', 0) > 500,
         score_delta=+0.15),
    Rule("CARD_TESTING_PATTERN",
         condition=lambda t: getattr(t, 'amount', 100) < 1.0 and getattr(t, 'user_txn_count_5min', 0) > 3,
         score_delta=+0.4),
    Rule("VERIFIED_MERCHANT",
         condition=lambda t: getattr(t, 'merchant_id', '') in trusted_merchants,
         score_delta=-0.1),
]

THRESHOLDS = {
    "DECLINE": 0.85,    # Auto-decline
    "REVIEW": 0.5,      # Send to human review queue
    "STEP_UP": 0.3,     # Request 3D Secure / additional auth
    "APPROVE": 0.0,     # Auto-approve below this
}

class RulesEngine:
    def evaluate_hard_rules(self, transaction) -> List[str]:
        violations = []
        for rule in HARD_BLOCK_RULES:
            try:
                if rule.condition(transaction):
                    violations.append(rule.name)
            except Exception:
                pass
        return violations
        
    def evaluate_soft_rules(self, transaction) -> float:
        total_delta = 0.0
        for rule in SOFT_RULES:
            try:
                if rule.condition(transaction):
                    total_delta += rule.score_delta
            except Exception:
                pass
        return total_delta
