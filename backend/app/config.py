from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str

    enable_scheduler: bool = True
    scrape_interval_hours: int = 4

    class Config:
        env_file = ".env"


settings = Settings()