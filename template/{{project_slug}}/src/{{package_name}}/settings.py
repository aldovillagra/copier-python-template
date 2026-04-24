from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import tomllib


class CompanySettings(BaseModel):
    name: str = "Company Name"

class Settings(BaseSettings):
    # --------------------
    # CONFIG BÁSICA
    # --------------------
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    company: CompanySettings = Field(default_factory=CompanySettings)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )


settings = Settings()


def load_extra_config(path: Path) -> None:
    """
    Carga configuración adicional desde archivo .env, .toml o .json.

    Args:
        path (Path): Ruta del archivo de configuración.

    Raises:
        FileNotFoundError: Si el archivo especificado no existe.
        ValueError: Si la extensión del archivo no es soportada.
    """

    if not path.exists():
        raise FileNotFoundError(f"Archivo de configuración no encontrado: {path}")

    suffix = path.suffix.lower()

    # --------------------
    # Soporte para archivos .env
    # --------------------
    if suffix == ".env":
        load_dotenv(path, override=True)
        # re-render settings after environment override
        global settings
        settings = Settings()
        return

    # --------------------
    # Archivos TOML / JSON
    # --------------------
    if suffix in (".toml", ".json"):
        raw = tomllib.loads(path.read_text())
        if not isinstance(raw, dict):
            raise ValueError("El archivo de configuración TOML/JSON no contiene un dict válido")

        for key, value in raw.items():
            setattr(settings, key, value)

        return

    # --------------------
    # Extensiones no soportadas
    # --------------------
    raise ValueError(f"Formato de archivo no soportado: {suffix}")
