import logging
from pathlib import Path

from dotenv import find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    gfycat_client_secret: str
    gfycat_client_id: str
    save_directory: Path
    discord_token: str
    log_level: int = logging.DEBUG
    sync: bool = False
    sync_guild_id: int | None = None
    model_config = SettingsConfigDict(env_file=find_dotenv(usecwd=True), extra="ignore")
