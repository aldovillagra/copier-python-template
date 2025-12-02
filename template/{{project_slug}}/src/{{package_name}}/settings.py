from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import tomllib


class Settings(BaseSettings):
    """
    Configuración principal del proyecto.

    Esta clase carga, valida y proporciona acceso a todas las configuraciones
    de la aplicación. Las fuentes de configuración, de menor a mayor prioridad:

    1. Valores por defecto definidos aquí
    2. Configuración desde el archivo .env
    3. Variables de entorno del sistema
    4. Configuración cargada manualmente desde archivos externos (TOML/JSON)
    """

    # --------------------
    # CONFIG BÁSICA
    # --------------------
    debug: bool = False
    database_url: str | None = None
    workers: int = 4
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


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
