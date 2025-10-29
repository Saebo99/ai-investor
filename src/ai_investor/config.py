"""Application configuration helpers."""

from functools import lru_cache
from typing import Literal, Optional

from pydantic import BaseSettings, Field, HttpUrl, PositiveInt


class Settings(BaseSettings):
    """Load runtime settings from environment variables."""

    anthropic_api_key: str = Field(..., env="ANTHROPIC_API_KEY")
    eodhd_api_key: str = Field(..., env="EODHD_API_KEY")
    nordnet_username: str = Field(..., env="NORDNET_USERNAME")
    nordnet_password: str = Field(..., env="NORDNET_PASSWORD")
    nordnet_account_id: str = Field(..., env="NORDNET_ACCOUNT_ID")

    default_exchange: str = Field("US", env="DEFAULT_EXCHANGE")
    shortlist_target_size: PositiveInt = Field(25, env="SHORTLIST_TARGET_SIZE")
    shortlist_refresh_days: PositiveInt = Field(7, env="SHORTLIST_REFRESH_DAYS")

    scheduler_cron: str = Field("0 6 * * *", env="SCHEDULER_CRON")
    scheduler_timezone: str = Field("UTC", env="SCHEDULER_TIMEZONE")

    approval_mode: Literal["cli"] = Field("cli", env="APPROVAL_MODE")

    thesis_storage_path: str = Field("data/thesis_log.jsonl", env="THESIS_STORAGE_PATH")
    trade_log_path: str = Field("data/trade_log.jsonl", env="TRADE_LOG_PATH")

    eodhd_base_url: HttpUrl = Field(
        "https://eodhd.com/api/", env="EODHD_BASE_URL"
    )
    nordnet_base_url: HttpUrl = Field(
        "https://www.nordnet.se/api/", env="NORDNET_BASE_URL"
    )

    email_smtp_server: Optional[str] = Field(None, env="EMAIL_SMTP_SERVER")
    email_from: Optional[str] = Field(None, env="EMAIL_FROM")
    email_recipients: Optional[str] = Field(None, env="EMAIL_RECIPIENTS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()
