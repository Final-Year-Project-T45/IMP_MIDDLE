"""
Automated Test Suite for Agentic Scenarios and Workflow Invariant Propagation.
Validates multi-agent coordination, conversational short-circuiting,
research-halt propagation, and write-operation suppression for read requests.
"""

import pytest
from app.agents.orchestrator import orchestrator_entry_node, orchestrator_exit_node
from app.agents.planner import planner_node
from app.agents.researcher import researcher_node
from app.agents.executor import executor_node
from app.agents.auditor import auditor_node
from app.schemas.state import AgentState


def test_conversational_direct_routing(monkeypatch):
    """
    Greetings / casual assistance should be handled directly by Orchestrator
    without triggering Planner, Researcher, or Executor write tools.
    """
    class MockOrchestratorLLM:
        @staticmethod
        def generate_json(*args, **kwargs):
            return {
                "route": "direct",
                "task_category": "GREETING",
                "objective": "Greet user and state capabilities",
                "direct_response": "Hello! I am FinSecure, your autonomous banking operations platform."
            }

        @staticmethod
        def is_llm_error(text):
            return False

        @staticmethod
        def get_error_type(text):
            return ""

    monkeypatch.setattr("app.agents.orchestrator.llm_service", MockOrchestratorLLM)

    initial_state: AgentState = {
        "original_request": "Hello, who are you?",
        "status": "PENDING",
        "agent_history": [],
        "errors": []
    }

    state = orchestrator_entry_node(initial_state)

    assert state["status"] == "COMPLETED"
    assert state["task_category"] == "GREETING"
    assert "FinSecure" in state["final_result"]
    assert state["execution_output"]["status"] == "NOT_REQUIRED"
    assert state["audit_result"]["audit_status"] == "NOT_REQUIRED"


def test_research_failure_stops_executor():
    """
    If the research phase fails, the Executor MUST immediately halt
    and NOT perform any write tools. Status must propagate as FAILED.
    """
    state: AgentState = {
        "original_request": "Transfer ₹10,000 from ACC-4821 to ACC-9034",
        "plan": ["Lookup accounts", "Verify balance", "Transfer funds"],
        "context": {
            "research_status": "FAILED",
            "research_error": "Groq rate limit exceeded after retries."
        },
        "status": "EXECUTING",
        "agent_history": [],
        "errors": []
    }

    exec_state = executor_node(state)

    assert exec_state["status"] == "AUDITING"
    assert exec_state["execution_output"]["status"] == "FAILED"
    assert exec_state["execution_output"]["tool_called"] == "none"
    assert exec_state["failure_stage"] == "Researcher"
    assert "research failed" in exec_state["execution_output"]["error"].lower()


def test_read_only_request_suppresses_write_action(monkeypatch):
    """
    When the user asks for policy or balance, the Executor LLM should
    decide that no write tool is required, returning status NOT_REQUIRED.
    """
    class MockChoice:
        class Message:
            tool_calls = None
            content = "Research is complete. Account balance retrieved; no write action required."
        message = Message()

    class MockResult:
        success = True
        error_type = ""
        error_message = ""

    class MockLLMService:
        @staticmethod
        def chat_with_tools(*args, **kwargs):
            return MockChoice(), MockResult()

        @staticmethod
        def is_llm_error(text):
            return False

    monkeypatch.setattr("app.agents.executor.llm_service", MockLLMService)

    state: AgentState = {
        "original_request": "What is the retail wire transfer policy?",
        "objective": "Retrieve wire transfer policy details",
        "plan": ["Search policy database", "Summarize findings"],
        "context": {
            "research_status": "COMPLETED",
            "search_policy": {"status": "SUCCESS", "results": [{"content": "Daily limit is 1,00,000"}]},
            "researcher_summary": "Daily transfer limit is ₹1,00,000 for retail customers."
        },
        "status": "EXECUTING",
        "agent_history": [],
        "errors": []
    }

    exec_state = executor_node(state)

    assert exec_state["execution_output"]["status"] == "NOT_REQUIRED"
    assert exec_state["execution_output"]["tool_called"] == "none"
    assert "no write action" in exec_state["execution_output"]["message"].lower()


def test_orchestrator_exit_failure_aggregation():
    """
    If either execution failed or audit failed, Orchestrator exit MUST
    report the overall workflow status as FAILED.
    """
    state: AgentState = {
        "original_request": "Transfer 50,000 from ACC-4821 to ACC-9034",
        "context": {},
        "execution_output": {
            "status": "FAILED",
            "tool_called": "transfer_funds",
            "error": "Insufficient funds."
        },
        "audit_result": {
            "audit_status": "FAILED",
            "validation_summary": "Execution failed: Insufficient funds."
        },
        "agent_history": []
    }

    exit_state = orchestrator_exit_node(state)
    assert exit_state["status"] == "FAILED"
