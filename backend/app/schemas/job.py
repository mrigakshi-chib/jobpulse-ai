from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel


JobStatus = Literal[
    "new",
    "saved",
    "applied",
    "rejected",
    "not_relevant",
    "interview",
    "offer",
]


class JobBase(BaseModel):
    source: str
    title: str
    company: str
    location: Optional[str] = None
    job_url: str
    apply_url: Optional[str] = None
    description: Optional[str] = None
    status: JobStatus = "new"
    score: int = 0


class JobCreate(JobBase):
    pass


class JobStatusUpdate(BaseModel):
    status: JobStatus


class JobApplicationUpdate(BaseModel):
    applied_at: Optional[datetime] = None
    follow_up_date: Optional[date] = None
    notes: Optional[str] = None
    resume_version: Optional[str] = None


class JobResponse(JobBase):
    id: int
    fingerprint: Optional[str] = None

    applied_at: Optional[datetime] = None
    follow_up_date: Optional[date] = None
    notes: Optional[str] = None
    resume_version: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True