from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.job import Job
from app.scrapers.jobspy_adapter import fetch_jobs_from_jobspy
from app.services.dedupe import calculate_job_fingerprint
from app.services.scoring import calculate_job_score, is_fresher_friendly


BAD_TITLE_KEYWORDS = [
    "senior",
    "sr.",
    "lead",
    "staff",
    "principal",
    "architect",
    "manager",
    "director",
    "head",
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
    "software engineer",
    "software developer",
    "sde",
    "associate software",
    "junior software",
    "backend",
    "frontend",
    "front end",
    "full stack",
    "fullstack",
    "python developer",
    "java developer",
    "react developer",
    "node developer",
    "web developer",
    "graduate engineer trainee",
    "trainee software",
    "intern",
    "internship",
]


DEFAULT_SEARCH_TERMS = [
    # Broad fallback searches because not every fresher role says "fresher"
    "software engineer",
    "software developer",
    "sde 1",
    "sde1",
    "sde-1",
    "sde i",
    "software engineer i",
    "software developer i",

    # Fresher / new grad full-time roles
    "software engineer fresher",
    "software developer fresher",
    "associate software engineer",
    "associate software developer",
    "junior software engineer",
    "junior software developer",
    "entry level software engineer",
    "entry level software developer",
    "graduate engineer trainee software",
    "trainee software engineer",
    "software engineer trainee",
    "2025 batch software engineer",
    "2025 batch software developer",
    "2024 batch software engineer",
    "new grad software engineer",

    # Backend-focused roles
    "backend developer fresher",
    "backend engineer fresher",
    "junior backend developer",
    "python developer fresher",
    "java developer fresher",
    "node developer fresher",
    "fastapi developer fresher",
    "django developer fresher",

    # Frontend-focused roles
    "frontend developer fresher",
    "frontend engineer fresher",
    "junior frontend developer",
    "react developer fresher",
    "next.js developer fresher",
    "javascript developer fresher",
    "typescript developer fresher",

    # Full-stack roles
    "full stack developer fresher",
    "fullstack developer fresher",
    "mern stack developer fresher",
    "junior full stack developer",

    # Internship / PPO / conversion roles
    "software engineer intern",
    "software developer intern",
    "backend developer intern",
    "frontend developer intern",
    "full stack developer intern",
    "python developer intern",
    "java developer intern",
    "react developer intern",
    "node developer intern",
    "web developer intern",
    "software development intern",
    "software internship 2025",
    "PPO software internship",
    "internship with PPO software",
    "graduate software intern",
]


def is_good_scraped_job(job: dict) -> bool:
    title = (job.get("title") or "").lower()
    company = (job.get("company") or "").lower()

    if not title or not company:
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


def check_fresher_friendly(job_data: dict) -> bool:
    title = job_data.get("title") or ""
    description = job_data.get("description") or ""

    try:
        return is_fresher_friendly(title=title, description=description)
    except TypeError:
        return is_fresher_friendly(job_data)


def save_jobs_to_db(
    fetched_jobs: list[dict],
    db: Session,
    min_score: int = 65,
) -> dict:
    inserted_count = 0
    skipped_duplicates = 0
    skipped_not_fresher_friendly = 0
    skipped_low_score = 0
    skipped_low_quality = 0

    seen_urls_this_run = set()
    seen_fingerprints_this_run = set()

    for job_data in fetched_jobs:
        if not is_good_scraped_job(job_data):
            skipped_low_quality += 1
            continue

        job_data["score"] = get_job_score(job_data)
        job_data["fingerprint"] = get_job_fingerprint(job_data)

        if not check_fresher_friendly(job_data):
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
        "skipped_low_quality": skipped_low_quality,
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
    total_skipped_low_quality = 0

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
        total_skipped_not_fresher_friendly += save_summary[
            "skipped_not_fresher_friendly"
        ]
        total_skipped_low_score += save_summary["skipped_low_score"]
        total_skipped_low_quality += save_summary["skipped_low_quality"]

    return {
        "message": "JobSpy scrape completed",
        "location": location,
        "hours_old": hours_old,
        "min_score": min_score,
        "search_terms_count": len(search_terms),
        "total_fetched": total_fetched,
        "total_inserted": total_inserted,
        "inserted": total_inserted,
        "total_skipped_duplicates": total_skipped_duplicates,
        "total_skipped_not_fresher_friendly": total_skipped_not_fresher_friendly,
        "total_skipped_low_score": total_skipped_low_score,
        "total_skipped_low_quality": total_skipped_low_quality,
        "skipped_low_quality": total_skipped_low_quality,
        "term_summaries": term_summaries,
    }