import logging
from pathlib import Path
from typing import Literal

from dotenv import find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    gfycat_client_secret: str
    gfycat_client_id: str
    discord_token: str
    log_level: int = logging.DEBUG
    sync: bool = False
    sync_guild_id: int | None = None
    archive_mode: Literal["local", "cloud"] = "local"
    save_directory: Path | None = None
    cloud_project_id: str | None = None
    cloud_bucket_name: str | None = None
    model_config = SettingsConfigDict(env_file=find_dotenv(usecwd=True), extra="ignore")
    environment: str | None = None
