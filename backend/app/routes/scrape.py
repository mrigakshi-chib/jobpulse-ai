from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.job import Job
from app.scrapers.jobspy_adapter import fetch_jobs_from_jobspy
from app.services.dedupe import calculate_job_fingerprint
from app.services.scoring import calculate_job_score, is_fresher_friendly


router = APIRouter(
    prefix="/scrape",
    tags=["Scraping"],
)


@router.post("/jobspy")
def scrape_jobspy_jobs(
    search_term: str = Query(default="software engineer fresher"),
    location: str = Query(default="India"),
    results_wanted: int = Query(default=25, ge=1, le=100),
    min_score: int = Query(default=65, ge=0, le=100),
    hours_old: int = Query(default=24, ge=1, le=168),
    db: Session = Depends(get_db),
):
    fetched_jobs = fetch_jobs_from_jobspy(
        search_term=search_term,
        location=location,
        results_wanted=results_wanted,
        hours_old=hours_old,
    )

    inserted_count = 0
    skipped_duplicates = 0
    skipped_not_fresher_friendly = 0
    skipped_low_score = 0

    for job_data in fetched_jobs:
        job_data["score"] = calculate_job_score(job_data)
        job_data["fingerprint"] = calculate_job_fingerprint(job_data)

        if not is_fresher_friendly(job_data):
            skipped_not_fresher_friendly += 1
            continue

        if job_data["score"] < min_score:
            skipped_low_score += 1
            continue

        existing_job = (
            db.query(Job)
            .filter(
                or_(
                    Job.job_url == job_data["job_url"],
                    Job.fingerprint == job_data["fingerprint"],
                )
            )
            .first()
        )

        if existing_job:
            skipped_duplicates += 1
            continue

        new_job = Job(**job_data)
        db.add(new_job)
        inserted_count += 1

    db.commit()

    return {
        "message": "JobSpy scrape completed",
        "search_term": search_term,
        "location": location,
        "hours_old": hours_old,
        "fetched": len(fetched_jobs),
        "inserted": inserted_count,
        "skipped_duplicates": skipped_duplicates,
        "skipped_not_fresher_friendly": skipped_not_fresher_friendly,
        "skipped_low_score": skipped_low_score,
        "min_score": min_score,
    }