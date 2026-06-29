from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.company_scrape_runner import run_company_scrape


router = APIRouter(
    prefix="/scrape/companies",
    tags=["Company Career Pages"],
)


@router.post("/")
def scrape_company_career_pages(
    min_score: int = Query(default=60, ge=0, le=100),
    db: Session = Depends(get_db),
):
    return run_company_scrape(
        db=db,
        min_score=min_score,
    )