from sqlalchemy import text

from app.database import engine


def add_application_tracking_columns():
    with engine.begin() as connection:
        connection.execute(
            text("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS applied_at TIMESTAMPTZ;")
        )
        connection.execute(
            text("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS follow_up_date DATE;")
        )
        connection.execute(
            text("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS notes TEXT;")
        )
        connection.execute(
            text("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS resume_version VARCHAR(100);")
        )


if __name__ == "__main__":
    add_application_tracking_columns()
    print("Application tracking fields migration completed successfully.")