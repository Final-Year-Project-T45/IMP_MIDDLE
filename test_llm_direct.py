import sys
import os
sys.path.insert(0, os.path.abspath("backend"))

from app.services.llm_service import llm_service
from app.agents.tool_registry import RESEARCHER_TOOLS

print("Testing generate()...")
res = llm_service.generate("Hello world", agent="TestAgent")
print("generate result:", res[:100])

print("\nTesting generate_json()...")
json_res = llm_service.generate_json("Return a JSON with key 'greeting' and value 'hello'", agent="TestAgent")
print("generate_json result:", json_res)

print("\nTesting chat_with_tools()...")
choice, result = llm_service.chat_with_tools(
    [{"role": "user", "content": "What is the balance of account 4821?"}],
    RESEARCHER_TOOLS,
    agent="TestAgent"
)
print("chat_with_tools success:", result.success)
if choice and choice.message.tool_calls:
    print("tool calls:", [tc.function.name for tc in choice.message.tool_calls])
elif choice:
    print("content:", choice.message.content)
