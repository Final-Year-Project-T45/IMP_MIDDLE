"""Auditor Agent — independent LLM evidence review for Phase 1."""

import json
import logging
from datetime import datetime, timezone

from app.schemas.state import AgentState
from app.schemas.security_hooks import SecurityBlock
from app.services.llm_service import llm_service

logger = logging.getLogger("finsecure.auditor")

AUDITOR_SYSTEM_PROMPT = """\
You are the Auditor Agent of FinSecure, an autonomous banking operations platform.

Independently evaluate whether the employee's request was fulfilled based
STRICTLY on the evidence provided:
1. original request
2. planner output
3. research evidence
4. actual backend execution result

Do not invent facts or assume that an LLM statement is equivalent to a backend
operation. A tool result is evidence of what the backend actually returned.

Distinguish:
- PASSED: the evidence is sufficient and the requested task was fulfilled.
- FAILED: the evidence shows the task was not fulfilled or the backend operation failed.
- INCONCLUSIVE: there is not enough reliable evidence to determine whether the
  task was fulfilled (for example, the audit model itself lacks usable evidence).
- NOT_REQUIRED: a conversational request did not require banking execution.

Return ONLY valid JSON:
{
  "audit_status": "PASSED" | "FAILED" | "INCONCLUSIVE" | "NOT_REQUIRED",
  "confidence": 0.0,
  "summary": "clear audit conclusion",
  "issues": [],
  "evidence": []
}
"""


def auditor_node(state: AgentState) -> AgentState:
    timestamp = datetime.now(timezone.utc).isoformat()
    req = state["original_request"]
    plan = state.get("plan", [])
    context = state.get("context", {})
    exec_out = state.get("execution_output", {})

    audit_prompt = (
        f"Original employee request:\n{req}\n\n"
        f"Planner output:\n{json.dumps({'objective': state.get('objective', req), 'steps': plan}, indent=2, default=str)}\n\n"
        f"Research evidence:\n{json.dumps(context, indent=2, default=str)}\n\n"
        f"Actual backend execution result:\n{json.dumps(exec_out, indent=2, default=str)}\n\n"
        "Return the independent audit verdict."
    )

    raw = llm_service.generate(
        audit_prompt,
        system_prompt=AUDITOR_SYSTEM_PROMPT,
        temperature=0.1,
        agent="Auditor",
    )

    if llm_service.is_llm_error(raw):
        err_type = llm_service.get_error_type(raw)
        # Do not turn an unavailable Auditor into a PASSED verdict.
        audit_status = "INCONCLUSIVE"
        confidence = 0.0
        summary = f"Auditor LLM unavailable ({err_type}); independent verification could not be completed."
        issues = ["AUDITOR_UNAVAILABLE"]
        evidence = [f"Auditor LLM error: {err_type}"]
        state.setdefault("errors", []).append({"agent": "Auditor", "error": err_type})
    else:
        try:
            cleaned = raw.replace("```json", "").replace("```", "").strip()
            verdict = json.loads(cleaned)
            audit_status = verdict.get("audit_status", "INCONCLUSIVE")
            confidence = float(verdict.get("confidence", 0.0))
            summary = verdict.get("summary", "Audit completed.")
            issues = verdict.get("issues", [])
            evidence = verdict.get("evidence", [])

            if audit_status not in {"PASSED", "FAILED", "INCONCLUSIVE", "NOT_REQUIRED"}:
                audit_status = "INCONCLUSIVE"
                issues = list(issues) + ["INVALID_AUDIT_STATUS"]
        except Exception as exc:
            logger.warning("Auditor JSON parse failed: %s", exc)
            audit_status = "INCONCLUSIVE"
            confidence = 0.0
            summary = "Auditor returned an unusable verdict; independent verification is inconclusive."
            issues = ["AUDITOR_INVALID_RESPONSE"]
            evidence = []

    audit_result = {
        "audit_status": audit_status,
        "confidence": confidence,
        "validation_summary": (
            f"Auditor reviewed {len(plan)} plan step(s) against the available research and backend execution evidence. "
            f"{summary} Issues: {len(issues)}."
        ),
        "summary": summary,
        "issues": issues,
        "evidence": evidence,
        "verified_at": timestamp,
    }

    state["audit_result"] = audit_result
    state["status"] = "COMPLETED" if audit_status not in {"FAILED", "INCONCLUSIVE"} else audit_status

    state["agent_history"].append({
        "agent": "Auditor",
        "action": f"LLM evidence audit completed: {audit_status} ({confidence:.0%} confidence).",
        "audit_summary": audit_result,
        "timestamp": timestamp,
    })

    SecurityBlock.intercept("Auditor", "Orchestrator", {"audit_status": audit_status}, state)
    return state
