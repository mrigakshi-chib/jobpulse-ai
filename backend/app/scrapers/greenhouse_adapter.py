from typing import Any

import httpx


def normalize_greenhouse_job(job: dict[str, Any], company_name: str, board_token: str) -> dict[str, Any]:
    offices = job.get("offices") or []
    location = None

    if offices:
        location = offices[0].get("name")

    job_url = job.get("absolute_url") or ""

    return {
        "source": f"greenhouse:{board_token}",
        "title": str(job.get("title") or "Untitled Role"),
        "company": company_name,
        "location": location,
        "job_url": job_url,
        "apply_url": job_url,
        "description": job.get("content"),
        "status": "new",
    }


def fetch_greenhouse_jobs(company_name: str, board_token: str) -> list[dict[str, Any]]:
    url = f"https://api.greenhouse.io/v1/boards/{board_token}/jobs"

    params = {
        "content": "true",
    }

    try:
        response = httpx.get(url, params=params, timeout=20)
        response.raise_for_status()
    except httpx.HTTPError as error:
        print(f"Greenhouse fetch failed for {company_name}: {error}")
        return []

    data = response.json()
    raw_jobs = data.get("jobs", [])

    jobs = []

    for job in raw_jobs:
        normalized_job = normalize_greenhouse_job(
            job=job,
            company_name=company_name,
            board_token=board_token,
        )

        if normalized_job["job_url"]:
            jobs.append(normalized_job)

    print(f"Fetched {len(jobs)} Greenhouse jobs for {company_name}")
    return jobs