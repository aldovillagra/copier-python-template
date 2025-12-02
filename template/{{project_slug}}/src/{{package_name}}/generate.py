from __future__ import annotations

import typer
from pathlib import Path
from rich.console import Console

console = Console()
app = typer.Typer(help="Generador de scaffolding para el proyecto")


# ============================================================
# Helpers
# ============================================================

def create_file(path: Path, content: str = "") -> None:
    """
    Crea un archivo si no existe. No sobrescribe.
    """
    if path.exists():
        console.print(f"[yellow]⚠ El archivo ya existe y no se sobrescribirá: {path}[/]")
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    console.print(f"[green]✔ Archivo creado:[/] {path}")


def create_module_structure(name: str, template: str, test_template: str) -> None:
    """
    Crea un módulo dentro de src/{{package_name}}/
    con su archivo principal y test asociado.
    """
    base = Path(__file__).parent  # src/{{package_name}}

    module_dir = base / name
    module_dir.mkdir(parents=True, exist_ok=True)

    # __init__.py
    create_file(module_dir / "__init__.py", f'"""Módulo {name}."""\n')

    # módulo principal
    create_file(module_dir / f"{name}.py", template)

    # test asociado
    test_file = Path("tests") / f"test_{name}.py"
    create_file(test_file, test_template)

    console.rule(f"[bold green]✔ Módulo {name} generado exitosamente[/]")


# ============================================================
# Comando: module
# ============================================================

@app.command()
def module(name: str):
    """
    Genera un módulo simple con una función main().
    """
    template = f"""def main():
    print("Hola desde el módulo {name}!")
"""

    test_template = f"""def test_{name}_basic():
    assert True
"""

    create_module_structure(name, template, test_template)


# ============================================================
# Comando: service
# ============================================================

@app.command()
def service(name: str):
    """
    Genera un servicio orientado a lógica de negocio.
    """
    class_name = name.capitalize() + "Service"

    template = f"""class {class_name}:
    \"""Servicio {name}: agregar lógica de negocio aquí.\"""\n
    def run(self):
        print("Ejecutando servicio {name}...")
"""

    test_template = f"""def test_{name}_service():
    # Importación diferida para que pytest lo encuentre
    from {{package_name}}.{name}.{name} import {class_name}
    svc = {class_name}()
    assert hasattr(svc, "run")
"""

    create_module_structure(name, template, test_template)


# ============================================================
# Comando: model
# ============================================================

@app.command()
def model(name: str):
    """
    Genera un modelo tipado basado en Pydantic.
    """
    class_name = name.capitalize()

    template = f"""from pydantic import BaseModel

class {class_name}(BaseModel):
    \"""Modelo {name}. Agregue campos aquí.\"""\n
    name: str
"""

    test_template = f"""def test_{name}_model():
    from {{package_name}}.{name}.{name} import {class_name}
    m = {class_name}(name="test")
    assert m.name == "test"
"""

    create_module_structure(name, template, test_template)


# ============================================================
# Comando: util
# ============================================================

@app.command()
def util(name: str):
    """
    Genera una utilidad (función independiente).
    """
    template = f"""def {name}():
    \"""Función utilitaria {name}.\"""
    return True
"""

    test_template = f"""def test_{name}_util():
    from {{package_name}}.{name}.{name} import {name}
    assert {name}() is True
"""

    create_module_structure(name, template, test_template)


# ============================================================
# Typer entry (para CLI principal)
# ============================================================

if __name__ == "__main__":
    app()
