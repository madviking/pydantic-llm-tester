"""CLI command for querying model prices from OpenRouter API."""

import typer
import logging
from typing import List, Optional
from enum import Enum

from pydantic_llm_tester.cli.core import price_query_logic

logger = logging.getLogger(__name__)

# Create a Typer app for the 'prices' command group
app = typer.Typer(
    name="prices",
    help="Query and display model prices from the model registry."
)

class SortField(str, Enum):
    """Enum for sort field options."""
    TOTAL_COST = "total_cost"
    NAME = "name"
    PROVIDER = "provider"
    CONTEXT_LENGTH = "context_length"
    INPUT_COST = "cost_input"
    OUTPUT_COST = "cost_output"

@app.command("list")
def list_prices(
    providers: Optional[List[str]] = typer.Option(
        None, "--providers", "-p", 
        help="Filter by provider names (e.g., openrouter, openai).",
        autocompletion=price_query_logic.get_available_providers_for_suggestions
    ),
    model_pattern: Optional[str] = typer.Option(
        None, "--model", "-m",
        help="Filter by model name pattern (regex)."
    ),
    max_cost: Optional[float] = typer.Option(
        None, "--max-cost",
        help="Filter by maximum cost per 1M tokens (input + output combined)."
    ),
    min_context: Optional[int] = typer.Option(
        None, "--min-context",
        help="Filter by minimum context length (input + output tokens)."
    ),
    sort_by: SortField = typer.Option(
        SortField.TOTAL_COST, "--sort-by", "-s",
        help="Field to sort results by."
    ),
    ascending: bool = typer.Option(
        True, "--asc/--desc",
        help="Sort in ascending (--asc) or descending (--desc) order."
    ),
    show_all: bool = typer.Option(
        False, "--all",
        help="Show all available models, not just configured ones."
    ),
):
    """
    List and filter model prices from all enabled providers in the model registry.
    
    Prices are shown per 1M tokens in USD. This information is sourced from the 
    central model registry, which gets updated when OpenRouter is enabled.
    """
    logger.info("Executing 'prices list' command")
    
    # Get model prices with filters
    models = price_query_logic.get_all_model_prices(
        provider_filter=providers,
        model_pattern=model_pattern,
        max_cost=max_cost,
        min_context_length=min_context,
        show_all_models=show_all
    )
    
    # Display results
    price_query_logic.display_model_prices(
        models=models,
        sort_by=sort_by.value,
        ascending=ascending
    )

@app.command("refresh")
def refresh_prices():
    """
    Refresh model information in the registry.
    
    This forces a refresh of the cache, and if OpenRouter is enabled,
    fetches the latest pricing and model data from the OpenRouter API.
    """
    logger.info("Executing 'prices refresh' command")
    
    # Confirm before proceeding
    confirm = typer.confirm("This will fetch fresh data from OpenRouter API. Proceed?", abort=True)
    
    # Refresh prices
    success, message = price_query_logic.refresh_openrouter_models()
    
    if success:
        typer.echo(typer.style(message, fg=typer.colors.GREEN))
    else:
        typer.echo(typer.style(f"Error: {message}", fg=typer.colors.RED))
        raise typer.Exit(code=1)

if __name__ == "__main__":
    # Allows running the subcommand module directly for testing
    app()