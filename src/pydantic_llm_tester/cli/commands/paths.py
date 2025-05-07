import typer
import os

from pydantic_llm_tester.utils.common import (
    get_package_dir,
    get_project_root,
    get_templates_dir,
    get_py_models_dir,
    get_external_py_models_dir
)

app = typer.Typer()

@app.command("show")
def show_paths():
    """
    Displays various important paths used by the pydantic-llm-tester.
    """
    typer.echo("--- Important Paths ---")
    typer.echo(f"Package directory: {get_package_dir()}")
    typer.echo(f"Project root: {get_project_root()}")
    typer.echo(f"Templates directory: {get_templates_dir()}")
    typer.echo(f"Built-in py_models directory: {get_py_models_dir()}")
    typer.echo(f"External py_models directory: {get_external_py_models_dir()}")

    typer.echo("\n--- Directory Existence Check ---")
    typer.echo(f"Package directory exists: {os.path.exists(get_package_dir())}")
    typer.echo(f"Project root exists: {os.path.exists(get_project_root())}")
    typer.echo(f"Templates directory exists: {os.path.exists(get_templates_dir())}")
    typer.echo(f"Built-in py_models directory exists: {os.path.exists(get_py_models_dir())}")
    typer.echo(f"External py_models directory exists: {os.path.exists(get_external_py_models_dir())}")

@app.command("check")
def check_paths():
    """
    Checks if important directories exist and reports the result.
    """
    typer.echo("--- Directory Existence Check ---")
    typer.echo(f"Package directory exists: {os.path.exists(get_package_dir())}")
    typer.echo(f"Project root exists: {os.path.exists(get_project_root())}")
    typer.echo(f"Templates directory exists: {os.path.exists(get_templates_dir())}")
    typer.echo(f"Built-in py_models directory exists: {os.path.exists(get_py_models_dir())}")
    typer.echo(f"External py_models directory exists: {os.path.exists(get_external_py_models_dir())}")
