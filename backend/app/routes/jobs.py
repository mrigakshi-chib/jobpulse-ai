from datetime import date, datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.job import Job
from app.schemas.job import (
    JobApplicationUpdate,
    JobCreate,
    JobResponse,
    JobStatusUpdate,
)
from app.services.dedupe import calculate_job_fingerprint
from app.services.scoring import calculate_job_score


router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"],
)


@router.post("/", response_model=JobResponse)
def create_job(job: JobCreate, db: Session = Depends(get_db)):
    job_data = job.model_dump()
    job_data["score"] = calculate_job_score(job_data)
    job_data["fingerprint"] = calculate_job_fingerprint(job_data)

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
        raise HTTPException(
            status_code=400,
            detail="Duplicate job already exists",
        )

    new_job = Job(**job_data)

    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    return new_job


@router.get("/", response_model=List[JobResponse])
def get_jobs(
    status: Optional[str] = Query(default=None),
    source: Optional[str] = Query(default=None),
    min_score: Optional[int] = Query(default=None, ge=0, le=100),
    search: Optional[str] = Query(default=None),
    location: Optional[str] = Query(default=None),
    exclude_internships: bool = Query(default=False),
    exclude_testing_roles: bool = Query(default=False),
    has_follow_up: Optional[bool] = Query(default=None),
    follow_up_before: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(Job)

    if status:
        query = query.filter(Job.status == status)

    if source:
        query = query.filter(Job.source == source)

    if location:
        location_pattern = f"%{location}%"
        query = query.filter(Job.location.ilike(location_pattern))

    if exclude_internships:
        query = query.filter(~Job.title.ilike("%intern%"))
        query = query.filter(~Job.description.ilike("%internship%"))

    if exclude_testing_roles:
        query = query.filter(
            ~or_(
                Job.title.ilike("%test%"),
                Job.title.ilike("%testing%"),
                Job.title.ilike("%qa%"),
                Job.title.ilike("%quality assurance%"),
                Job.title.ilike("%sdet%"),
                Job.title.ilike("%validation%"),
                Job.title.ilike("%support%"),
            )
        )

    if min_score is not None:
        query = query.filter(Job.score >= min_score)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Job.title.ilike(search_pattern),
                Job.company.ilike(search_pattern),
                Job.location.ilike(search_pattern),
                Job.description.ilike(search_pattern),
            )
        )

    if has_follow_up is True:
        query = query.filter(Job.follow_up_date.isnot(None))

    if has_follow_up is False:
        query = query.filter(Job.follow_up_date.is_(None))

    if follow_up_before:
        query = query.filter(Job.follow_up_date <= follow_up_before)

    jobs = query.order_by(Job.created_at.desc()).all()

    return jobs

@router.get("/stats")
def get_job_stats(db: Session = Depends(get_db)):
    total_jobs = db.query(Job).count()

    status_counts = (
        db.query(Job.status, func.count(Job.id))
        .group_by(Job.status)
        .all()
    )

    source_counts = (
        db.query(Job.source, func.count(Job.id))
        .group_by(Job.source)
        .all()
    )

    high_score_jobs = db.query(Job).filter(Job.score >= 80).count()

    follow_ups_due = (
        db.query(Job)
        .filter(Job.follow_up_date.isnot(None))
        .filter(Job.follow_up_date <= date.today())
        .count()
    )

    return {
        "total_jobs": total_jobs,
        "high_score_jobs": high_score_jobs,
        "follow_ups_due": follow_ups_due,
        "status_counts": {
            status: count for status, count in status_counts
        },
        "source_counts": {
            source: count for source, count in source_counts
        },
    }

@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    return job


@router.patch("/{job_id}/status", response_model=JobResponse)
def update_job_status(
    job_id: int,
    status_update: JobStatusUpdate,
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    job.status = status_update.status

    if status_update.status == "applied" and job.applied_at is None:
        job.applied_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(job)

    return job


@router.patch("/{job_id}/application", response_model=JobResponse)
def update_job_application_details(
    job_id: int,
    application_update: JobApplicationUpdate,
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    update_data = application_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(job, field, value)

    db.commit()
    db.refresh(job)

    return job