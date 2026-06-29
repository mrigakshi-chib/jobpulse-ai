from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.scrape_runner import DEFAULT_SEARCH_TERMS, run_jobspy_scrape


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
    return run_jobspy_scrape(
        db=db,
        search_terms=[search_term],
        location=location,
        results_wanted_per_term=results_wanted,
        min_score=min_score,
        hours_old=hours_old,
    )


@router.post("/jobspy/batch")
def scrape_jobspy_batch(
    location: str = Query(default="India"),
    results_wanted_per_term: int = Query(default=15, ge=1, le=50),
    min_score: int = Query(default=65, ge=0, le=100),
    hours_old: int = Query(default=24, ge=1, le=168),
    db: Session = Depends(get_db),
):
    return run_jobspy_scrape(
        db=db,
        search_terms=DEFAULT_SEARCH_TERMS,
        location=location,
        results_wanted_per_term=results_wanted_per_term,
        min_score=min_score,
        hours_old=hours_old,
    )