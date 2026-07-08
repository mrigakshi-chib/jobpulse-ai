from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.data.company_sources import COMPANY_SOURCES
from app.models.job import Job
from app.scrapers.greenhouse_adapter import fetch_greenhouse_jobs
from app.scrapers.lever_adapter import fetch_lever_jobs
from app.services.dedupe import calculate_job_fingerprint
from app.services.scoring import calculate_job_score


BAD_TITLE_KEYWORDS = [
    # Senior / non-entry roles
    "senior",
    "sr.",
    "lead",
    "principal",
    "architect",
    "manager",
    "director",
    "head",
    "vp",
    "vice president",

    # Non-target roles
    "qa",
    "quality assurance",
    "test",
    "testing",
    "sdet",
    "validation",
    "support",
    "technical support",
    "customer support",
    "devops",
    "site reliability",
    "sre",
    "release",
    "embedded",
    "firmware",
    "hardware",
    "sales",
    "marketing",
    "business analyst",
    "data analyst",
    "data engineer",
    "solutions engineer",
    "customer success",
]

BAD_COMPANY_KEYWORDS = [
    "retail hiring",
    "jewellery",
    "jewelry",
    "hiring",
    "recruitment",
    "staffing",
    "placement",
    "consultancy",
    "consultants",
    "manpower",
    "hr services",
]

GOOD_TITLE_KEYWORDS = [
    # Fresher / junior / associate roles
    "associate software engineer",
    "associate software developer",
    "junior software engineer",
    "junior software developer",
    "software engineer i",
    "software developer i",
    "sde i",
    "sde-i",
    "sde 1",
    "sde-1",
    "sde1",
    "software development engineer",

    # General target software roles
    "software engineer",
    "software developer",
    "backend engineer",
    "backend developer",
    "back end engineer",
    "back end developer",
    "frontend engineer",
    "frontend developer",
    "front end engineer",
    "front end developer",
    "full stack engineer",
    "full stack developer",
    "full-stack engineer",
    "full-stack developer",
    "fullstack engineer",
    "fullstack developer",
    "web developer",

    # Tech-specific roles
    "python developer",
    "java developer",
    "react developer",
    "node developer",
    "javascript developer",
    "typescript developer",

    # Trainee / new grad / intern
    "graduate engineer trainee",
    "software engineer trainee",
    "trainee software engineer",
    "software developer trainee",
    "engineering intern",
    "engineer intern",
    "software engineer intern",
    "software developer intern",
    "backend developer intern",
    "frontend developer intern",
    "full stack developer intern",
    "web developer intern",

    # Some company pages use this title
    "member of technical staff",
]
def is_good_company_job(job: dict) -> bool:
    title = (job.get("title") or "").lower()
    company = (job.get("company") or "").lower()
    job_url = job.get("job_url")

    if not title or not company or not job_url:
        return False

    if any(keyword in title for keyword in BAD_TITLE_KEYWORDS):
        return False

    if any(keyword in company for keyword in BAD_COMPANY_KEYWORDS):
        return False

    if not any(keyword in title for keyword in GOOD_TITLE_KEYWORDS):
        return False

    return True


def get_job_score(job_data: dict) -> int:
    title = job_data.get("title") or ""
    description = job_data.get("description") or ""

    try:
        return calculate_job_score(title=title, description=description)
    except TypeError:
        return calculate_job_score(job_data)


def get_job_fingerprint(job_data: dict) -> str:
    title = job_data.get("title") or ""
    company = job_data.get("company") or ""
    location = job_data.get("location") or ""

    try:
        return calculate_job_fingerprint(
            title=title,
            company=company,
            location=location,
        )
    except TypeError:
        return calculate_job_fingerprint(job_data)


def save_company_jobs_to_db(
    fetched_jobs: list[dict],
    db: Session,
    min_score: int = 60,
) -> dict:
    inserted_count = 0
    skipped_duplicates = 0
    skipped_non_target_role = 0
    skipped_low_score = 0

    seen_urls_this_run = set()
    seen_fingerprints_this_run = set()

    for job_data in fetched_jobs:
        if not is_good_company_job(job_data):
            skipped_non_target_role += 1
            continue

        job_data["score"] = get_job_score(job_data)
        job_data["fingerprint"] = get_job_fingerprint(job_data)

        if job_data["score"] < min_score:
            skipped_low_score += 1
            continue

        job_url = job_data.get("job_url")
        fingerprint = job_data.get("fingerprint")

        if (
            job_url in seen_urls_this_run
            or fingerprint in seen_fingerprints_this_run
        ):
            skipped_duplicates += 1
            continue

        existing_job = (
            db.query(Job)
            .filter(
                or_(
                    Job.job_url == job_url,
                    Job.fingerprint == fingerprint,
                )
            )
            .first()
        )

        if existing_job:
            skipped_duplicates += 1
            continue

        db.add(Job(**job_data))

        seen_urls_this_run.add(job_url)
        seen_fingerprints_this_run.add(fingerprint)

        inserted_count += 1

    db.commit()

    return {
        "inserted": inserted_count,
        "skipped_duplicates": skipped_duplicates,
        "skipped_non_target_role": skipped_non_target_role,
        "skipped_low_score": skipped_low_score,

        # Kept for compatibility with older response handling
        "skipped_not_fresher_friendly": skipped_non_target_role,
    }


def run_company_scrape(
    db: Session,
    min_score: int = 60,
) -> dict:
    total_fetched = 0
    total_inserted = 0
    total_skipped_duplicates = 0
    total_skipped_non_target_role = 0
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
            fetched_jobs = fetch_greenhouse_jobs(
                company_name=company,
                board_token=token,
            )
        elif ats == "lever":
            fetched_jobs = fetch_lever_jobs(
                company_name=company,
                company_token=token,
            )
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
        total_skipped_non_target_role += save_summary["skipped_non_target_role"]
        total_skipped_low_score += save_summary["skipped_low_score"]

    return {
        "message": "Company career scrape completed",
        "enabled_sources": len(enabled_sources),
        "total_fetched": total_fetched,
        "total_inserted": total_inserted,
        "inserted": total_inserted,
        "total_skipped_duplicates": total_skipped_duplicates,
        "total_skipped_non_target_role": total_skipped_non_target_role,
        "total_skipped_low_score": total_skipped_low_score,

        # Kept for compatibility with older response handling
        "total_skipped_not_fresher_friendly": total_skipped_non_target_role,

        "source_summaries": source_summaries,
    }