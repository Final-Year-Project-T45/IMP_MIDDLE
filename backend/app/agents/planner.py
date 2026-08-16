"""
Planner Agent — Fast Objective Synthesis
==========================================
The Planner uses a single minimal LLM call to produce a one-sentence objective
and a concise step list. This is NOT a full JSON generation call — it is a fast
structured prompt that keeps the pipeline moving quickly.

Why keep the LLM here at all:
  The Planner's output feeds the audit trail and is read by Researcher + Executor
  as framing context. The LLM produces a task-specific objective sentence that is
  more meaningful than any static template, and helps the Researcher LLM understand
  the exact intent before deciding which tools to call.

  Without ANY LLM call here, the Researcher has to infer intent purely from the raw
  original_request — which works but is less reliable for ambiguous prompts.

Optimisation vs original:
  Original: full JSON plan generation (5-step array, multiple keys, ~300 tokens out)
  Fixed:    single fast sentence + short steps (max_tokens=120, ~50 tokens out)
  Saving:   ~60% of the LLM compute cost of this step.

Phase 1 Baseline — SecurityBlock is a pass-through hook only.
"""

import logging
from datetime import datetime, timezone

from app.schemas.state import AgentState
from app.schemas.security_hooks import SecurityBlock
from app.services.llm_service import llm_service

logger = logging.getLogger("finsecure.planner")

PLANNER_SYSTEM_PROMPT = """\
You are the Planner Agent of FinSecure, an autonomous banking operations platform.

Given a banking request, produce a brief JSON plan:
{
  "objective": "One clear sentence stating the goal",
  "steps": ["Step 1", "Step 2", "Step 3"]
}

Rules:
- Maximum 3 to 4 steps. Keep each step short (under 10 words).
- Steps describe WHAT must happen, not HOW the code does it.
- For POLICY_LOOKUP inquiries (e.g. questions about rules, limits, loan policy): Plan MUST only involve searching the policy knowledge base and formatting the policy summary. Do NOT plan loan disbursements, transfers, or account status changes.
- For financial mutations (transfers, freezes, disbursements): Only plan execution if explicitly commanded with specific identifiers.
- Return ONLY valid JSON. No markdown. No explanation outside the JSON.
"""


def planner_node(state: AgentState) -> AgentState:
    """
    Planner Agent Node — fast LLM call for objective and step list.
    Uses max_tokens=150 to keep the call short and cheap.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    req       = state["original_request"]

    # ── Fast LLM plan call ──────────────────────────────────────────────
    plan_result = llm_service.generate_json(
        prompt=f"Banking Request: {req}\n\nGenerate a brief execution plan.",
        system_prompt=PLANNER_SYSTEM_PROMPT,
        agent="Planner"
    )

    err = plan_result.get("error")
    if err or not plan_result.get("steps"):
        # Graceful fallback — log actual error type, pipeline continues regardless
        logger.warning(f"Planner: LLM plan call failed ({err or 'empty steps'}). Using safe fallback.")
        objective  = req
        plan_steps = [
            "Identify required entities from the request.",
            "Retrieve relevant banking data.",
            "Execute the required operation.",
            "Validate the result.",
        ]
    else:
        objective  = plan_result.get("objective", req)
        plan_steps = plan_result["steps"]

    state["plan"]   = plan_steps
    state["status"] = "RESEARCHING"

    state["agent_history"].append({
        "agent":        "Planner",
        "action":       (
            f"LLM generated plan with {len(plan_steps)} steps. "
            f"Objective: '{objective}'. Delegating to Researcher Agent."
        ),
        "plan_summary": plan_steps,
        "objective":    objective,
        "timestamp":    timestamp
    })

    SecurityBlock.intercept(
        "Planner", "Researcher",
        {"steps_count": len(plan_steps)},
        state
    )

    return state