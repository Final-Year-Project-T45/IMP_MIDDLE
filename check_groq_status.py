import os
import time
from groq import Groq
from dotenv import load_dotenv

load_dotenv("backend/.env")
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]

for m in models:
    print(f"Testing model: {m}...")
    try:
        t0 = time.time()
        res = client.chat.completions.create(
            model=m,
            messages=[{"role": "user", "content": "Say OK"}],
            max_tokens=10
        )
        latency = (time.time() - t0) * 1000
        print(f"  -> SUCCESS! Response: '{res.choices[0].message.content.strip()}' (took {latency:.0f}ms)")
    except Exception as e:
        print(f"  -> FAILED: {e}")
