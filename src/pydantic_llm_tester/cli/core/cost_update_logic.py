"""Logic for updating model costs from OpenRouter API."""

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
from pydantic_llm_tester.utils.cost_manager import (
    load_model_pricing,
    save_model_pricing,
    get_pricing_config_path
)

logger = logging.getLogger(__name__)
console = Console()

def update_model_costs(
    provider_filter: Optional[List[str]] = None,
    update_provider_configs: bool = False,
    force_refresh: bool = False
) -> Dict[str, Any]:
    """
    Update model costs from OpenRouter API.
    
    Args:
        provider_filter: Optional list of provider names to filter by
        update_provider_configs: Whether to update provider config files with context length and other metadata
        force_refresh: Whether to force refresh the OpenRouter API cache
        
    Returns:
        Dictionary containing update summary
    """
    # Get all available providers
    all_providers = get_available_providers()
    
    # Apply provider filter if specified
    if provider_filter:
        providers = [p for p in all_providers if p in provider_filter]
        if not providers:
            logger.warning(f"No matching providers found for filter: {provider_filter}")
            return {
                "success": False,
                "message": f"No matching providers found for filter: {provider_filter}",
                "updated": 0,
                "added": 0,
                "unchanged": 0
            }
    else:
        providers = all_providers
    
    # Fetch models from OpenRouter API
    logger.info("Fetching models from OpenRouter API...")
    api_models_data = _fetch_openrouter_models_with_cache(force_refresh=force_refresh)
    
    if not api_models_data:
        logger.error("Failed to fetch models from OpenRouter API")
        return {
            "success": False,
            "message": "Failed to fetch models from OpenRouter API",
            "updated": 0,
            "added": 0,
            "unchanged": 0
        }
    
    # Load current pricing data
    current_pricing = load_model_pricing()
    
    # Track changes
    updated_models = []
    added_models = []
    unchanged_models = []
    
    # Process models from API
    for model_data in api_models_data:
        model_id = model_data.get("id")
        if not model_id:
            logger.debug("Skipping API model entry without an 'id'.")
            continue
        
        # Extract provider from model_id (format is usually provider/model_name)
        provider_name = model_id.split("/")[0] if "/" in model_id else None
        
        # Skip if not in filtered providers
        if provider_filter and provider_name not in provider_filter:
            continue
        
        # Skip if provider not recognized
        if provider_name not in providers:
            logger.debug(f"Skipping model {model_id} from unrecognized provider {provider_name}")
            continue
        
        # Extract pricing information
        pricing = model_data.get("pricing", {})
        cost_input_str = pricing.get("prompt", "0.0")
        cost_output_str = pricing.get("completion", "0.0")
        
        # Convert cost per token to cost per 1M tokens
        cost_input = float(cost_input_str) * 1_000_000 if cost_input_str else 0.0
        cost_output = float(cost_output_str) * 1_000_000 if cost_output_str else 0.0
        
        # Check if provider exists in current pricing
        if provider_name not in current_pricing:
            current_pricing[provider_name] = {}
        
        # Get model name (without provider prefix)
        model_name = model_id.split("/")[1] if "/" in model_id else model_id
        
        # Check if model exists in current pricing
        if model_name in current_pricing[provider_name]:
            # Check if pricing has changed
            current_input = current_pricing[provider_name][model_name].get("input", 0.0)
            current_output = current_pricing[provider_name][model_name].get("output", 0.0)
            
            if abs(current_input - cost_input) > 0.001 or abs(current_output - cost_output) > 0.001:
                # Update pricing
                current_pricing[provider_name][model_name] = {
                    "input": cost_input,
                    "output": cost_output
                }
                updated_models.append({
                    "provider": provider_name,
                    "model": model_name,
                    "old_input": current_input,
                    "old_output": current_output,
                    "new_input": cost_input,
                    "new_output": cost_output
                })
            else:
                unchanged_models.append({
                    "provider": provider_name,
                    "model": model_name,
                    "input": cost_input,
                    "output": cost_output
                })
        else:
            # Add new model
            current_pricing[provider_name][model_name] = {
                "input": cost_input,
                "output": cost_output
            }
            added_models.append({
                "provider": provider_name,
                "model": model_name,
                "input": cost_input,
                "output": cost_output
            })
    
    # Save updated pricing
    save_model_pricing(current_pricing)
    logger.info(f"Updated pricing information saved to {get_pricing_config_path()}")
    
    # Update provider config files if requested
    if update_provider_configs:
        _update_provider_configs(api_models_data, providers)
    
    # Reset caches to ensure new information is used immediately
    reset_caches()
    logger.info("Provider caches reset to ensure new information is used immediately")
    
    # Return summary
    return {
        "success": True,
        "message": f"Successfully updated pricing information for {len(updated_models)} models, added {len(added_models)} new models",
        "updated": len(updated_models),
        "added": len(added_models),
        "unchanged": len(unchanged_models),
        "updated_models": updated_models,
        "added_models": added_models,
        "unchanged_models": unchanged_models
    }

