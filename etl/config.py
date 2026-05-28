from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://user:pass@localhost:5432/platform"

    # MySQL Internal System (read-only)
    mysql_host: str = "internal-mysql.company.internal"
    mysql_port: int = 3306
    mysql_user: str = "readonly_client"
    mysql_password: str = ""
    mysql_database: str = "main_db"

    # ETL / FastAPI
    etl_port: int = 8000

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # Next.js
    next_public_base_url: str = "https://platform.example.com"

    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache
def get_settings() -> Settings:
    return Settings()