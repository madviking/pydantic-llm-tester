import typer
import os
import json
from typing import Optional, List, Dict, Any, ClassVar
from pydantic import BaseModel, Field
from datetime import date

app = typer.Typer(help="Commands for scaffolding new providers and py_models.")

# Determine the directory containing the templates relative to the package root
_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_cli_dir = os.path.dirname(_current_file_dir) # Go up one level to src/cli
_llm_tester_dir = os.path.dirname(_cli_dir) # Go up another level to src
_templates_dir = os.path.join(_llm_tester_dir, "cli", "templates") # Path is src/cli/templates

def _read_template(template_name: str, **kwargs) -> str:
    """Reads a template file and replaces placeholders."""
    template_path = os.path.join(_templates_dir, template_name)
    if not os.path.exists(template_path):
        typer.echo(f"Error: Template file not found at {template_path}", err=True)
        raise typer.Exit(code=1)

    with open(template_path, "r") as f:
        content = f.read()

    # Replace placeholders
    for key, value in kwargs.items():
        placeholder = "{{" + key + "}}"
        content = content.replace(placeholder, str(value))

    return content

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
        _llm_tester_dir = os.path.dirname(_cli_dir) # Go up two levels from commands
        base_dir = os.path.join(_llm_tester_dir, "llms")

    provider_path = os.path.join(base_dir, provider_name)

    if os.path.exists(provider_path):
        typer.echo(f"Error: Provider directory already exists at {provider_path}", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"Scaffolding new provider: {provider_name} in {base_dir}")

    try:
        # Create directory structure
        os.makedirs(provider_path)
        os.makedirs(os.path.join(provider_path, "tests")) # Optional: Add tests directory structure later if needed

        # Read and process templates
        provider_name_capitalized = provider_name.capitalize()
        provider_name_upper = provider_name.upper()

        init_content = _read_template(
            "provider_init.py.tmpl",
            provider_name=provider_name,
            provider_name_capitalized=provider_name_capitalized
        )
        config_content = _read_template(
            "provider_config.json.tmpl",
            provider_name=provider_name,
            provider_name_upper=provider_name_upper
        )
        provider_content = _read_template(
            "provider_provider.py.tmpl",
            provider_name=provider_name,
            provider_name_capitalized=provider_name_capitalized,
            provider_name_upper=provider_name_upper
        )

        # Write files
        with open(os.path.join(provider_path, "__init__.py"), "w") as f:
            f.write(init_content)

        with open(os.path.join(provider_path, "config.json"), "w") as f:
            f.write(config_content)

        with open(os.path.join(provider_path, "provider.py"), "w") as f:
            f.write(provider_content)

        typer.echo(f"Successfully scaffolded provider '{provider_name}' at {provider_path}")

    except OSError as e:
        typer.echo(f"Error creating provider directory or files: {e}", err=True)
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

    model_path = os.path.join(base_dir, model_name)

    if os.path.exists(model_path):
        typer.echo(f"Error: Model directory already exists at {model_path}", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"Scaffolding new model: {model_name} in {base_dir}")

    try:
        # Create directory structure
        os.makedirs(os.path.join(model_path, "tests", "sources"))
        os.makedirs(os.path.join(model_path, "tests", "prompts", "optimized"))
        os.makedirs(os.path.join(model_path, "tests", "expected"))
        os.makedirs(os.path.join(model_path, "reports"))

        # Read and process templates
        model_name_capitalized = model_name.capitalize()

        model_init_content = _read_template(
            "model_init.py.tmpl",
            model_name=model_name,
            model_name_capitalized=model_name_capitalized
        )
        model_model_content = _read_template(
            "model_model.py.tmpl",
            model_name=model_name,
            model_name_capitalized=model_name_capitalized
        )
        model_tests_init_content = _read_template(
            "model_tests_init.py.tmpl",
            model_name=model_name
        )
        model_test_source_content = _read_template(
            "model_test_source.txt.tmpl",
            model_name=model_name
        )
        model_test_prompt_content = _read_template(
            "model_test_prompt.txt.tmpl",
            model_name=model_name
        )
        model_test_expected_content = _read_template(
            "model_test_expected.json.tmpl"
            # No model_name placeholder in expected.json template
        )


        # Write files
        with open(os.path.join(model_path, "__init__.py"), "w") as f:
            f.write(model_init_content)

        with open(os.path.join(model_path, "model.py"), "w") as f:
            f.write(model_model_content)

        with open(os.path.join(model_path, "tests", "__init__.py"), "w") as f:
            f.write(model_tests_init_content)

        with open(os.path.join(model_path, "tests", "sources", "example.txt"), "w") as f:
            f.write(model_test_source_content)

        with open(os.path.join(model_path, "tests", "prompts", "example.txt"), "w") as f:
            f.write(model_test_prompt_content)

        with open(os.path.join(model_path, "tests", "expected", "example.json"), "w") as f:
            f.write(model_test_expected_content)

    except OSError as e:
        typer.echo(f"Error creating model directory or files: {e}", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"An unexpected error occurred during model scaffolding: {e}", err=True)
        raise typer.Exit(code=1)

    # Success message outside the try block
    typer.echo(f"Successfully scaffolded model '{model_name}' at {model_path}")
