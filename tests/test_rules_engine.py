import pytest
import sys
import os

# Add parent dir to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.decision_engine.rules_engine import RulesEngine

class MockTransaction:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

def test_hard_block_card():
    engine = RulesEngine()
    t = MockTransaction(card_id="card_123") # In blocklist
    violations = engine.evaluate_hard_rules(t)
    assert "BLOCKED_CARD" in violations

def test_hard_block_country():
    engine = RulesEngine()
    t = MockTransaction(country="CU") # Sanctioned
    violations = engine.evaluate_hard_rules(t)
    assert "SANCTIONED_COUNTRY" in violations

def test_soft_rule_high_amount_new_user():
    engine = RulesEngine()
    t = MockTransaction(amount=1500, user_account_age_days=10) # Triggers HIGH_AMOUNT_NEW_USER
    score_delta = engine.evaluate_soft_rules(t)
    assert score_delta >= 0.3

def test_soft_rule_card_testing():
    engine = RulesEngine()
    t = MockTransaction(amount=0.50, user_txn_count_5min=4) # Triggers CARD_TESTING_PATTERN
    score_delta = engine.evaluate_soft_rules(t)
    assert score_delta >= 0.4

def test_verified_merchant_reduction():
    engine = RulesEngine()
    t = MockTransaction(merchant_id="merch_amazon") # Triggers VERIFIED_MERCHANT
    score_delta = engine.evaluate_soft_rules(t)
    assert score_delta == -0.1
