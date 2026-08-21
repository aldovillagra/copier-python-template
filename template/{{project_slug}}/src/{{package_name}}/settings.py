from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    debug: bool = False

    log_level: Literal[
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ] = "INFO"

    log_format: Literal["simple", "verbose"] = "simple"
    log_dir: str = "logs"
    log_file: str = ""

    app_dir: Path = Field(
        default_factory=lambda: Path.home() / ".{{ project_name }}",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    @property
    def cache_dir(self) -> Path:
        path = self.app_dir / "cache"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def pdf_cache_path(self) -> Path:
        return self.cache_dir / "pdf_index.json"
