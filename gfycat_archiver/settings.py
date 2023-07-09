from pathlib import Path

from dotenv import find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    gfycat_secret: str
    gfycat_client_id: str
    save_directory: Path
    model_config = SettingsConfigDict(env_file=find_dotenv(usecwd=True))
