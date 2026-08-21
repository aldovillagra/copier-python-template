from __future__ import annotations

import logging

import typer
from rich.console import Console

from bitr_toolkit import AppContext, create_app

from {{project_name}}.settings import Settings


console = Console()

app = create_app(
    app_name="{{ project_name }}",
    settings_cls=Settings,
    help_text="Main CLI for {{ project_name }}",
)


@app.command()
def info(ctx: typer.Context) -> None:
    """Muestra la configuración actual del proyecto."""
    app_context: AppContext[Settings] = ctx.ensure_object(AppContext)
    settings = app_context.settings

    logger = logging.getLogger(__name__)
    logger.debug("CLI started")

    console.rule("[bold cyan]{{ project_name }} configuration[/bold cyan]")
    console.print(settings.model_dump(mode="json"), highlight=True)


if __name__ == "__main__":
    app()
