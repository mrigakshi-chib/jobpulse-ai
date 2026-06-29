from fastapi import APIRouter

from app.services.scheduler import get_scheduler_status, scheduled_jobspy_scrape


router = APIRouter(
    prefix="/scheduler",
    tags=["Scheduler"],
)


@router.get("/status")
def scheduler_status():
    return get_scheduler_status()


@router.post("/run-now")
def run_scheduler_now():
    scheduled_jobspy_scrape()

    return {
        "message": "Scheduled scrape triggered manually"
    }