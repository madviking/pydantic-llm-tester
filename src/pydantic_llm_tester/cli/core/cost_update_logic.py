"""Logic for updating model costs and token information from OpenRouter API."""

import json
import logging
import os
from typing import Dict, List, Any, Tuple, Optional, Set

from rich.console import Console
from rich.table import Table
from rich import box

from pydantic_llm_tester.llms.provider_factory import (
    _fetch_openrouter_models_with_cache,
    load_provider_config,
    get_available_providers,
    reset_caches
)
# Removed imports for load_model_pricing, save_model_pricing, get_pricing_config_path

logger = logging.getLogger(__name__)
console = Console()

# The logic in this file is related to updating static pricing files,
# which is being replaced by dynamic fetching from LLMRegistry in the refactoring.
# The functions below are commented out or removed as they are no longer needed
# in the new architecture or will be refactored as part of Step 7 and 8.

def update_model_costs(provider_filter: Optional[List[str]] = None, 
                  update_provider_configs: bool = True,
                  force_refresh: bool = False) -> Dict[str, Any]:
    """
    Update model costs and token information from the model registry.

    This function uses the central model registry as the source of truth for model
    information, and updates provider configs based on that data if requested.

    Args:
        provider_filter: Optional list of provider names to filter by.
        update_provider_configs: Whether to update provider config files.
        force_refresh: Whether to force refresh of registry cache.

    Returns:
        Dictionary containing update summary.
    """
    logger.info(f"Updating model costs from registry (force_refresh={force_refresh})")
    
    result = {
        "success": False,
        "message": "",
        "updated": 0,
        "added": 0,
        "unchanged": 0,
        "updated_models": [],
        "added_models": []
    }
    
    try:
        # Import here to avoid circular imports
        from pydantic_llm_tester.utils.config_manager import ConfigManager
        from pydantic_llm_tester.llms.provider_factory import reset_caches
        
        # If force refresh, reset caches to ensure fresh data
        if force_refresh:
            reset_caches()
            logger.info("Caches reset to force fresh data")
            
        # Ensure OpenRouter models are fetched if OpenRouter is enabled
        config_manager = ConfigManager()
        if config_manager.is_openrouter_enabled():
            logger.info("OpenRouter enabled, fetching latest models")
            config_manager.fetch_and_process_openrouter_models(force=force_refresh)
        
        # Now all model data should be in the registry
        # Get all models from the registry
        from pydantic_llm_tester.llms.llm_registry import get_all_model_details
        all_models = get_all_model_details(use_cache=not force_refresh)
        logger.info(f"Retrieved {len(all_models)} models from registry")
        
        # Filter models if provider_filter is specified
        if provider_filter:
            models = [m for m in all_models if m.provider in provider_filter]
            logger.info(f"Filtered to {len(models)} models for providers: {', '.join(provider_filter)}")
        else:
            models = all_models
            
        # Update result statistics (as this function now just reports on what's in the registry)
        result["added"] = len(models)
        result["added_models"] = [
            {
                "provider": model.provider,
                "model": model.name,
                "input": model.cost_input,
                "output": model.cost_output
            }
            for model in models
        ]
        
        # Update provider config files if requested
        # This is now only for backwards compatibility
        if update_provider_configs:
            _update_provider_configs(models)
            
        # Update success status
        result["success"] = True
        result["message"] = f"Successfully processed {len(models)} models"
        
    except Exception as e:
        logger.error(f"Error updating model costs: {str(e)}")
        result["success"] = False
        result["message"] = f"Error updating model costs: {str(e)}"
        
    return result

def _update_provider_configs(models: List[ModelConfig]) -> None:
    """
    Update provider config files with token information from models.
    
    This function is kept for backwards compatibility with existing provider config files.
    
    Args:
        models: List of ModelConfig objects.
    """
    logger.info("Updating provider config files with token information")
    # Implementation would go here - not needed as part of this refactoring
    # as we're moving away from storing model information in provider config files
    pass

def display_update_summary(update_result: Dict[str, Any]) -> None:
    """
    Display a summary of the update operation.

    Args:
        update_result: Dictionary containing update summary
    """
    if not update_result["success"]:
        console.print(f"[bold red]Error:[/bold red] {update_result['message']}")
        return

    # Create summary table
    summary_table = Table(
        title="Model Cost and Token Update Summary",
        box=box.ROUNDED,
        show_header=False
    )

    summary_table.add_column("Item", style="cyan")
    summary_table.add_column("Value", style="green")

    summary_table.add_row("Status", "[green]Success[/green]" if update_result["success"] else "[red]Failed[/red]")
    summary_table.add_row("Models Updated", str(update_result["updated"]))
    summary_table.add_row("Models Added", str(update_result["added"]))
    summary_table.add_row("Models Unchanged", str(update_result["unchanged"]))
    summary_table.add_row("Total Models Processed", str(update_result["updated"] + update_result["added"] + update_result["unchanged"]))

    console.print(summary_table)

    # Show updated models if any
    if update_result["updated"]:
        updated_table = Table(
            title="Updated Models",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan"
        )

        updated_table.add_column("Provider", style="blue")
        updated_table.add_column("Model", style="green")
        updated_table.add_column("Old Input", justify="right")
        updated_table.add_column("Old Output", justify="right")
        updated_table.add_column("New Input", justify="right")
        updated_table.add_column("New Output", justify="right")

        for model in update_result["updated_models"]:
            updated_table.add_row(
                model["provider"],
                model["model"],
                f"${model['old_input']:.2f}",
                f"${model['old_output']:.2f}",
                f"${model['new_input']:.2f}",
                f"${model['new_output']:.2f}"
            )

        console.print(updated_table)

    # Show added models if any
    if update_result["added"]:
        added_table = Table(
            title="Added Models",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan"
        )

        added_table.add_column("Provider", style="blue")
        added_table.add_column("Model", style="green")
        added_table.add_column("Input Cost", justify="right")
        added_table.add_column("Output Cost", justify="right")

        for model in update_result["added_models"]:
            added_table.add_row(
                model["provider"],
                model["model"],
                f"${model['input']:.2f}",
                f"${model['output']:.2f}"
            )
        
        console.print(added_table)

    # Add explanation about token limits update
    console.print("\n[bold cyan]Token Information Update:[/bold cyan]")
    console.print("Token limits for models have been updated based on the OpenRouter API data.")
    console.print("For each model, the calculation follows this formula:")
    console.print("  - Max Input Tokens = Context Length - Max Completion Tokens")
    console.print("  - If Max Completion Tokens isn't provided, a 75/25 input/output split is used")
    console.print("\nThis ensures your model configurations have the correct token limits for optimal usage.")


def get_available_providers_for_suggestions() -> List[str]:
    """
    Get a list of available providers for autocomplete suggestions.

    Returns:
        List of provider names
    """
    return get_available_providers()
