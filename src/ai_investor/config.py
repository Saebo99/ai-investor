"""
Configuration models and helpers for the AI Investor agent.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import BaseSettings, Field, validator


class DataProvidersSettings(BaseSettings):
    """Credentials and endpoints for external data sources."""

    eodhd_api_key: str = Field(default="", alias="EODHD_API_KEY")
    nordnet_username: str = Field(default="", alias="NORDNET_USERNAME")
    nordnet_password: str = Field(default="", alias="NORDNET_PASSWORD")

    class Config:
        env_file = ".env"
        case_sensitive = False


class AgentSettings(BaseSettings):
    """Core agent configuration."""

    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    strategy_file: Path = Field(
        default=Path("strategy/minimise_risk_long_term.md"),
        description="Path to a markdown file detailing the investment strategy.",
    )
    report_recipient: str = Field(default="patrick.alfei.sabo@gmail.com")

    class Config:
        env_file = ".env"
        case_sensitive = False

    @validator("strategy_file")
    def ensure_strategy_file_relative(cls, value: Path) -> Path:
        if value.is_absolute():
            return value
        return Path.cwd() / value


class Settings(BaseSettings):
    """Aggregate configuration accessible to the agent."""

    data_providers: DataProvidersSettings = DataProvidersSettings()
    agent: AgentSettings = AgentSettings()

    class Config:
        env_file = ".env"
        case_sensitive = False


CACHED_SETTINGS: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Retrieve global settings instance with simple caching.
    """
    global CACHED_SETTINGS
    if CACHED_SETTINGS is None:
        CACHED_SETTINGS = Settings()
    return CACHED_SETTINGS
