"""Logic for querying and displaying model prices from OpenRouter API."""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich import box

from pydantic_llm_tester.llms.provider_factory import (
    get_available_providers,
    _fetch_openrouter_models_with_cache,
    load_provider_config
)
from pydantic_llm_tester.llms.llm_registry import LLMRegistry, get_all_model_details  # Import LLMRegistry and get_all_model_details
from pydantic_llm_tester.llms.base import ModelConfig # Import ModelConfig

logger = logging.getLogger(__name__)
console = Console()

def get_all_model_prices(
    provider_filter: Optional[List[str]] = None,
    model_pattern: Optional[str] = None,
    max_cost: Optional[float] = None,
    min_context_length: Optional[int] = None,
    show_all_models: bool = False
) -> List[Dict[str, Any]]:
    """
    Get pricing information for all models from the LLMRegistry, with optional filtering.

    Args:
        provider_filter: Optional list of provider names to filter by
        model_pattern: Optional regex pattern to filter model names
        max_cost: Optional maximum cost per 1M tokens (input + output combined)
        min_context_length: Optional minimum context length
        show_all_models: If True, show all available models; if False, show only configured models

    Returns:
        List of dictionaries containing model pricing information
    """
    # Use the global function we added to get all model details
    # Only show configured models by default
    all_models_from_registry = get_all_model_details(only_configured=not show_all_models)
    
    if show_all_models:
        logger.debug(f"Retrieved all {len(all_models_from_registry)} models from registry")
    else:
        logger.debug(f"Retrieved {len(all_models_from_registry)} configured models from registry")

    # Apply provider filter if specified
    if provider_filter:
        filtered_models = [
            model for model in all_models_from_registry
            if model.provider in provider_filter
        ]
        if not filtered_models:
            logger.warning(f"No matching providers found for filter: {provider_filter}")
            return []
    else:
        filtered_models = all_models_from_registry

    # Compile regex pattern if specified
    pattern = None
    if model_pattern:
        try:
            pattern = re.compile(model_pattern, re.IGNORECASE)
        except re.error as e:
            logger.error(f"Invalid regex pattern: {model_pattern}. Error: {e}")
            return []

    # Apply remaining filters and format data
    final_models = []
    for model in filtered_models:
        # Skip disabled models
        if not model.enabled:
            continue

        # Apply model name pattern filter if specified
        if pattern and not pattern.search(model.name):
            continue

        # Calculate total cost (handle None values)
        cost_input = model.cost_input if model.cost_input is not None else 0.0
        cost_output = model.cost_output if model.cost_output is not None else 0.0
        total_cost = cost_input + cost_output

        # Apply max cost filter if specified
        if max_cost is not None and total_cost > max_cost:
            continue

        # Calculate context length (handle None values)
        input_tokens = model.max_input_tokens if model.max_input_tokens is not None else 0
        output_tokens = model.max_output_tokens if model.max_output_tokens is not None else 0
        context_length = input_tokens + output_tokens

        # Apply min context length filter if specified
        if min_context_length is not None and context_length < min_context_length:
            continue

        # Add model to results
        model_info = {
            "provider": model.provider,
            "name": model.name,
            "cost_input": cost_input,
            "cost_output": cost_output,
            "total_cost": total_cost,
            "context_length": context_length,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_category": model.cost_category # Assuming cost_category is available in ModelConfig
        }
        final_models.append(model_info)

    return final_models

def display_model_prices(
    models: List[Dict[str, Any]],
    sort_by: str = "total_cost",
    ascending: bool = True
) -> None:
    """
    Display model pricing information in a formatted table.
    
    Args:
        models: List of model information dictionaries
        sort_by: Field to sort by (total_cost, name, provider, context_length)
        ascending: Whether to sort in ascending order
    """
    if not models:
        console.print("[yellow]No models found matching the specified criteria.[/yellow]")
        return
    
    # Sort models
    valid_sort_fields = ["total_cost", "name", "provider", "context_length", "cost_input", "cost_output"]
    if sort_by not in valid_sort_fields:
        logger.warning(f"Invalid sort field: {sort_by}. Using 'total_cost' instead.")
        console.print(f"[yellow]Warning: Invalid sort field '{sort_by}'. Using 'total_cost' instead.[/yellow]")
        sort_by = "total_cost"
    
    sorted_models = sorted(models, key=lambda x: x[sort_by], reverse=not ascending)
    
    # Create table
    table = Table(
        title="LLM Model Pricing (cost per 1M tokens in USD)",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan"
    )
    
    # Add columns
    table.add_column("Provider", style="green")
    table.add_column("Model", style="blue")
    table.add_column("Input Cost", justify="right")
    table.add_column("Output Cost", justify="right")
    table.add_column("Total Cost", justify="right")
    table.add_column("Context Length", justify="right")
    table.add_column("Category", style="magenta")
    
    # Add rows
    for model in sorted_models:
        # Format costs with color based on price
        input_cost = f"${model['cost_input']:.2f}"
        output_cost = f"${model['cost_output']:.2f}"
        total_cost = f"${model['total_cost']:.2f}"
        
        # Color code the total cost
        if model['total_cost'] == 0:
            total_cost_text = Text(total_cost, style="green")
        elif model['total_cost'] < 5.0:
            total_cost_text = Text(total_cost, style="green")
        elif model['total_cost'] < 20.0:
            total_cost_text = Text(total_cost, style="yellow")
        else:
            total_cost_text = Text(total_cost, style="red")
        
        table.add_row(
            model['provider'],
            model['name'],
            input_cost,
            output_cost,
            total_cost_text,
            f"{model['context_length']:,}",
            model['cost_category']
        )
    
    # Print table
    console.print(table)
    console.print(f"\nTotal models: {len(models)}")

def get_available_providers_for_suggestions() -> List[str]:
    """
    Get a list of available providers for autocomplete suggestions.
    
    Returns:
        List of provider names
    """
    return get_available_providers()

def refresh_openrouter_models() -> Tuple[bool, str]:
    """
    Force refresh of OpenRouter models from API.
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Clear registry cache
        from pydantic_llm_tester.llms.provider_factory import reset_caches
        reset_caches()
        
        # Force refresh of OpenRouter models
        from pydantic_llm_tester.utils.config_manager import ConfigManager
        config_manager = ConfigManager()
        
        if config_manager.is_openrouter_enabled():
            # Fetch and process the OpenRouter models
            models_data = config_manager.fetch_and_process_openrouter_models(force=True)
            
            if not models_data:
                logger.warning("OpenRouter API returned no valid model data")
                return False, "OpenRouter API returned no valid model data"
                
            # Get count of models for reporting
            model_count = len(models_data) if isinstance(models_data, list) else (
                len(models_data.get("data", [])) if isinstance(models_data, dict) else 0
            )
            
            return True, f"Successfully refreshed {model_count} models from OpenRouter API"
        else:
            return False, "OpenRouter provider is not enabled in configuration."
    except Exception as e:
        logger.error(f"Error refreshing OpenRouter models: {e}")
        return False, f"Error refreshing OpenRouter models: {str(e)}"
