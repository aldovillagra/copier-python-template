from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from .settings import settings, load_extra_config
from .generate import app as generate_app

console = Console()
app = typer.Typer(help="CLI principal del proyecto {{ project_name }}")
app.add_typer(generate_app, name="generate")


# ---------------------------------------------------------
#   Comando: info
# ---------------------------------------------------------
@app.command()
def info() -> None:
    """
    Muestra la configuración actual del proyecto.
    """
    console.rule("[bold cyan]Configuración del Proyecto[/bold cyan]")
    console.print(settings.model_dump(), highlight=True)


# ---------------------------------------------------------
#   Comando: run
# ---------------------------------------------------------
@app.command()
def run(
    config: Path | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Archivo opcional de configuración (.env, .toml, .json)",
    ),
    debug: bool | None = typer.Option(
        None,
        "--debug",
        help="Ejecutar en modo debug",
    ),
) -> None:
    """
    Ejecuta el sistema principal del proyecto.
    """

    # Cargar archivo externo si existe
    if config:
        load_extra_config(config)
        console.print(f"[green]Configuración extra cargada desde {config}[/]")

    # Override del modo debug si se pasa por CLI
    if debug is not None:
        settings.debug = debug

    console.rule("[bold green]Iniciando Sistema[/bold green]")
    console.print(settings.model_dump())

    # Aquí va la lógica principal del proyecto
    console.print("[bold yellow] → Ejecutando lógica principal...[/]")


# ---------------------------------------------------------
#   Punto de entrada
# ---------------------------------------------------------
if __name__ == "__main__":
    app()
