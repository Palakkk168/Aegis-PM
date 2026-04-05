"""Configuration management for Aegis PM."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded from environment variables."""

    api_host: str
    api_port: int
    data_dir: Path
    max_parallel_tasks: int
    log_level: str
    github_token: str | None
    github_repo_owner: str | None
    github_repo_name: str | None
    slack_bot_token: str | None
    slack_default_channel: str | None
    jira_base_url: str | None
    jira_user_email: str | None
    jira_api_token: str | None
    jira_project_key: str | None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""
    root = Path(__file__).resolve().parent.parent
    data_dir = Path(os.getenv("AEGIS_DATA_DIR", root / "data"))
    data_dir.mkdir(parents=True, exist_ok=True)
    return Settings(
        api_host=os.getenv("AEGIS_API_HOST", "127.0.0.1"),
        api_port=int(os.getenv("AEGIS_API_PORT", "8080")),
        data_dir=data_dir,
        max_parallel_tasks=int(os.getenv("AEGIS_MAX_PARALLEL_TASKS", "3")),
        log_level=os.getenv("AEGIS_LOG_LEVEL", "INFO"),
        github_token=os.getenv("GITHUB_TOKEN"),
        github_repo_owner=os.getenv("GITHUB_REPO_OWNER"),
        github_repo_name=os.getenv("GITHUB_REPO_NAME"),
        slack_bot_token=os.getenv("SLACK_BOT_TOKEN"),
        slack_default_channel=os.getenv("SLACK_DEFAULT_CHANNEL"),
        jira_base_url=os.getenv("JIRA_BASE_URL"),
        jira_user_email=os.getenv("JIRA_USER_EMAIL"),
        jira_api_token=os.getenv("JIRA_API_TOKEN"),
        jira_project_key=os.getenv("JIRA_PROJECT_KEY"),
    )
