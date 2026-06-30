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

router = APIRouter(prefix="/jobs", tags=["jobs"])


def schema_to_dict(schema, exclude_unset: bool = False):
    if hasattr(schema, "model_dump"):
        return schema.model_dump(exclude_unset=exclude_unset)

    return schema.dict(exclude_unset=exclude_unset)


@router.post("/", response_model=JobResponse, status_code=201)
def create_job(job: JobCreate, db: Session = Depends(get_db)):
    job_data = schema_to_dict(job)

    fingerprint = calculate_job_fingerprint(
        title=job.title,
        company=job.company,
        location=job.location,
    )

    existing_job = (
        db.query(Job)
        .filter(
            or_(
                Job.job_url == job.job_url,
                Job.fingerprint == fingerprint,
            )
        )
        .first()
    )

    if existing_job:
        raise HTTPException(
            status_code=409,
            detail="Job already exists",
        )

    score = calculate_job_score(
        title=job.title,
        description=job.description or "",
    )

    new_job = Job(
        **job_data,
        fingerprint=fingerprint,
        score=score,
    )

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
    locations: Optional[str] = Query(default=None),
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

    if location:
        location_pattern = f"%{location}%"
        query = query.filter(Job.location.ilike(location_pattern))

    if locations:
        location_terms = [
            term.strip()
            for term in locations.split(",")
            if term.strip()
        ]

        if location_terms:
            query = query.filter(
                or_(
                    *[
                        Job.location.ilike(f"%{term}%")
                        for term in location_terms
                    ]
                )
            )

    if target_role:
        role = target_role.lower().strip()

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
                    Job.description.ilike("%node%"),
                )
            )

        elif role == "frontend":
            query = query.filter(
                or_(
                    Job.title.ilike("%frontend%"),
                    Job.title.ilike("%front end%"),
                    Job.title.ilike("%react%"),
                    Job.title.ilike("%next%"),
                    Job.title.ilike("%web developer%"),
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
                    Job.title.ilike("%full-stack%"),
                    Job.title.ilike("%fullstack%"),
                    Job.title.ilike("%mern%"),
                    Job.description.ilike("%full stack%"),
                    Job.description.ilike("%full-stack%"),
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
                    Job.title.ilike("%junior software developer%"),
                    Job.title.ilike("%backend developer%"),
                    Job.title.ilike("%backend engineer%"),
                    Job.title.ilike("%frontend developer%"),
                    Job.title.ilike("%frontend engineer%"),
                    Job.title.ilike("%front end developer%"),
                    Job.title.ilike("%full stack developer%"),
                    Job.title.ilike("%full-stack developer%"),
                    Job.title.ilike("%python developer%"),
                    Job.title.ilike("%java developer%"),
                    Job.title.ilike("%react developer%"),
                    Job.title.ilike("%node developer%"),
                    Job.title.ilike("%web developer%"),
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
        query = query.filter(
            ~or_(
                Job.title.ilike("%intern%"),
                Job.title.ilike("%internship%"),
                Job.title.ilike("%trainee intern%"),
                Job.description.ilike("%internship%"),
                Job.description.ilike("%intern%"),
            )
        )

    if exclude_testing_roles:
        query = query.filter(
            ~or_(
                Job.title.ilike("%test%"),
                Job.title.ilike("%testing%"),
                Job.title.ilike("%qa%"),
                Job.title.ilike("%quality assurance%"),
                Job.title.ilike("%sdet%"),
                Job.title.ilike("%automation tester%"),
                Job.title.ilike("%manual tester%"),
                Job.title.ilike("%validation%"),
                Job.title.ilike("%support%"),
            )
        )

    if exclude_non_target_roles:
        query = query.filter(
        ~or_(
            Job.title.ilike("%senior%"),
            Job.title.ilike("%sr.%"),
            Job.title.ilike("%lead%"),
            Job.title.ilike("%staff%"),
            Job.title.ilike("%principal%"),
            Job.title.ilike("%architect%"),
            Job.title.ilike("%manager%"),
            Job.title.ilike("%director%"),
            Job.title.ilike("%head%"),
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
            Job.title.ilike("%data engineer%"),
            Job.title.ilike("%customer success%"),
            Job.title.ilike("%customer support%"),
            Job.title.ilike("%technical support%"),
            Job.title.ilike("%sales%"),
            Job.title.ilike("%marketing%"),
        )
    )

    if has_follow_up is True:
        query = query.filter(Job.follow_up_date.isnot(None))

    if has_follow_up is False:
        query = query.filter(Job.follow_up_date.is_(None))

    if follow_up_before:
        query = query.filter(Job.follow_up_date <= follow_up_before)

    jobs = query.order_by(Job.score.desc(), Job.created_at.desc()).all()

    return jobs


@router.get("/stats")
def get_job_stats(db: Session = Depends(get_db)):
    total_jobs = db.query(func.count(Job.id)).scalar() or 0

    high_score_jobs = (
        db.query(func.count(Job.id))
        .filter(Job.score >= 65)
        .scalar()
        or 0
    )

    follow_ups_due = (
        db.query(func.count(Job.id))
        .filter(
            Job.follow_up_date.isnot(None),
            Job.follow_up_date <= date.today(),
            Job.status != "not_relevant",
        )
        .scalar()
        or 0
    )

    status_rows = (
        db.query(Job.status, func.count(Job.id))
        .group_by(Job.status)
        .all()
    )

    source_rows = (
        db.query(Job.source, func.count(Job.id))
        .group_by(Job.source)
        .all()
    )

    status_counts = {
        status_value or "unknown": count
        for status_value, count in status_rows
    }

    source_counts = {
        source_value or "unknown": count
        for source_value, count in source_rows
    }

    return {
        "total_jobs": total_jobs,
        "high_score_jobs": high_score_jobs,
        "follow_ups_due": follow_ups_due,
        "status_counts": status_counts,
        "source_counts": source_counts,
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
def update_job_application(
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

    update_data = schema_to_dict(application_update, exclude_unset=True)

    for field, value in update_data.items():
        setattr(job, field, value)

    db.commit()
    db.refresh(job)

    return job