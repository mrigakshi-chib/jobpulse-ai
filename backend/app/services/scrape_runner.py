from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.job import Job
from app.scrapers.jobspy_adapter import fetch_jobs_from_jobspy
from app.services.dedupe import calculate_job_fingerprint
from app.services.scoring import calculate_job_score, is_fresher_friendly


DEFAULT_SEARCH_TERMS = [
    "software engineer fresher",
    "associate software engineer fresher",
    "graduate engineer trainee software",
    "software developer fresher",
    "junior software engineer",
    "junior backend developer fresher",
    "junior frontend developer fresher",
    "python developer fresher",
    "react developer fresher",
    "2025 batch software engineer",
]


def save_jobs_to_db(
    fetched_jobs: list[dict],
    db: Session,
    min_score: int = 65,
) -> dict:
    inserted_count = 0
    skipped_duplicates = 0
    skipped_not_fresher_friendly = 0
    skipped_low_score = 0

    seen_urls_this_run = set()
    seen_fingerprints_this_run = set()

    for job_data in fetched_jobs:
        job_data["score"] = calculate_job_score(job_data)
        job_data["fingerprint"] = calculate_job_fingerprint(job_data)

        if not is_fresher_friendly(job_data):
            skipped_not_fresher_friendly += 1
            continue

        if job_data["score"] < min_score:
            skipped_low_score += 1
            continue

        if (
            job_data["job_url"] in seen_urls_this_run
            or job_data["fingerprint"] in seen_fingerprints_this_run
        ):
            skipped_duplicates += 1
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

        seen_urls_this_run.add(job_data["job_url"])
        seen_fingerprints_this_run.add(job_data["fingerprint"])

        inserted_count += 1

    db.commit()

    return {
        "inserted": inserted_count,
        "skipped_duplicates": skipped_duplicates,
        "skipped_not_fresher_friendly": skipped_not_fresher_friendly,
        "skipped_low_score": skipped_low_score,
    }


def run_jobspy_scrape(
    db: Session,
    search_terms: Optional[list[str]] = None,
    location: str = "India",
    results_wanted_per_term: int = 25,
    min_score: int = 65,
    hours_old: int = 24,
) -> dict:
    if search_terms is None:
        search_terms = DEFAULT_SEARCH_TERMS

    total_fetched = 0
    total_inserted = 0
    total_skipped_duplicates = 0
    total_skipped_not_fresher_friendly = 0
    total_skipped_low_score = 0

    term_summaries = []

    for search_term in search_terms:
        fetched_jobs = fetch_jobs_from_jobspy(
            search_term=search_term,
            location=location,
            results_wanted=results_wanted_per_term,
            hours_old=hours_old,
        )

        save_summary = save_jobs_to_db(
            fetched_jobs=fetched_jobs,
            db=db,
            min_score=min_score,
        )

        term_summary = {
            "search_term": search_term,
            "fetched": len(fetched_jobs),
            **save_summary,
        }

        term_summaries.append(term_summary)

        total_fetched += len(fetched_jobs)
        total_inserted += save_summary["inserted"]
        total_skipped_duplicates += save_summary["skipped_duplicates"]
        total_skipped_not_fresher_friendly += save_summary["skipped_not_fresher_friendly"]
        total_skipped_low_score += save_summary["skipped_low_score"]

    return {
        "message": "JobSpy scrape completed",
        "location": location,
        "hours_old": hours_old,
        "min_score": min_score,
        "search_terms_count": len(search_terms),
        "total_fetched": total_fetched,
        "total_inserted": total_inserted,
        "total_skipped_duplicates": total_skipped_duplicates,
        "total_skipped_not_fresher_friendly": total_skipped_not_fresher_friendly,
        "total_skipped_low_score": total_skipped_low_score,
        "term_summaries": term_summaries,
    }