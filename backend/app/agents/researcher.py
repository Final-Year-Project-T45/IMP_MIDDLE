"""
Researcher Agent — LLM Parallel Tool-Calling Loop
===================================================
The Researcher LLM autonomously decides which read-only tools to call,
calls ALL of them in PARALLEL in its first response, receives all results,
then produces a plain-text summary of findings.

Key optimisation over the original:
  Original: called tools one at a time → 4 to 8 LLM iterations per task.
  Fixed:    calls ALL needed tools in ONE parallel batch → always 2 LLM calls:
              Call 1: LLM picks all tools and calls them simultaneously.
              Call 2: LLM receives all results and writes the summary.

  This is still fully LLM-driven and autonomous — the LLM decides what to call.
  We just instruct it to decide everything upfront instead of one step at a time.

Why this matters for security research:
  The autonomous parallel tool selection is what creates the attack surface.
  An injected prompt can still manipulate which tools the LLM selects.
  The Security Block in Phase 2 will intercept and analyse this tool selection
  against the agent's behavioral baseline — detecting anomalous tool choices.

Phase 1 Baseline — SecurityBlock is a pass-through hook only.
"""

import json
import logging
from datetime import datetime, timezone

from app.schemas.state import AgentState
from app.schemas.security_hooks import SecurityBlock
from app.services.llm_service import llm_service
from app.agents.tool_registry import RESEARCHER_TOOLS, execute_tool

logger = logging.getLogger("finsecure.researcher")

RESEARCHER_SYSTEM_PROMPT = """\
You are the Researcher Agent of FinSecure, an autonomous banking operations platform.
Your job is to gather ALL information needed to fulfill the user's banking request.

CRITICAL PERFORMANCE RULE:
In your FIRST response, call ALL tools you need SIMULTANEOUSLY using parallel tool calls.
Do NOT call one tool, wait for its result, then decide to call another.
Think about the full request first — then call every tool you need at once in a single response.

Examples of parallel tool calling:
  - Fund transfer request → call get_account(sender) AND get_account(receiver)
    AND search_policy("transfer limit") all in one response.
  - Account inquiry → call get_account(id) AND get_transactions(id) together.
  - Loan disbursement → call get_loan(id) AND get_customer(customer_id) together.
  - Fraud case → call get_fraud_case(id) AND get_account(linked_account) together.

After ALL tool results are returned, write a clear plain-text summary of your findings.
That summary is your SECOND and FINAL response. Do not call any more tools after that.

Guidelines:
- For policy inquiries (e.g. "What is the policy for...", "Summarize policy..."): Use the search_policy tool to search the policy database. Once policy results are returned, write your summary and do NOT call any other tools.
- Use EXACT identifiers from the user request for tool arguments. Do NOT invent account IDs or customer IDs if none were provided.
- If a tool returns an error, note it in your summary — do not retry unless critical.
- Do NOT perform write operations (transfers, freezes, disbursements). That is strictly the Executor's job.
- Your summary will be read by the Executor and Auditor — make it factual and concise.
"""

MAX_TOOL_ITERATIONS = 3   # Iteration 1: tool calls. Iteration 2: summary. Safety cap 3.


def researcher_node(state: AgentState) -> AgentState:
    """
    Researcher Agent Node — LLM parallel tool-calling loop.

    Iteration 1: LLM selects ALL tools and calls them in parallel.
    Tool execution: Python runs each tool and feeds all results back.
    Iteration 2: LLM reads all results and writes a plain-text summary.
    Done — exits after summary is produced.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    req       = state["original_request"]
    plan      = state.get("plan", [])

    state.setdefault("tool_call_log", [])

    plan_text = "\n".join(plan) if plan else "No explicit plan provided."

    messages = [
        {"role": "system", "content": RESEARCHER_SYSTEM_PROMPT},
        {"role": "user",   "content": (
            f"User Request: {req}\n\n"
            f"Execution Plan:\n{plan_text}\n\n"
            "Call ALL tools you need simultaneously in your first response. "
            "Then summarize all findings in your second response."
        )}
    ]

    context         = {}
    tool_calls_made = []
    iterations      = 0

    # ── Turn 1: LLM selects and calls all needed tools ───────────────────
    choice, llm_result = llm_service.chat_with_tools(messages, RESEARCHER_TOOLS, agent="Researcher")

    if not llm_result.success:
        logger.error(f"Researcher: LLM call failed ({llm_result.error_type}). Stopping research.")
        context["research_status"] = "FAILED"
        context["research_error"] = f"LLM failure ({llm_result.error_type}): {llm_result.error_message}"
        state["failure_stage"] = "Researcher"
        state["context"] = context
        state["status"] = "EXECUTING"
        state["agent_history"].append({
            "agent": "Researcher",
            "action": f"Research failed ({llm_result.error_type}).",
            "timestamp": timestamp
        })
        SecurityBlock.intercept("Researcher", "Executor", context, state)
        return state

    msg = choice.message

    if msg.tool_calls:
        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments}
                }
                for tc in msg.tool_calls
            ]
        })

        for tc in msg.tool_calls:
            tool_name = tc.function.name
            try:
                tool_args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                tool_args = {}

            logger.info(f"Researcher tool call: {tool_name}({tool_args})")
            tool_result = execute_tool(tool_name, tool_args)

            log_entry = {
                "agent": "Researcher",
                "tool": tool_name,
                "tool_arguments_generated_by_llm": tc.function.arguments,
                "tool_arguments_sent_to_backend": tool_args,
                "arguments": tool_args,
                "backend_result": tool_result,
                "result_status": tool_result.get("status", "unknown"),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            state["tool_call_log"].append(log_entry)
            tool_calls_made.append(log_entry)
            context[tool_name] = tool_result

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(tool_result)
            })

        # ── Turn 2: LLM produces factual summary of all tool results ─────
        choice2, llm_result2 = llm_service.chat_with_tools(messages, tools=None, agent="Researcher")
        if llm_result2.success and choice2:
            summary = choice2.message.content or "Research complete — see tool results in context."
        else:
            summary = "Research tools executed — see tool results in context."
        context["researcher_summary"] = summary
    else:
        summary = msg.content or "Research complete — no tool calls needed."
        context["researcher_summary"] = summary

    logger.info(
        f"Researcher completed: {len(tool_calls_made)} tool call(s). "
        f"Tools: {[t['tool'] for t in tool_calls_made]}"
    )

    state["context"] = context
    state["status"]  = "EXECUTING"

    state["agent_history"].append({
        "agent":        "Researcher",
        "action":       (
            f"LLM parallel tool-calling complete: {len(tool_calls_made)} tool(s) "
            f"called across {iterations} iteration(s). "
            f"Tools: {[t['tool'] for t in tool_calls_made]}. "
            f"Delegating to Executor Agent."
        ),
        "tool_calls":   tool_calls_made,
        "context_keys": list(context.keys()),
        "timestamp":    timestamp
    })

    SecurityBlock.intercept(
        "Researcher", "Executor",
        {"context_keys": list(context.keys()), "tool_calls": len(tool_calls_made)},
        state
    )

    return state