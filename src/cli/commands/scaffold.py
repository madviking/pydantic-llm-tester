import typer
import os
from typing import Optional

# Import core scaffolding logic
from src.cli.core.scaffold_logic import scaffold_provider_files, scaffold_model_files
# Import core config logic to update config after scaffolding
from src.cli.core import config_logic, provider_logic

app = typer.Typer(help="Commands for scaffolding new providers and py_models.")

# Determine the directory containing the templates relative to the package root
# This is now handled within scaffold_logic.py

@app.command("provider")
def scaffold_provider(
    provider_name: Optional[str] = typer.Argument(None, help="The name of the new provider to scaffold (optional if using interactive mode)."),
    providers_dir: Optional[str] = typer.Option(None, "--providers-dir", help="Directory to create the provider in (defaults to src/llms)."),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Enable interactive mode for scaffolding.")
):
    """
    Scaffolds a new LLM provider directory structure and template files.
    """
    if interactive:
        typer.echo("Interactive Provider Scaffolding")
        provider_name = typer.prompt("Enter the name of the new provider")
        if not provider_name:
            typer.echo("Provider name cannot be empty.", err=True)
            raise typer.Exit(code=1)
        # Optionally prompt for providers_dir in interactive mode
        # providers_dir = typer.prompt("Enter the directory to create the provider in (default: src/llms)", default="src/llms")
    elif not provider_name:
        typer.echo("Error: Provider name must be provided in non-interactive mode.", err=True)
        raise typer.Exit(code=1)

    # Determine the base directory for providers
    if providers_dir:
        base_dir = providers_dir
    else:
        # Default to src/llms relative to the package directory
        # Need to determine the package root from this file's location
        _current_file_dir = os.path.dirname(os.path.abspath(__file__))
        _cli_dir = os.path.dirname(_current_file_dir) # Go up one level to src/cli
        _llm_tester_dir = os.path.dirname(_cli_dir) # Go up another level to src
        base_dir = os.path.join(_llm_tester_dir, "llms")

    # Call the core scaffolding logic
    success, message = scaffold_provider_files(provider_name, base_dir)

    if success:
        typer.echo(message)
        # Attempt to enable the newly scaffolded provider in the config
        enable_success, enable_message = provider_logic.enable_provider(provider_name)
        if enable_success:
            typer.echo(f"Provider '{provider_name}' automatically enabled.")
        else:
            typer.echo(f"Warning: Could not automatically enable provider '{provider_name}'. {enable_message}", err=True)
            typer.echo("You may need to manually enable it using 'llm-tester providers enable'.", err=True)
    else:
        typer.echo(message, err=True)
        raise typer.Exit(code=1)


@app.command("model")
def scaffold_model(
    model_name: Optional[str] = typer.Argument(None, help="The name of the new model to scaffold (optional if using interactive mode)."),
    models_dir: Optional[str] = typer.Option(None, "--py_models-dir", help="Directory to create the model in (defaults to ./py_models)."),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Enable interactive mode for scaffolding.")
):
    """
    Scaffolds a new LLM tester model directory structure and template files.
    """
    if interactive:
        typer.echo("Interactive Model Scaffolding")
        model_name = typer.prompt("Enter the name of the new model")
        if not model_name:
            typer.echo("Model name cannot be empty.", err=True)
            raise typer.Exit(code=1)
        # Optionally prompt for models_dir in interactive mode
        # models_dir = typer.prompt("Enter the directory to create the model in (default: ./py_models)", default="./py_models")
    elif not model_name:
        typer.echo("Error: Model name must be provided in non-interactive mode.", err=True)
        raise typer.Exit(code=1)

    # Determine the base directory for py_models
    base_dir = models_dir or "./py_models" # Default to a 'py_models' directory in the current working directory

    # Call the core scaffolding logic
    success, message = scaffold_model_files(model_name, base_dir)

    if success:
        typer.echo(message)
        # Note: Models are not automatically enabled in a central config like providers.
        # They are discovered based on the test_dir. No config update needed here.
    else:
        typer.echo(message, err=True)
        raise typer.Exit(code=1)
