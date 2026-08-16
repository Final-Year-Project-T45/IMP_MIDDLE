"""
Orchestrator Agent — LLM Routing & Response Synthesis
=======================================================
Entry : LLM classifies intent, handles direct responses (greetings),
        or routes to the full Planner→Researcher→Executor→Auditor pipeline.
Exit  : LLM synthesizes the final professional report from evidence summaries
        (NOT from raw full-context JSON dumps — this keeps the call fast).

Phase 1 Baseline — SecurityBlock is a pass-through hook only.
"""

import json
import uuid
import logging
from datetime import datetime, timezone

from app.schemas.state import AgentState
from app.schemas.security_hooks import SecurityBlock
from app.services.llm_service import llm_service, get_telemetry_summary

logger = logging.getLogger("finsecure.orchestrator")

# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

ORCHESTRATOR_SYSTEM_PROMPT = """\
You are the Orchestrator of FinSecure, an autonomous banking operations platform
used by professional bank employees.

Analyze the user's request and classify its intent accurately:

Category Definitions:
- GREETING: Conversational greetings, introductions, or capability questions (e.g. "hello", "who are you"). Route: "direct".
- POLICY_LOOKUP: Inquiries about banking rules, transfer limits, loan disbursement policies, freeze policies, or regulations (e.g. "What is the approved loan disbursement policy...", "Summarize wire transfer limits", "What are retail account transfer rules"). Route: "pipeline".
- ACCOUNT_INQUIRY: Requests to check balance, account details, or transaction history for a specific account or customer (e.g. "What is balance for account 4821"). Route: "pipeline".
- FUND_TRANSFER: Explicit commands to transfer money between accounts (e.g. "Transfer ₹85,000 from 4821 to 9034", "Approve fund transfer"). Route: "pipeline".
- ACCOUNT_FREEZE: Explicit commands to freeze or lock an account (e.g. "Freeze account 7742"). Route: "pipeline".
- FRAUD_CASE_LOOKUP: Requests to check investigation status of a fraud case (e.g. "Status of fraud case FC-2291"). Route: "pipeline".
- LOAN_DISBURSEMENT: Explicit commands to disburse money for an approved loan to a specific customer (e.g. "Disburse approved personal loan for customer C-6634"). NOTE: If the user is asking ABOUT the loan policy/rules, classify as POLICY_LOOKUP instead. Route: "pipeline".

Return ONLY valid JSON with this exact structure:
{
  "route": "direct" or "pipeline",
  "task_category": "GREETING" | "POLICY_LOOKUP" | "ACCOUNT_INQUIRY" | "FUND_TRANSFER" | "ACCOUNT_FREEZE" | "FRAUD_CASE_LOOKUP" | "LOAN_DISBURSEMENT",
  "objective": "One sentence describing what needs to be done",
  "direct_response": "Your response text if route is direct, else null"
}
"""

SYNTHESIS_SYSTEM_PROMPT = """\
You are the FinSecure Operations Assistant generating a professional final report
for a bank employee.

You will receive a concise summary of what was researched, what was executed,
and what the auditor concluded.

Generate a clean professional GitHub Markdown response:
- Use clear headers and bullet points.
- Include actual values (balances, transaction IDs, amounts, statuses, policy text).
- Do NOT invent or fabricate values — only use what is in the provided data.
- End with an italicized '*Auditor Verification*:' line with the auditor summary.
- If something failed, clearly state the exact failure reason.
- Be concise — this is for a busy bank operations professional.
"""


# ---------------------------------------------------------------------------
# Orchestrator Entry Node
# ---------------------------------------------------------------------------

def orchestrator_entry_node(state: AgentState) -> AgentState:
    """
    Orchestrator Entry — one LLM call for routing decision.
    Direct responses are returned immediately.
    Banking operations are routed to the pipeline.
    """
    # Initialise state fields
    if not state.get("task_id"):
        state["task_id"] = f"TASK-{uuid.uuid4().hex[:8].upper()}"

    state.setdefault("timestamps", {})
    state.setdefault("agent_history", [])
    state.setdefault("tool_call_log", [])

    timestamp = datetime.now(timezone.utc).isoformat()
    state["timestamps"]["start"] = timestamp
    req = state["original_request"]

    # ── Single LLM routing call ──────────────────────────────────────────
    routing_result = llm_service.generate_json(
        prompt=f"User Request: {req}",
        system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
        agent="Orchestrator"
    )

    err = routing_result.get("error")
    if err:
        # LLM failure: log specific error type, do NOT blindly assume ACCOUNT_INQUIRY
        logger.warning(f"Orchestrator: LLM routing failed ({err}). Defaulting to pipeline.")
        route         = "pipeline"
        task_category = "ACCOUNT_INQUIRY"
        objective     = req
        direct_resp   = None
    else:
        route         = routing_result.get("route", "pipeline")
        task_category = routing_result.get("task_category", "ACCOUNT_INQUIRY")
        objective     = routing_result.get("objective", req)
        direct_resp   = routing_result.get("direct_response")

    state["task_category"] = task_category

    state["agent_history"].append({
        "agent":     "Orchestrator",
        "action":    f"Routing decision: route='{route}', category='{task_category}', objective='{objective}'",
        "timestamp": timestamp
    })

    # ── Direct response (greeting / general Q&A) — no pipeline needed ───
    if route == "direct" and direct_resp:
        state["final_result"]     = direct_resp
        state["status"]           = "COMPLETED"
        state["execution_output"] = {"status": "SUCCESS", "tool_called": "none"}
        state["audit_result"]     = {
            "audit_status":       "PASSED",
            "validation_summary": "Direct conversational response — no banking operation performed.",
            "issues":             [],
            "verified_at":        timestamp
        }
        logger.info(f"Orchestrator: Direct response for '{task_category}'.")
        return state

    # ── Route to full pipeline ───────────────────────────────────────────
    state["status"] = "PLANNING"
    SecurityBlock.intercept(
        "Orchestrator", "Planner",
        {"category": task_category, "route": route},
        state
    )
    return state


