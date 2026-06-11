from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class JobBase(BaseModel):
    source: str
    title: str
    company: str
    location: Optional[str] = None
    job_url: str
    apply_url: Optional[str] = None
    description: Optional[str] = None
    status: str = "new"
    score: int = 0


class JobCreate(JobBase):
    pass


class JobResponse(JobBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True