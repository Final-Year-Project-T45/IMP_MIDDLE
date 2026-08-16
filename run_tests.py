import requests, json

prompt = "What's the current balance and last 5 transactions for account 4821?"
print(f"Test: {prompt}")
r = requests.post("http://localhost:8000/api/tasks/execute", json={"request": prompt}, timeout=120)
data = r.json()
tool_log = data.get("tool_call_log", [])
agent_hist = data.get("agent_history", [])

print(f"Category:     {data.get('task_category')}")
print(f"Tools called: {[t['tool'] for t in tool_log]}")
print(f"Agent hops:   {len(agent_hist)}")
print(f"Audit status: {data.get('audit_result', {}).get('audit_status')}")
print()
final = (data.get("final_result") or "")[:500].encode("ascii", "ignore").decode()
print(f"Final result preview:\n{final}")
print()
print("--- Tool call log ---")
for t in tool_log:
    args_keys = list(t.get("arguments", {}).keys())
    print(f"  [{t['agent']}] {t['tool']}({args_keys}) -> {t['result_status']}")

# Check for error sentinels that should NOT appear
final_result = data.get("final_result", "")
if "__LLM_ERROR::" in final_result:
    print("\nWARN: LLM error sentinel found in final_result!")
elif "Groq LLM client not initialized" in final_result:
    print("\nFAIL: Old error message still appearing in output!")
else:
    print("\nPASS: No error sentinels in final_result.")

# Check audit
audit = data.get("audit_result", {})
if "Expecting value" in str(audit):
    print("FAIL: JSON parse error leaked into audit_result!")
else:
    print("PASS: No JSON parse errors in audit_result.")
