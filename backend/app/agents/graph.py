"""LangGraph runtime for the Phase 1 autonomous banking baseline.

The graph deliberately keeps a stable lifecycle for observability:
Orchestrator -> Planner -> Researcher -> Executor -> Auditor -> Orchestrator.
The agents, not Python keyword branches, make the substantive decisions inside
that lifecycle. Phase 2 will add security enforcement at the existing hooks.
"""

from langgraph.graph import StateGraph, END
from app.schemas.state import AgentState
from app.agents.orchestrator import orchestrator_entry_node, orchestrator_exit_node
from app.agents.planner import planner_node
from app.agents.researcher import researcher_node
from app.agents.executor import executor_node
from app.agents.auditor import auditor_node


def _route_from_orchestrator(state: AgentState) -> str:
    # This is runtime control flow. The Orchestrator LLM already decided
    # whether the request is direct or needs the multi-agent pipeline.
    return "orchestrator_exit" if state.get("status") == "COMPLETED" else "planner"


def build_finsecure_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("orchestrator_entry", orchestrator_entry_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("auditor", auditor_node)
    workflow.add_node("orchestrator_exit", orchestrator_exit_node)

    workflow.set_entry_point("orchestrator_entry")

    workflow.add_conditional_edges(
        "orchestrator_entry",
        _route_from_orchestrator,
        {
            "planner": "planner",
            "orchestrator_exit": "orchestrator_exit",
        },
    )

    workflow.add_edge("planner", "researcher")
    workflow.add_edge("researcher", "executor")
    workflow.add_edge("executor", "auditor")
    workflow.add_edge("auditor", "orchestrator_exit")
    workflow.add_edge("orchestrator_exit", END)

    return workflow.compile()


finsecure_workflow = build_finsecure_graph()
