import httpx


def extract_location(job: dict) -> str:
    location = job.get("location")

    if isinstance(location, str):
        return location

    if isinstance(location, dict):
        return (
            location.get("location")
            or location.get("name")
            or location.get("city")
            or "Remote"
        )

    location_text = job.get("locationName")
    if location_text:
        return location_text

    return "Remote"


def extract_description(job: dict) -> str:
    description_parts = []

    description_html = job.get("descriptionHtml")
    description_plain = job.get("descriptionPlain")
    description = job.get("description")

    if description_plain:
        description_parts.append(description_plain)

    if description:
        description_parts.append(description)

    if description_html:
        description_parts.append(description_html)

    return "\n\n".join(description_parts)


def fetch_ashby_jobs(company_name: str, company_token: str) -> list[dict]:
    url = (
        f"https://api.ashbyhq.com/posting-api/job-board/"
        f"{company_token}?includeCompensation=true"
    )

    response = httpx.get(url, timeout=30)
    response.raise_for_status()

    data = response.json()
    jobs = data.get("jobs", [])

    normalized_jobs = []

    for job in jobs:
        title = job.get("title")
        job_id = job.get("id")

        if not title or not job_id:
            continue

        job_url = (
            job.get("jobUrl")
            or job.get("applyUrl")
            or f"https://jobs.ashbyhq.com/{company_token}/{job_id}/application"
        )

        apply_url = job.get("applyUrl") or job_url

        normalized_jobs.append(
            {
                "source": f"ashby:{company_token}",
                "title": title,
                "company": company_name,
                "location": extract_location(job),
                "job_url": job_url,
                "apply_url": apply_url,
                "description": extract_description(job),
                "status": "new",
            }
        )

    return normalized_jobs