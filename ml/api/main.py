from fastapi import FastAPI

app = FastAPI(
    title="eCommerce ML Intelligence API",
    description="Minimal API for health checks and future ML tasks.",
    version="1.0.0"
)

@app.get("/health")
def health_check():
    return {"status": "online", "message": "ML Intelligence Service is running."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
