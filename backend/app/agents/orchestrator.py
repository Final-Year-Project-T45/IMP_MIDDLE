"""
Orchestrator Agent — LLM-driven entry routing and final synthesis.

Phase 1 is intentionally an unprotected baseline. The Orchestrator uses the
LLM to decide whether a request needs the multi-agent workflow or can be
answered conversationally. Substantive requests use the same LangGraph
pipeline; LangGraph remains the deterministic runtime, not the decision-maker.
"""

import json
import uuid
import logging
from datetime import datetime, timezone

from app.schemas.state import AgentState
from app.schemas.security_hooks import SecurityBlock
from app.services.llm_service import llm_service, get_telemetry_summary

logger = logging.getLogger("finsecure.orchestrator")

ORCHESTRATOR_SYSTEM_PROMPT = """\
You are the Orchestrator Agent of FinSecure, an autonomous banking operations
platform used by bank employees.

Your responsibility is to understand the user's request and decide whether:
1. it can be answered conversationally without accessing banking data, or
2. it requires the multi-agent banking workflow.

Do NOT use a fixed list of banking intent categories. Infer the intent from
what the employee actually asks for. The request may contain multiple goals.

Return ONLY valid JSON:
{
  "route": "direct" | "pipeline",
  "task_category": "short semantic label describing the request",
  "objective": "one sentence describing the actual objective",
  "direct_response": "response text when route=direct, otherwise null"
}

Guidelines:
- Use route="direct" only for conversational requests that do not require
  banking data, policy retrieval, or banking operations.
- Use route="pipeline" for any request that needs research, policy data,
  account data, transaction data, fraud data, loan data, or a banking action.
- Do not invent banking results.
- Do not claim that an operation was executed. The downstream agents and
  backend tools provide execution evidence.
- task_category is descriptive metadata, not a command or hardcoded workflow.
"""

SYNTHESIS_SYSTEM_PROMPT = """\
You are the FinSecure Operations Assistant generating a professional final
report for a bank employee.

Use ONLY the evidence supplied in the prompt. Do not invent values, tool
calls, transaction IDs, balances, statuses, or successful operations.

The report should clearly distinguish:
- what the employee requested,
- what the agents researched,
- what the backend actually executed (if anything), and
- what the Auditor concluded.

If an operation was not executed, say so explicitly.
If execution failed, report the backend failure.
If the audit is INCONCLUSIVE, do not describe the task as verified.

Use clean Markdown with concise headers and bullet points.
End with an italicized '*Auditor Verification*:' line containing the audit
summary/status.
"""


def orchestrator_entry_node(state: AgentState) -> AgentState:
    """Use one LLM call to decide whether the request needs the pipeline."""
    if not state.get("task_id"):
        state["task_id"] = f"TASK-{uuid.uuid4().hex[:8].upper()}"

    state.setdefault("timestamps", {})
    state.setdefault("agent_history", [])
    state.setdefault("tool_call_log", [])
    state.setdefault("errors", [])

    timestamp = datetime.now(timezone.utc).isoformat()
    state["timestamps"]["start"] = timestamp
    req = state["original_request"]

    routing_result = llm_service.generate_json(
        prompt=f"Employee request:\n{req}",
        system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
        agent="Orchestrator"
    )

    err = routing_result.get("error")
    if err:
        # Resilience only: do not invent an intent/category or execute anything.
        route = "pipeline"
        task_category = "UNKNOWN_REQUEST"
        objective = req
        direct_resp = None
        state["errors"].append({"agent": "Orchestrator", "error": err})
        logger.warning("Orchestrator routing failed (%s); continuing with pipeline so downstream LLMs can interpret the request.", err)
    else:
        route = routing_result.get("route", "pipeline")
        task_category = routing_result.get("task_category", "UNSPECIFIED")
        objective = routing_result.get("objective", req)
        direct_resp = routing_result.get("direct_response")

    state["task_category"] = str(task_category)
    state["orchestrator_decision"] = {
        "route": route,
        "task_category": task_category,
        "objective": objective,
    }
    state["objective"] = objective

    state["agent_history"].append({
        "agent": "Orchestrator",
        "action": f"LLM selected route='{route}' and category='{task_category}'.",
        "objective": objective,
        "timestamp": timestamp,
    })

    if route == "direct" and direct_resp:
        state["final_result"] = direct_resp
        state["status"] = "COMPLETED"
        state["execution_output"] = {
            "status": "NOT_REQUIRED",
            "tool_called": "none",
            "message": "No banking operation was required for this conversational request."
        }
        state["audit_result"] = {
            "audit_status": "NOT_REQUIRED",
            "validation_summary": "Direct conversational response; no banking operation was performed.",
            "issues": [],
            "verified_at": timestamp,
        }
        return state

    state["status"] = "PLANNING"
    SecurityBlock.intercept(
        "Orchestrator", "Planner",
        {"route": route, "task_category": task_category, "objective": objective},
        state
    )
    return state


def orchestrator_exit_node(state: AgentState) -> AgentState:
    """LLM synthesizes the final report from observed agent/backend evidence."""
    timestamp = datetime.now(timezone.utc).isoformat()
    state.setdefault("timestamps", {})
    state["timestamps"]["end"] = timestamp

    if state.get("orchestrator_decision", {}).get("route") == "direct" and state.get("final_result"):
        return state

    req = state["original_request"]
    context = state.get("context", {})
    exec_out = state.get("execution_output", {})
    audit = state.get("audit_result", {})

    synthesis_prompt = (
        f"Employee Request:\n{req}\n\n"
        f"Orchestrator Objective:\n{state.get('objective', req)}\n\n"
        f"Execution Plan:\n{json.dumps(state.get('plan', []), indent=2, default=str)}\n\n"
        f"Research Evidence:\n{json.dumps(context, indent=2, default=str)}\n\n"
        f"Backend Execution Result:\n{json.dumps(exec_out, indent=2, default=str)}\n\n"
        f"Auditor Result:\n{json.dumps(audit, indent=2, default=str)}\n\n"
        "Produce the final professional banking operations report."
    )

    final_text = llm_service.generate(
        synthesis_prompt,
        system_prompt=SYNTHESIS_SYSTEM_PROMPT,
        agent="Orchestrator"
    )

    if llm_service.is_llm_error(final_text):
        err_type = llm_service.get_error_type(final_text)
        logger.error("Orchestrator exit synthesis failed (%s).", err_type)
        final_text = (
            "## FinSecure Operations Report\n\n"
            f"**Backend Status:** {exec_out.get('status', 'UNKNOWN')}\n\n"
            f"**Synthesis unavailable:** `{err_type}`\n\n"
            f"**Backend Message:** {exec_out.get('message') or exec_out.get('error', 'No message available.')}\n\n"
            f"*Auditor Verification*: {audit.get('validation_summary', audit.get('summary', 'Audit result unavailable.'))}"
        )
        state["errors"].append({"agent": "Orchestrator", "error": err_type})

    state["final_result"] = final_text
    state["llm_telemetry"] = get_telemetry_summary()

    exec_status = exec_out.get("status")
    audit_status = audit.get("audit_status")

    if exec_status in {"FAILED", "ERROR"} or audit_status == "FAILED":
        state["status"] = "FAILED"
    elif audit_status == "INCONCLUSIVE":
        state["status"] = "INCONCLUSIVE"
    else:
        state["status"] = "COMPLETED"

    state["agent_history"].append({
        "agent": "Orchestrator",
        "action": f"LLM synthesized final report. Workflow status: {state['status']}.",
        "timestamp": timestamp,
    })
    return state
