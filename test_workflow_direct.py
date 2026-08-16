import sys
import os
sys.path.insert(0, os.path.abspath("backend"))

from app.agents.graph import finsecure_workflow
import json

prompt = "What's the current balance and last 5 transactions for account 4821?"
initial_state = {
    "task_id": "TEST-TASK-001",
    "user_id": "test_user",
    "original_request": prompt,
    "task_category": "UNKNOWN",
    "status": "PENDING",
    "plan": [],
    "context": {},
    "execution_request": {},
    "execution_output": {},
    "audit_result": {},
    "final_result": "",
    "errors": [],
    "timestamps": {},
    "agent_history": [],
    "audit_trail": [],
    "tool_call_log": [],
    "security_context": None,
    "trust_score": 1.0,
    "provenance_chain": []
}

print(f"Executing workflow for prompt: {prompt}")
final_state = finsecure_workflow.invoke(initial_state)

print("\n--- WORKFLOW EXECUTION RESULTS ---")
print(f"Task Category:  {final_state.get('task_category')}")
print(f"Status:         {final_state.get('status')}")
print(f"Plan:           {final_state.get('plan')}")
tools = [t["tool"] for t in final_state.get("tool_call_log", [])]
print(f"Tools called:   {tools}")
print(f"Audit status:   {final_state.get('audit_result', {}).get('audit_status')}")
print(f"Audit summary:  {final_state.get('audit_result', {}).get('validation_summary')}")
print("\n--- FINAL REPORT ---")
print(final_state.get("final_result", "")[:600])

from app.services.llm_service import get_total_llm_calls
print(f"\nTotal LLM calls in this run: {get_total_llm_calls()}")
