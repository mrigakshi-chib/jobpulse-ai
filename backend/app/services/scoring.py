GOOD_KEYWORDS = [
    "fresher",
    "2025 batch",
    "2024 batch",
    "graduate engineer trainee",
    "software engineer trainee",
    "associate software engineer",
    "junior software engineer",
    "junior developer",
    "entry level",
    "0-1 years",
    "0 to 1 years",
    "0-2 years",
    "0 to 2 years",
    "off-campus",
    "campus hiring",
]

TECH_KEYWORDS = [
    "python",
    "java",
    "javascript",
    "typescript",
    "react",
    "next.js",
    "node",
    "express",
    "django",
    "fastapi",
    "sql",
    "postgresql",
    "mysql",
    "mongodb",
    "rest api",
    "backend",
    "frontend",
    "full stack",
    "data structures",
    "algorithms",
]

BAD_KEYWORDS = [
    "3+ years",
    "4+ years",
    "5+ years",
    "senior",
    "lead engineer",
    "architect",
    "manager",
    "unpaid",
    "training fee",
    "bond",
    "sales",
    "customer support",
]


def calculate_job_score(job_data: dict) -> int:
    text = " ".join([
        str(job_data.get("title", "")),
        str(job_data.get("company", "")),
        str(job_data.get("location", "")),
        str(job_data.get("description", "")),
    ]).lower()

    score = 50

    for keyword in GOOD_KEYWORDS:
        if keyword in text:
            score += 8

    for keyword in TECH_KEYWORDS:
        if keyword in text:
            score += 4

    for keyword in BAD_KEYWORDS:
        if keyword in text:
            score -= 15

    if "remote" in text:
        score += 5

    if "hybrid" in text:
        score += 3

    return max(0, min(score, 100))