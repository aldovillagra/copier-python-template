from __future__ import annotations

import logging
import sys
import tomllib
from datetime import datetime
from pathlib import Path
from typing import Literal

import tomli_w
import typer
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class CompanySettings(BaseModel):
    name: str = "Company Name"


class Settings(BaseSettings):
    # --------------------
    # CONFIG BÁSICA
    # --------------------
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL",] = "INFO"
    log_format: Literal["simple", "verbose"] = "simple"
    log_dir: str = "logs"
    log_file: str = ""

    company: CompanySettings = Field(default_factory=CompanySettings)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )


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


def bootstrap_settings(project_name: str) -> Settings:
    path = Path.home() / f".{project_name}.toml"

    if not path.exists():
        settings = Settings()

        toml_text = tomli_w.dumps(settings.model_dump(mode="json"))

        typer.echo("Default config:\n")
        typer.echo(toml_text)

        if typer.confirm("Create config file?", default=True):
            path.write_text(toml_text, encoding="utf-8")
            typer.echo(f"Created: {path}")
        else:
            raise typer.Exit(1)

    with path.open("rb") as f:
        data = tomllib.load(f)

    return Settings(**data)

def get_settings(ctx: typer.Context) -> Settings:
    return ctx.obj

def setup_logging(settings: Settings):
    level = "DEBUG" if settings.debug else settings.log_level

    handlers: list[logging.Handler] = []
    console_handler = logging.StreamHandler(sys.stderr)

    if settings.log_format == "verbose":
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | "
            "%(filename)s:%(lineno)d | %(message)s"
        )
    else:
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    console_handler.setFormatter(formatter)
    handlers.append(console_handler)

    # Si no esta definido log dir y log_file, se define por defecto en
    if not settings.log_dir:
        settings.log_dir = "logs"
    if not settings.log_file:
        settings.log_file = f"{settings.log_dir}/{datetime.now():%Y%m%d_%H%M}.log"

    if settings.log_file and str(settings.log_file).strip():
        log_path = Path(settings.log_file).expanduser().resolve()
        if log_path.exists() and log_path.is_dir():
            raise ValueError(
                f"log_file apunta a un directorio, no a un archivo: {log_path}"
            )
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(
            log_path,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    logging.basicConfig(
        level=level,
        handlers=handlers,
        force=True,
    )
    return logging
