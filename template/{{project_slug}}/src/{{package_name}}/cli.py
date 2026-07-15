from __future__ import annotations

import logging

import typer
from rich.console import Console

from typing import Optional, Annotated
from .settings import bootstrap_settings, get_settings, setup_logging

console = Console()
app = typer.Typer(help="CLI principal del proyecto {{ project_name }}")


@app.callback()
def main(
    ctx: typer.Context,
    debug: bool | None = typer.Option(
        None,
        "--debug",
        help="Run with debug mode ON",
    ),
    log_level: Annotated[
        Optional[str],
        typer.Option("--log-level", help="Log level => DEBUG, INFO, WARNING, ERROR, CRITICAL",),
    ] = None,
    log_format: Annotated[
        Optional[str],
        typer.Option("--log-format", help="Log format => simple or verbose",),
    ] = None,
):
    ctx.obj = bootstrap_settings("{{ package_name }}")
    if debug is not None:
        ctx.obj.debug = debug
    if log_level:
        ctx.obj.log_level = log_level

    if log_format:
        ctx.obj.log_format = log_format

    setup_logging(ctx.obj)

# ---------------------------------------------------------
#   Comando: info
# ---------------------------------------------------------
@app.command()
def info(ctx: typer.Context) -> None:
    """
    Muestra la configuración actual del proyecto.
    """
    settings = get_settings(ctx)
    logger = logging.getLogger(__name__)
    logger.debug("CLI started")
    console.rule("[bold cyan]Configuración del Proyecto[/bold cyan]")
    console.print(settings.model_dump(mode="json"), highlight=True)


# ---------------------------------------------------------
#   Comando: run
# ---------------------------------------------------------
@app.command()
def run(
    ctx: typer.Context,
) -> None:
    """
    Ejecuta el sistema principal del proyecto.
    """
    settings = get_settings(ctx)
    logger = logging.getLogger(__name__)
    logger.debug("CLI started")
    # Override del modo debug si se pasa por CLI
    if settings.debug is not False:
        import pdb; pdb.set_trace()


    console.rule("[bold green]Iniciando Sistema[/bold green]")
    console.print(settings.model_dump())

    # Aquí va la lógica principal del proyecto
    console.print("[bold yellow] → Ejecutando lógica principal...[/]")


# ---------------------------------------------------------
#   Punto de entrada
# ---------------------------------------------------------
def main() -> None:
    app()

if __name__ == "__main__":
    main()
