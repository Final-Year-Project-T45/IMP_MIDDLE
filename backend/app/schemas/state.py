from typing import TypedDict, List, Dict, Any, Optional


class AgentState(TypedDict, total=False):
    task_id: str
    user_id: str
    original_request: str

    # LLM-generated semantic interpretation. It is metadata, not a hardcoded
    # routing enum used by Python business logic.
    task_category: str
    objective: str
    orchestrator_decision: Dict[str, Any]

    status: str
    plan: List[str]
    context: Dict[str, Any]
    researcher_summary: str

    # Retained for API compatibility with the existing frontend/backend.
    execution_request: Dict[str, Any]
    execution_output: Dict[str, Any]
    audit_result: Dict[str, Any]
    final_result: str
    llm_telemetry: Dict[str, Any]

    errors: List[Any]
    timestamps: Dict[str, str]
    agent_history: List[Dict[str, Any]]
    audit_trail: List[Dict[str, Any]]
    tool_call_log: List[Dict[str, Any]]
    failure_stage: str

    # Reserved for the Phase 2 Zero-Trust implementation. These fields are
    # intentionally unused by the Phase 1 baseline.
    security_context: Optional[Dict[str, Any]]
    trust_score: Optional[float]
    provenance_chain: Optional[List[str]]
