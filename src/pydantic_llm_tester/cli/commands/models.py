"""CLI command for managing LLM models for providers."""

import typer
import logging
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum

# Use absolute imports for clarity
from pydantic_llm_tester.cli.core import model_config_logic
from pydantic_llm_tester.cli.core import provider_logic

logger = logging.getLogger(__name__)

# Create a Typer app for the main 'models' command group
app = typer.Typer(
    name="models",
    help="Manage LLM models for providers (add, edit, remove, list)."
)

class CostCategory(str, Enum):
    """Cost categories for models"""
    CHEAP = "cheap"
    STANDARD = "standard"
    EXPENSIVE = "expensive"

# --- Top-level Model Commands ---

@app.command("list")
def list_models(
    provider: str = typer.Argument(..., help="Name of the provider whose models to list.")
):
    """
    List all models for a specific provider and their configuration.
    """
    logger.info(f"Executing 'models list' command for provider: {provider}")
    
    # Check if provider exists
    if provider not in provider_logic.get_discovered_providers():
        print(f"Error: Provider '{provider}' not found.")
        raise typer.Exit(code=1)
    
    # Get provider config
    config_data = model_config_logic.get_provider_config(provider)
    if not config_data:
        print(f"Error: Could not load configuration for provider '{provider}'.")
        raise typer.Exit(code=1)
    
    # Get models
    models = config_data.get("llm_models", [])
    if not models:
        print(f"No models found for provider '{provider}'.")
        return
    
    print(f"Models for provider '{provider}':")
    for model in models:
        name = model.get("name", "N/A")
        default = "Default" if model.get("default", False) else ""
        preferred = "Preferred" if model.get("preferred", False) else ""
        enabled = "Enabled" if model.get("enabled", True) else "Disabled"
        cost_input = model.get("cost_input", 0.0)
        cost_output = model.get("cost_output", 0.0)
        cost_category = model.get("cost_category", "standard")
        
        status = []
        if default:
            status.append(default)
        if preferred:
            status.append(preferred)
        status.append(enabled)
        
        print(f"  - {name} ({', '.join(status)})")
        print(f"    Cost: ${cost_input}/1M input tokens, ${cost_output}/1M output tokens ({cost_category})")
        print(f"    Max tokens: {model.get('max_input_tokens', 'N/A')} input, {model.get('max_output_tokens', 'N/A')} output")

@app.command("add")
def add_model(
    provider: str = typer.Argument(..., help="Name of the provider to add the model to."),
    name: str = typer.Option(..., "--name", "-n", help="Name of the model."),
    default: bool = typer.Option(False, "--default", "-d", help="Set as default model for the provider."),
    preferred: bool = typer.Option(False, "--preferred", "-p", help="Mark as preferred model."),
    enabled: bool = typer.Option(True, "--enabled", "-e", help="Enable the model."),
    cost_input: float = typer.Option(..., "--cost-input", "-i", help="Cost per 1M input tokens in USD."),
    cost_output: float = typer.Option(..., "--cost-output", "-o", help="Cost per 1M output tokens in USD."),
    cost_category: CostCategory = typer.Option(CostCategory.STANDARD, "--cost-category", "-c", help="Cost category."),
    max_input_tokens: int = typer.Option(4096, "--max-input", help="Maximum input tokens supported."),
    max_output_tokens: int = typer.Option(4096, "--max-output", help="Maximum output tokens supported."),
    interactive: bool = typer.Option(False, "--interactive", help="Use interactive mode with prompts.")
):
    """
    Add a new model to a provider's configuration.
    """
    logger.info(f"Executing 'models add' command for provider: {provider}")
    
    # Check if provider exists
    if provider not in provider_logic.get_discovered_providers():
        print(f"Error: Provider '{provider}' not found.")
        raise typer.Exit(code=1)
    
    # If interactive mode, prompt for values
    if interactive:
        name, model_config = _prompt_for_model_config(provider, None)
    else:
        # Create model config from arguments
        model_config = {
            "name": name,
            "default": default,
            "preferred": preferred,
            "enabled": enabled,
            "cost_input": cost_input,
            "cost_output": cost_output,
            "cost_category": cost_category.value,
            "max_input_tokens": max_input_tokens,
            "max_output_tokens": max_output_tokens
        }
    
    # Add model to provider
    success, message = model_config_logic.add_model_to_provider(provider, name, model_config)
    
    # If model is set as default, update other models
    if success and model_config.get("default", False):
        default_success, default_message = model_config_logic.set_default_model(provider, name)
        if not default_success:
            print(f"Warning: {default_message}")
    
    print(message)
    if not success:
        raise typer.Exit(code=1)

