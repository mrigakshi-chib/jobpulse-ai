from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.data.company_sources import COMPANY_SOURCES
from app.models.job import Job
from app.scrapers.greenhouse_adapter import fetch_greenhouse_jobs
from app.scrapers.lever_adapter import fetch_lever_jobs
from app.services.dedupe import calculate_job_fingerprint
from app.services.scoring import calculate_job_score, is_fresher_friendly


def save_company_jobs_to_db(
    fetched_jobs: list[dict],
    db: Session,
    min_score: int = 60,
) -> dict:
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

        db.add(Job(**job_data))
        inserted_count += 1

    db.commit()

    return {
        "inserted": inserted_count,
        "skipped_duplicates": skipped_duplicates,
        "skipped_not_fresher_friendly": skipped_not_fresher_friendly,
        "skipped_low_score": skipped_low_score,
    }


def run_company_scrape(
    db: Session,
    min_score: int = 60,
) -> dict:
    total_fetched = 0
    total_inserted = 0
    total_skipped_duplicates = 0
    total_skipped_not_fresher_friendly = 0
    total_skipped_low_score = 0

    source_summaries = []

    enabled_sources = [
        source for source in COMPANY_SOURCES if source.get("enabled") is True
    ]

    for source in enabled_sources:
        company = source["company"]
        ats = source["ats"]
        token = source["token"]

        if ats == "greenhouse":
            fetched_jobs = fetch_greenhouse_jobs(company_name=company, board_token=token)
        elif ats == "lever":
            fetched_jobs = fetch_lever_jobs(company_name=company, company_token=token)
        else:
            fetched_jobs = []

        save_summary = save_company_jobs_to_db(
            fetched_jobs=fetched_jobs,
            db=db,
            min_score=min_score,
        )

        source_summary = {
            "company": company,
            "ats": ats,
            "token": token,
            "fetched": len(fetched_jobs),
            **save_summary,
        }

        source_summaries.append(source_summary)

        total_fetched += len(fetched_jobs)
        total_inserted += save_summary["inserted"]
        total_skipped_duplicates += save_summary["skipped_duplicates"]
        total_skipped_not_fresher_friendly += save_summary["skipped_not_fresher_friendly"]
        total_skipped_low_score += save_summary["skipped_low_score"]

    return {
        "message": "Company career scrape completed",
        "enabled_sources": len(enabled_sources),
        "total_fetched": total_fetched,
        "total_inserted": total_inserted,
        "total_skipped_duplicates": total_skipped_duplicates,
        "total_skipped_not_fresher_friendly": total_skipped_not_fresher_friendly,
        "total_skipped_low_score": total_skipped_low_score,
        "source_summaries": source_summaries,
    }