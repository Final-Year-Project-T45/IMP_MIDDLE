"""Auditor Agent — independent LLM evidence review and deterministic domain verification."""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

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


def verify_deterministic_invariants(exec_out: Dict[str, Any]) -> Dict[str, Any]:
    """
    Modular deterministic domain verification for banking operations.
    Validates physical backend status and financial balance conservation laws.

    Returns:
      {
        "status": "PASSED" | "FAILED" | "INCONCLUSIVE" | "NOT_APPLICABLE",
        "issues": List[str],
        "evidence": List[str]
      }
    """
    if not exec_out:
        return {
            "status": "NOT_APPLICABLE",
            "issues": [],
            "evidence": []
        }

    backend_status = exec_out.get("status")
    tool_called = exec_out.get("tool_called")
    tool_calls = exec_out.get("tool_calls", [])

    # Rule 1: If backend execution status explicitly failed/errored, deterministic check fails.
    if backend_status in {"FAILED", "ERROR"}:
        err_msg = exec_out.get("error") or exec_out.get("message") or "Backend operation failed"
        return {
            "status": "FAILED",
            "issues": [f"BACKEND_EXECUTION_FAILED: {err_msg}"],
            "evidence": [f"Authoritative backend execution status: {backend_status}"]
        }

    # Rule 2: Financial Transfer Invariant Verification
    is_transfer = (tool_called == "transfer_funds") or any(
        isinstance(tc, dict) and tc.get("tool") == "transfer_funds" for tc in tool_calls
    )

    if is_transfer and backend_status == "SUCCESS":
        sender_before = exec_out.get("sender_before_balance")
        receiver_before = exec_out.get("receiver_before_balance")
        sender_after = exec_out.get("sender_new_balance")
        receiver_after = exec_out.get("receiver_new_balance")
        amount = exec_out.get("amount")
        tx_id = exec_out.get("transaction_id")

        required = [sender_before, receiver_before, sender_after, receiver_after, amount, tx_id]
        if any(v is None for v in required):
            return {
                "status": "INCONCLUSIVE",
                "issues": ["TRANSFER_INVARIANT_EVIDENCE_MISSING"],
                "evidence": ["Required balance snapshots or transaction ID missing from transfer execution output."]
            }

        try:
            sb = float(sender_before)
            rb = float(receiver_before)
            sa = float(sender_after)
            ra = float(receiver_after)
            amt = float(amount)
        except (ValueError, TypeError):
            return {
                "status": "INCONCLUSIVE",
                "issues": ["TRANSFER_INVARIANT_NUMERIC_PARSE_ERROR"],
                "evidence": ["Balances or transfer amount could not be parsed as numeric values."]
            }

        issues: List[str] = []

        # Invariant 1: sender_after == sender_before - amount
        if round(sa, 2) != round(sb - amt, 2):
            issues.append(
                f"INVARIANT_VIOLATION_SENDER: sender_after ({sa}) != sender_before ({sb}) - amount ({amt})"
            )

        # Invariant 2: receiver_after == receiver_before + amount
        if round(ra, 2) != round(rb + amt, 2):
            issues.append(
                f"INVARIANT_VIOLATION_RECEIVER: receiver_after ({ra}) != receiver_before ({rb}) + amount ({amt})"
            )

        # Invariant 3: sender_before + receiver_before == sender_after + receiver_after
        if round(sb + rb, 2) != round(sa + ra, 2):
            issues.append(
                f"INVARIANT_VIOLATION_CONSERVATION: total before ({sb + rb}) != total after ({sa + ra})"
            )

        # Invariant 4: transaction ID presence
        if not tx_id:
            issues.append("INVARIANT_VIOLATION_TX_ID: Missing transaction ID")

        if issues:
            return {
                "status": "FAILED",
                "issues": issues,
                "evidence": [f"Deterministic financial invariant verification failed: {'; '.join(issues)}"]
            }

        return {
            "status": "PASSED",
            "issues": [],
            "evidence": [
                f"Deterministic financial invariants verified: sender ({sb} -> {sa}), "
                f"receiver ({rb} -> {ra}), amount={amt}, tx_id={tx_id}."
            ]
        }

    return {
        "status": "NOT_APPLICABLE",
        "issues": [],
        "evidence": []
    }


def _extract_json_substring(raw: str) -> str:
    cleaned = raw.replace("```json", "").replace("```", "").strip()
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return cleaned[first_brace:last_brace + 1]
    return cleaned


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
            cleaned = _extract_json_substring(raw)
            verdict = json.loads(cleaned)
            audit_status = verdict.get("audit_status", "INCONCLUSIVE")
            confidence = float(verdict.get("confidence", 0.0))
            summary = verdict.get("summary", "Audit completed.")
            issues = list(verdict.get("issues", []))
            evidence = list(verdict.get("evidence", []))

            if audit_status not in {"PASSED", "FAILED", "INCONCLUSIVE", "NOT_REQUIRED"}:
                audit_status = "INCONCLUSIVE"
                issues.append("INVALID_AUDIT_STATUS")
        except Exception as exc:
            logger.warning("Auditor JSON parse failed: %s", exc)
            audit_status = "INCONCLUSIVE"
            confidence = 0.0
            summary = "Auditor returned an unusable verdict; independent verification is inconclusive."
            issues = ["AUDITOR_INVALID_RESPONSE"]
            evidence = []

    # ── Modular Deterministic Backend / Invariant Verification ──────────────
    det_result = verify_deterministic_invariants(exec_out)

    if det_result["status"] == "FAILED":
        # The LLM must not override a deterministic invariant or backend execution failure.
        audit_status = "FAILED"
        confidence = 1.0
        issues.extend(det_result["issues"])
        evidence.extend(det_result["evidence"])
        summary = f"{summary} Deterministic verification FAILED: {'; '.join(det_result['issues'])}."

    elif det_result["status"] == "INCONCLUSIVE":
        # If required evidence is missing, do not guess; mark verification as inconclusive.
        if audit_status == "PASSED":
            audit_status = "INCONCLUSIVE"
            confidence = 0.5
        issues.extend(det_result["issues"])
        evidence.extend(det_result["evidence"])
        summary = f"{summary} Deterministic verification INCONCLUSIVE: missing required invariant evidence."

    elif det_result["status"] == "PASSED":
        evidence.extend(det_result["evidence"])

    # Double-check: Never let execution failure report PASSED
    if exec_out.get("status") in {"FAILED", "ERROR"} and audit_status == "PASSED":
        audit_status = "FAILED"
        issues.append("EXECUTION_STATUS_FAILED")

    audit_result = {
        "audit_status": audit_status,
        "confidence": confidence,
        "validation_summary": (
            f"Auditor reviewed {len(plan)} plan step(s) against research and backend execution evidence. "
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
        "action": f"Evidence audit completed: {audit_status} ({confidence:.0%} confidence).",
        "audit_summary": audit_result,
        "timestamp": timestamp,
    })

    SecurityBlock.intercept("Auditor", "Orchestrator", {"audit_status": audit_status}, state)
    return state
