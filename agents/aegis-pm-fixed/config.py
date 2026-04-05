"""Application configuration for Aegis PM."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment."""

    google_api_key: str = Field(alias="GOOGLE_API_KEY")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    postgres_url: str = Field(alias="POSTGRES_URL")
    chroma_path: Path = Field(default=Path("./data/chroma"), alias="CHROMA_PATH")
    github_token: str = Field(alias="GITHUB_TOKEN")
    github_repo: str = Field(default="owner/repo", alias="GITHUB_REPO")
    slack_bot_token: str = Field(alias="SLACK_BOT_TOKEN")
    slack_channel: str = Field(default="#general", alias="SLACK_CHANNEL")
    jira_email: str = Field(alias="JIRA_EMAIL")
    jira_api_token: str = Field(alias="JIRA_API_TOKEN")
    jira_base_url: str = Field(alias="JIRA_BASE_URL")
    jira_project_key: str = Field(default="AP", alias="JIRA_PROJECT_KEY")
    max_concurrent_tasks: int = Field(default=5, alias="MAX_CONCURRENT_TASKS")
    replan_budget: int = Field(default=3, alias="REPLAN_BUDGET")
    risk_threshold: float = Field(default=0.7, alias="RISK_THRESHOLD")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    app_name: str = Field(default="aegis_pm", alias="APP_NAME")
    api_host: str = Field(default="127.0.0.1", alias="API_HOST")
    api_port: int = Field(default=8080, alias="API_PORT")
    state_ttl_seconds: int = Field(default=604800, alias="STATE_TTL_SECONDS")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings."""
    settings = Settings()
    settings.chroma_path.mkdir(parents=True, exist_ok=True)
    return settings
