from fastapi import FastAPI

app = FastAPI(
    title="JobPulse AI",
    description="AI-assisted job discovery and application tracker for freshers",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "message": "JobPulse AI backend is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }