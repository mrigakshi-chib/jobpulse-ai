from app.database import SessionLocal
from app.models.job import Job


def delete_indeed_jobs():
    db = SessionLocal()

    try:
        deleted_count = db.query(Job).filter(Job.source == "indeed").delete()
        db.commit()
        print(f"Deleted {deleted_count} Indeed jobs.")

    finally:
        db.close()


if __name__ == "__main__":
    delete_indeed_jobs()