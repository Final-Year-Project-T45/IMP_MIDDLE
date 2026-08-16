from langgraph.graph import StateGraph, END
from app.schemas.state import AgentState
from app.agents.orchestrator import orchestrator_entry_node, orchestrator_exit_node
from app.agents.planner import planner_node
from app.agents.researcher import researcher_node
from app.agents.executor import executor_node
from app.agents.auditor import auditor_node

def _route_from_orchestrator(state: AgentState) -> str:
    """
    Conditional routing from Orchestrator entry node.
    If the LLM decided to handle directly (greeting/general), go straight to exit.
    Otherwise, route through the full Planner→Researcher→Executor→Auditor pipeline.
    """
    if state.get("status") == "COMPLETED":
        return "orchestrator_exit"
    return "planner"

def build_finsecure_graph():
    """
    Assembles the FinSecure Phase 1 LangGraph StateGraph workflow.
    Routing from Orchestrator is LLM-driven (conditional edge).
    Full pipeline: Orchestrator → Planner → Researcher → Executor → Auditor → Orchestrator (exit)
    Short circuit: Orchestrator → Orchestrator (exit) for direct conversational responses.
    """
    workflow = StateGraph(AgentState)

    # Add agent nodes
    workflow.add_node("orchestrator_entry", orchestrator_entry_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("auditor", auditor_node)
    workflow.add_node("orchestrator_exit", orchestrator_exit_node)

    # Entry point
    workflow.set_entry_point("orchestrator_entry")

    # Conditional routing from Orchestrator entry (LLM-driven decision)
    workflow.add_conditional_edges(
        "orchestrator_entry",
        _route_from_orchestrator,
        {
            "planner": "planner",
            "orchestrator_exit": "orchestrator_exit",
        }
    )

    # Linear pipeline edges
    workflow.add_edge("planner", "researcher")
    workflow.add_edge("researcher", "executor")
    workflow.add_edge("executor", "auditor")
    workflow.add_edge("auditor", "orchestrator_exit")
    workflow.add_edge("orchestrator_exit", END)

    app = workflow.compile()
    return app

# Singleton compiled graph instance
finsecure_workflow = build_finsecure_graph()
