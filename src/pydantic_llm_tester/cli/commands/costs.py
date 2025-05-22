"""CLI command for updating model costs and token information from OpenRouter API."""

import typer
import logging
from typing import List, Optional

from pydantic_llm_tester.cli.core import cost_update_logic

logger = logging.getLogger(__name__)

# Create a Typer app for the 'costs' command group
app = typer.Typer(
    name="costs",
    help="Update and manage model costs and token information from OpenRouter API."
)

@app.command("update")
def update_costs(
    providers: Optional[List[str]] = typer.Option(
        None, "--providers", "-p", 
        help="Filter by provider names (e.g., openrouter, openai).",
        autocompletion=cost_update_logic.get_available_providers_for_suggestions
    ),
    update_configs: bool = typer.Option(
        True, "--update-configs/--no-update-configs", "-u/-nu",
        help="Update provider config files with token information (context length, max input/output tokens) and other metadata."
    ),
    force: bool = typer.Option(
        False, "--force", "-f",
        help="Force refresh of OpenRouter API cache."
    ),
):
    """
    Update model costs and token information from OpenRouter API.
    
    This command fetches the latest model information from OpenRouter API and updates:
    1. Pricing information in models_pricing.json for cost tracking
    2. Token limits in provider config files using the formula:
       max_input_tokens = context_length - max_completion_tokens
    
    This ensures your model configurations have both accurate pricing and
    optimal token limits for each model.
    """
    logger.info("Executing 'costs update' command")
    
    # Confirm before proceeding
    confirm = typer.confirm(
        "This will update model costs and token information from OpenRouter API and modify configuration files. Proceed?", 
        abort=True
    )
    
    # Update model costs
    update_result = cost_update_logic.update_model_costs(
        provider_filter=providers,
        update_provider_configs=update_configs,
        force_refresh=force
    )
    
    # Display results
    cost_update_logic.display_update_summary(update_result)
    
    if not update_result["success"]:
        raise typer.Exit(code=1)

@app.command("reset-cache")
def reset_cache():
    """
    Reset provider caches to force rediscovery of models and pricing.
    
    This is useful if you've made manual changes to config files or
    if you're experiencing issues with cached data.
    """
    logger.info("Executing 'costs reset-cache' command")
    
    # Confirm before proceeding
    confirm = typer.confirm(
        "This will reset all provider caches. Proceed?", 
        abort=True
    )
    
    # Reset caches
    from pydantic_llm_tester.llms.provider_factory import reset_caches
    reset_caches()
    
    typer.echo(typer.style("Provider caches reset successfully.", fg=typer.colors.GREEN))

if __name__ == "__main__":
    # Allows running the subcommand module directly for testing
    app()