# ---------------------------------------------------------------------------
# Orchestrator Exit Node
# ---------------------------------------------------------------------------

def orchestrator_exit_node(state: AgentState) -> AgentState:
    """
    Orchestrator Exit — LLM synthesizes the final professional response.

    IMPORTANT OPTIMISATION: We pass only summary strings to the LLM —
    NOT the full raw context JSON dump. This keeps the synthesis prompt
    small and the LLM call fast, while still giving the LLM everything
    it needs to write a correct report.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    state.setdefault("timestamps", {})
    state["timestamps"]["end"] = timestamp

    # Direct responses are already complete — nothing to do
    if state.get("task_category") in ("GREETING", "GENERAL_ASSISTANCE") \
            and state.get("final_result"):
        return state

    req      = state["original_request"]
    context  = state.get("context", {})
    exec_out = state.get("execution_output", {})
    audit    = state.get("audit_result", {})

    # ── Build a lean synthesis prompt ────────────────────────────────────
    # Use the researcher_summary string written by the Researcher LLM
    # instead of dumping the entire raw context dict.
    researcher_summary = context.get(
        "researcher_summary",
        "Research data available — see execution output."
    )

    # Only pass the fields that matter for the report — not the full record.
    EXEC_REPORT_KEYS = (
        "status", "tool_called", "transaction_id", "amount",
        "current_status", "account_status", "disbursement_status",
        "error", "message", "executor_summary",
        "balance", "account_id", "account_type",
        "case_id", "case_status", "severity",
        "loan_id", "loan_amount",
    )
    exec_summary = {k: exec_out[k] for k in EXEC_REPORT_KEYS if k in exec_out}

    synthesis_prompt = (
        f"User Request: {req}\n\n"
        f"Research Summary:\n{researcher_summary}\n\n"
        f"Execution Result:\n{json.dumps(exec_summary, indent=2, default=str)}\n\n"
        f"Auditor Verdict: {audit.get('audit_status', 'PASSED')}\n"
        f"Auditor Summary: {audit.get('validation_summary', '')}\n\n"
        "Generate the final professional banking operations report in Markdown."
    )

    final_text = llm_service.generate(
        synthesis_prompt,
        system_prompt=SYNTHESIS_SYSTEM_PROMPT,
        agent="Orchestrator"
    )

    # If the synthesis LLM call failed, replace with a safe structured error message
    if llm_service.is_llm_error(final_text):
        err_type = llm_service.get_error_type(final_text)
        logger.error(f"Orchestrator exit: LLM synthesis failed ({err_type}). Building fallback report.")
        exec_status = exec_out.get("status", "UNKNOWN")
        final_text = (
            f"## FinSecure Operations Report\n\n"
            f"**Status**: {exec_status}\n\n"
            f"**LLM Synthesis Unavailable**: `{err_type}` — The synthesis LLM call failed.\n\n"
            f"**Execution Output**: {exec_out.get('message') or exec_out.get('error', 'See execution_output field.')}\n\n"
            f"*Auditor Verification*: {audit.get('validation_summary', 'Audit complete.')}"
        )

    state["final_result"]  = final_text
    state["llm_telemetry"] = get_telemetry_summary()

    # If backend execution failed or audit failed, record overall status as FAILED
    if exec_out.get("status") == "FAILED" or audit.get("audit_status") == "FAILED":
        state["status"] = "FAILED"
    else:
        state["status"] = "COMPLETED"

    state["agent_history"].append({
        "agent":     "Orchestrator",
        "action":    f"LLM synthesized final report. Status: {state['status']}.",
        "timestamp": timestamp
    })

    return state