from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "SwimCoach"
    environment: str = "development"
    frontend_url: str = "http://localhost:3000"

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080

    database_url: str = "sqlite:///./swim_coach.db"

    mp_access_token: str
    mp_public_key: str
    mp_webhook_secret: str
    mp_preapproval_plan_id: str = "pro_monthly"

    adsense_client_id: str = ""
    adsense_slot_banner: str = ""
    adsense_slot_interstitial: str = ""

    umami_website_id: str = ""
    sentry_dsn: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()