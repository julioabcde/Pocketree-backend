from pydantic import ConfigDict
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env")
    database_url: str
    secret_key: str
    access_token_expire_minutes: int = 60
    reports_cache_enabled: bool = False
    redis_url: str | None = None
    reports_cache_ttl_overview: int = 300
    reports_cache_ttl_trend: int = 600
    reports_cache_ttl_breakdown: int = 600
    reports_cache_ttl_top_transactions: int = 600
    reports_cache_ttl_period_comparison: int = 600
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash-lite"

settings = Settings()
