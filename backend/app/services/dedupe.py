import hashlib
import re


def clean_text(value: str | None) -> str:
    if not value:
        return ""

    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def calculate_job_fingerprint(job_data: dict) -> str:
    raw_text = "|".join([
        clean_text(job_data.get("title")),
        clean_text(job_data.get("company")),
        clean_text(job_data.get("location")),
    ])

    return hashlib.sha256(raw_text.encode("utf-8")).hexdigest()