"""
Executor Agent — LLM Decisive Write Operation
===============================================
The Executor LLM reads the plan, original request, and researcher summary,
then makes ONE decisive tool call in its FIRST response.

Key optimisation over the original:
  Original: while loop up to 5 iterations with deliberation across turns.
  Fixed:    LLM is instructed to decide and act in its FIRST response.
            After the tool result comes back, it writes a one-sentence confirmation.
            Always exactly 2 LLM calls for any write task.

Why this stays fully autonomous:
  The LLM still decides WHICH write tool to call and WITH WHAT PARAMETERS.
  It reads the researcher_summary (from context) to extract exact IDs and amounts.
  A prompt injection attack can still manipulate this decision — for example
  causing the executor to call transfer_funds with a different receiver account.
  The Security Block in Phase 2 will detect this via the Provenance DAG and
  Behavioral Trust Engine.

Phase 1 Baseline — SecurityBlock is a pass-through hook only.
"""

import json
import logging
from datetime import datetime, timezone

from app.schemas.state import AgentState
from app.schemas.security_hooks import SecurityBlock
from app.services.llm_service import llm_service
from app.agents.tool_registry import EXECUTOR_TOOLS, execute_tool

logger = logging.getLogger("finsecure.executor")

EXECUTOR_SYSTEM_PROMPT = """\
You are the Executor Agent of FinSecure, an autonomous banking operations platform.
Your job is to perform the exact banking operation requested by the user.

CRITICAL PERFORMANCE RULE:
Make your decision and call the write tool in your VERY FIRST response.
Do not deliberate. You have the full research context — use it immediately.

Guidelines:
- VALID TOOLS: You have access to ONLY write tools: [transfer_funds, freeze_account, unfreeze_account, disburse_loan, update_fraud_case_status].
- PROHIBITION: Do NOT attempt to call read tools or hallucinate tool names like 'get_account_balance', 'get_account', 'fetch_balance', etc. These tools do NOT exist in this agent.
- READ-ONLY & POLICY QUESTIONS: If the user is asking a question, policy inquiry, balance check, transaction inquiry, or general question (e.g. "What is...", "Show me balance...", "Summarize policy...", "Explain...", "How much..."), do NOT call any tool. Output plain text confirming that research findings contain the requested information.
- WRITE ACTIONS: Only call a write tool (transfer_funds, freeze_account, unfreeze_account, disburse_loan, update_fraud_case_status) when the user explicitly commands a financial mutation (e.g. "Transfer ₹X", "Freeze account Y", "Disburse loan Z", "Approve transfer").
- Use the EXACT account IDs, loan IDs, case IDs, and amounts from the research findings. Do NOT substitute, invent, or guess values.
- If the research context shows an error for any required entity (e.g. account not found, loan not approved), do NOT attempt the operation. Instead produce a text response explaining the failure — do not call any tool.
- After the tool result is returned, produce ONE sentence confirming the outcome.
"""

MAX_TOOL_ITERATIONS = 4   # 2 is normal (call + confirm). 4 is a generous safety cap.


