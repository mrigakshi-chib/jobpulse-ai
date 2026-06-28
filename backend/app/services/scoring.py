import re


GOOD_KEYWORDS = [
    "fresher",
    "freshers",
    "2025 batch",
    "2024 batch",
    "graduate engineer trainee",
    "software engineer trainee",
    "trainee software engineer",
    "associate software engineer",
    "junior software engineer",
    "junior developer",
    "entry level",
    "entry-level",
    "0-1 years",
    "0 to 1 years",
    "0-2 years",
    "0 to 2 years",
    "off-campus",
    "campus hiring",
    "new grad",
    "recent graduate",
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
    "software engineer",
    "software developer",
    "data structures",
    "algorithms",
]

BAD_KEYWORDS = [
    "senior",
    "sr.",
    "lead engineer",
    "tech lead",
    "architect",
    "manager",
    "staff engineer",
    "principal engineer",
    "unpaid",
    "training fee",
    "bond",
    "sales",
    "customer support",
    "bpo",
    "technical support",
]


def get_job_text(job_data: dict) -> str:
    return " ".join([
        str(job_data.get("title", "")),
        str(job_data.get("company", "")),
        str(job_data.get("location", "")),
        str(job_data.get("description", "")),
    ]).lower()


def has_high_experience_requirement(text: str) -> bool:
    patterns = [
        r"([3-9]|[1-9][0-9])\+?\s*years",
        r"([3-9]|[1-9][0-9])\+?\s*yrs",
        r"minimum\s+([3-9]|[1-9][0-9])\s*years",
        r"at least\s+([3-9]|[1-9][0-9])\s*years",
    ]

    return any(re.search(pattern, text) for pattern in patterns)


def is_fresher_friendly(job_data: dict) -> bool:
    text = get_job_text(job_data)

    if has_high_experience_requirement(text):
        return False

    if any(keyword in text for keyword in BAD_KEYWORDS):
        return False

    fresher_signals = any(keyword in text for keyword in GOOD_KEYWORDS)
    junior_title_signals = any(
        keyword in text
        for keyword in [
            "fresher",
            "trainee",
            "graduate",
            "junior",
            "associate software engineer",
            "entry level",
            "entry-level",
            "0-1",
            "0 to 1",
            "0-2",
            "0 to 2",
        ]
    )

    return fresher_signals or junior_title_signals


def calculate_job_score(job_data: dict) -> int:
    text = get_job_text(job_data)

    if has_high_experience_requirement(text):
        return 10

    score = 50

    for keyword in GOOD_KEYWORDS:
        if keyword in text:
            score += 8

    for keyword in TECH_KEYWORDS:
        if keyword in text:
            score += 4

    for keyword in BAD_KEYWORDS:
        if keyword in text:
            score -= 20

    if "remote" in text:
        score += 5

    if "hybrid" in text:
        score += 3

    return max(0, min(score, 100))