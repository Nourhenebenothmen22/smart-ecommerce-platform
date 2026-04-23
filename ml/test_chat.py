import sys
import os
import time

_ML_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ML_ROOT not in sys.path:
    sys.path.insert(0, _ML_ROOT)

from api.main import app
from fastapi.testclient import TestClient
from core.db import get_db_cursor

client = TestClient(app)

print("--- Testing /chat endpoint ---")
response = client.post("/chat", json={"query": "je cherche un iphone", "user_id": 1})
print(f"Status: {response.status_code}")
data = response.json()
print("Response JSON:")
import json
print(json.dumps(data, indent=2, ensure_ascii=False))

time.sleep(2) # Leave time to background task to log to DB

print("\n--- Verifying Database Interaction Logging ---")
try:
    with get_db_cursor() as cur:
        cur.execute("SELECT id, user_query, llm_response FROM chatbot_interactions ORDER BY created_at DESC LIMIT 1;")
        res = cur.fetchone()
        if res:
            print(f"SUCCESS! DB recorded interaction ID: {res[0]} | Query: {res[1]} | Response lengths: {len(res[2]) if res[2] else 0} chars")
        else:
            print("FAILURE! No record found in DB.")
except Exception as e:
    print(f"Database verification error: {e}")
