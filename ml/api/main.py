from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import psycopg2
from typing import List
import os

from core.config import settings
from seeder.core import seed_user_features

app = FastAPI(
    title="eCommerce ML Intelligence API",
    description="API for ML model registration, feature computation, and segmentation.",
    version="1.0.0"
)

# ─── MODELS ──────────────────────────────────────────────────

class SegmentUpdate(BaseModel):
    user_id: int
    segment_id: int
    segment_label: str
    model_name: str
    model_version: str
    confidence: float = None

class BatchSegments(BaseModel):
    segments: List[SegmentUpdate]

# ─── ENDPOINTS ────────────────────────────────────────────────

@app.get("/health")
def health_check():
    return {"status": "online", "message": "ML Intelligence Service is running."}

@app.post("/trigger/recalculate-features")
def trigger_recalculate_features(background_tasks: BackgroundTasks):
    """
    Triggers the SQL-based feature recalculation for all users.
    Executed as a background task to avoid blocking.
    """
    background_tasks.add_task(run_feature_computation)
    return {"success": True, "message": "User feature recalculation started in background."}

# ─── HELPERS ──────────────────────────────────────────────────

def run_feature_computation():
    """
    Connects to DB and runs the unified SQL upsert logic.
    """
    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(**settings.db_config_dict)
        cursor = conn.cursor()
        seed_user_features(cursor, conn)
        print("✅ Background Task: User features recalculated successfully.")
    except Exception as e:
        print(f"❌ Background Task Error: {e}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
