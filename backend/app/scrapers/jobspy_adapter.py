from datetime import datetime, timezone
from typing import Any

from jobspy import scrape_jobs


def normalize_jobspy_row(row: dict[str, Any]) -> dict[str, Any]:
    job_url = row.get("job_url") or row.get("job_url_direct") or ""

    return {
        "source": str(row.get("site") or "jobspy"),
        "title": str(row.get("title") or "Untitled Role"),
        "company": str(row.get("company") or "Unknown Company"),
        "location": row.get("location"),
        "job_url": job_url,
        "apply_url": row.get("job_url_direct") or job_url,
        "description": row.get("description"),
        "status": "new",
    }


def fetch_jobs_from_jobspy(
    search_term: str = "software engineer fresher",
    location: str = "India",
    results_wanted: int = 25,
    hours_old: int = 24,
) -> list[dict[str, Any]]:
    jobs_df = scrape_jobs(
        site_name=["indeed"],
        search_term=search_term,
        location=location,
        results_wanted=results_wanted,
        hours_old=hours_old,
        country_indeed="india",
        description_format="markdown",
        verbose=1,
    )

    jobs: list[dict[str, Any]] = []

    for _, row in jobs_df.iterrows():
        normalized_job = normalize_jobspy_row(row.to_dict())

        if normalized_job["job_url"]:
            jobs.append(normalized_job)

    print(
        f"[{datetime.now(timezone.utc).isoformat()}] "
        f"Fetched {len(jobs)} jobs from JobSpy "
        f"for search='{search_term}', location='{location}', hours_old={hours_old}"
    )

    return jobs