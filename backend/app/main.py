from fastapi import FastAPI

from app.database import Base, engine
from app.models.job import Job
from app.routes.jobs import router as jobs_router
from app.routes.scrape import router as scrape_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="JobPulse AI",
    description="AI-assisted job discovery and application tracker for freshers",
    version="0.1.0",
)

app.include_router(jobs_router)
app.include_router(scrape_router)


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


@app.get("/db-health")
def db_health_check():
    return {
        "database": "connected",
        "table": "jobs"
    }