def executor_node(state: AgentState) -> AgentState:
    """
    Executor Agent Node — decisive LLM write tool execution.

    Iteration 1: LLM calls the appropriate write tool immediately.
    Tool execution: Python executes the tool safely from the allowlist.
    Iteration 2: LLM confirms the result in one sentence.
    Done.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    req       = state["original_request"]
    plan      = state.get("plan", [])
    context   = state.get("context", {})

    state.setdefault("tool_call_log", [])

    plan_text = "\n".join(plan) if plan else "No explicit plan provided."

    # ── Build the executor prompt from concise researcher summary ────────
    # We pass researcher_summary (a plain text paragraph) instead of the
    # full raw context dict — this keeps the prompt lean and fast.
    # ── Check if research failed before executing write actions ──────────
    if context.get("research_status") == "FAILED" or "research_error" in context:
        logger.warning("Executor: Research phase reported failure. Halting write operations.")
        exec_output = {
            "status": "FAILED",
            "error_type": "RESEARCH_FAILED",
            "error": f"Cannot execute operation because research phase failed: {context.get('research_error', 'Unknown research error')}",
            "tool_called": "none",
            "executor_summary": "Execution halted because prerequisites could not be researched."
        }
        state["execution_output"] = exec_output
        state["status"] = "AUDITING"
        state["agent_history"].append({
            "agent": "Executor",
            "action": "Research phase failed. Halting write operations safely.",
            "exec_summary": exec_output,
            "timestamp": timestamp
        })
        SecurityBlock.intercept("Executor", "Auditor", {"status": "FAILED", "tool_called": "none"}, state)
        return state

    researcher_summary = context.get(
        "researcher_summary",
        json.dumps(
            {k: v for k, v in context.items() if k != "researcher_summary"},
            default=str
        )[:1000]   # Hard cap on fallback context size
    )

    messages = [
        {"role": "system", "content": EXECUTOR_SYSTEM_PROMPT},
        {"role": "user",   "content": (
            f"User Request: {req}\n\n"
            f"Execution Plan:\n{plan_text}\n\n"
            f"Research Findings (use EXACT values from here):\n{researcher_summary}\n\n"
            "If a write operation (transfer, freeze, disburse, update) is needed, call the appropriate tool now. "
            "If this is a read-only request or no write action is required, respond with text stating research is complete."
        )}
    ]

    exec_output     = {}
    tool_calls_made = []
    iterations      = 0

    # ── Turn 1: LLM decides and calls write tool (or produces text) ──────
    choice, llm_result = llm_service.chat_with_tools(messages, EXECUTOR_TOOLS, agent="Executor")

    if not llm_result.success:
        logger.error(f"Executor: LLM call failed ({llm_result.error_type}). Stopping execution.")
        exec_output = {
            "status": "FAILED",
            "error_type": llm_result.error_type,
            "error": f"LLM failure ({llm_result.error_type}): {llm_result.error_message}",
            "tool_called": "none",
            "executor_summary": f"Execution halted due to LLM error: {llm_result.error_type}"
        }
        state["failure_stage"] = "Executor"
        state["execution_output"] = exec_output
        state["status"] = "AUDITING"
        state["agent_history"].append({
            "agent": "Executor",
            "action": f"Execution failed ({llm_result.error_type}).",
            "exec_summary": exec_output,
            "timestamp": timestamp
        })
        SecurityBlock.intercept("Executor", "Auditor", exec_output, state)
        return state

    msg = choice.message

    # ── Case 1: LLM called a write tool ─────────────────────────────────
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

            logger.info(f"Executor tool call: {tool_name}({tool_args})")
            tool_result = execute_tool(tool_name, tool_args)

            log_entry = {
                "agent":                           "Executor",
                "tool":                            tool_name,
                "tool_arguments_generated_by_llm": tc.function.arguments,
                "tool_arguments_sent_to_backend":  tool_args,
                "arguments":                       tool_args,
                "backend_result":                  tool_result,
                "result_status":                   tool_result.get("status", "unknown"),
                "timestamp":                       datetime.now(timezone.utc).isoformat()
            }
            state["tool_call_log"].append(log_entry)
            tool_calls_made.append(log_entry)

            exec_output = tool_result
            exec_output["tool_called"] = tool_name

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(tool_result)
            })

        # ── Turn 2: LLM produces one-sentence confirmation ───────────────
        choice2, llm_result2 = llm_service.chat_with_tools(messages, tools=None, agent="Executor")
        if llm_result2.success and choice2:
            exec_output["executor_summary"] = choice2.message.content or "Write tool executed."
        else:
            exec_output["executor_summary"] = "Write tool executed."

    # ── Case 2: LLM decided no write action was needed ──────────────────
    else:
        final_summary = msg.content or "No write action required for this request."
        exec_output = {
            "status": "SUCCESS",
            "message": final_summary,
            "tool_called": "none",
            "executor_summary": final_summary
        }

    logger.info(
        f"Executor completed: tool={exec_output.get('tool_called')}, status={exec_output.get('status')}."
    )

    state["execution_output"] = exec_output
    state["status"]           = "AUDITING"

    state["agent_history"].append({
        "agent":            "Executor",
        "action":           (
            f"LLM executed tool '{exec_output.get('tool_called', 'none')}'. "
            f"Status: {exec_output.get('status', 'unknown')}. "
            f"Delegating to Auditor Agent."
        ),
        "execution_summary": {
            k: v for k, v in exec_output.items()
            if k not in ("executor_summary",)
        },
        "timestamp":        timestamp
    })

    SecurityBlock.intercept(
        "Executor", "Auditor",
        {"execution_status": exec_output.get("status")},
        state
    )

    return state