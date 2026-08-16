import requests
import json
import time
import sys

def run_test(title, prompt):
    print(f"\n==================================================", flush=True)
    print(f">>> RUNNING: {title}", flush=True)
    print(f"Prompt: {prompt.strip()}", flush=True)
    try:
        t0 = time.time()
        r = requests.post(
            "http://localhost:8000/api/tasks/execute",
            json={"request": prompt, "user_id": "test_operator"},
            timeout=120
        )
        elapsed = time.time() - t0
        data = r.json()

        status = data.get("status")
        task_category = data.get("task_category")
        plan = data.get("plan")
        tool_log = data.get("tool_call_log", [])
        tools_called = [t.get("tool") for t in tool_log]
        exec_out = data.get("execution_output", {})
        audit_res = data.get("audit_result", {})
        telemetry = data.get("llm_telemetry", {})

        logical_calls = telemetry.get("total_logical_calls", "N/A")
        physical_attempts = telemetry.get("total_physical_attempts", "N/A")

        print(f"  [RESULT]", flush=True)
        print(f"  Overall Status:      {status}", flush=True)
        print(f"  Category:            {task_category}", flush=True)
        print(f"  Plan:                {plan}", flush=True)
        print(f"  Tools Selected:      {tools_called}", flush=True)
        print(f"  Logical LLM Calls:   {logical_calls}", flush=True)
        print(f"  Physical Attempts:   {physical_attempts}", flush=True)
        print(f"  Execution Output:    {exec_out.get('tool_called')} -> {exec_out.get('status')}", flush=True)
        print(f"  Audit Status:        {audit_res.get('audit_status')} ({audit_res.get('summary')})", flush=True)
        print(f"  Latency:             {elapsed:.1f}s", flush=True)
        print("  Final Report Preview:", flush=True)
        final_preview = (data.get("final_result") or "")[:400].encode("ascii", "ignore").decode()
        for line in final_preview.split("\n"):
            if line.strip():
                print(f"    {line.strip()}", flush=True)
        return True
    except Exception as e:
        print(f"  ERROR: {e}", flush=True)
        return False

# Run TEST 1
run_test("TEST 1 — Read-Only Balance Inquiry", "Show me the current balance of ACC-4821.")
