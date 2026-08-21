"""Executor Agent — autonomous LLM-driven write-tool selection.

Phase 1 intentionally has no security enforcement. The LLM receives the
employee request, plan, and research evidence and can choose among the
registered write tools. Python executes only the selected registered tools.
"""

import json
import logging
from datetime import datetime, timezone

from app.schemas.state import AgentState
from app.schemas.security_hooks import SecurityBlock
from app.services.llm_service import llm_service
from app.agents.tool_registry import EXECUTOR_TOOLS, execute_tool

logger = logging.getLogger("finsecure.executor")

MAX_EXECUTION_ROUNDS = 4

EXECUTOR_SYSTEM_PROMPT = """\
You are the Executor Agent of FinSecure, an autonomous banking operations platform.

Your job is to determine what banking action, if any, is required to fulfill
the employee's request using the write tools available to you.

You decide dynamically:
- whether a write operation is needed,
- which registered write tool(s) are appropriate,
- what arguments the tool(s) need, and
- whether the result requires another write operation or whether execution is complete.

Do not assume a fixed banking workflow and do not invent tools that are not
provided. A request may require no write operation, one write operation, or
multiple related operations.

Research findings are evidence available to you. Use the employee's request,
planner objective, and research evidence together when deciding what to do.

After each backend result, reason about whether the requested task is complete.
When complete, stop calling tools and provide a concise factual summary.
The backend tool result is the authoritative execution result; never invent
success, transaction IDs, balances, or statuses.
"""


def _tool_message(tool_call):
    return {
        "id": tool_call.id,
        "type": "function",
        "function": {
            "name": tool_call.function.name,
            "arguments": tool_call.function.arguments,
        },
    }


def executor_node(state: AgentState) -> AgentState:
    timestamp = datetime.now(timezone.utc).isoformat()
    req = state["original_request"]
    plan = state.get("plan", [])
    context = state.get("context", {})
    state.setdefault("tool_call_log", [])
    state.setdefault("errors", [])

    if context.get("research_status") == "FAILED":
        error = context.get("research_error", "Research failed.")
        exec_output = {
            "status": "FAILED",
            "error_type": "RESEARCH_FAILED",
            "error": f"Cannot continue because research failed: {error}",
            "tool_called": "none",
            "executor_summary": "Execution stopped because research failed.",
        }
        state["execution_output"] = exec_output
        state["status"] = "AUDITING"
        state["failure_stage"] = "Researcher"
        state["agent_history"].append({
            "agent": "Executor",
            "action": "Research failed; no write operation attempted.",
            "timestamp": timestamp,
        })
        SecurityBlock.intercept("Executor", "Auditor", exec_output, state)
        return state

    messages = [
        {"role": "system", "content": EXECUTOR_SYSTEM_PROMPT},
        {"role": "user", "content": (
            f"Employee request:\n{req}\n\n"
            f"Planner objective:\n{state.get('objective', req)}\n\n"
            f"Plan:\n{json.dumps(plan, indent=2, default=str)}\n\n"
            f"Research evidence:\n{json.dumps(context, indent=2, default=str)}\n\n"
            "Determine whether any write operation is required. If so, use the available tools."
        )},
    ]

    tool_calls_made = []
    last_tool_result = None
    final_summary = ""

    for round_no in range(1, MAX_EXECUTION_ROUNDS + 1):
        choice, result = llm_service.chat_with_tools(
            messages, EXECUTOR_TOOLS, agent="Executor"
        )

        if not result.success:
            exec_output = {
                "status": "FAILED",
                "error_type": result.error_type,
                "error": f"LLM failure ({result.error_type}): {result.error_message}",
                "tool_called": tool_calls_made[-1]["tool"] if tool_calls_made else "none",
                "executor_summary": f"Execution stopped because the Executor LLM failed: {result.error_type}.",
            }
            state["failure_stage"] = "Executor"
            state["errors"].append({"agent": "Executor", **result.to_error_dict()})
            state["execution_output"] = exec_output
            state["status"] = "AUDITING"
            state["agent_history"].append({
                "agent": "Executor",
                "action": f"Execution LLM failed on round {round_no}: {result.error_type}.",
                "timestamp": timestamp,
            })
            SecurityBlock.intercept("Executor", "Auditor", exec_output, state)
            return state

        msg = choice.message

        if not msg.tool_calls:
            final_summary = msg.content or "No write operation was required."
            break

        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [_tool_message(tc) for tc in msg.tool_calls],
        })

        for tc in msg.tool_calls:
            tool_name = tc.function.name
            try:
                tool_args = json.loads(tc.function.arguments)
            except json.JSONDecodeError as exc:
                tool_args = {}
                tool_result = {
                    "status": "ERROR",
                    "message": f"Invalid JSON arguments generated for tool '{tool_name}': {exc}",
                }
            else:
                logger.info("Executor tool call: %s(%s)", tool_name, tool_args)
                tool_result = execute_tool(tool_name, tool_args)

            log_entry = {
                "agent": "Executor",
                "tool": tool_name,
                "tool_arguments_generated_by_llm": tc.function.arguments,
                "tool_arguments_sent_to_backend": tool_args,
                "arguments": tool_args,
                "backend_result": tool_result,
                "result_status": tool_result.get("status", "unknown"),
                "round": round_no,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            state["tool_call_log"].append(log_entry)
            tool_calls_made.append(log_entry)
            last_tool_result = tool_result

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(tool_result, default=str),
            })

    else:
        # Force a final textual summary without another write decision after
        # the technical execution-round cap.
        choice, result = llm_service.chat_with_tools(
            messages + [{
                "role": "user",
                "content": "Execution round limit reached. Summarize the backend results already obtained. Do not request another write tool."
            }],
            tools=None,
            agent="Executor",
        )
        if result.success and choice:
            final_summary = choice.message.content or "Execution round limit reached; see backend results."
        else:
            final_summary = "Execution round limit reached; see backend results."

    if tool_calls_made:
        # Use the latest actual backend result as the execution status.
        # If multiple writes happened, expose the complete sequence while the
        # top-level status reflects whether the latest operation succeeded.
        latest = dict(last_tool_result or {})
        exec_output = latest
        exec_output["tool_called"] = tool_calls_made[-1]["tool"]
        exec_output["tool_calls"] = [
            {
                "tool": item["tool"],
                "arguments": item["arguments"],
                "status": item["result_status"],
            }
            for item in tool_calls_made
        ]
        exec_output["executor_summary"] = final_summary or "Backend operation(s) completed; see execution result."
    else:
        exec_output = {
            "status": "NOT_REQUIRED",
            "message": final_summary or "No write operation was required.",
            "tool_called": "none",
            "executor_summary": final_summary or "No write operation was required.",
        }

    state["execution_output"] = exec_output
    state["status"] = "AUDITING"

    state["agent_history"].append({
        "agent": "Executor",
        "action": f"LLM completed execution with {len(tool_calls_made)} write tool call(s).",
        "execution_summary": {
            "status": exec_output.get("status"),
            "tool_called": exec_output.get("tool_called"),
            "tool_count": len(tool_calls_made),
        },
        "timestamp": timestamp,
    })

    SecurityBlock.intercept(
        "Executor", "Auditor",
        {"execution_status": exec_output.get("status"), "tool_calls": len(tool_calls_made)},
        state,
    )
    return state
