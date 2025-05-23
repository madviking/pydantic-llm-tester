import os

import typer
import logging
from typing import List, Dict, Any # Added Optional, Dict, Any

# Use absolute imports for clarity
from pydantic_llm_tester.cli.core import provider_logic

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

    Status is based on the 'enabled' flag in the pyllm_config.json file.
    """
    logger.info("Executing 'providers list' command.")
    status_dict = provider_logic.get_enabled_status()

    if not status_dict:
        print("No providers discovered in 'src/llms/'.")
        return

    print("Provider Status (based on pyllm_config.json):")

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
    Enable a specific provider by setting its 'enabled' flag to true in pyllm_config.json.
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
    Disable a specific provider by setting its 'enabled' flag to false in pyllm_config.json.
    """
    logger.info(f"Executing 'providers disable' for provider: {provider_name}")
    success, message = provider_logic.disable_provider(provider_name)
    # Disabling is often not considered an error even if already disabled or file missing
    print(message)
    if not success:
        # Raise exit code only on actual write errors
        raise typer.Exit(code=1)

# Removed 'manage' subcommand and its associated commands (list, enable, disable, update)
# as per the refactoring plan to remove LLM model management from the CLI.


if __name__ == "__main__":
    # Allows running the subcommand module directly for testing (optional)
    # e.g., python -m src.cli.commands.providers list
    app()
