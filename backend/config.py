import re
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_HERE = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(_HERE.parent / ".env"), str(_HERE / ".env")),
        extra="ignore",
    )

    DATABASE_URL: str
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-20b"
    REDIS_URL: str = ""
    WEATHER_API_KEY: str = ""
    JWT_SECRET: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    MAX_STEPS: int = 5
    RATE_LIMIT_PER_MIN: int = 20
    CACHE_TTL: int = 1800

    @field_validator("REDIS_URL")
    @classmethod
    def _clean_redis_url(cls, v: str) -> str:
        """Accept a plain URL or an Upstash-style `redis-cli --tls -u redis://...` string."""
        m = re.search(r"rediss?://\S+", v)
        if not m:
            return ""
        url = m.group(0)
        if "--tls" in v and url.startswith("redis://"):
            url = "rediss://" + url[len("redis://"):]
        return url


settings = Settings()  # type: ignore[call-arg]