@app.command("edit")
def edit_model(
    provider: str = typer.Argument(..., help="Name of the provider."),
    name: str = typer.Argument(..., help="Name of the model to edit."),
    default: Optional[bool] = typer.Option(None, "--default", "-d", help="Set as default model for the provider."),
    preferred: Optional[bool] = typer.Option(None, "--preferred", "-p", help="Mark as preferred model."),
    enabled: Optional[bool] = typer.Option(None, "--enabled", "-e", help="Enable the model."),
    cost_input: Optional[float] = typer.Option(None, "--cost-input", "-i", help="Cost per 1M input tokens in USD."),
    cost_output: Optional[float] = typer.Option(None, "--cost-output", "-o", help="Cost per 1M output tokens in USD."),
    cost_category: Optional[CostCategory] = typer.Option(None, "--cost-category", "-c", help="Cost category."),
    max_input_tokens: Optional[int] = typer.Option(None, "--max-input", help="Maximum input tokens supported."),
    max_output_tokens: Optional[int] = typer.Option(None, "--max-output", help="Maximum output tokens supported."),
    interactive: bool = typer.Option(False, "--interactive", help="Use interactive mode with prompts.")
):
    """
    Edit an existing model in a provider's configuration.
    """
    logger.info(f"Executing 'models edit' command for provider: {provider}, model: {name}")
    
    # Check if provider exists
    if provider not in provider_logic.get_discovered_providers():
        print(f"Error: Provider '{provider}' not found.")
        raise typer.Exit(code=1)
    
    # Get current model config
    current_config = model_config_logic.get_model_from_provider(provider, name)
    if not current_config:
        print(f"Error: Model '{name}' not found in provider '{provider}'.")
        raise typer.Exit(code=1)
    
    # If interactive mode, prompt for values
    if interactive:
        _, updated_config = _prompt_for_model_config(provider, current_config)
    else:
        # Update model config from arguments, preserving existing values if not specified
        updated_config = current_config.copy()
        if default is not None:
            updated_config["default"] = default
        if preferred is not None:
            updated_config["preferred"] = preferred
        if enabled is not None:
            updated_config["enabled"] = enabled
        if cost_input is not None:
            updated_config["cost_input"] = cost_input
        if cost_output is not None:
            updated_config["cost_output"] = cost_output
        if cost_category is not None:
            updated_config["cost_category"] = cost_category.value
        if max_input_tokens is not None:
            updated_config["max_input_tokens"] = max_input_tokens
        if max_output_tokens is not None:
            updated_config["max_output_tokens"] = max_output_tokens
    
    # Edit model in provider
    success, message = model_config_logic.edit_model_in_provider(provider, name, updated_config)
    
    # If model is set as default, update other models
    if success and updated_config.get("default", False):
        default_success, default_message = model_config_logic.set_default_model(provider, name)
        if not default_success:
            print(f"Warning: {default_message}")
    
    print(message)
    if not success:
        raise typer.Exit(code=1)

@app.command("remove")
def remove_model(
    provider: str = typer.Argument(..., help="Name of the provider."),
    name: str = typer.Argument(..., help="Name of the model to remove.")
):
    """
    Remove a model from a provider's configuration.
    """
    logger.info(f"Executing 'models remove' command for provider: {provider}, model: {name}")
    
    # Check if provider exists
    if provider not in provider_logic.get_discovered_providers():
        print(f"Error: Provider '{provider}' not found.")
        raise typer.Exit(code=1)
    
    # Confirm removal
    confirm = typer.confirm(f"Are you sure you want to remove model '{name}' from provider '{provider}'?")
    if not confirm:
        print("Operation cancelled.")
        return
    
    # Remove model from provider
    success, message = model_config_logic.remove_model_from_provider(provider, name)
    print(message)
    if not success:
        raise typer.Exit(code=1)

