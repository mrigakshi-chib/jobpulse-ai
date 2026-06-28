from sqlalchemy import text

from app.database import SessionLocal, engine
from app.models.job import Job
from app.services.dedupe import calculate_job_fingerprint


def add_fingerprint_column():
    with engine.begin() as connection:
        connection.execute(
            text("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS fingerprint VARCHAR(64);")
        )
        connection.execute(
            text("CREATE INDEX IF NOT EXISTS ix_jobs_fingerprint ON jobs (fingerprint);")
        )


def backfill_existing_jobs():
    db = SessionLocal()

    try:
        jobs = db.query(Job).all()

        for job in jobs:
            job_data = {
                "title": job.title,
                "company": job.company,
                "location": job.location,
            }

            job.fingerprint = calculate_job_fingerprint(job_data)

        db.commit()

        print(f"Backfilled fingerprints for {len(jobs)} jobs.")

    finally:
        db.close()


if __name__ == "__main__":
    add_fingerprint_column()
    backfill_existing_jobs()
    print("Fingerprint migration completed successfully.")