from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)

    source = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)

    job_url = Column(Text, nullable=False, unique=True)
    apply_url = Column(Text, nullable=True)

    fingerprint = Column(String(64), nullable=True, index=True)

    description = Column(Text, nullable=True)

    status = Column(String(50), nullable=False, default="new")
    score = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())