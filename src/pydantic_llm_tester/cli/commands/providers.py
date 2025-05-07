import os

import typer
import logging
from typing import List, Dict, Any # Added Optional, Dict, Any

# Use absolute imports for clarity
from pydantic_llm_tester.cli.core import provider_logic, llm_model_logic as model_logic

logger = logging.getLogger(__name__)

# Create a Typer app for the main 'providers' command group
app = typer.Typer(
    name="providers",
    help="Manage LLM providers (discover, enable, disable) and their specific LLM py_models."
)

# --- Top-level Provider Commands ---

@app.command("list")
def list_providers():
    """
    List all discoverable providers and their enabled/disabled status.

    Status is based on the presence and content of 'enabled_providers.json'
    in the project root. If the file doesn't exist, all providers are enabled.
    """
    logger.info("Executing 'providers list' command.")
    status_dict = provider_logic.get_enabled_status()

    if not status_dict:
        print("No providers discovered in 'src/llms/'.")
        return

    enabled_file_path = provider_logic.get_enabled_providers_path()
    if not os.path.exists(enabled_file_path):
         print("No 'enabled_providers.json' found. All discovered providers are considered enabled:")
    else:
         print(f"Provider Status (based on '{provider_logic.ENABLED_PROVIDERS_FILENAME}'):")

    # Sort by provider name for consistent output
    sorted_providers = sorted(status_dict.keys())

    for provider in sorted_providers:
        status = "Enabled" if status_dict[provider] else "Disabled"
        print(f"  - {provider} ({status})")

@app.command("enable")
def enable_provider(
    provider_name: str = typer.Argument(..., help="Name of the provider to enable.")
):
    """
    Enable a specific provider by adding it to 'enabled_providers.json'.

    Creates the file if it doesn't exist.
    """
    logger.info(f"Executing 'providers enable' for provider: {provider_name}")
    success, message = provider_logic.enable_provider(provider_name)
    if success:
        print(message)
    else:
        print(f"Error: {message}")
        raise typer.Exit(code=1)

@app.command("disable")
def disable_provider(
    provider_name: str = typer.Argument(..., help="Name of the provider to disable.")
):
    """
    Disable a specific provider by removing it from 'enabled_providers.json'.
    """
    logger.info(f"Executing 'providers disable' for provider: {provider_name}")
    success, message = provider_logic.disable_provider(provider_name)
    # Disabling is often not considered an error even if already disabled or file missing
    print(message)
    if not success:
        # Raise exit code only on actual write errors
        raise typer.Exit(code=1)

# --- 'manage' Subcommand Group for LLM Models ---

manage_app = typer.Typer(
    name="manage",
    help="Manage LLM py_models for a specific provider (list, enable, disable, update)."
)
app.add_typer(manage_app, name="manage") # Add 'manage' as a subcommand of 'providers'

@manage_app.command("list")
def list_llm_models(
    provider: str = typer.Argument(..., help="Name of the provider whose LLM py_models to list.")
):
    """
    List LLM py_models for a specific provider and their enabled/disabled status.

    Reads the 'enabled' flag from the provider's config.json.
    Defaults to enabled=True if the flag is missing.
    """
    logger.info(f"Executing 'providers manage list' for provider: {provider}")
    models: List[Dict[str, Any]] = model_logic.get_models_from_provider(provider)

    if not models:
        # Error message already logged by get_models_from_provider if config was missing/invalid
        print(f"No LLM py_models found or configuration error for provider '{provider}'.")
        return

    print(f"LLM Models for provider '{provider}':")
    for model in models:
        name = model.get('name', 'N/A')
        # Default to True if 'enabled' key is missing
        enabled = model.get('enabled', True)
        status = "Enabled" if enabled else "Disabled"
        print(f"  - {name} ({status})")

@manage_app.command("enable")
def enable_llm_model(
    provider: str = typer.Argument(..., help="Name of the provider."),
    model_name: str = typer.Argument(..., help="Name of the LLM model to enable.")
):
    """
    Enable a specific LLM model within its provider's config file.

    Sets the 'enabled' flag to true in the provider's config.json.
    """
    logger.info(f"Executing 'providers manage enable' for: {provider}/{model_name}")
    # No need to parse ID here, provider and model are separate args
    success, message = model_logic.set_model_enabled_status(provider, model_name, enabled=True)
    print(message)
    if not success:
        raise typer.Exit(code=1)

@manage_app.command("disable")
def disable_llm_model(
    provider: str = typer.Argument(..., help="Name of the provider."),
    model_name: str = typer.Argument(..., help="Name of the LLM model to disable.")
):
    """
    Disable a specific LLM model within its provider's config file.

    Sets the 'enabled' flag to false in the provider's config.json.
    """
    logger.info(f"Executing 'providers manage disable' for: {provider}/{model_name}")
    success, message = model_logic.set_model_enabled_status(provider, model_name, enabled=False)
    print(message)
    if not success:
        raise typer.Exit(code=1)

@manage_app.command("update")
def update_llm_models(
    provider: str = typer.Argument(..., help="Provider whose LLM py_models to update from API (currently only 'openrouter').")
):
    """
    Update LLM model details (cost, limits) from the provider's API.

    Currently only supports 'openrouter'. Fetches latest data and merges it
    with the existing config.json, preserving flags like 'enabled'.
    """
    logger.info(f"Executing 'providers manage update' for provider: {provider}")

    # Confirmation prompt before proceeding
    confirm = typer.confirm(f"This will fetch data from '{provider}' API and potentially overwrite parts of its config.json. Proceed?", abort=True)

    success, message = model_logic.update_provider_models_from_api(provider)
    print(message)
    if not success:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    # Allows running the subcommand module directly for testing (optional)
    # e.g., python -m src.cli.commands.providers list
    # e.g., python -m src.cli.commands.providers manage list openrouter
    app()
