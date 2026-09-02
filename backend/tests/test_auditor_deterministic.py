"""
Automated Test Suite for Auditor Agent.
Tests deterministic domain invariant verification, financial conservation checks,
error handling, and resilience against hallucinated passes.
"""

import pytest
from app.agents.auditor import verify_deterministic_invariants, auditor_node
from app.schemas.state import AgentState


def test_invariant_successful_transfer():
    exec_out = {
        "status": "SUCCESS",
        "tool_called": "transfer_funds",
        "transaction_id": "TX-12345678",
        "amount": 5000.0,
        "sender_before_balance": 50000.0,
        "receiver_before_balance": 10000.0,
        "sender_new_balance": 45000.0,
        "receiver_new_balance": 15000.0
    }
    result = verify_deterministic_invariants(exec_out)
    assert result["status"] == "PASSED"
    assert len(result["issues"]) == 0
    assert "verified" in result["evidence"][0].lower()


def test_invariant_violation_sender_math():
    exec_out = {
        "status": "SUCCESS",
        "tool_called": "transfer_funds",
        "transaction_id": "TX-12345678",
        "amount": 5000.0,
        "sender_before_balance": 50000.0,
        "receiver_before_balance": 10000.0,
        # Sender balance only deducted by 1000 instead of 5000!
        "sender_new_balance": 49000.0,
        "receiver_new_balance": 15000.0
    }
    result = verify_deterministic_invariants(exec_out)
    assert result["status"] == "FAILED"
    assert any("INVARIANT_VIOLATION_SENDER" in issue for issue in result["issues"])
    assert any("INVARIANT_VIOLATION_CONSERVATION" in issue for issue in result["issues"])


def test_invariant_violation_receiver_math():
    exec_out = {
        "status": "SUCCESS",
        "tool_called": "transfer_funds",
        "transaction_id": "TX-12345678",
        "amount": 5000.0,
        "sender_before_balance": 50000.0,
        "receiver_before_balance": 10000.0,
        "sender_new_balance": 45000.0,
        # Receiver balance credited 10000 instead of 5000!
        "receiver_new_balance": 20000.0
    }
    result = verify_deterministic_invariants(exec_out)
    assert result["status"] == "FAILED"
    assert any("INVARIANT_VIOLATION_RECEIVER" in issue for issue in result["issues"])
    assert any("INVARIANT_VIOLATION_CONSERVATION" in issue for issue in result["issues"])


def test_invariant_missing_evidence():
    exec_out = {
        "status": "SUCCESS",
        "tool_called": "transfer_funds",
        # Missing sender_before_balance and receiver_before_balance
        "amount": 5000.0,
        "sender_new_balance": 45000.0,
        "receiver_new_balance": 15000.0
    }
    result = verify_deterministic_invariants(exec_out)
    assert result["status"] == "INCONCLUSIVE"
    assert "TRANSFER_INVARIANT_EVIDENCE_MISSING" in result["issues"]


def test_invariant_backend_execution_failed():
    exec_out = {
        "status": "FAILED",
        "tool_called": "transfer_funds",
        "error": "Sender account 'ACC-4821' is FROZEN. Transfer rejected."
    }
    result = verify_deterministic_invariants(exec_out)
    assert result["status"] == "FAILED"
    assert any("BACKEND_EXECUTION_FAILED" in issue for issue in result["issues"])


def test_auditor_node_deterministic_override(monkeypatch):
    """
    Even if the LLM hallucinates a PASSED audit, if the deterministic
    invariant check fails, the final audit verdict MUST be FAILED.
    """
    # Mock LLM to return hallucinated PASSED verdict
    class MockLLM:
        @staticmethod
        def generate(*args, **kwargs):
            return '{"audit_status": "PASSED", "confidence": 0.99, "summary": "Looks great!", "issues": [], "evidence": []}'

        @staticmethod
        def is_llm_error(text):
            return False

        @staticmethod
        def get_error_type(text):
            return ""

    monkeypatch.setattr("app.agents.auditor.llm_service", MockLLM)

    # State with mathematically corrupt transfer
    state: AgentState = {
        "original_request": "Transfer 5000 from ACC-1001 to ACC-1002",
        "plan": ["Transfer funds"],
        "context": {},
        "execution_output": {
            "status": "SUCCESS",
            "tool_called": "transfer_funds",
            "transaction_id": "TX-MOCK",
            "amount": 5000.0,
            "sender_before_balance": 50000.0,
            "receiver_before_balance": 10000.0,
            "sender_new_balance": 50000.0,  # NOT DEDUCTED!
            "receiver_new_balance": 15000.0
        },
        "agent_history": []
    }

    result_state = auditor_node(state)
    audit = result_state["audit_result"]

    # Invariant failure must override hallucinated LLM pass
    assert audit["audit_status"] == "FAILED"
    assert any("INVARIANT_VIOLATION" in issue for issue in audit["issues"])
    assert result_state["status"] == "FAILED"


def test_auditor_node_llm_failure_handling(monkeypatch):
    """
    If the Auditor LLM fails, it must NEVER be converted to PASSED.
    It must report INCONCLUSIVE.
    """
    class MockLLMFailure:
        @staticmethod
        def generate(*args, **kwargs):
            return "__LLM_ERROR::RATE_LIMIT::Rate limit exceeded"

        @staticmethod
        def is_llm_error(text):
            return True

        @staticmethod
        def get_error_type(text):
            return "RATE_LIMIT"

    monkeypatch.setattr("app.agents.auditor.llm_service", MockLLMFailure)

    state: AgentState = {
        "original_request": "Check account balance for ACC-4821",
        "plan": ["Retrieve balance"],
        "context": {"get_account": {"balance": 50000.0}},
        "execution_output": {"status": "NOT_REQUIRED", "tool_called": "none"},
        "agent_history": []
    }

    result_state = auditor_node(state)
    audit = result_state["audit_result"]

    assert audit["audit_status"] == "INCONCLUSIVE"
    assert audit["confidence"] == 0.0
    assert "AUDITOR_UNAVAILABLE" in audit["issues"]
    assert result_state["status"] == "INCONCLUSIVE"


def test_auditor_node_malformed_llm_output(monkeypatch):
    """
    If the Auditor LLM returns garbage / invalid JSON, it must report INCONCLUSIVE.
    """
    class MockLLMGarbage:
        @staticmethod
        def generate(*args, **kwargs):
            return "Sorry, I am unable to analyze this output right now."

        @staticmethod
        def is_llm_error(text):
            return False

        @staticmethod
        def get_error_type(text):
            return ""

    monkeypatch.setattr("app.agents.auditor.llm_service", MockLLMGarbage)

    state: AgentState = {
        "original_request": "Check account balance for ACC-4821",
        "plan": ["Retrieve balance"],
        "context": {"get_account": {"balance": 50000.0}},
        "execution_output": {"status": "NOT_REQUIRED", "tool_called": "none"},
        "agent_history": []
    }

    result_state = auditor_node(state)
    audit = result_state["audit_result"]

    assert audit["audit_status"] == "INCONCLUSIVE"
    assert "AUDITOR_INVALID_RESPONSE" in audit["issues"]
    assert result_state["status"] == "INCONCLUSIVE"