@app.command("set-default")
def set_default(
    provider: str = typer.Argument(..., help="Name of the provider."),
    name: str = typer.Argument(..., help="Name of the model to set as default.")
):
    """
    Set a model as the default for a provider.
    """
    logger.info(f"Executing 'models set-default' command for provider: {provider}, model: {name}")
    
    # Check if provider exists
    if provider not in provider_logic.get_discovered_providers():
        print(f"Error: Provider '{provider}' not found.")
        raise typer.Exit(code=1)
    
    # Set model as default
    success, message = model_config_logic.set_default_model(provider, name)
    print(message)
    if not success:
        raise typer.Exit(code=1)

# --- Helper Functions ---

def _prompt_for_model_config(provider: str, current_config: Optional[Dict[str, Any]]) -> Tuple[str, Dict[str, Any]]:
    """
    Prompt the user for model configuration values.
    
    Args:
        provider: The name of the provider.
        current_config: The current model configuration, if editing an existing model.
        
    Returns:
        Tuple of (model_name, model_config).
    """
    is_edit = current_config is not None
    action = "Editing" if is_edit else "Adding"
    
    print(f"\n--- {action} Model for Provider: {provider} ---")
    
    # Start with template or current config
    if is_edit:
        model_config = current_config.copy()
        default_name = model_config.get("name", "")
    else:
        model_config = model_config_logic.get_model_template()
        default_name = ""
    
    # Prompt for values
    name = typer.prompt("Model name", default=default_name)
    
    # For editing, show current values as defaults
    if is_edit:
        model_config["default"] = typer.confirm(
            "Set as default model?", 
            default=model_config.get("default", False)
        )
        model_config["preferred"] = typer.confirm(
            "Mark as preferred model?", 
            default=model_config.get("preferred", False)
        )
        model_config["enabled"] = typer.confirm(
            "Enable model?", 
            default=model_config.get("enabled", True)
        )
        model_config["cost_input"] = typer.prompt(
            "Cost per 1M input tokens (USD)", 
            default=model_config.get("cost_input", 0.0), 
            type=float
        )
        model_config["cost_output"] = typer.prompt(
            "Cost per 1M output tokens (USD)", 
            default=model_config.get("cost_output", 0.0), 
            type=float
        )
        
        # For cost category, show options
        print("\nCost categories:")
        print("1. cheap")
        print("2. standard")
        print("3. expensive")
        
        current_category = model_config.get("cost_category", "standard")
        category_map = {"1": "cheap", "2": "standard", "3": "expensive"}
        category_default = next((k for k, v in category_map.items() if v == current_category), "2")
        
        category_choice = typer.prompt(
            "Select cost category",
            default=category_default
        )
        if category_choice not in category_map:
            print(f"Warning: Invalid category choice '{category_choice}'. Using 'standard' instead.")
        model_config["cost_category"] = category_map.get(category_choice, "standard")
        
        model_config["max_input_tokens"] = typer.prompt(
            "Maximum input tokens", 
            default=model_config.get("max_input_tokens", 4096), 
            type=int
        )
        model_config["max_output_tokens"] = typer.prompt(
            "Maximum output tokens", 
            default=model_config.get("max_output_tokens", 4096), 
            type=int
        )
    else:
        # For new models, don't show defaults
        model_config["default"] = typer.confirm("Set as default model?")
        model_config["preferred"] = typer.confirm("Mark as preferred model?")
        model_config["enabled"] = typer.confirm("Enable model?", default=True)
        model_config["cost_input"] = typer.prompt("Cost per 1M input tokens (USD)", type=float)
        model_config["cost_output"] = typer.prompt("Cost per 1M output tokens (USD)", type=float)
        
        # For cost category, show options
        print("\nCost categories:")
        print("1. cheap")
        print("2. standard")
        print("3. expensive")
        
        category_choice = typer.prompt("Select cost category", default="2")
        category_map = {"1": "cheap", "2": "standard", "3": "expensive"}
        if category_choice not in category_map:
            print(f"Warning: Invalid category choice '{category_choice}'. Using 'standard' instead.")
        model_config["cost_category"] = category_map.get(category_choice, "standard")
        
        model_config["max_input_tokens"] = typer.prompt("Maximum input tokens", default=4096, type=int)
        model_config["max_output_tokens"] = typer.prompt("Maximum output tokens", default=4096, type=int)
    
    return name, model_config


if __name__ == "__main__":
    # Allows running the subcommand module directly for testing
    # e.g., python -m src.cli.commands.models list openai
    app()