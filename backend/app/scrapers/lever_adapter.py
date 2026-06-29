from typing import Any

import httpx


def normalize_lever_job(job: dict[str, Any], company_name: str, company_token: str) -> dict[str, Any]:
    categories = job.get("categories") or {}

    location = categories.get("location")
    team = categories.get("team")
    commitment = categories.get("commitment")

    description_parts = [
        job.get("descriptionPlain"),
        job.get("additionalPlain"),
        f"Team: {team}" if team else None,
        f"Commitment: {commitment}" if commitment else None,
    ]

    description = "\n\n".join(
        part for part in description_parts if part
    )

    job_url = job.get("hostedUrl") or job.get("applyUrl") or ""

    return {
        "source": f"lever:{company_token}",
        "title": str(job.get("text") or "Untitled Role"),
        "company": company_name,
        "location": location,
        "job_url": job_url,
        "apply_url": job.get("applyUrl") or job_url,
        "description": description,
        "status": "new",
    }


def fetch_lever_jobs(company_name: str, company_token: str) -> list[dict[str, Any]]:
    url = f"https://api.lever.co/v0/postings/{company_token}"

    params = {
        "mode": "json",
    }

    try:
        response = httpx.get(url, params=params, timeout=20)
        response.raise_for_status()
    except httpx.HTTPError as error:
        print(f"Lever fetch failed for {company_name}: {error}")
        return []

    raw_jobs = response.json()

    jobs = []

    for job in raw_jobs:
        normalized_job = normalize_lever_job(
            job=job,
            company_name=company_name,
            company_token=company_token,
        )

        if normalized_job["job_url"]:
            jobs.append(normalized_job)

    print(f"Fetched {len(jobs)} Lever jobs for {company_name}")
    return jobs