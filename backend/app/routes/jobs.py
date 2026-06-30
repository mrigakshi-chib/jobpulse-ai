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
    target_role: Optional[str] = Query(default=None),
    exclude_internships: bool = Query(default=False),
    exclude_testing_roles: bool = Query(default=False),
    exclude_non_target_roles: bool = Query(default=False),
    exclude_not_relevant: bool = Query(default=False),
    has_follow_up: Optional[bool] = Query(default=None),
    follow_up_before: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(Job)

    if status:
        query = query.filter(Job.status == status)
    
    if exclude_not_relevant:
        query = query.filter(Job.status != "not_relevant")

    if source:
        query = query.filter(Job.source == source)

    if location:
        location_pattern = f"%{location}%"
        query = query.filter(Job.location.ilike(location_pattern))

    if target_role:
        role = target_role.lower()

        if role == "backend":
            query = query.filter(
                or_(
                    Job.title.ilike("%backend%"),
                    Job.title.ilike("%back end%"),
                    Job.title.ilike("%python%"),
                    Job.title.ilike("%java%"),
                    Job.title.ilike("%node%"),
                    Job.title.ilike("%api%"),
                    Job.description.ilike("%backend%"),
                    Job.description.ilike("%rest api%"),
                    Job.description.ilike("%fastapi%"),
                    Job.description.ilike("%django%"),
                    Job.description.ilike("%spring%"),
                )
            )

        elif role == "frontend":
            query = query.filter(
                or_(
                    Job.title.ilike("%frontend%"),
                    Job.title.ilike("%front end%"),
                    Job.title.ilike("%react%"),
                    Job.title.ilike("%next%"),
                    Job.description.ilike("%frontend%"),
                    Job.description.ilike("%react%"),
                    Job.description.ilike("%javascript%"),
                    Job.description.ilike("%typescript%"),
                    Job.description.ilike("%next.js%"),
                )
            )

        elif role == "fullstack":
            query = query.filter(
                or_(
                    Job.title.ilike("%full stack%"),
                    Job.title.ilike("%fullstack%"),
                    Job.title.ilike("%mern%"),
                    Job.description.ilike("%full stack%"),
                    Job.description.ilike("%fullstack%"),
                    Job.description.ilike("%react%"),
                    Job.description.ilike("%node%"),
                )
            )

        elif role == "software":
            query = query.filter(
                or_(
                    Job.title.ilike("%software engineer%"),
                    Job.title.ilike("%software developer%"),
                    Job.title.ilike("%associate software engineer%"),
                    Job.title.ilike("%junior software engineer%"),
                    Job.title.ilike("%developer%"),
                )
            )

        elif role == "python":
            query = query.filter(
                or_(
                    Job.title.ilike("%python%"),
                    Job.description.ilike("%python%"),
                )
            )

        elif role == "react":
            query = query.filter(
                or_(
                    Job.title.ilike("%react%"),
                    Job.description.ilike("%react%"),
                    Job.description.ilike("%next.js%"),
                )
            )

        elif role == "java":
            query = query.filter(
                or_(
                    Job.title.ilike("%java%"),
                    Job.description.ilike("%java%"),
                    Job.description.ilike("%spring%"),
                )
            )

        elif role == "node":
            query = query.filter(
                or_(
                    Job.title.ilike("%node%"),
                    Job.description.ilike("%node%"),
                    Job.description.ilike("%express%"),
                )
            )

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

    if exclude_non_target_roles:
        query = query.filter(
            ~or_(
                Job.title.ilike("%release%"),
                Job.title.ilike("%devops%"),
                Job.title.ilike("%site reliability%"),
                Job.title.ilike("%sre%"),
                Job.title.ilike("%embedded%"),
                Job.title.ilike("%firmware%"),
                Job.title.ilike("%hardware%"),
                Job.title.ilike("%validation%"),
                Job.title.ilike("%support%"),
                Job.title.ilike("%consultant%"),
                Job.title.ilike("%business analyst%"),
                Job.title.ilike("%data analyst%"),
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