from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import settings
from app.database import SessionLocal
from app.services.scrape_runner import DEFAULT_SEARCH_TERMS, run_jobspy_scrape


scheduler = BackgroundScheduler(timezone="Asia/Kolkata")


def scheduled_jobspy_scrape():
    print(
        f"[{datetime.now(timezone.utc).isoformat()}] "
        "Starting scheduled JobSpy scrape..."
    )

    db = SessionLocal()

    try:
        summary = run_jobspy_scrape(
            db=db,
            search_terms=DEFAULT_SEARCH_TERMS,
            location="India",
            results_wanted_per_term=15,
            min_score=65,
            hours_old=24,
        )

        print("Scheduled scrape summary:")
        print(summary)

    except Exception as error:
        print(f"Scheduled scrape failed: {error}")

    finally:
        db.close()


def start_scheduler():
    if not settings.enable_scheduler:
        print("Scheduler disabled.")
        return

    if scheduler.running:
        print("Scheduler already running.")
        return

    scheduler.add_job(
        scheduled_jobspy_scrape,
        trigger="interval",
        hours=settings.scrape_interval_hours,
        id="jobspy_scrape_every_4_hours",
        replace_existing=True,
        max_instances=1,
    )

    scheduler.start()

    print(
        f"Scheduler started. JobSpy scrape will run every "
        f"{settings.scrape_interval_hours} hours."
    )


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        print("Scheduler stopped.")


def get_scheduler_status():
    jobs = scheduler.get_jobs()

    return {
        "running": scheduler.running,
        "jobs": [
            {
                "id": job.id,
                "next_run_time": str(job.next_run_time),
            }
            for job in jobs
        ],
    }