def _update_provider_configs(api_models_data: List[Dict[str, Any]], providers: List[str]) -> None:
    """
    Update provider config files with context length and other metadata.
    
    Args:
        api_models_data: List of model data from OpenRouter API
        providers: List of provider names to update
    """
    # Group models by provider
    provider_models = {}
    for model_data in api_models_data:
        model_id = model_data.get("id")
        if not model_id or "/" not in model_id:
            continue
        
        provider_name, model_name = model_id.split("/", 1)
        if provider_name not in providers:
            continue
        
        if provider_name not in provider_models:
            provider_models[provider_name] = []
        
        provider_models[provider_name].append((model_name, model_data))
    
    # Update each provider's config
    for provider_name, models in provider_models.items():
        # Load provider config
        provider_config = load_provider_config(provider_name)
        if not provider_config:
            logger.warning(f"Could not load config for provider: {provider_name}")
            continue
        
        # Create a map of existing models for easy lookup
        existing_models = {model.name: model for model in provider_config.llm_models}
        
        # Track changes
        updated_count = 0
        
        # Update each model
        for model_name, model_data in models:
            if model_name in existing_models:
                model_config = existing_models[model_name]
                
                # Update context length if available
                context_length = model_data.get("context_length")
                if context_length:
                    # OpenRouter API often provides max_completion_tokens within top_provider details
                    max_output_tokens_api = model_data.get("top_provider", {}).get("max_completion_tokens")
                    
                    if max_output_tokens_api is not None:
                        max_output_tokens = int(max_output_tokens_api)
                        max_input_tokens = int(context_length) - max_output_tokens
                        
                        # Ensure max_input_tokens is positive
                        if max_input_tokens <= 0:
                            max_input_tokens = max(1, int(context_length) // 2)
                            max_output_tokens = int(context_length) - max_input_tokens
                        
                        # Update model config
                        if model_config.max_input_tokens != max_input_tokens or model_config.max_output_tokens != max_output_tokens:
                            model_config.max_input_tokens = max_input_tokens
                            model_config.max_output_tokens = max_output_tokens
                            updated_count += 1
                    elif context_length != (model_config.max_input_tokens + model_config.max_output_tokens):
                        # If max_output_tokens not provided, split context length evenly
                        max_input_tokens = int(context_length) // 2
                        max_output_tokens = int(context_length) - max_input_tokens
                        
                        # Update model config
                        model_config.max_input_tokens = max_input_tokens
                        model_config.max_output_tokens = max_output_tokens
                        updated_count += 1
        
        # Save provider config if changes were made
        if updated_count > 0:
            # Save config file
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                      "llms", provider_name, "config.json")
            
            try:
                with open(config_path, 'w') as f:
                    json.dump(provider_config.model_dump(mode='json'), f, indent=2)
                logger.info(f"Updated {updated_count} models in {provider_name} config")
            except Exception as e:
                logger.error(f"Error saving config for provider {provider_name}: {e}")

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
        title="Model Cost Update Summary",
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

def get_available_providers_for_suggestions() -> List[str]:
    """
    Get a list of available providers for autocomplete suggestions.
    
    Returns:
        List of provider names
    """
    return get_available_providers()