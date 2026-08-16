from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    task_id: str
    user_id: str
    original_request: str
    task_category: str          # set by Orchestrator LLM routing decision
    status: str                 # PENDING, PLANNING, RESEARCHING, EXECUTING, AUDITING, COMPLETED, FAILED
    plan: List[str]             # Planner output: list of step strings
    context: Dict[str, Any]     # Researcher output: collected data from tool calls
    execution_request: Dict[str, Any]
    execution_output: Dict[str, Any]  # Executor output
    audit_result: Dict[str, Any]      # Auditor structured verdict
    final_result: str                 # Orchestrator final markdown response
    errors: List[str]
    timestamps: Dict[str, str]
    agent_history: List[Dict[str, Any]]   # Observability: per-agent step telemetry
    audit_trail: List[Dict[str, Any]]
    tool_call_log: List[Dict[str, Any]]   # All LLM tool calls across all agents (observability)

    # Phase 2 future security placeholders (Zero-Trust hooks)
    security_context: Optional[Dict[str, Any]]
    trust_score: Optional[float]
    provenance_chain: Optional[List[str]]
